"""
Voice channel meeting transcription + summarization.
Uses discord-ext-voice-recv for audio capture from each speaker.
When an exec starts a meeting via /meeting start, the bot joins the voice channel,
records each speaker's audio separately, transcribes with Whisper, then posts a
Gemini-generated summary with per-user attribution when /meeting end is called.
"""

import asyncio
import io
import logging
import os
import struct
import tempfile
import wave
from collections import defaultdict
from pathlib import Path
from typing import Optional

import discord
from discord.ext import voice_recv
from discord.opus import OpusError
import discord.ext.voice_recv.opus as voice_recv_opus

logger = logging.getLogger(__name__)

# Active meeting sessions keyed by guild_id
_active_meetings: dict[int, "MeetingSession"] = {}
_VOICE_RECV_PATCHED = False
_CORRUPT_PACKET_COUNTS: dict[int, int] = defaultdict(int)
_RECOVERED_PACKET_COUNTS: dict[int, int] = defaultdict(int)


def _patch_voice_recv_corrupted_packets() -> None:
    """
    Guard discord-ext-voice-recv against Opus decode crashes.

    Some voice packets are occasionally corrupt on Discord's RTP stream. Without this
    patch, OpusError can crash PacketRouter and stop recording entirely.
    """
    global _VOICE_RECV_PATCHED
    if _VOICE_RECV_PATCHED:
        return

    original_decode = voice_recv_opus.PacketDecoder._decode_packet

    def _candidate_payload_slices(raw_bytes: bytes) -> list[bytes]:
        """Generate likely Opus payload slices when extra headers are present."""
        if not raw_bytes:
            return []

        candidates: list[bytes] = [raw_bytes]

        # RFC8285 one-byte extension profile (0xBEDE)
        if len(raw_bytes) >= 8 and raw_bytes[:2] == b"\xbe\xde":
            ext_words = int.from_bytes(raw_bytes[2:4], byteorder="big", signed=False)
            ext_offset = 4 + (ext_words * 4)
            if 0 < ext_offset < len(raw_bytes):
                candidates.append(raw_bytes[ext_offset:])

        # Generic short-prefix offsets observed in modern Discord RTP payloads.
        for off in (1, 2, 4, 8, 12, 16, 20, 24):
            if off < len(raw_bytes):
                candidates.append(raw_bytes[off:])

        # Deduplicate while preserving order
        uniq: list[bytes] = []
        seen = set()
        for c in candidates:
            key = (len(c), c[:8])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(c)
        return uniq

    def safe_decode(self, packet):
        samples = getattr(voice_recv_opus.Decoder, "SAMPLES_PER_FRAME", 960)
        silence = b"\x00" * samples * 2 * 2  # 48kHz, stereo, 16-bit, 20ms

        # Discord voice audio is Opus payload type 120. Non-audio RTP packets can
        # still appear; do not feed them into Opus decode.
        payload_type = getattr(packet, "payload", None)
        if payload_type is not None and payload_type != 120:
            return packet, silence

        try:
            return original_decode(self, packet)
        except OpusError as e:
            decoder = getattr(self, "_decoder", None)
            seq = getattr(packet, "sequence", "unknown")
            ssrc = getattr(self, "ssrc", "unknown")
            ssrc_key = ssrc if isinstance(ssrc, int) else -1
            raw = getattr(packet, "decrypted_data", None)
            raw_bytes = bytes(raw) if isinstance(raw, (bytes, bytearray)) else b""

            # Recovery path: try likely payload slices in case extra framing bytes
            # are present before Opus data.
            if decoder and raw_bytes:
                for idx, candidate in enumerate(_candidate_payload_slices(raw_bytes)):
                    try:
                        recovered_pcm = decoder.decode(candidate, fec=False)
                        _RECOVERED_PACKET_COUNTS[ssrc_key] += 1
                        if _RECOVERED_PACKET_COUNTS[ssrc_key] <= 5:
                            logger.warning(
                                "Recovered packet decode on ssrc=%s seq=%s candidate=%s orig_len=%s new_len=%s",
                                ssrc,
                                seq,
                                idx,
                                len(raw_bytes),
                                len(candidate),
                            )
                        return packet, recovered_pcm
                    except OpusError:
                        pass

            _CORRUPT_PACKET_COUNTS[ssrc_key] += 1
            count = _CORRUPT_PACKET_COUNTS[ssrc_key]
            logger.warning(
                "Skipping corrupted voice packet on ssrc=%s seq=%s payload=%s len=%s count=%s: %s",
                ssrc,
                seq,
                payload_type,
                len(raw_bytes),
                count,
                e,
            )
            return packet, silence

    voice_recv_opus.PacketDecoder._decode_packet = safe_decode
    _VOICE_RECV_PATCHED = True
    logger.info("Applied voice-recv corrupted packet guard")


_patch_voice_recv_corrupted_packets()


class UserAudioBuffer:
    """Accumulates raw PCM frames for a single user."""

    def __init__(self):
        self.frames: list[bytes] = []

    def write(self, data: bytes):
        self.frames.append(data)

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def byte_count(self) -> int:
        return sum(len(frame) for frame in self.frames)

    def to_wav_bytes(self) -> bytes:
        """Convert accumulated PCM frames to a WAV byte stream."""
        raw = b"".join(self.frames)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(2)       # Discord stereo
            wf.setsampwidth(2)       # 16-bit
            wf.setframerate(48000)   # 48kHz
            wf.writeframes(raw)
        return buf.getvalue()


class ClubmateSink(voice_recv.AudioSink):
    """Collects per-user PCM audio during a meeting."""

    def __init__(self):
        super().__init__()
        self.user_buffers: dict[int, UserAudioBuffer] = defaultdict(UserAudioBuffer)
        self._ssrc_to_user_id: dict[int, int] = {}

    def wants_opus(self) -> bool:
        return False  # We want decoded PCM

    def write(self, user: Optional[discord.Member], data: voice_recv.VoiceData):
        packet = getattr(data, "packet", None)
        ssrc = getattr(packet, "ssrc", None)

        if user is not None and ssrc is not None:
            self._ssrc_to_user_id[ssrc] = user.id

        if user is None:
            # If member mapping is late/missing, still retain audio by stable SSRC-derived ID.
            # This prevents complete audio loss when data.source is None.
            if ssrc is None:
                return
            user_id = self._ssrc_to_user_id.get(ssrc, -(ssrc + 1))
        else:
            user_id = user.id

        pcm = data.pcm
        if pcm:
            self.user_buffers[user_id].write(pcm)

    def cleanup(self):
        pass


class MeetingSession:
    def __init__(
        self,
        voice_client: discord.VoiceClient,
        summary_channel: discord.TextChannel,
        title: str,
    ):
        self.voice_client = voice_client
        self.summary_channel = summary_channel
        self.title = title
        self.sink = ClubmateSink()
        self._member_names: dict[int, str] = {}

    def start_recording(self):
        # Store member names at start time
        if self.voice_client.channel:
            for member in self.voice_client.channel.members:
                self._member_names[member.id] = member.display_name
        logger.info(
            "Starting voice capture: mode=%s channel=%s members=%d",
            getattr(self.voice_client, "mode", "unknown"),
            getattr(self.voice_client.channel, "name", "unknown"),
            len(self._member_names),
        )
        self.voice_client.listen(self.sink)

    async def stop_and_summarize(self):
        if self.voice_client.is_listening():
            self.voice_client.stop_listening()

        if self.voice_client.is_connected():
            await self.voice_client.disconnect()

        await _process_recording(
            self.sink,
            self.summary_channel,
            self.title,
            self._member_names,
        )


async def _process_recording(
    sink: ClubmateSink,
    summary_channel: discord.TextChannel,
    title: str,
    member_names: dict[int, str],
):
    """Transcribe per-user audio and post summary."""
    await summary_channel.send(f"Meeting **{title}** ended. Transcribing audio...")

    if not sink.user_buffers:
        await summary_channel.send("No audio was recorded in this meeting.")
        return

    transcripts: list[str] = []

    for user_id, buffer in sink.user_buffers.items():
        if user_id < 0:
            ssrc = -user_id - 1
            name = f"Speaker {ssrc}"
        else:
            name = member_names.get(user_id, f"User {user_id}")
        try:
            wav_bytes = buffer.to_wav_bytes()
            logger.info(
                "Transcribing %s: %d frames, %d PCM bytes, %d WAV bytes",
                name,
                buffer.frame_count,
                buffer.byte_count,
                len(wav_bytes),
            )
            text = await _transcribe(wav_bytes)
            if text.strip():
                transcripts.append(f"**{name}**: {text.strip()}")
        except Exception as e:
            logger.error("Transcription failed for %s: %s", name, e)
            transcripts.append(f"**{name}**: [transcription failed: {e}]")

    if not transcripts:
        await summary_channel.send("No speech detected in the meeting recording.")
        return

    full_transcript = "\n".join(transcripts)

    await summary_channel.send("Generating summary...")

    try:
        summary = await _summarize(full_transcript, title)
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        await summary_channel.send(f"Summarization failed: {e}")
        return

    await summary_channel.send(f"## Meeting Summary — {title}\n\n{summary}")

    await summary_channel.send("**Full Transcript:**")
    chunks = [full_transcript[i:i+1900] for i in range(0, len(full_transcript), 1900)]
    for chunk in chunks:
        await summary_channel.send(f"```\n{chunk}\n```")


async def _transcribe(wav_bytes: bytes) -> str:
    """Transcribe WAV bytes using Whisper (local or API)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from config import settings

    if settings.whisper_mode == "api":
        return await _transcribe_api(wav_bytes, settings.openai_api_key)
    else:
        return await asyncio.to_thread(_transcribe_local, wav_bytes)


def _transcribe_local(wav_bytes: bytes) -> str:
    """Transcribe using local Whisper model."""
    import whisper

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path)
        return result.get("text", "")
    finally:
        os.unlink(tmp_path)


async def _transcribe_api(wav_bytes: bytes, api_key: str) -> str:
    """Transcribe using OpenAI Whisper API."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("audio.wav", wav_bytes, "audio/wav")},
            data={"model": "whisper-1"},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("text", "")


async def _summarize(transcript: str, title: str) -> str:
    """Summarize the transcript using Gemini."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from config import settings
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"""You are summarizing meeting notes for a university club.

Meeting title: {title}

Transcript (format is "Speaker: what they said"):
{transcript}

Write a clear, structured meeting summary with:
1. **Key Discussion Points** — main topics covered
2. **Decisions Made** — any decisions or outcomes
3. **Action Items** — tasks assigned (include who if mentioned)
4. **Next Steps** — follow-ups or upcoming events mentioned

Be concise and use bullet points."""

    response = await client.aio.models.generate_content(
        model=settings.default_llm_model,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=2048),
    )
    return response.text


# ── Public API ────────────────────────────────────────────────────────────────

async def start_meeting(
    interaction: discord.Interaction,
    title: str,
    summary_channel: discord.TextChannel,
) -> str:
    guild_id = interaction.guild_id

    if guild_id in _active_meetings:
        return "A meeting is already in progress. Use `/meeting end` first."

    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        return "You must be in a voice channel to start a meeting."

    vc = None
    try:
        vc = await voice_state.channel.connect(
            cls=voice_recv.VoiceRecvClient,
            timeout=20.0,
            reconnect=False,
        )
    except discord.ClientException as e:
        msg = str(e)
        if "already connected" in msg.lower():
            return "Bot is already connected to a voice channel."
        return f"Failed to connect to voice: {e}"
    except Exception as e:
        logger.error("Voice connect failed: %s", e, exc_info=True)
        return (
            "Failed to connect to voice (Discord handshake error). "
            "Please try again in a few seconds."
        )

    if not vc or not vc.is_connected():
        if vc:
            try:
                await vc.disconnect(force=True)
            except Exception:
                pass
        return (
            "Voice connection was not established. "
            "Please retry `/meeting start`."
        )

    session = MeetingSession(vc, summary_channel, title)
    try:
        session.start_recording()
    except Exception as e:
        logger.error("Failed to start voice recording: %s", e, exc_info=True)
        try:
            if vc.is_connected():
                await vc.disconnect(force=True)
        except Exception:
            pass
        return f"Connected to voice but failed to start recording: {e}"

    _active_meetings[guild_id] = session

    return (
        f"Joined **{voice_state.channel.name}** and started recording **{title}**. "
        f"Summary will be posted to {summary_channel.mention} when you run `/meeting end`."
    )


async def end_meeting(interaction: discord.Interaction) -> str:
    guild_id = interaction.guild_id

    if guild_id not in _active_meetings:
        return "No active meeting session. Use `/meeting start` first."

    session = _active_meetings.pop(guild_id)
    asyncio.create_task(session.stop_and_summarize())
    return "Recording stopped. Transcribing and summarizing — summary will be posted shortly."

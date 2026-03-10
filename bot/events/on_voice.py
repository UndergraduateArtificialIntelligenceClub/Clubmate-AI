"""
Voice channel meeting transcription + summarization.
Uses discord-ext-voice-recv for audio capture from each speaker.
When an exec starts a meeting via /meeting start, the bot joins the voice channel,
captures voice packets, builds speaker turns, transcribes audio (Gemini/Whisper),
then posts a Gemini-generated summary when /meeting end is called.
"""

import asyncio
import io
import logging
import os
import tempfile
import time
import wave
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import discord
from discord.ext import voice_recv
from discord.opus import OpusError

logger = logging.getLogger(__name__)
STOP_GRACE_SECONDS = 1.0
SEGMENT_GAP_SECONDS = 0.9
SEGMENT_MAX_SECONDS = 20.0
SEGMENT_MIN_SECONDS = 0.15

# Active meeting sessions keyed by guild_id
_active_meetings: dict[int, "MeetingSession"] = {}
_VOICE_RECV_PATCHED = False


def _patch_voice_recv_decoder():
    """
    Guard discord-ext-voice-recv against occasional corrupted opus packets.
    Without this, one decode error can terminate the packet router thread and
    recording stops after the first few seconds.
    """
    global _VOICE_RECV_PATCHED
    if _VOICE_RECV_PATCHED:
        return

    packet_decoder_cls = voice_recv.opus.PacketDecoder
    original_pop_data = packet_decoder_cls.pop_data

    def safe_pop_data(self, *, timeout: float = 0):
        try:
            return original_pop_data(self, timeout=timeout)
        except OpusError as e:
            logger.warning("Skipping corrupted voice packet on ssrc=%s: %s", getattr(self, "ssrc", "?"), e)
            return None

    packet_decoder_cls.pop_data = safe_pop_data
    _VOICE_RECV_PATCHED = True


class UserAudioBuffer:
    """Accumulates raw PCM frames for a single user."""

    def __init__(self):
        self.frames: list[bytes] = []

    def write(self, data: bytes):
        self.frames.append(data)

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


@dataclass
class DialogueSegment:
    """A contiguous speaking segment for one speaker."""

    user_id: Optional[int]
    start_offset: float
    end_offset: float
    frames: list[bytes] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_offset - self.start_offset)

    def write(self, pcm: bytes, offset: float):
        self.frames.append(pcm)
        self.end_offset = offset

    def to_wav_bytes(self) -> bytes:
        raw = b"".join(self.frames)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(raw)
        return buf.getvalue()


class ClubmateSink(voice_recv.AudioSink):
    """Collects PCM audio and builds chronological speaker segments."""

    def __init__(self):
        super().__init__()
        self.user_buffers: dict[int, UserAudioBuffer] = defaultdict(UserAudioBuffer)
        self.unknown_buffer = UserAudioBuffer()
        self._started_at = time.monotonic()
        self._active_segment: Optional[DialogueSegment] = None
        self.dialogue_segments: list[DialogueSegment] = []

    def wants_opus(self) -> bool:
        return False  # We want decoded PCM

    def _resolve_user(self, user: Optional[discord.Member], data: voice_recv.VoiceData):
        if user is not None:
            return user
        try:
            packet = getattr(data, "packet", None)
            ssrc = getattr(packet, "ssrc", None)
            if ssrc is not None and self.voice_client is not None:
                user_id = self.voice_client._get_id_from_ssrc(ssrc)
                if user_id:
                    return self.voice_client.guild.get_member(user_id)
        except Exception:
            return None
        return None

    def _flush_active_segment(self):
        segment = self._active_segment
        if segment is None:
            return
        if segment.frames and segment.duration >= SEGMENT_MIN_SECONDS:
            self.dialogue_segments.append(segment)
        self._active_segment = None

    def finalize_segments(self):
        self._flush_active_segment()

    def write(self, user: Optional[discord.Member], data: voice_recv.VoiceData):
        pcm = data.pcm
        if not pcm:
            return

        user = self._resolve_user(user, data)
        offset = time.monotonic() - self._started_at
        user_id = user.id if user is not None else None

        active = self._active_segment
        if active is None:
            active = DialogueSegment(user_id=user_id, start_offset=offset, end_offset=offset)
            self._active_segment = active
        else:
            gap = offset - active.end_offset
            same_speaker = active.user_id == user_id
            if (not same_speaker) or (gap > SEGMENT_GAP_SECONDS) or (active.duration >= SEGMENT_MAX_SECONDS):
                self._flush_active_segment()
                active = DialogueSegment(user_id=user_id, start_offset=offset, end_offset=offset)
                self._active_segment = active

        active.write(pcm, offset)

        if user is None:
            self.unknown_buffer.write(pcm)
            return

        self.user_buffers[user.id].write(pcm)

    def cleanup(self):
        self.finalize_segments()


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
        self.voice_client.listen(self.sink)

    async def stop_and_summarize(self):
        if self.voice_client.is_listening():
            # Small flush window so the last spoken words are less likely to be cut.
            await asyncio.sleep(STOP_GRACE_SECONDS)
            self.voice_client.stop_listening()
        self.sink.finalize_segments()

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
    """Transcribe meeting audio, summarize it, and save transcript to Google Docs."""
    await summary_channel.send(f"Meeting **{title}** ended. Transcribing audio...")

    if not sink.dialogue_segments:
        await summary_channel.send("No audio was recorded in this meeting.")
        return

    transcript_lines: list[str] = []

    for segment in sink.dialogue_segments:
        speaker = (
            member_names.get(segment.user_id, f"User {segment.user_id}")
            if segment.user_id is not None
            else "Unknown speaker"
        )
        try:
            wav_bytes = segment.to_wav_bytes()
            text = await _transcribe(wav_bytes)
            if text.strip():
                clean = " ".join(text.strip().split())
                transcript_lines.append(
                    f"[{_format_offset(segment.start_offset)}] {speaker}: {clean}"
                )
        except Exception as e:
            logger.error("Transcription failed for segment speaker=%s: %s", speaker, e)

    if not transcript_lines:
        await summary_channel.send("No speech detected in the meeting recording.")
        return

    full_transcript = "\n".join(transcript_lines)

    await summary_channel.send("Generating summary...")

    try:
        summary = await _summarize(full_transcript, title)
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        await summary_channel.send(f"Summarization failed: {e}")
        return

    await summary_channel.send(f"## Meeting Summary — {title}\n\n{summary}")
    try:
        doc_url = await asyncio.to_thread(_save_transcript_to_google_doc, title, summary, full_transcript)
        await summary_channel.send(f"📝 Full transcript saved to Google Doc: {doc_url}")
    except Exception as e:
        logger.error("Failed to save transcript to Google Doc: %s", e)
        await summary_channel.send(
            f"⚠️ Could not save transcript to Google Doc: {e}. "
            "Reconnect Google in dashboard if needed."
        )


async def _transcribe(wav_bytes: bytes) -> str:
    """Transcribe WAV bytes using Whisper (local or API)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from config import settings

    mode = (settings.whisper_mode or "local").strip().lower()

    if mode in {"gemini", "google"}:
        return await _transcribe_gemini(
            wav_bytes,
            settings.gemini_api_key,
            settings.default_llm_model,
        )
    if mode in {"api", "openai"}:
        return await _transcribe_api(wav_bytes, settings.openai_api_key)
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


async def _transcribe_gemini(wav_bytes: bytes, api_key: str, model: str) -> str:
    """Transcribe using Gemini audio input (uses GEMINI_API_KEY)."""
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set for Gemini transcription mode.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = (
        "Transcribe this meeting audio verbatim. "
        "Return only the transcript text with punctuation. "
        "Do not add headings or commentary."
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=4096,
        ),
    )
    return (response.text or "").strip()


def _format_offset(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _save_transcript_to_google_doc(title: str, summary: str, transcript: str) -> str:
    """Create a Google Doc for the meeting transcript and return its URL."""
    import sys
    import time

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from mcp_servers.google_auth import get_service

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc_title = f"Meeting Transcript - {title} ({now_str})"
    body = (
        f"Meeting: {title}\n"
        f"Generated: {now_str}\n\n"
        "Summary\n"
        f"{summary}\n\n"
        "Transcript\n"
        f"{transcript}\n"
    )

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            service = get_service("docs", "v1")
            created = service.documents().create(body={"title": doc_title}).execute()
            doc_id = created.get("documentId")
            if not doc_id:
                raise RuntimeError("Google Docs API did not return a document ID.")

            service.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {
                            "insertText": {
                                "location": {"index": 1},
                                "text": body,
                            }
                        }
                    ]
                },
            ).execute()

            return f"https://docs.google.com/document/d/{doc_id}/edit"
        except OSError as e:
            # Retry transient file-lock deadlocks seen on mounted volumes.
            last_error = e
            if getattr(e, "errno", None) == 35 and attempt < 3:
                time.sleep(0.4 * attempt)
                continue
            raise

    raise RuntimeError(f"Failed to save transcript after retries: {last_error}")


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

Transcript (format is "[mm:ss] Speaker: what they said"):
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
    _patch_voice_recv_decoder()
    guild_id = interaction.guild_id

    if guild_id in _active_meetings:
        return "A meeting is already in progress. Use `/meeting end` first."

    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        return "You must be in a voice channel to start a meeting."

    try:
        vc = await voice_state.channel.connect(cls=voice_recv.VoiceRecvClient)
    except discord.ClientException:
        return "Bot is already connected to a voice channel."

    session = MeetingSession(vc, summary_channel, title)
    session.start_recording()
    _active_meetings[guild_id] = session

    return (
        f"Joined **{voice_state.channel.name}** and started recording **{title}**. "
        f"Summary and transcript doc link will be posted to {summary_channel.mention} when you run `/meeting end`."
    )


async def end_meeting(interaction: discord.Interaction) -> str:
    guild_id = interaction.guild_id

    if guild_id not in _active_meetings:
        return "No active meeting session. Use `/meeting start` first."

    session = _active_meetings.pop(guild_id)
    asyncio.create_task(session.stop_and_summarize())
    return "Recording stopped. Transcribing and summarizing — summary will be posted shortly."

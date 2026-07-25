"""Tests for bot.events.on_voice — UserAudioBuffer and transcription helpers."""

import io
import struct
import wave
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


class TestUserAudioBuffer:
    def _make_buffer(self):
        from bot.events.on_voice import UserAudioBuffer
        return UserAudioBuffer()

    def test_initial_state(self):
        buf = self._make_buffer()
        assert buf.frame_count == 0
        assert buf.byte_count == 0
        assert buf.frames == []

    def test_write_adds_frame(self):
        buf = self._make_buffer()
        buf.write(b"\x00\x01\x02\x03")
        assert buf.frame_count == 1
        assert buf.byte_count == 4

    def test_multiple_writes(self):
        buf = self._make_buffer()
        buf.write(b"\x00\x01")
        buf.write(b"\x02\x03\x04\x05")
        assert buf.frame_count == 2
        assert buf.byte_count == 6

    def test_to_wav_bytes_produces_valid_wav(self):
        buf = self._make_buffer()
        # 48kHz stereo 16-bit: each sample is 2 bytes, 2 channels = 4 bytes per frame
        pcm_data = b"\x00\x00" * 100  # 100 stereo samples
        buf.write(pcm_data)
        wav = buf.to_wav_bytes()
        assert wav[:4] == b"RIFF"
        # Verify we can read it back
        with wave.open(io.BytesIO(wav), "rb") as wf:
            assert wf.getnchannels() == 2
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 48000

    def test_to_wav_empty_frames(self):
        buf = self._make_buffer()
        wav = buf.to_wav_bytes()
        assert wav[:4] == b"RIFF"


class TestTranscribeLocal:
    @patch("whisper.load_model")
    @patch("bot.events.on_voice.tempfile.NamedTemporaryFile")
    @patch("bot.events.on_voice.os.unlink")
    def test_transcribe_local_calls_whisper(self, mock_unlink, mock_tmp, mock_whisper):
        from bot.events.on_voice import _transcribe_local

        mock_file = MagicMock()
        mock_file.name = "/tmp/test.wav"
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_tmp.return_value = mock_file

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mock_whisper.return_value = mock_model

        result = _transcribe_local(b"fake wav data")
        assert result == "Hello world"
        mock_whisper.assert_called_once_with("base")
        mock_model.transcribe.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/test.wav")


class TestTranscribeApi:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_transcribe_api_makes_post_request(self, mock_httpx_cls):
        from bot.events.on_voice import _transcribe_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Transcribed text"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        result = await _transcribe_api(b"fake wav", "test-api-key")
        assert result == "Transcribed text"
        mock_client.post.assert_called_once()


class TestSummarize:
    @pytest.mark.asyncio
    @patch("google.genai.Client")
    @patch("config.settings")
    async def test_summarize_calls_gemini(self, mock_settings, mock_genai):
        from bot.events.on_voice import _summarize

        mock_settings.gemini_api_key = "test-key"
        mock_settings.default_llm_model = "gemini-2.5-flash"

        mock_response = MagicMock()
        mock_response.text = "Meeting summary content"

        mock_client = MagicMock()
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_genai.return_value = mock_client

        result = await _summarize("Speaker 1: Hello\nSpeaker 2: World", "Test Meeting")
        assert result == "Meeting summary content"
        mock_genai.assert_called_once_with(api_key="test-key")


class TestStartMeeting:
    @pytest.mark.asyncio
    @patch("bot.events.on_voice._active_meetings", {})
    async def test_start_meeting_already_in_progress(self):
        from bot.events.on_voice import start_meeting, _active_meetings

        _active_meetings[123] = MagicMock()
        interaction = MagicMock()
        interaction.guild_id = 123

        result = await start_meeting(interaction, "Test", MagicMock())
        assert "already in progress" in result
        _active_meetings.clear()

    @pytest.mark.asyncio
    @patch("bot.events.on_voice._active_meetings", {})
    async def test_start_meeting_no_voice_state(self):
        from bot.events.on_voice import start_meeting

        interaction = MagicMock()
        interaction.guild_id = 123
        interaction.user.voice = None

        result = await start_meeting(interaction, "Test", MagicMock())
        assert "must be in a voice channel" in result


class TestEndMeeting:
    @pytest.mark.asyncio
    @patch("bot.events.on_voice._active_meetings", {})
    async def test_end_meeting_no_active(self):
        from bot.events.on_voice import end_meeting

        interaction = MagicMock()
        interaction.guild_id = 123

        result = await end_meeting(interaction)
        assert "No active meeting" in result

    @pytest.mark.asyncio
    @patch("bot.events.on_voice._active_meetings", {})
    async def test_end_meeting_stops_session(self):
        from bot.events.on_voice import end_meeting, _active_meetings
        from unittest.mock import patch as patch_async

        session = MagicMock()
        session.stop_and_summarize = AsyncMock()
        _active_meetings[123] = session

        interaction = MagicMock()
        interaction.guild_id = 123

        with patch("bot.events.on_voice.asyncio.create_task"):
            result = await end_meeting(interaction)
        assert "Recording stopped" in result
        assert 123 not in _active_meetings

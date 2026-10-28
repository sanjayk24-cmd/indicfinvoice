"""Audio contract regressions; models are stubbed so these run offline."""
import io
from unittest.mock import Mock

import numpy as np
import pytest
import soundfile as sf

from backend.services.asr_service import ASRService, INDIC_MODEL_ID, WHISPER_MODEL_ID
from asr.transcribe_indicconformer import transcribe_fixed_language


def wav_bytes(silence=False, rate=16000, duration=1):
    samples = np.zeros(int(rate * duration), dtype=np.float32)
    if not silence:
        samples = (0.1 * np.sin(2 * np.pi * 440 * np.arange(len(samples)) / rate)).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, samples, rate, format="WAV")
    return buffer.getvalue()


@pytest.mark.parametrize("requested", ["auto", "indicconformer", "whisper"])
def test_english_never_uses_hindi_head(requested):
    service = ASRService()
    service._whisper_pipe = Mock(return_value={"text": "My account balance"})
    service._indic_pipe = Mock(side_effect=AssertionError("English sent to Hindi decoder"))
    result = service.transcribe_audio_bytes(wav_bytes(), "en", requested)
    assert result["model_id"] == WHISPER_MODEL_ID
    assert result["transcript"] == "My account balance"
    assert service._whisper_pipe.call_args.kwargs["generate_kwargs"]["language"] == "en"


@pytest.mark.parametrize("lang", ["hi", "ta"])
def test_indic_language_and_blank_rnnt_fallback(lang):
    service = ASRService()
    service._indic_pipe = Mock(side_effect=["", "recognized speech"])
    result = service.transcribe_audio_bytes(wav_bytes(), lang)
    assert result["model_id"] == INDIC_MODEL_ID
    assert result["transcript"] == "recognized speech"
    assert [call.args[1:] for call in service._indic_pipe.call_args_list] == [(lang, "rnnt"), (lang, "ctc")]


def test_silence_does_not_load_models():
    service = ASRService()
    assert service.transcribe_audio_bytes(wav_bytes(silence=True), "hi")["status"] == "silence"
    assert not any(service.is_loaded().values())


def test_decoder_failure_is_not_a_transcript():
    service = ASRService()
    service._indic_pipe = Mock(side_effect=RuntimeError("decoder failed"))
    with pytest.raises(RuntimeError, match="decoder failed"):
        service.transcribe_audio_bytes(wav_bytes(), "ta")


@pytest.mark.parametrize("audio", [b"not a wav", wav_bytes(duration=0.1)])
def test_invalid_audio_rejected(audio):
    with pytest.raises(ValueError):
        ASRService().transcribe_audio_bytes(audio)


def test_stereo_resampling(tmp_path):
    path = tmp_path / "stereo.wav"
    sf.write(path, np.ones((48000, 2), dtype=np.float32) * 0.1, 48000)
    pipe = Mock(return_value="speech")
    assert transcribe_fixed_language(pipe, str(path), "hi") == "speech"
    assert tuple(pipe.call_args.args[0].shape) == (1, 16000)


@pytest.mark.parametrize("route", ["/voice", "/transcribe"])
def test_api_invalid_audio_is_400(route):
    from fastapi.testclient import TestClient
    from backend.main import app
    response = TestClient(app).post(route, files={"file": ("bad.wav", b"broken", "audio/wav")})
    assert response.status_code == 400


def test_voice_silence_does_not_enter_dialogue(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app, conversation_service
    process = Mock(side_effect=AssertionError("silence entered dialogue"))
    monkeypatch.setattr(conversation_service, "process_message", process)
    response = TestClient(app).post("/voice", data={"lang": "en"}, files={"file": ("silent.wav", wav_bytes(True), "audio/wav")})
    assert response.status_code == 200
    assert response.json()["status"] == "silence"
    assert response.json()["asr_model"] == WHISPER_MODEL_ID
    process.assert_not_called()


@pytest.mark.parametrize("text, expected", [("मेरा बैलेंस", "hi"), ("எனது இருப்பு", "ta"), ("My balance", "en")])
def test_auto_speech_does_not_force_language(text, expected):
    service = ASRService()
    service._whisper_pipe = Mock(return_value={"text": text})
    result = service.transcribe_audio_bytes(wav_bytes(), "auto")
    assert result["lang"] == expected
    assert "language" not in service._whisper_pipe.call_args.kwargs["generate_kwargs"]

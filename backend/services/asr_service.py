"""
backend/services/asr_service.py - Speech-to-Text Service with Model Caching
"""

import os
import re
from collections import Counter
import sys
import tempfile
from threading import RLock
from core.lang_id import identify_language
from typing import Dict, Optional, Tuple
import soundfile as sf
import torch

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from asr.transcribe import get_pipeline as get_whisper_pipeline, normalise_text
from asr.transcribe_indicconformer import load_asr as load_indic_model, transcribe_fixed_language

INDIC_MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"
WHISPER_MODEL_ID = "openai/whisper-medium"


class ASRService:
    """
    Manages STT pipelines with singleton in-memory caching:
      - English ('en') -> openai/whisper-medium via asr/transcribe.py
      - Hindi ('hi') & Tamil ('ta') -> ai4bharat/indic-conformer-600m-multilingual via asr/transcribe_indicconformer.py
    """

    def __init__(self):
        self._whisper_pipe = None
        self._indic_pipe = None
        self._inference_lock = RLock()

    def get_whisper(self):
        if self._whisper_pipe is None:
            self._whisper_pipe = get_whisper_pipeline()
        return self._whisper_pipe

    def get_indic_conformer(self):
        if self._indic_pipe is None:
            self._indic_pipe = load_indic_model(INDIC_MODEL_ID)
        return self._indic_pipe

    def is_loaded(self) -> Dict[str, bool]:
        return {
            "whisper_medium": self._whisper_pipe is not None,
            "indic_conformer": self._indic_pipe is not None,
        }

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        lang: str = "hi",
        model: Optional[str] = "auto",
    ) -> Dict[str, str]:
        # Bound memory use and prevent concurrent requests loading duplicate models.
        with self._inference_lock:
            return self._transcribe_audio_bytes(audio_bytes, lang, model)

    def _transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        lang: str = "hi",
        model: Optional[str] = "auto",
    ) -> Dict[str, str]:
        """
        Saves bytes to temporary file, dispatches to IndicConformer (default) or Whisper.
        """
        lang = (lang or "hi").lower().strip()
        model = (model or "auto").lower().strip()
        if lang not in ("auto", "en", "hi", "ta"):
            raise ValueError("Unsupported speech language.")
        if model not in ("auto", "whisper", "indicconformer"):
            raise ValueError("Unsupported ASR model.")
        # English has no IndicConformer language head, including for older clients.
        if model == "auto" or (model == "indicconformer" and lang == "en"):
            model = "whisper" if lang in ("auto", "en") else "indicconformer"

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                temp_path = tmp.name

            # Validate audio readability with soundfile
            try:
                data, sr = sf.read(temp_path)
            except Exception as e:
                raise ValueError(f"Invalid audio format or corrupted WAV file: {e}")

            # Ensure mono float32
            import numpy as np
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            data = data.astype(np.float32)
            if not len(data) or not np.isfinite(data).all():
                raise ValueError("Audio contains no valid samples.")
            if len(data) / sr < 0.3:
                raise ValueError("Recording is too short. Please record a complete sentence.")

            # Measure audio energy (silence / low volume detection)
            max_amp = float(np.max(np.abs(data))) if len(data) > 0 else 0.0
            rms = float(np.sqrt(np.mean(data ** 2))) if len(data) > 0 else 0.0
            print(f"[ASR] Received {len(data)} samples, sr={sr}, max_amp={max_amp:.4f}, rms={rms:.5f}, lang={lang}, model={model}")

            # If input is pure silence or mic background hiss below threshold
            if max_amp < 0.001 and rms < 0.0001:
                return {
                    "transcript": "",
                    "lang": lang,
                    "model_id": INDIC_MODEL_ID if model == "indicconformer" else WHISPER_MODEL_ID,
                    "status": "silence",
                }

            # Peak normalize audio so soft microphone input or low gain recordings transcribe cleanly
            if max_amp > 1e-4:
                data = data * min(3.0, 0.9 / max_amp)

            # ROUTING: Primary STT pipeline is AI4Bharat IndicConformer
            if model == "whisper":
                pipe = self.get_whisper()
                if pipe is None:
                    raise RuntimeError("Whisper ASR pipeline failed to initialize.")
                if sr != 16000:
                    import librosa
                    data = librosa.resample(data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                kwargs = {"task": "transcribe", "do_sample": False, "max_new_tokens": 128}
                if lang != "auto":
                    kwargs["language"] = lang
                result = pipe({"raw": data, "sampling_rate": sr}, generate_kwargs=kwargs)
                transcript = result.get("text", "") if isinstance(result, dict) else str(result)
                transcript = transcript.strip()
                if lang == "auto":
                    lang = identify_language(transcript)

                if transcript.lower() in ("you", "thank you", "thank you.", "thanks for watching", "bye") and rms < 0.02:
                    print(f"[ASR] Filtered Whisper silence hallucination '{transcript}' on low rms {rms:.5f}")
                    transcript = ""

                model_id = WHISPER_MODEL_ID
                effective_lang = lang
            else:
                # Primary Architecture: AI4Bharat IndicConformer (600M Multilingual)
                if sr != 16000:
                    import librosa
                    data = librosa.resample(data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                sf.write(temp_path, data, 16000)

                # Route to Hindi or Tamil head (defaults to 'hi' if unassigned or en)
                target_indic_lang = lang

                pipe = self.get_indic_conformer()
                if pipe is None:
                    raise RuntimeError("IndicConformer ASR pipeline failed to initialize.")
                transcript = transcribe_fixed_language(pipe, temp_path, target_indic_lang)
                model_id = INDIC_MODEL_ID
                effective_lang = target_indic_lang

            tokens = re.findall(r"\w+", transcript.lower())
            if len(tokens) >= 10 and Counter(tokens).most_common(1)[0][1] / len(tokens) > 0.6:
                transcript = ""
            if len(transcript) > 30 and len(set(transcript.replace(" ", ""))) <= 3:
                transcript = ""
            return {
                "transcript": transcript,
                "lang": lang,
                "model_id": model_id,
                "status": "success" if transcript.strip() else "no_speech",
            }

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


# Singleton ASR service instance
asr_service = ASRService()

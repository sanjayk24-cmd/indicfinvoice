#!/usr/bin/env python3
"""
asr/transcribe_indicconformer.py - AI4Bharat IndicConformer Transcription Module

Loads AI4Bharat IndicConformer checkpoints once per evaluation session.
Provides transcribe_fixed_language for Hindi and Tamil inference.
Reuses normalise_text from asr.transcribe without redefinition.
"""

import os
import soundfile as sf
import torch
from transformers import AutoModel

# Import normalise_text from asr/transcribe.py directly; do not redefine it
from asr.transcribe import normalise_text


def load_asr(model_id: str):
    """
    Loads IndicConformer model using the appropriate device and precision
    supported by IndicConformer.
    Loaded once per call of the evaluation script.
    """
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True)
    return model


def transcribe_fixed_language(pipe, path: str, language: str) -> str:
    """
    Transcribes audio at path using the IndicConformer transcription interface
    and the appropriate language parameter ('hi' or 'ta').
    """
    if language not in ("hi", "ta"):
        raise ValueError("IndicConformer supports Hindi and Tamil in this application.")
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    wav = torch.from_numpy(audio).float().unsqueeze(0)

    with torch.inference_mode():
        # Use RNNT decoder for accurate conformer transcription
        transcript = pipe(wav, language, "rnnt")
        if not isinstance(transcript, str):
            raise RuntimeError("IndicConformer returned an invalid transcript.")
        # The hybrid model has independent decoders; retry a blank RNNT result.
        if not transcript.strip():
            transcript = pipe(wav, language, "ctc")
        if not isinstance(transcript, str):
            raise RuntimeError("IndicConformer returned an invalid transcript.")
        return transcript.strip()


def free_model(pipe):
    """
    Frees GPU memory between models.
    """
    del pipe
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

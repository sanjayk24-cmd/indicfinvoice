#!/usr/bin/env python3
"""
asr/transcribe.py - Whisper Speech-to-Text Transcription Module

Loads openai/whisper-medium lazily with fp16 on CUDA.
Transcribes audio without passing language argument (auto-detection).
Provides normalise_text for standardising references and hypotheses.
"""

import os
import re
import string
from typing import Optional
import soundfile as sf
import torch
from transformers import pipeline

# Global pipeline instance loaded once
_PIPELINE = None

# Unicode punctuation mapping: standard ASCII punctuation + Indic danda / double danda + dashes / quotes
PUNCT_TABLE = str.maketrans(
    {c: " " for c in string.punctuation + "।॥—–…«»“”‘’"}
)


def normalise_text(text: str) -> str:
    """
    Lowercase, remove punctuation (including Devanagari danda and double danda),
    and collapse whitespace.
    """
    if not text:
        return ""
    t = text.lower().translate(PUNCT_TABLE)
    return " ".join(t.split())


# Alias for backwards compatibility
normalise_transcript = normalise_text


def get_pipeline():
    """
    Initializes and returns the singleton Whisper pipeline.
    Uses CUDA and float16 if available.
    """
    global _PIPELINE
    if _PIPELINE is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        _PIPELINE = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-medium",
            torch_dtype=torch_dtype,
            device=device,
        )
    return _PIPELINE


# Load lazily: importing text normalization must not download/load Whisper.


def transcribe(path: str) -> str:
    """
    Transcribes audio at path using whisper-medium.
    Loads audio with soundfile at native sample rate (16 kHz mono).
    Does NOT pass language argument (pure auto-detection).
    """
    if not os.path.exists(path):
        return ""

    pipe = get_pipeline()
    if pipe is not None:
        try:
            audio, sr = sf.read(path)
            # Pass generate_kwargs with task="transcribe" only, NO language argument
            result = pipe(audio, generate_kwargs={"task": "transcribe"})
            if isinstance(result, dict):
                return result.get("text", "").strip()
            return str(result).strip()
        except Exception as e:
            return f"Error in transcription: {e}"

    return ""

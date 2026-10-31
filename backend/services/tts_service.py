"""
backend/services/tts_service.py - Multilingual Text-to-Speech (TTS) Service
Uses Microsoft Neural TTS (edge-tts) for studio-grade natural voices in:
  - English ('en'): en-IN-NeerjaNeural (Female) / en-IN-PrabhatNeural (Male)
  - Hindi ('hi'): hi-IN-SwaraNeural (Female) / hi-IN-MadhurNeural (Male)
  - Tamil ('ta'): ta-IN-PallaviNeural (Female) / ta-IN-ValluvarNeural (Male)
Features:
  - Financial symbol phonetic expansion (Rupees, account masking, dates)
  - In-memory LRU audio caching for ultra-low latency
  - Asynchronous generation with graceful fallback
"""

import base64
import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger("indicfinvoice.tts")

# Voice Persona Matrix
VOICE_MAP: Dict[str, Dict[str, str]] = {
    "en": {
        "female": "en-IN-NeerjaNeural",
        "male": "en-IN-PrabhatNeural",
    },
    "hi": {
        "female": "hi-IN-SwaraNeural",
        "male": "hi-IN-MadhurNeural",
    },
    "ta": {
        "female": "ta-IN-PallaviNeural",
        "male": "ta-IN-ValluvarNeural",
    },
}

# In-memory LRU cache for synthesized audio (key: (text, voice_id), val: bytes)
_AUDIO_CACHE: Dict[Tuple[str, str], bytes] = {}
_MAX_CACHE_SIZE = 128


def clean_text_for_speech(text: str, lang: str = "en") -> str:
    """
    Cleans and expands banking text so speech engines pronounce numbers,
    currency, and masks naturally without reading out markdown syntax.
    """
    if not text:
        return ""

    t = text.strip()

    # 1. Strip emojis and UI decoration characters
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    t = re.sub(r"[🎙️⚠️✅●■↗•]", " ", t)

    # 2. Strip markdown headers, bold, italics, links
    t = re.sub(r"#{1,6}\s*", "", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # 3. Currency symbol normalization
    if lang == "hi":
        t = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 रुपये", t)
        t = re.sub(r"INR\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 रुपये", t)
    elif lang == "ta":
        t = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ரூபாய்", t)
        t = re.sub(r"INR\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 ரூபாய்", t)
    else:  # English
        t = re.sub(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 rupees", t)
        t = re.sub(r"INR\s*([0-9,]+(?:\.[0-9]+)?)", r"\1 rupees", t)

    # 4. Account masking normalization (XXXX 1234 -> ending in 1 2 3 4)
    def mask_replacer(match):
        digits = match.group(1)
        spaced = " ".join(list(digits))
        if lang == "hi":
            return f"जिसका अंतिम नंबर {spaced} है"
        elif lang == "ta":
            return f"கடைசி எண் {spaced}"
        return f"ending in {spaced}"

    t = re.sub(r"(?:X{2,}|•{2,}|\*{2,})\s*([0-9]{4})", mask_replacer, t, flags=re.IGNORECASE)

    # 5. Collapse excessive whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def get_voice_id(lang: str = "en", gender: str = "female") -> str:
    """
    Returns the appropriate Microsoft Neural Voice ID.
    Defaults to female persona if unassigned.
    """
    lang = (lang or "en").lower().strip()
    gender = (gender or "female").lower().strip()

    if lang not in VOICE_MAP:
        lang = "en"
    if gender not in ("female", "male"):
        gender = "female"

    return VOICE_MAP[lang][gender]


async def synthesize_speech(
    text: str,
    lang: str = "en",
    gender: str = "female",
) -> Optional[bytes]:
    """
    Synthesizes speech asynchronously using edge-tts.
    Returns MP3 audio bytes, or None on network failure.
    """
    cleaned = clean_text_for_speech(text, lang=lang)
    if not cleaned:
        return None

    voice_id = get_voice_id(lang=lang, gender=gender)
    cache_key = (cleaned, voice_id)

    if cache_key in _AUDIO_CACHE:
        return _AUDIO_CACHE[cache_key]

    try:
        import edge_tts

        communicate = edge_tts.Communicate(cleaned, voice_id)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        audio_bytes = b"".join(chunks)
        if audio_bytes:
            # Maintain bounded LRU cache
            if len(_AUDIO_CACHE) >= _MAX_CACHE_SIZE:
                _AUDIO_CACHE.pop(next(iter(_AUDIO_CACHE)))
            _AUDIO_CACHE[cache_key] = audio_bytes
            return audio_bytes

    except Exception as e:
        logger.warning(f"edge-tts synthesis failed for voice '{voice_id}': {e}. Falling back to browser TTS.")

    return None


async def synthesize_speech_base64(
    text: str,
    lang: str = "en",
    gender: str = "female",
) -> Tuple[Optional[str], str]:
    """
    Returns (audio_data_uri, voice_id).
    If synthesis succeeds, returns 'data:audio/mp3;base64,...'.
    If synthesis fails or is offline, returns (None, voice_id) so client falls back.
    """
    voice_id = get_voice_id(lang=lang, gender=gender)
    audio_bytes = await synthesize_speech(text, lang=lang, gender=gender)

    if audio_bytes:
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        return f"data:audio/mp3;base64,{b64}", voice_id

    return None, voice_id


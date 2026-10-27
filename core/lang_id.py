#!/usr/bin/env python3
"""
core/lang_id.py - Script-Based Language Identification

Identifies the language of an input text:
  - Tamil script (\u0B80 - \u0BFF) -> "ta"
  - Devanagari script (\u0900 - \u097F) -> "hi"
  - Latin script / Default -> "en"
"""


def identify_language(text: str) -> str:
    """
    Returns 'ta', 'hi', or 'en' based on Unicode script frequency in the input text.
    """
    if not text:
        return "en"

    ta_count = 0
    hi_count = 0

    for ch in text:
        code = ord(ch)
        if 0x0B80 <= code <= 0x0BFF:
            ta_count += 1
        elif 0x0900 <= code <= 0x097F:
            hi_count += 1

    if ta_count > 0 and ta_count >= hi_count:
        return "ta"
    if hi_count > 0 and hi_count > ta_count:
        return "hi"

    return "en"

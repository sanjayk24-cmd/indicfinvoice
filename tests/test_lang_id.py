#!/usr/bin/env python3
"""
tests/test_lang_id.py - Unit tests for core/lang_id.py
Verifies identify_language on at least 10 examples per language (en, hi, ta).
"""

import pytest
from core.lang_id import identify_language


EN_EXAMPLES = [
    "What is my account balance?",
    "When is my crop loan due?",
    "Check status for claim CLM-771",
    "I want to dispute transaction TXN-9001",
    "Can you help me with my banking?",
    "Please repeat that again",
    "How much money is left in my savings account?",
    "My card was stolen yesterday",
    "Cancel this transaction dispute",
    "Tell me the outstanding amount on my personal loan",
]

HI_EXAMPLES = [
    "मेरे खाते का बैलेंस बताओ",
    "मेरा फसल ऋण कब देय है",
    "दावा संख्या CLM-771 की स्थिति क्या है",
    "लेनदेन TXN-9001 पर आपत्ति दर्ज करें",
    "नमस्ते, क्या आप मेरी मदद कर सकते हैं",
    "कृपया दोबारा कहें",
    "बचत खाते में कितने पैसे हैं",
    "मेरा कार्ड खो गया है",
    "इस अनुरोध को रद्द करें",
    "किसान क्रेडिट कार्ड की शेष राशि बताएं",
]

TA_EXAMPLES = [
    "என் சேமிப்புக் கணக்கு இருப்பு என்ன?",
    "என் பயிர்க் கடன் எப்போது செலுத்த வேண்டும்?",
    "என் கிளைம் CLM-771 நிலை என்ன?",
    "பரிவர்த்தனை TXN-9001 மீது புகார் பதிவு செய்",
    "வணக்கம், எனக்கு உதவி செய்ய முடியுமா?",
    "மீண்டும் சொல்லுங்கள்",
    "நடப்புக் கணக்கில் எவ்வளவு பணம் உள்ளது?",
    "என் கார்டு தொலைந்துவிட்டது",
    "இந்த கோரிக்கையை ரத்து செய்",
    "கேசிசி கடன் நிலுவை தொகை என்ன?",
]


@pytest.mark.parametrize("text", EN_EXAMPLES)
def test_identify_english(text):
    assert identify_language(text) == "en"


@pytest.mark.parametrize("text", HI_EXAMPLES)
def test_identify_hindi(text):
    assert identify_language(text) == "hi"


@pytest.mark.parametrize("text", TA_EXAMPLES)
def test_identify_tamil(text):
    assert identify_language(text) == "ta"


def test_empty_and_mixed():
    assert identify_language("") == "en"
    # English with loan / digit
    assert identify_language("C001 loan due 1500") == "en"
    # Hindi with English reference number
    assert identify_language("दावा CLM-771 चेक करो") == "hi"
    # Tamil with English reference number
    assert identify_language("கிளைம் CLM-771 விவரம்") == "ta"

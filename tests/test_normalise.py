#!/usr/bin/env python3
"""
tests/test_normalise.py - Tests for core/normalise.py covering en, hi, and ta forms.
At least 5 examples per slot type, plus unknown value exclusion.
"""

import datetime
import pytest
from core.normalise import (
    normalise_account_type,
    normalise_loan_type,
    normalise_claim_id,
    normalise_transaction_ref,
    normalise_amount,
    normalise_date,
    normalise_slots,
)


# ----------------------------------------------------
# account_type tests
# ----------------------------------------------------
def test_normalise_account_type():
    # English
    assert normalise_account_type("savings") == "savings"
    assert normalise_account_type("current") == "current"
    assert normalise_account_type("KCC") == "kcc"
    # Hindi
    assert normalise_account_type("बचत") == "savings"
    assert normalise_account_type("चालू") == "current"
    assert normalise_account_type("केसीसी") == "kcc"
    # Tamil
    assert normalise_account_type("சேமிப்பு") == "savings"
    assert normalise_account_type("நடப்பு") == "current"
    assert normalise_account_type("கேசிசி") == "kcc"
    # Unknown
    assert normalise_account_type("demat") is None
    assert normalise_account_type("crypto") is None


# ----------------------------------------------------
# loan_type tests
# ----------------------------------------------------
def test_normalise_loan_type():
    # English
    assert normalise_loan_type("crop") == "crop"
    assert normalise_loan_type("home") == "home"
    assert normalise_loan_type("personal") == "personal"
    # Hindi
    assert normalise_loan_type("फसल") == "crop"
    assert normalise_loan_type("होम") == "home"
    assert normalise_loan_type("पर्सनल") == "personal"
    # Tamil
    assert normalise_loan_type("பயிர்") == "crop"
    assert normalise_loan_type("வீடு") == "home"
    assert normalise_loan_type("தனிநபர்") == "personal"
    # Unknown
    assert normalise_loan_type("education") is None
    assert normalise_loan_type("gold") is None


# ----------------------------------------------------
# claim_id tests
# ----------------------------------------------------
def test_normalise_claim_id():
    assert normalise_claim_id("CLM 771") == "CLM-771"
    assert normalise_claim_id("clm-771") == "CLM-771"
    assert normalise_claim_id("CLM-402") == "CLM-402"
    assert normalise_claim_id("सी एल एम सात सात एक") == "CLM-771"
    assert normalise_claim_id("சி எல் எம் ஏழு ஏழு ஒன்று") == "CLM-771"
    assert normalise_claim_id("CLM 930") == "CLM-930"
    # Unknown
    assert normalise_claim_id("ABC-XYZ") is None
    assert normalise_claim_id("hello") is None


# ----------------------------------------------------
# transaction_ref tests
# ----------------------------------------------------
def test_normalise_transaction_ref():
    assert normalise_transaction_ref("TXN 9001") == "TXN-9001"
    assert normalise_transaction_ref("txn9001") == "TXN-9001"
    assert normalise_transaction_ref("TXN-9002") == "TXN-9002"
    assert normalise_transaction_ref("टी एक्स एन नौ शून्य शून्य एक") == "TXN-9001"
    assert normalise_transaction_ref("டி எக்ஸ் என் ஒன்பது பூஜ்ஜியம் பூஜ்ஜியம் ஒன்று") == "TXN-9001"
    # Unknown
    assert normalise_transaction_ref("random_text") is None


# ----------------------------------------------------
# amount tests
# ----------------------------------------------------
def test_normalise_amount():
    assert normalise_amount("1500") == 1500
    assert normalise_amount("1.5k") == 1500
    assert normalise_amount("15 सौ") == 1500
    assert normalise_amount("पंद्रह सौ") == 1500
    assert normalise_amount("ஆயிரத்து ஐந்நூறு") == 1500
    assert normalise_amount("500") == 500
    assert normalise_amount("22k") == 22000
    assert normalise_amount("75000") == 75000
    # Unknown
    assert normalise_amount("some amount") is None


# ----------------------------------------------------
# date tests
# ----------------------------------------------------
def test_normalise_date():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    assert normalise_date("today") == today.isoformat()
    assert normalise_date("आज") == today.isoformat()
    assert normalise_date("இன்று") == today.isoformat()

    assert normalise_date("yesterday") == yesterday.isoformat()
    assert normalise_date("कल") == yesterday.isoformat()
    assert normalise_date("நேற்று") == yesterday.isoformat()

    assert normalise_date("12 October") == f"{today.year}-10-12"
    assert normalise_date("12 अक्टूबर") == f"{today.year}-10-12"
    assert normalise_date("12 அக்டோபர்") == f"{today.year}-10-12"
    assert normalise_date("5 November") == f"{today.year}-11-05"
    # Unknown
    assert normalise_date("some day") is None


# ----------------------------------------------------
# full normalise_slots dictionary test
# ----------------------------------------------------
def test_normalise_slots_complete():
    raw = {
        "account_type": "केसीसी",
        "loan_type": "फसल",
        "claim_id": "CLM 771",
        "amount": "1.5k",
        "date": "today",
        "unknown_slot": "some_random_value",
    }
    norm = normalise_slots(raw)
    assert norm["account_type"] == "kcc"
    assert norm["loan_type"] == "crop"
    assert norm["claim_id"] == "CLM-771"
    assert norm["amount"] == 1500
    assert norm["date"] == datetime.date.today().isoformat()
    assert "unknown_slot" not in norm

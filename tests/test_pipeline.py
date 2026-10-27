#!/usr/bin/env python3
"""
tests/test_pipeline.py - End-to-End Pipeline Tests for BankingAssistant

Acceptance criteria:
  - all tests pass
  - "mera crop loan kab due hai" returns a due date
  - a lost-card query returns the refusal with bank helpline
  - two-turn dialogue test
  - dispute flow without and with PIN
"""

import pytest
from pipeline import BankingAssistant


@pytest.fixture(scope="module")
def assistant():
    return BankingAssistant()


def test_mera_crop_loan_kab_due_hai(assistant):
    """
    Acceptance test: 'mera crop loan kab due hai' returns a due date.
    """
    res = assistant.handle_text("mera crop loan kab due hai", customer_id="C001")
    assert res["action"] == "call_api"
    assert res["intent"] == "loan_due_date"
    assert res["slots"].get("loan_type") == "crop"
    # C001 crop loan due date is 2026-11-30
    assert "2026-11-30" in res["reply"]
    assert res["pending"] is None


def test_lost_card_returns_refusal(assistant):
    """
    Acceptance test: a lost-card query returns the refusal.
    """
    # English
    res_en = assistant.handle_text("I lost my card yesterday", customer_id="C001")
    assert res_en["action"] == "refusal"
    assert "[BANK_HELPLINE_NUMBER]" in res_en["reply"]

    # Hindi
    res_hi = assistant.handle_text("मेरा कार्ड खो गया है", customer_id="C001")
    assert res_hi["action"] == "refusal"
    assert "[BANK_HELPLINE_NUMBER]" in res_hi["reply"]

    # Tamil
    res_ta = assistant.handle_text("என் கார்டு தொலைந்துவிட்டது", customer_id="C001")
    assert res_ta["action"] == "refusal"
    assert "[BANK_HELPLINE_NUMBER]" in res_ta["reply"]


def test_two_turn_dialogue(assistant):
    """
    Two-turn case: User asks balance without account type, system asks,
    user responds with account type, system returns the balance.
    """
    # Turn 1: balance check without specifying account type
    res1 = assistant.handle_text("check my balance please", customer_id="C001")
    assert res1["action"] == "ask"
    assert res1["slots"].get("account_type") is None
    assert res1["pending"] is not None
    assert res1["pending"]["awaiting"] == "account_type"

    # Turn 2: User says "savings"
    res2 = assistant.handle_text(
        "savings",
        customer_id="C001",
        pending=res1["pending"],
    )
    assert res2["action"] == "call_api"
    assert res2["slots"]["account_type"] == "savings"
    # C001 savings balance is 45000
    assert "45000" in res2["reply"]
    assert res2["pending"] is None


def test_dispute_flow_with_pin(assistant):
    """
    Dispute request without PIN prompts for PIN; providing PIN registers dispute.
    """
    # Step 1: Submit dispute info without PIN
    text = "dispute transaction TXN-9001 amount 1500 on 2026-10-24"
    res1 = assistant.handle_text(text, customer_id="C001", pin=None)
    assert res1["action"] == "need_pin"
    assert res1["pending"] is not None

    # Step 2: Provide correct PIN "1234" for C001
    res2 = assistant.handle_text(
        text,
        customer_id="C001",
        pending=res1["pending"],
        pin="1234",
    )
    assert res2["action"] == "call_api"
    assert "DSP-" in res2["reply"]
    assert res2["pending"] is None


def test_dispute_wrong_pin(assistant):
    """
    Dispute with wrong PIN returns error message without raising exception.
    """
    text = "dispute transaction TXN-9001 amount 1500 on 2026-10-24"
    res = assistant.handle_text(text, customer_id="C001", pin="9999")
    assert res["action"] == "error"
    assert "Invalid PIN" in res["reply"]


def test_cancel_flow(assistant):
    """
    Cancel word clears pending state.
    """
    res1 = assistant.handle_text("check my balance please", customer_id="C001")
    assert res1["pending"] is not None

    res2 = assistant.handle_text("cancel", customer_id="C001", pending=res1["pending"])
    assert res2["action"] == "cancel"
    assert res2["pending"] is None

#!/usr/bin/env python3
"""
tests/test_rules.py - Tests for core/rules.py next_action logic
Covers all branches:
  - Low confidence (< 0.6) -> repeat
  - Out of scope -> help
  - Unsupported banking (e.g. lost card) -> refusal with bank helpline
  - Missing required slots for each intent -> ask
  - Empty string slot counts as missing
  - Dispute with all slots -> need_pin
  - Valid banking requests -> call_api
"""

import pytest
from core.rules import next_action, CONFIDENCE_THRESHOLD, QUESTIONS, HELPLINE_PHONE


def test_low_confidence_repeat():
    res = next_action(intent="balance_check", slots={"account_type": "savings"}, confidence=0.59)
    assert res["action"] == "repeat"

    res_zero = next_action(intent="balance_check", slots={"account_type": "savings"}, confidence=0.0)
    assert res_zero["action"] == "repeat"


def test_out_of_scope_help():
    res = next_action(intent="out_of_scope", slots={}, confidence=0.95)
    assert res["action"] == "help"


def test_unsupported_banking_refusal():
    res1 = next_action(intent="unsupported_banking", slots={}, confidence=0.92)
    assert res1["action"] == "refusal"
    assert res1["reason"] == "unsupported_banking"
    assert HELPLINE_PHONE in res1["message"]

    res2 = next_action(intent="lost_or_stolen_card", slots={}, confidence=0.88)
    assert res2["action"] == "refusal"
    assert res2["reason"] == "unsupported_banking"
    assert HELPLINE_PHONE in res2["message"]


def test_missing_slots_ask():
    # balance_check requires account_type
    res_bal = next_action(intent="balance_check", slots={}, confidence=0.85)
    assert res_bal["action"] == "ask"
    assert res_bal["slot"] == "account_type"
    assert res_bal["question"] == QUESTIONS["account_type"]

    # loan_due_date requires loan_type
    res_loan = next_action(intent="loan_due_date", slots={}, confidence=0.85)
    assert res_loan["action"] == "ask"
    assert res_loan["slot"] == "loan_type"
    assert res_loan["question"] == QUESTIONS["loan_type"]

    # crop_insurance_status requires claim_id
    res_claim = next_action(intent="crop_insurance_status", slots={}, confidence=0.85)
    assert res_claim["action"] == "ask"
    assert res_claim["slot"] == "claim_id"
    assert res_claim["question"] == QUESTIONS["claim_id"]

    # transaction_dispute requires transaction_ref, amount, date in order
    res_disp1 = next_action(intent="transaction_dispute", slots={}, confidence=0.85)
    assert res_disp1["action"] == "ask"
    assert res_disp1["slot"] == "transaction_ref"

    res_disp2 = next_action(intent="transaction_dispute", slots={"transaction_ref": "TXN-9001"}, confidence=0.85)
    assert res_disp2["action"] == "ask"
    assert res_disp2["slot"] == "amount"

    res_disp3 = next_action(
        intent="transaction_dispute",
        slots={"transaction_ref": "TXN-9001", "amount": 1500},
        confidence=0.85,
    )
    assert res_disp3["action"] == "ask"
    assert res_disp3["slot"] == "date"


def test_empty_string_counts_as_missing():
    # Empty string
    res = next_action(intent="balance_check", slots={"account_type": ""}, confidence=0.9)
    assert res["action"] == "ask"
    assert res["slot"] == "account_type"

    # Whitespace only
    res_ws = next_action(intent="loan_due_date", slots={"loan_type": "   "}, confidence=0.9)
    assert res_ws["action"] == "ask"
    assert res_ws["slot"] == "loan_type"


def test_dispute_need_pin():
    slots = {
        "transaction_ref": "TXN-9001",
        "amount": 1500,
        "date": "2026-10-24",
    }
    res = next_action(intent="transaction_dispute", slots=slots, confidence=0.89)
    assert res["action"] == "need_pin"
    assert res["intent"] == "transaction_dispute"
    assert res["slots"] == slots


def test_call_api_branches():
    res_bal = next_action(intent="balance_check", slots={"account_type": "savings"}, confidence=0.85)
    assert res_bal["action"] == "call_api"
    assert res_bal["intent"] == "balance_check"

    res_loan = next_action(intent="loan_due_date", slots={"loan_type": "crop"}, confidence=0.85)
    assert res_loan["action"] == "call_api"
    assert res_loan["intent"] == "loan_due_date"

    res_claim = next_action(intent="crop_insurance_status", slots={"claim_id": "CLM-771"}, confidence=0.85)
    assert res_claim["action"] == "call_api"
    assert res_claim["intent"] == "crop_insurance_status"

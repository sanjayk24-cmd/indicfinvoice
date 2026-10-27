#!/usr/bin/env python3
"""
tests/test_dialogue.py - Unit tests for core/dialogue.py
Covers:
  - Two-turn dialogue continuation
  - Cancel words in en, hi, ta
  - 5-minute expiry rule
  - New intent overriding pending request
  - Dictionary serialization and deserialization
"""

import time
import pytest
from core.dialogue import DialogueState, is_cancel_word, EXPIRY_SECONDS


def test_two_turn_case():
    state = DialogueState()

    # Turn 1: User asks balance without account_type
    state.update(
        new_intent="balance_check",
        new_slots={},
        required_slots=["account_type"],
    )
    assert state.intent == "balance_check"
    assert state.awaiting == "account_type"
    assert "account_type" not in state.slots

    # Turn 2: User says "savings"
    state.update(
        new_intent=None,
        new_slots={"account_type": "savings"},
        required_slots=["account_type"],
    )
    assert state.intent == "balance_check"
    assert state.awaiting is None
    assert state.slots["account_type"] == "savings"


def test_cancel_words():
    assert is_cancel_word("cancel") is True
    assert is_cancel_word("रद्द") is True
    assert is_cancel_word("ரத்து") is True
    assert is_cancel_word("kcc balance") is False

    state = DialogueState(intent="balance_check", awaiting="account_type")
    assert state.intent is not None
    state.clear()
    assert state.intent is None
    assert state.awaiting is None
    assert state.slots == {}


def test_expiry():
    past_time = time.time() - 350.0  # > 5 minutes ago
    state = DialogueState(
        intent="loan_due_date",
        awaiting="loan_type",
        last_active=past_time,
    )
    assert state.is_expired() is True

    # When update is called after expiry, old pending request is discarded
    state.update(
        new_intent="crop_insurance_status",
        new_slots={"claim_id": "CLM-771"},
        required_slots=["claim_id"],
    )
    assert state.intent == "crop_insurance_status"
    assert state.slots == {"claim_id": "CLM-771"}
    assert state.awaiting is None


def test_new_intent_overrides_pending():
    state = DialogueState(
        intent="balance_check",
        slots={},
        awaiting="account_type",
        last_active=time.time(),
    )

    # User instead asks for crop loan due date
    state.update(
        new_intent="loan_due_date",
        new_slots={"loan_type": "crop"},
        required_slots=["loan_type"],
    )
    assert state.intent == "loan_due_date"
    assert state.slots == {"loan_type": "crop"}
    assert state.awaiting is None


def test_multi_slot_sequence():
    # Dispute requires: transaction_ref, amount, date
    state = DialogueState()
    reqs = ["transaction_ref", "amount", "date"]

    # Turn 1: provide txn only
    state.update(
        new_intent="transaction_dispute",
        new_slots={"transaction_ref": "TXN-9001"},
        required_slots=reqs,
    )
    assert state.intent == "transaction_dispute"
    assert state.awaiting == "amount"

    # Turn 2: provide amount
    state.update(
        new_slots={"amount": 1500},
        required_slots=reqs,
    )
    assert state.awaiting == "date"

    # Turn 3: provide date
    state.update(
        new_slots={"date": "2026-10-24"},
        required_slots=reqs,
    )
    assert state.awaiting is None
    assert state.slots == {
        "transaction_ref": "TXN-9001",
        "amount": 1500,
        "date": "2026-10-24",
    }


def test_dict_serialization():
    s1 = DialogueState(
        intent="balance_check",
        slots={"account_type": "kcc"},
        awaiting=None,
        last_active=12345678.0,
    )
    d = s1.to_dict()
    s2 = DialogueState.from_dict(d)
    assert s2.intent == "balance_check"
    assert s2.slots == {"account_type": "kcc"}
    assert s2.awaiting is None
    assert s2.last_active == 12345678.0

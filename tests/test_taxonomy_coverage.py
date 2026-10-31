#!/usr/bin/env python3
"""
tests/test_taxonomy_coverage.py - Comprehensive coverage for the 25-section Mobile Banking Taxonomy (temp1.md)

Validates:
  1. Section 14 & 20: Sensitive content display & manual-only security actions refused with helpline.
  2. Section 15: High-risk fraud & unrecognized transaction disputes recognized cleanly.
  3. Section 25: Conversational meta-intents (Agent bypass, bot capabilities, clear chat).
  4. Section 2: User profile & KYC status display.
  5. Section 17 & 21: Branch & offline services guidance (chequebook, locker, mutilated notes).
  6. Prevention of false refusals: "money debited without otp" must route to dispute, not refusal.
"""

import pytest
from backend.services.conversation import ConversationService
from core.rules import HELPLINE_PHONE
from nlu.predict import check_unsupported_banking, predict
from pipeline import BankingAssistant


@pytest.fixture
def conv_service():
    return ConversationService()


@pytest.fixture
def assistant():
    return BankingAssistant()


# ---------------------------------------------------------------------------
# Section 14 & 20: Sensitive Content & Manual Security Refusals
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "what is my cvv",
        "tell me my card cvv number",
        "cvv kya hai",
        "what is my otp",
        "tell me my 2fa code",
        "show my atm pin",
        "what is my upi pin",
        "net banking password batao",
        "show my full 16 digit card number",
        "show my pan card number",
        "mera aadhaar number dikhao",
        "statement pdf password kya hai",
        "i lost my debit card",
        "mera credit card kho gaya",
        "mera phone chori ho gaya",
        "my mobile phone was stolen",
        "someone told me to install anydesk",
        "4111 2222 3333 4444",
    ],
)
def test_sensitive_security_actions_refused(text):
    assert check_unsupported_banking(text) is True
    pred = predict(text)
    assert pred["intent"] == "unsupported_banking"
    assert pred["confidence"] >= 0.95


def test_sensitive_query_pipeline_refusal(assistant):
    res = assistant.handle_text("what is my cvv number", customer_id="C001")
    assert res["action"] == "refusal"
    assert res["intent"] == "unsupported_banking"
    assert HELPLINE_PHONE in res["reply"]


# ---------------------------------------------------------------------------
# Section 15: Fraud & Unrecognized Transaction Disputes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "money was debited twice for the same purchase",
        "atm did not dispense cash but money was cut",
        "i do not recognize this transaction on my card",
        "money debited without otp",  # Crucial distinction: dispute, not refusal!
        "charged two times for single transaction",
        "unauthorized direct debit from my account",
        "ek hi transaction ke do baar paise kat gaye",
        "atm se paise nahi nikle lekin khate se kat gaye",
    ],
)
def test_fraud_and_dispute_queries(query):
    pred = predict(query)
    assert pred["intent"] == "transaction_dispute"
    assert pred["confidence"] >= 0.85


# ---------------------------------------------------------------------------
# Section 25: Conversational Meta-Intents
# ---------------------------------------------------------------------------
def test_agent_bypass_returns_helpline(conv_service):
    res = conv_service.process_message("connect me to a human agent please", "en")
    assert res["intent"] == "human_agent"
    assert res["action"] == "account_information"
    assert HELPLINE_PHONE in res["reply"]


def test_bot_identity_and_capabilities(conv_service):
    res = conv_service.process_message("who are you and what can you do", "en")
    assert res["intent"] == "bot_capabilities"
    assert res["action"] == "account_information"
    assert "IndicFinVoice" in res["reply"]
    assert "balance" in res["reply"].lower()


def test_clear_chat_history(conv_service):
    sid = "test-session-clear"
    # Initiate pending session
    conv_service.process_message("check my balance", "en", session_id=sid)
    # Clear session
    res = conv_service.process_message("clear chat history", "en", session_id=sid)
    assert res["intent"] == "clear_chat"
    assert "cleared" in res["reply"].lower()
    # Ensure pending state is completely wiped
    _, pending = conv_service.session_manager.get_or_create(sid)
    assert pending is None


# ---------------------------------------------------------------------------
# Section 2: User Profile & KYC Status Display
# ---------------------------------------------------------------------------
def test_kyc_status_display(conv_service):
    res = conv_service.process_message("what is my kyc status", "en")
    assert res["intent"] == "kyc_status"
    assert "C001" in res["reply"]
    assert "KYC" in res["reply"]


# ---------------------------------------------------------------------------
# Section 17 & 21: Branch & Offline Services Guidance
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        "i want to order a chequebook",
        "how to apply for a bank locker",
        "where can i exchange mutilated notes",
        "i need a demand draft",
    ],
)
def test_branch_offline_services(conv_service, query):
    res = conv_service.process_message(query, "en")
    assert res["intent"] == "branch_services"
    assert "branch" in res["reply"].lower()


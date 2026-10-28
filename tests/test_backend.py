"""
tests/test_backend.py - Unit tests for IndicFinVoice FastAPI Backend Application
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "IndicFinVoice API"
    assert "en" in data["supported_languages"]
    assert "hi" in data["supported_languages"]
    assert "ta" in data["supported_languages"]


def test_chat_english_balance():
    payload = {
        "message": "What is my account balance?",
        "lang": "en",
        "session_id": "test-session-1",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-1"
    assert data["intent"] in ("balance_check", "ask")
    assert "reply" in data
    assert len(data["reply"]) > 0


def test_chat_hindi():
    payload = {
        "message": "मेरा बचत खाता का बैलेंस क्या है",
        "lang": "hi",
        "session_id": "test-session-hi",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "hi"
    assert "खाते" in data["reply"] or "बैलेंस" in data["reply"] or "शेष" in data["reply"]


def test_chat_tamil():
    payload = {
        "message": "எனது சேமிப்பு கணக்கு இருப்பு என்ன",
        "lang": "ta",
        "session_id": "test-session-ta",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lang"] == "ta"
    assert len(data["reply"]) > 0


def test_chat_refusal_block_card():
    payload = {
        "message": "I want to block my card",
        "lang": "en",
        "session_id": "test-session-refusal",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "refusal"
    assert "[BANK_HELPLINE_NUMBER]" in data["reply"]


def test_chat_transactions_query():
    payload = {
        "message": "Show my recent transactions",
        "lang": "en",
        "session_id": "test-session-txns",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "show_transactions"
    assert data["transactions"] is not None
    assert len(data["transactions"]) >= 1


def test_invalid_language():
    payload = {
        "message": "Hello",
        "lang": "fr",  # French not supported
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]


def test_empty_message():
    payload = {
        "message": "   ",
        "lang": "en",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_account_summary_endpoint():
    response = client.get("/account/summary?customer_id=C001")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "C001"
    assert "Savings Account" in data["account_type"]
    assert "XXXX" in data["masked_account"]
    assert data["balance"] > 0

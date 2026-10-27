#!/usr/bin/env python3
"""
tests/test_api.py - Unit tests for mockbank FastAPI endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from mockbank.api import app

client = TestClient(app)


def test_balance_success():
    res = client.get("/balance?customer_id=C001&account_type=savings")
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "C001"
    assert data["account_type"] == "savings"
    assert data["balance"] == 45000

    res_kcc = client.get("/balance?customer_id=C001&account_type=kcc")
    assert res_kcc.status_code == 200
    assert res_kcc.json()["balance"] == 25000


def test_balance_errors():
    # Missing customer_id
    res = client.get("/balance?account_type=savings")
    assert res.status_code == 400
    assert "customer_id" in res.json()["detail"]

    # Missing account_type
    res = client.get("/balance?customer_id=C001")
    assert res.status_code == 400
    assert "account_type" in res.json()["detail"]

    # Unknown customer
    res = client.get("/balance?customer_id=C999&account_type=savings")
    assert res.status_code == 404

    # Unknown account_type
    res = client.get("/balance?customer_id=C001&account_type=crypto")
    assert res.status_code == 400
    assert "savings" in res.json()["detail"]


def test_loan_due_success():
    res = client.get("/loan/due?customer_id=C001&loan_type=crop")
    assert res.status_code == 200
    data = res.json()
    assert data["loan_type"] == "crop"
    assert data["due_date"] == "2026-11-30"
    assert data["outstanding"] == 125000


def test_loan_due_errors():
    # Missing loan_type
    res = client.get("/loan/due?customer_id=C001")
    assert res.status_code == 400
    assert "loan_type" in res.json()["detail"]

    # Unknown loan_type
    res = client.get("/loan/due?customer_id=C001&loan_type=boat")
    assert res.status_code == 400

    # Customer doesn't have this loan
    res = client.get("/loan/due?customer_id=C001&loan_type=home")
    assert res.status_code == 404


def test_claim_status_success():
    res = client.get("/claim/status?customer_id=C001&claim_id=CLM-771")
    assert res.status_code == 200
    data = res.json()
    assert data["claim_id"] == "CLM-771"
    assert data["status"] == "in_process"
    assert data["amount"] == 22000


def test_claim_status_errors():
    # Missing claim_id
    res = client.get("/claim/status?customer_id=C001")
    assert res.status_code == 400
    assert "claim_id" in res.json()["detail"]

    # Unknown claim_id
    res = client.get("/claim/status?customer_id=C001&claim_id=CLM-000")
    assert res.status_code == 404


def test_dispute_success():
    payload = {
        "customer_id": "C001",
        "transaction_ref": "TXN-9001",
        "amount": 1500,
        "date": "2026-10-24",
        "pin": "1234",
    }
    res = client.post("/dispute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "dispute_registered"
    assert data["reference"].startswith("DSP-")
    assert len(data["reference"]) == 8  # 'DSP-' + 4 digits


def test_dispute_errors():
    # Missing field
    payload_missing = {
        "customer_id": "C001",
        "transaction_ref": "TXN-9001",
        "date": "2026-10-24",
        "pin": "1234",
    }
    res = client.post("/dispute", json=payload_missing)
    assert res.status_code == 400
    assert "amount" in res.json()["detail"]

    # Wrong PIN
    payload_wrong_pin = {
        "customer_id": "C001",
        "transaction_ref": "TXN-9001",
        "amount": 1500,
        "date": "2026-10-24",
        "pin": "0000",
    }
    res = client.post("/dispute", json=payload_wrong_pin)
    assert res.status_code == 401
    assert "Invalid PIN" in res.json()["detail"]

    # Unknown transaction_ref
    payload_bad_txn = {
        "customer_id": "C001",
        "transaction_ref": "TXN-8888",
        "amount": 1500,
        "date": "2026-10-24",
        "pin": "1234",
    }
    res = client.post("/dispute", json=payload_bad_txn)
    assert res.status_code == 404

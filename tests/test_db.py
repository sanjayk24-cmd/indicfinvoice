#!/usr/bin/env python3
"""
tests/test_db.py - Validates mockbank/db.json integrity and schema requirements.
"""

import json
import os
import pytest

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "mockbank", "db.json")


def load_db():
    assert os.path.exists(DB_PATH), f"db.json not found at {DB_PATH}"
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_customers_exist():
    db = load_db()
    for cid in ["C001", "C002", "C003"]:
        assert cid in db, f"Customer {cid} missing from db.json"


def test_customer_schema_and_pin():
    db = load_db()
    required_keys = {"pin", "accounts", "loans", "claims", "transactions"}
    for cid, data in db.items():
        assert required_keys.issubset(data.keys()), f"{cid} missing required keys"
        pin = data["pin"]
        assert isinstance(pin, str), f"{cid} PIN must be string"
        assert len(pin) == 4 and pin.isdigit(), f"{cid} PIN must be a 4-digit string"
        assert "savings" in data["accounts"]
        assert set(data["accounts"]).issubset({"savings", "kcc"})  # Some customers have no KCC account.


def test_c001_specific_requirements():
    db = load_db()
    c001 = db["C001"]
    assert "crop" in c001["loans"], "C001 must have a crop loan"
    assert "CLM-771" in c001["claims"], "C001 must have claim CLM-771"
    assert "TXN-9001" in c001["transactions"], "C001 must have transaction TXN-9001"

#!/usr/bin/env python3
"""
mockbank/api.py - Mock Bank API Service

Endpoints:
  - GET /balance?customer_id=&account_type=
  - GET /loan/due?customer_id=&loan_type=
  - GET /claim/status?customer_id=&claim_id=
  - POST /dispute with body {customer_id, transaction_ref, amount, date, pin}
"""

import json
import os
import random
from decimal import Decimal, InvalidOperation
from datetime import date as calendar_date
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "db.json")

VALID_ACCOUNT_TYPES = ["savings", "kcc"]
VALID_LOAN_TYPES = ["crop", "home", "personal"]

# Load database once at startup
with open(DB_PATH, "r", encoding="utf-8") as f:
    BANK_DB: Dict[str, Any] = json.load(f)

# In-memory storage for disputes
DISPUTES: List[Dict[str, Any]] = []

app = FastAPI(title="MockBank API", description="Simulated Core Banking Service")


class DisputePayload(BaseModel):
    customer_id: Optional[Any] = None
    transaction_ref: Optional[Any] = None
    amount: Optional[Any] = None
    date: Optional[Any] = None
    pin: Optional[Any] = None


@app.get("/")
def health_check():
    return {"status": "ok", "service": "mockbank"}


@app.get("/balance")
def get_balance(
    customer_id: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
):
    if not customer_id:
        raise HTTPException(status_code=400, detail="Missing required field: customer_id")
    if not account_type:
        raise HTTPException(status_code=400, detail="Missing required field: account_type")

    cust = BANK_DB.get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    acct_norm = account_type.strip().lower()
    if acct_norm not in VALID_ACCOUNT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown account_type '{account_type}'. Valid values are: {VALID_ACCOUNT_TYPES}",
        )

    accounts = cust.get("accounts", {})
    if acct_norm not in accounts:
        raise HTTPException(
            status_code=404,
            detail=f"Account type '{account_type}' not found for customer '{customer_id}'",
        )

    balance = accounts[acct_norm]["balance"]
    return {
        "customer_id": customer_id,
        "account_type": acct_norm,
        "balance": balance,
    }


@app.get("/loan/due")
def get_loan_due(
    customer_id: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
):
    if not customer_id:
        raise HTTPException(status_code=400, detail="Missing required field: customer_id")
    if not loan_type:
        raise HTTPException(status_code=400, detail="Missing required field: loan_type")

    cust = BANK_DB.get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    loan_norm = loan_type.strip().lower()
    if loan_norm not in VALID_LOAN_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown loan_type '{loan_type}'. Valid values are: {VALID_LOAN_TYPES}",
        )

    loans = cust.get("loans", {})
    if loan_norm not in loans:
        raise HTTPException(
            status_code=404,
            detail=f"Loan type '{loan_type}' not found for customer '{customer_id}'",
        )

    loan_info = loans[loan_norm]
    return {
        "customer_id": customer_id,
        "loan_type": loan_norm,
        "due_date": loan_info["due_date"],
        "outstanding": loan_info["outstanding"],
    }


@app.get("/claim/status")
def get_claim_status(
    customer_id: Optional[str] = Query(None),
    claim_id: Optional[str] = Query(None),
):
    if not customer_id:
        raise HTTPException(status_code=400, detail="Missing required field: customer_id")
    if not claim_id:
        raise HTTPException(status_code=400, detail="Missing required field: claim_id")

    cust = BANK_DB.get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    claim_key = claim_id.strip()
    claims = cust.get("claims", {})
    if claim_key not in claims:
        # Check case-insensitive match
        matched_k = next((k for k in claims if k.lower() == claim_key.lower()), None)
        if matched_k:
            claim_key = matched_k
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Claim ID '{claim_id}' not found for customer '{customer_id}'",
            )

    claim_info = claims[claim_key]
    return {
        "customer_id": customer_id,
        "claim_id": claim_key,
        "status": claim_info["status"],
        "amount": claim_info["amount"],
    }


@app.post("/dispute")
def post_dispute(payload: DisputePayload):
    # Required fields check
    for field_name in ["customer_id", "transaction_ref", "amount", "date", "pin"]:
        val = getattr(payload, field_name)
        if val is None or str(val).strip() == "":
            raise HTTPException(status_code=400, detail=f"Missing required field: {field_name}")

    # Typed text only PIN requirement
    if not isinstance(payload.pin, str):
        raise HTTPException(status_code=400, detail="PIN must be provided as typed text only (string)")

    customer_id = str(payload.customer_id).strip()
    cust = BANK_DB.get(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

    # PIN check
    if payload.pin.strip() != cust.get("pin"):
        raise HTTPException(status_code=401, detail="Invalid PIN")

    # Transaction ref check
    txn_ref = str(payload.transaction_ref).strip()
    txns = cust.get("transactions", {})
    if txn_ref not in txns:
        matched_ref = next((k for k in txns if k.lower() == txn_ref.lower()), None)
        if matched_ref:
            txn_ref = matched_ref
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction reference '{txn_ref}' not found for customer '{customer_id}'",
            )

    # Validate against the customer's actual transaction, using decimal money.
    txn = txns[txn_ref]
    try:
        amount = Decimal(str(payload.amount))
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValueError()
        supplied_date = calendar_date.fromisoformat(str(payload.date))
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Provide a positive amount with at most two decimal places and a valid YYYY-MM-DD date")
    if amount != Decimal(str(txn['amount'])) or supplied_date.isoformat() != txn['date']:
        raise HTTPException(status_code=400, detail="Dispute amount and date must match the referenced transaction")
    if txn.get('status') != 'completed':
        raise HTTPException(status_code=409, detail="Only completed transactions can be disputed in this demo")
    for existing in DISPUTES:
        if existing['customer_id'] == customer_id and existing['transaction_ref'] == txn_ref:
            return {'status': existing['status'], 'reference': existing['reference']}

    # In-memory storage for dispute
    ref_digits = f"{random.randint(1000, 9999)}"
    dispute_ref = f"DSP-{ref_digits}"
    dispute_record = {
        "reference": dispute_ref,
        "customer_id": customer_id,
        "transaction_ref": txn_ref,
        "amount": payload.amount,
        "date": payload.date,
        "status": "dispute_registered",
    }
    DISPUTES.append(dispute_record)

    return {
        "status": "dispute_registered",
        "reference": dispute_ref,
    }

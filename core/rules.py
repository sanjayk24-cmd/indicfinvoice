#!/usr/bin/env python3
"""
core/rules.py - Rules Layer & Action Decision Engine

Decides next system action based on intent, slots, and confidence:
  - confidence < 0.6: repeat
  - intent == "out_of_scope": help
  - intent == "unsupported_banking": refusal with helpline message
  - missing/empty required slots: ask clarifying question
  - transaction_dispute with all slots: need_pin
  - valid request with all slots: call_api
"""

from typing import Any, Dict, List, Optional

CONFIDENCE_THRESHOLD = 0.6
HELPLINE_PHONE = "[BANK_HELPLINE_NUMBER]"

REQUIRED_SLOTS: Dict[str, List[str]] = {
    "balance_check": ["account_type"],
    "loan_due_date": ["loan_type"],
    "crop_insurance_status": ["claim_id"],
    "transaction_dispute": ["transaction_ref", "amount", "date"],
}

QUESTIONS: Dict[str, str] = {
    "account_type": "Aapko savings account ka balance dekhna hai ya KCC ka?",
    "loan_type": "Aapka loan type kya hai? Home, crop, ya personal?",
    "claim_id": "Kripya apna crop insurance claim ID batayein (jaise CLM-771)?",
    "transaction_ref": "Kripya transaction reference number batayein (jaise TXN-9001)?",
    "amount": "Dispute kiye ja rahe transaction ki amount kitni hai?",
    "date": "Yeh transaction kis tareekh ko hua tha?",
}

UNSUPPORTED_BANKING_INTENTS = {
    "unsupported_banking",
    "lost_or_stolen_card",
    "pin_blocked",
    "compromised_card",
    "change_pin",
    "pending_transfer",
    "failed_transfer",
    "cvv_inquiry",
    "otp_inquiry",
    "pin_reveal",
    "credential_request",
}


def next_action(
    intent: Optional[str],
    slots: Optional[Dict[str, Any]],
    confidence: float,
) -> Dict[str, Any]:
    """
    Evaluates rules deterministically to choose the next action.
    """
    slots = slots or {}

    # 1. Low confidence -> repeat
    if confidence < CONFIDENCE_THRESHOLD:
        return {"action": "repeat"}

    # 2. Out of scope -> help
    if intent == "out_of_scope":
        return {"action": "help"}

    # 3. Unsupported / sensitive banking query -> refusal with helpline
    if intent in UNSUPPORTED_BANKING_INTENTS:
        return {
            "action": "refusal",
            "reason": "unsupported_banking",
            "message": f"This request cannot be processed via automated assistant for security reasons. Please use secure in-app controls or call our 24x7 bank helpline at {HELPLINE_PHONE} immediately.",
            "helpline": HELPLINE_PHONE,
        }

    # 4. Check required slots
    req_slots = REQUIRED_SLOTS.get(intent, [])
    for slot_name in req_slots:
        val = slots.get(slot_name)
        # Empty string, None, or whitespace-only is treated as missing
        if val is None or str(val).strip() == "":
            return {
                "action": "ask",
                "slot": slot_name,
                "question": QUESTIONS.get(slot_name, f"Please provide {slot_name}."),
            }

    # 5. Transaction dispute requires PIN authentication
    if intent == "transaction_dispute":
        return {
            "action": "need_pin",
            "intent": intent,
            "slots": slots,
        }

    # 6. All required slots present -> call bank API
    return {
        "action": "call_api",
        "intent": intent,
        "slots": slots,
    }

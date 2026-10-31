#!/usr/bin/env python3
"""
pipeline.py - End-to-End Voice Banking Assistant Pipeline

Integrates:
  - Language Identification (core/lang_id.py)
  - Speech Recognition (asr/transcribe.py)
  - Joint NLU (nlu/predict.py)
  - Slot Normalisation (core/normalise.py)
  - Dialogue State Tracking (core/dialogue.py)
  - Deterministic Rule Engine (core/rules.py)
  - Multilingual Responses (core/responses.json)
  - MockBank API (mockbank/api.py)
"""

import json
import os
from typing import Any, Dict, Optional
import httpx
import yaml
from fastapi.testclient import TestClient

from asr.transcribe import transcribe
from core.dialogue import DialogueState, is_cancel_word
from core.lang_id import identify_language
from core.normalise import (
    normalise_account_type,
    normalise_amount,
    normalise_claim_id,
    normalise_date,
    normalise_loan_type,
    normalise_slots,
    normalise_transaction_ref,
)
from core.rules import next_action
from mockbank.api import app as mockbank_app
from nlu.predict import predict

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs", "settings.yaml")
RESPONSES_PATH = os.path.join(os.path.dirname(__file__), "core", "responses.json")


def load_responses() -> dict:
    if os.path.exists(RESPONSES_PATH):
        with open(RESPONSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_settings() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


RESPONSES = load_responses()
SETTINGS = load_settings()


class BankingAssistant:
    def __init__(self, settings_path: Optional[str] = None):
        self.settings = SETTINGS
        if settings_path and os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings = yaml.safe_load(f) or {}

        self.mockbank_url = self.settings.get("mockbank_url", "http://127.0.0.1:8000")
        self.test_client = TestClient(mockbank_app)

    def _call_bank_api(
        self,
        intent: str,
        slots: Dict[str, Any],
        customer_id: str,
        pin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls the mock bank API. Attempts live HTTP first; falls back to in-process TestClient.
        """
        try:
            if intent == "balance_check":
                account_type = slots.get("account_type")
                endpoint = f"/balance?customer_id={customer_id}&account_type={account_type}"
                try:
                    r = httpx.get(f"{self.mockbank_url}{endpoint}", timeout=2.0)
                    if r.status_code == 200:
                        return r.json()
                    return {"error": r.json().get("detail", f"HTTP {r.status_code}")}
                except (httpx.ConnectError, httpx.TimeoutException):
                    res = self.test_client.get(endpoint)
                    if res.status_code == 200:
                        return res.json()
                    return {"error": res.json().get("detail", f"HTTP {res.status_code}")}

            elif intent == "loan_due_date":
                loan_type = slots.get("loan_type")
                endpoint = f"/loan/due?customer_id={customer_id}&loan_type={loan_type}"
                try:
                    r = httpx.get(f"{self.mockbank_url}{endpoint}", timeout=2.0)
                    if r.status_code == 200:
                        return r.json()
                    return {"error": r.json().get("detail", f"HTTP {r.status_code}")}
                except (httpx.ConnectError, httpx.TimeoutException):
                    res = self.test_client.get(endpoint)
                    if res.status_code == 200:
                        return res.json()
                    return {"error": res.json().get("detail", f"HTTP {res.status_code}")}

            elif intent == "crop_insurance_status":
                claim_id = slots.get("claim_id")
                endpoint = f"/claim/status?customer_id={customer_id}&claim_id={claim_id}"
                try:
                    r = httpx.get(f"{self.mockbank_url}{endpoint}", timeout=2.0)
                    if r.status_code == 200:
                        return r.json()
                    return {"error": r.json().get("detail", f"HTTP {r.status_code}")}
                except (httpx.ConnectError, httpx.TimeoutException):
                    res = self.test_client.get(endpoint)
                    if res.status_code == 200:
                        return res.json()
                    return {"error": res.json().get("detail", f"HTTP {res.status_code}")}

            elif intent == "transaction_dispute":
                payload = {
                    "customer_id": customer_id,
                    "transaction_ref": slots.get("transaction_ref"),
                    "amount": slots.get("amount"),
                    "date": slots.get("date"),
                    "pin": str(pin).strip() if pin else "",
                }
                try:
                    r = httpx.post(f"{self.mockbank_url}/dispute", json=payload, timeout=2.0)
                    if r.status_code == 200:
                        return r.json()
                    return {"error": r.json().get("detail", f"HTTP {r.status_code}")}
                except (httpx.ConnectError, httpx.TimeoutException):
                    res = self.test_client.post("/dispute", json=payload)
                    if res.status_code == 200:
                        return res.json()
                    return {"error": res.json().get("detail", f"HTTP {res.status_code}")}

            return {"error": f"Unknown intent for bank API: {intent}"}

        except Exception as e:
            return {"error": str(e)}

    def handle_text(
        self,
        text: str,
        customer_id: str = "C001",
        pending: Optional[Dict[str, Any]] = None,
        pin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes a single turn of text input.
        Returns:
          {
            "reply": str,
            "intent": str,
            "confidence": float,
            "slots": dict,
            "action": str,
            "pending": dict | None
          }
        """
        lang = identify_language(text)

        # 1. Check cancel words
        if is_cancel_word(text):
            reply = RESPONSES.get("actions", {}).get("cancelled", {}).get(lang, "Request cancelled.")
            return {
                "reply": reply,
                "intent": "cancel",
                "confidence": 1.0,
                "slots": {},
                "action": "cancel",
                "pending": None,
            }

        # 2. Dialogue state recovery
        state = DialogueState.from_dict(pending)
        if state.is_expired():
            state.clear()

        # 3. NLU prediction
        pred = predict(text)
        intent = pred["intent"]
        slots = dict(pred["slots"])
        confidence = pred["confidence"]

        # 4. State updating & slot accumulation across turns
        if state.awaiting is not None:
            # Check if user switched to an entirely new banking intent
            is_new_request = (
                intent != state.intent
                and intent not in ("out_of_scope", "repeat", "unsupported_banking", None)
            )

            if is_new_request:
                # Discard previous request
                state.clear()
                state.update(new_intent=intent, new_slots=slots)
            else:
                # Continuation turn: extract value for awaiting slot if not already found
                if state.awaiting not in slots or not slots[state.awaiting]:
                    if state.awaiting == "account_type":
                        v = normalise_account_type(text)
                        if v:
                            slots["account_type"] = v
                    elif state.awaiting == "loan_type":
                        v = normalise_loan_type(text)
                        if v:
                            slots["loan_type"] = v
                    elif state.awaiting == "claim_id":
                        v = normalise_claim_id(text)
                        if v:
                            slots["claim_id"] = v
                    elif state.awaiting == "transaction_ref":
                        v = normalise_transaction_ref(text)
                        if v:
                            slots["transaction_ref"] = v
                    elif state.awaiting == "amount":
                        v = normalise_amount(text)
                        if v:
                            slots["amount"] = v
                    elif state.awaiting == "date":
                        v = normalise_date(text)
                        if v:
                            slots["date"] = v

                # Update state with continuation turn
                state.update(new_intent=state.intent, new_slots=slots)
                intent = state.intent
                slots = dict(state.slots)
                # If slot was filled, keep confidence high
                if confidence < 0.6 and slots.get(state.awaiting):
                    confidence = 0.95
        else:
            state.update(new_intent=intent, new_slots=slots)
            slots = dict(state.slots)

        # 5. Rule execution
        action_decision = next_action(intent, slots, confidence)
        action = action_decision["action"]

        # 6. Action dispatch & response formatting
        if action == "repeat":
            reply = RESPONSES.get("actions", {}).get("repeat", {}).get(
                lang, "Could you please repeat your request?"
            )
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": action,
                "pending": state.to_dict() if state.intent else None,
            }

        elif action == "help":
            reply = RESPONSES.get("actions", {}).get("help", {}).get(
                lang, "I can help with balance checks, loan due dates, insurance claims, or disputes."
            )
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": action,
                "pending": None,
            }

        elif action == "refusal":
            helpline = action_decision.get("helpline", "[BANK_HELPLINE_NUMBER]")
            template = RESPONSES.get("actions", {}).get("refusal", {}).get(lang)
            if template:
                reply = template.format(helpline=helpline)
            else:
                reply = action_decision.get("message", f"Please call bank helpline at {helpline}.")
            state.clear()
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": action,
                "pending": None,
            }

        elif action == "info":
            info_dict = action_decision.get("message", {})
            if isinstance(info_dict, dict):
                reply = info_dict.get(lang, info_dict.get("en", "Request information processed."))
            else:
                reply = str(info_dict)
            state.clear()
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": action,
                "pending": None,
            }

        elif action == "ask":
            missing_slot = action_decision["slot"]
            state.awaiting = missing_slot
            ask_dict = RESPONSES.get("actions", {}).get("ask", {}).get(missing_slot, {})
            reply = ask_dict.get(lang, action_decision.get("question", f"Please provide {missing_slot}."))
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": action,
                "pending": state.to_dict(),
            }

        elif action == "need_pin":
            if not pin or str(pin).strip() == "":
                reply = RESPONSES.get("actions", {}).get("need_pin", {}).get(
                    lang, "Please provide your 4-digit PIN."
                )
                return {
                    "reply": reply,
                    "intent": intent,
                    "confidence": confidence,
                    "slots": slots,
                    "action": "need_pin",
                    "pending": state.to_dict(),
                }
            else:
                # PIN is present, proceed to API execution
                action = "call_api"

        if action == "call_api":
            api_res = self._call_bank_api(intent, slots, customer_id, pin=pin)
            if "error" in api_res:
                err_msg = api_res["error"]
                err_tmpl = RESPONSES.get("actions", {}).get("error", {}).get(
                    lang, "An error occurred: {error}"
                )
                reply = err_tmpl.format(error=err_msg)
                return {
                    "reply": reply,
                    "intent": intent,
                    "confidence": confidence,
                    "slots": slots,
                    "action": "error",
                    "pending": state.to_dict(),
                }

            # Successful API response mapping
            template = RESPONSES.get("intents", {}).get(intent, {}).get(lang)
            if not template:
                template = RESPONSES.get("intents", {}).get(intent, {}).get("en", "Success: {status}")

            fmt_data = {}
            fmt_data.update(slots)
            fmt_data.update(api_res)
            try:
                reply = template.format(**fmt_data)
            except KeyError:
                reply = f"Bank API Result: {api_res}"

            state.clear()
            return {
                "reply": reply,
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "action": "call_api",
                "pending": None,
            }

        return {
            "reply": "Request processed.",
            "intent": intent,
            "confidence": confidence,
            "slots": slots,
            "action": action,
            "pending": None,
        }

    def handle_audio(
        self,
        path: str,
        customer_id: str = "C001",
        pending: Optional[Dict[str, Any]] = None,
        pin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribes speech audio, then runs handle_text.
        """
        transcript = transcribe(path)
        res = self.handle_text(transcript, customer_id=customer_id, pending=pending, pin=pin)
        res["transcript"] = transcript
        return res

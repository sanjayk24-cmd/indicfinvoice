#!/usr/bin/env python3
"""
core/dialogue.py - Dialogue State Tracking Across Turns

Maintains DialogueState:
  - intent: Current active intent (e.g. balance_check, loan_due_date, etc.)
  - slots: Accumulated normalised slot values
  - awaiting: Slot currently being prompted for (or None)
  - last_active: Epoch timestamp of last user interaction

Key Rules:
  - 5-minute expiry (300 seconds): If inactive > 5 minutes, state is reset.
  - Cancel words ("cancel", "रद्द", "ரத்து") clear the state.
  - If awaiting is set and input fills that slot, fill it and update awaiting.
  - If awaiting is set and input is a new banking request with different intent,
    discard old state and start the new request.
"""

import time
from typing import Any, Dict, List, Optional

CANCEL_WORDS = {
    "cancel",
    "रद्द",
    "रद्द करें",
    "रद्द करो",
    "ரத்து",
    "ரத்து செய்",
    "stop",
    "quit",
    "exit",
}

EXPIRY_SECONDS = 300.0  # 5 minutes


def is_cancel_word(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    for cw in CANCEL_WORDS:
        if t == cw or t.startswith(cw + " ") or t.endswith(" " + cw):
            return True
    return False


class DialogueState:
    def __init__(
        self,
        intent: Optional[str] = None,
        slots: Optional[Dict[str, Any]] = None,
        awaiting: Optional[str] = None,
        last_active: Optional[float] = None,
    ):
        self.intent = intent
        self.slots: Dict[str, Any] = dict(slots) if slots else {}
        self.awaiting = awaiting
        self.last_active = last_active if last_active is not None else time.time()

    def is_expired(self, current_time: Optional[float] = None, timeout: float = EXPIRY_SECONDS) -> bool:
        now = current_time if current_time is not None else time.time()
        return (now - self.last_active) > timeout

    def clear(self):
        self.intent = None
        self.slots = {}
        self.awaiting = None
        self.last_active = time.time()

    def update(
        self,
        new_intent: Optional[str] = None,
        new_slots: Optional[Dict[str, Any]] = None,
        required_slots: Optional[List[str]] = None,
        current_time: Optional[float] = None,
    ):
        now = current_time if current_time is not None else time.time()

        # Check expiry
        if self.is_expired(current_time=now):
            self.clear()

        new_slots = new_slots or {}

        # If we were awaiting a slot
        if self.awaiting is not None:
            # Check if this is a brand new banking intent that overrides the previous one
            is_new_banking_intent = (
                new_intent is not None
                and new_intent != self.intent
                and new_intent not in ("out_of_scope", "repeat", None)
            )

            if is_new_banking_intent:
                # Discard old state and start new request
                self.intent = new_intent
                self.slots = dict(new_slots)
            else:
                # Continuation turn: fill awaiting slot if provided
                if self.awaiting in new_slots:
                    val = new_slots[self.awaiting]
                    if val is not None and str(val).strip() != "":
                        self.slots[self.awaiting] = val
                # Also accept any other slots passed in
                for k, v in new_slots.items():
                    if v is not None and str(v).strip() != "":
                        self.slots[k] = v
        else:
            # Starting fresh or updating existing
            if new_intent and new_intent not in ("out_of_scope", "repeat"):
                self.intent = new_intent
            for k, v in new_slots.items():
                if v is not None and str(v).strip() != "":
                    self.slots[k] = v

        # Determine next awaiting slot from required_slots
        if required_slots and self.intent:
            missing = None
            for req in required_slots:
                val = self.slots.get(req)
                if val is None or str(val).strip() == "":
                    missing = req
                    break
            self.awaiting = missing
        else:
            self.awaiting = None

        self.last_active = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "slots": dict(self.slots),
            "awaiting": self.awaiting,
            "last_active": self.last_active,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DialogueState":
        if not data:
            return cls()
        return cls(
            intent=data.get("intent"),
            slots=data.get("slots", {}),
            awaiting=data.get("awaiting"),
            last_active=data.get("last_active"),
        )

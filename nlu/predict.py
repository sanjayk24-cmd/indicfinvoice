#!/usr/bin/env python3
"""
nlu/predict.py - NLU Prediction Service

Loads the trained JointNLU model and tokenizer once at module import.
Function:
  predict(text: str) -> dict
  Returns: {"intent": str, "slots": dict, "confidence": float}
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
import torch
from transformers import AutoTokenizer

from core.normalise import (
    normalise_account_type,
    normalise_loan_type,
    normalise_claim_id,
    normalise_transaction_ref,
    normalise_amount,
    normalise_date,
    normalise_slots,
)
from nlu.model import JointNLU

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "indicfinvoice_v1")
LABEL_MAPS_PATH = os.path.join(MODEL_DIR, "label_maps.json")

# Unsupported / sensitive banking keywords (e.g. lost/stolen card, blocked pin, etc.)
UNSUPPORTED_COMBOS = [
    # Lost or stolen card
    (
        ["card", "कार्ड", "கார்டு"],
        ["lost", "stolen", "missing", "खो", "चोरी", "गायब", "தொலைந்து", "திருடு"],
    ),
    # Blocked card or PIN
    (
        ["card", "pin", "कार्ड", "पिन", "கார்டு", "பின்"],
        ["block", "blocked", "बंद", "பிளாக்"],
    ),
    # Change / reset PIN
    (
        ["pin", "पिन", "பின்"],
        ["change", "reset", "बदल", "மாற்று"],
    ),
]

INTENT_KEYWORDS = {
    "transaction_dispute": ["dispute", "आपत्ति", "शिकायत", "புகார்", "சர்ச்சை", "txn-", "txn"],
    "crop_insurance_status": ["claim", "insurance", "दावा", "बीमा", "கிளைம்", "காப்பீடு", "clm-", "clm"],
    "loan_due_date": ["loan", "ऋण", "लोन", "கடன்", "due date", "किस्त", "due"],
    "balance_check": ["balance", "बैलेंस", "शेष", "இருப்பு", "மீதி"],
}

# Load model and tokenizer once at module import
if os.path.exists(MODEL_DIR) and os.path.exists(LABEL_MAPS_PATH):
    with open(LABEL_MAPS_PATH, "r", encoding="utf-8") as f:
        maps = json.load(f)
    ID2INTENT = maps["id2intent"]
    ID2TAG = maps["id2tag"]

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    TOKENIZER = AutoTokenizer.from_pretrained(MODEL_DIR)
    MODEL = JointNLU.from_pretrained(MODEL_DIR)
    MODEL.to(DEVICE)
    MODEL.eval()
else:
    ID2INTENT = {}
    ID2TAG = {}
    TOKENIZER = None
    MODEL = None
    DEVICE = "cpu"


def check_unsupported_banking(text: str) -> bool:
    t = text.lower()
    for g1, g2 in UNSUPPORTED_COMBOS:
        if any(w in t for w in g1) and any(w in t for w in g2):
            return True
    return False


def _heuristic_slot_extraction(text: str) -> Dict[str, Any]:
    """
    Extracts known slots directly from text using normalisers as a fallback / complement.
    """
    slots = {}
    tokens = text.strip().split()

    # Check whole text and n-grams for slot candidates
    # account_type
    acct = normalise_account_type(text)
    if acct:
        slots["account_type"] = acct
    else:
        for w in tokens:
            ac = normalise_account_type(w)
            if ac:
                slots["account_type"] = ac
                break

    # loan_type
    loan = normalise_loan_type(text)
    if loan:
        slots["loan_type"] = loan
    else:
        for w in tokens:
            ln = normalise_loan_type(w)
            if ln:
                slots["loan_type"] = ln
                break

    # claim_id
    cid = normalise_claim_id(text)
    if cid:
        slots["claim_id"] = cid

    # transaction_ref
    tref = normalise_transaction_ref(text)
    if tref:
        slots["transaction_ref"] = tref

    # amount
    amt = normalise_amount(text)
    if amt:
        slots["amount"] = amt

    # date
    dt = normalise_date(text)
    if dt:
        slots["date"] = dt

    return slots


def predict(text: str) -> Dict[str, Any]:
    """
    Predicts intent, slots, and confidence for a given input sentence.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return {"intent": "out_of_scope", "slots": {}, "confidence": 1.0}

    # 1. First check sensitive/unsupported banking patterns
    if check_unsupported_banking(cleaned_text):
        return {
            "intent": "unsupported_banking",
            "slots": {},
            "confidence": 0.99,
        }

    slots: Dict[str, Any] = {}
    confidence = 0.5
    predicted_intent = "out_of_scope"

    words = cleaned_text.split()

    if MODEL is not None and TOKENIZER is not None:
        try:
            encoding = TOKENIZER(
                words,
                is_split_into_words=True,
                return_tensors="pt",
                truncation=True,
                max_length=128,
            )
            input_ids = encoding["input_ids"].to(DEVICE)
            attention_mask = encoding["attention_mask"].to(DEVICE)

            with torch.no_grad():
                intent_logits, slot_logits = MODEL(input_ids, attention_mask)

            # Intent decoding
            probs = torch.softmax(intent_logits, dim=-1)[0]
            conf, pred_intent_id = torch.max(probs, dim=-1)
            confidence = float(conf.item())
            predicted_intent = ID2INTENT.get(str(pred_intent_id.item()), "out_of_scope")

            # Slot decoding
            pred_tags = torch.argmax(slot_logits[0], dim=-1).cpu().tolist()
            word_ids = encoding.word_ids(batch_index=0)

            # Map predictions to first subword of each word
            word_tags = []
            prev_word = None
            for token_idx, word_idx in enumerate(word_ids):
                if word_idx is None:
                    continue
                if word_idx != prev_word:
                    tag_id = pred_tags[token_idx]
                    tag_name = ID2TAG.get(str(tag_id), "O")
                    word_tags.append((words[word_idx], tag_name))
                    prev_word = word_idx

            # Extract entities from BIO tags
            cur_slot = None
            cur_tokens = []
            for word, tag in word_tags:
                if tag.startswith("B-"):
                    if cur_slot is not None:
                        slots[cur_slot] = " ".join(cur_tokens)
                    cur_slot = tag[2:]
                    cur_tokens = [word]
                elif tag.startswith("I-") and cur_slot == tag[2:]:
                    cur_tokens.append(word)
                else:
                    if cur_slot is not None:
                        slots[cur_slot] = " ".join(cur_tokens)
                    cur_slot = None
                    cur_tokens = []
            if cur_slot is not None:
                slots[cur_slot] = " ".join(cur_tokens)

        except Exception as e:
            # Fallback if inference fails
            predicted_intent = "out_of_scope"
            confidence = 0.5

    # Complement/normalise slot extraction
    heuristic_slots = _heuristic_slot_extraction(cleaned_text)
    for k, v in heuristic_slots.items():
        if k not in slots or not slots[k]:
            slots[k] = v

    # Keyword intent fallback if model output is uncertain or out_of_scope on clear banking query
    if predicted_intent == "out_of_scope" or confidence < 0.6:
        text_lower = cleaned_text.lower()
        for cand_intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                predicted_intent = cand_intent
                confidence = max(confidence, 0.95)
                break

    # Normalise all extracted slots
    normalised = normalise_slots(slots)
    # Explicitly labelled monetary values outrank noisy BIO tags (e.g. a year).
    explicit_amount = re.search(r'(?:amount|राशि|தொகை|₹|rs\.?|inr)\s*[:=]?\s*(\d[\d,]*(?:\.\d{1,2})?)', cleaned_text, re.IGNORECASE)
    if explicit_amount:
        from decimal import Decimal
        value = Decimal(explicit_amount.group(1).replace(',', ''))
        normalised['amount'] = int(value) if value == value.to_integral() else float(value)

    return {
        "intent": predicted_intent,
        "slots": normalised,
        "confidence": round(confidence, 4),
    }

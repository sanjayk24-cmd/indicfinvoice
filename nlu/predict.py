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
        ["card", "कार्ड", "கார்டு", "atm", "debit card", "credit card"],
        ["lost", "stolen", "missing", "खो", "चोरी", "गायब", "தொலைந்து", "திருடு", "kho gaya", "chori ho gaya"],
    ),
    # Blocked or freeze card / PIN
    (
        ["card", "pin", "कार्ड", "पिन", "கார்டு", "பின்", "atm", "debit card", "credit card"],
        ["block", "blocked", "blocking", "बंद", "பிளாக்", "freeze", "lock", "deactivate", "band kar", "band karo"],
    ),
    # Change / reset PIN
    (
        ["pin", "पिन", "பின்", "password", "पासवर्ड", "கடவுச்சொல்"],
        ["change", "reset", "बदल", "மாற்று", "forgot", "bhool"],
    ),
]

INTENT_KEYWORDS = {
    "crop_insurance_status": [
        # English
        "crop insurance", "insurance claim", "claim status", "crop claim", "insurance status",
        "pmfby", "clm-", "claim", "insurance", "policy status",
        # Hindi (Devanagari)
        "फसल बीमा", "बीमा दावा", "दावा स्थिति", "बीमा का क्या हुआ", "बीमा स्टेटस", "फसल क्लेम", "बीमा", "दावा", "पॉलिसी",
        # Hindi (Romanized / Hinglish)
        "fasal bima", "fasal beema", "bima", "claim status", "bima status", "claim ka kya hua", "bima ka kya hua", "kisan bima",
        # Tamil (Script)
        "பயிர் காப்பீடு", "காப்பீட்டு", "கிளைம்", "காப்பீடு நிலை", "பயிர் கிளைம்", "காப்பீடு", "பயிர் காப்பீட்டு",
        # Tamil (Latin)
        "payir kaappeedu", "kaappeedu", "kaapeedu",
    ],
    "transaction_dispute": [
        # English
        "dispute", "unauthorized", "unauthorised", "wrong transaction", "money deducted", "stole money",
        "stolen from account", "deducted without", "money cut", "fraudulent", "fraud", "txn-", "dispute transaction",
        "charged twice", "wrong debit", "debited wrongly", "incorrect charge", "stole",
        # Hindi (Devanagari)
        "आपत्ति", "शिकायत", "गलत लेनदेन", "पैसे कट गए", "पैसे कट गए हैं", "बिना अनुमति", "धोखाधड़ी", "फ्रॉड", "गलत कटा",
        # Hindi (Romanized / Hinglish)
        "paise kat gaye", "paise cut gaye", "galat transaction", "paise deduct", "kat gaye", "kat gaya", "paise cut",
        "galat kata", "shikayat",
        # Tamil (Script)
        "சர்ச்சை", "புகார்", "தவறான பரிவர்த்தனை", "பணம் எடுக்கப்பட்டுள்ளது", "பணம் கழிப்பட்டது", "மோசடி", "தவறாக பிடித்தம்",
        # Tamil (Latin)
        "thavarana", "panam edukkappattullathu", "pukaar",
    ],
    "loan_due_date": [
        # English
        "loan", "due date", "emi", "due", "pay my debt", "debt", "repay", "repayment", "installment",
        "next payment", "repayment date", "loan payment", "loan status", "emi due", "when to pay", "pay loan", "when is my emi",
        # Hindi (Devanagari)
        "ऋण", "लोन", "किस्त", "ईएमआई", "ड्यू डेट", "कब भरना", "कब भरनी", "कब देना", "चुकाना", "तारीख", "देय तिथि", "भुगतान",
        # Hindi (Romanized / Hinglish)
        "emi", "due date", "kab bharna", "kab bharni", "kab dena", "chukana", "kisht", "loan kab", "kcc loan", "home loan",
        # Tamil (Script)
        "கடன்", "தவணை", "ஈஎம்ஐ", "தேதி", "எப்போது கட்ட", "செலுத்த வேண்டும்", "கடைசி தேதி", "கடன் தவணை", "கடன் தேதி", "வீட்டுக் கடன்",
        # Tamil (Latin)
        "kadan", "thavanai", "eppothu katta", "thethi",
    ],
    "balance_check": [
        # English
        "balance", "how much money", "how much do i have", "money left", "account balance", "bank balance",
        "funds", "how much is in", "savings balance", "how much in my savings", "check balance", "current balance",
        "check my balance", "total balance", "remaining balance", "available balance", "money in my account", "how much in",
        # Hindi (Devanagari)
        "बैलेंस", "शेष", "कितना पैसा", "कितने पैसे", "पैसे कितने", "रुपये कितने", "राशि", "खाते में कितना",
        "बचा है", "खाता शेष", "पैसा कितना", "बैलेंस कितना", "रुपए कितने", "खाते का बैलेंस",
        # Hindi (Romanized / Hinglish)
        "paisa kitna", "paise kitne", "kitna paisa", "kitne paise", "kitna bacha", "kitne rupaye", "kitna rupaya",
        "rupaye kitne", "paise hain", "khate me kitna", "account me kitna", "balance kitna", "kitna balance",
        # Tamil (Script)
        "இருப்பு", "மீதி", "பேலன்ஸ்", "எவ்வளவு பணம்", "பணம் எவ்வளவு", "பணம் இருக்கு", "கணக்கில் எவ்வளவு",
        "தொகை எவ்வளவு", "எவ்வளவு இருக்கு", "கணக்கு இருப்பு", "சேமிப்பு இருப்பு",
        # Tamil (Latin)
        "iruppu", "meethi", "panam evvalavu", "evvalavu panam", "panam irukku",
    ],
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
        is_temporal_current = bool(re.search(r"\bcurrent\s+(?:balance|status|amount|emi|due|rate|date|month|year|situation)\b", text.lower()))
        for w in tokens:
            if is_temporal_current and w.lower() == "current":
                continue
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

    # Disambiguation / Keyword Matching
    text_lower = cleaned_text.lower()
    matched_intent = None
    for cand_intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched_intent = cand_intent
            break

    # Resolve intent with multi-tier validation:
    # 1. Direct slot evidence (e.g. claim_id is always crop_insurance, txn_ref is dispute)
    if slots.get("claim_id"):
        predicted_intent = "crop_insurance_status"
        confidence = max(confidence, 0.95)
    elif slots.get("transaction_ref") and matched_intent == "transaction_dispute":
        predicted_intent = "transaction_dispute"
        confidence = max(confidence, 0.95)
    elif matched_intent == "crop_insurance_status":
        # Never allow crop insurance queries to be misclassified as loan_due_date
        predicted_intent = "crop_insurance_status"
        confidence = max(confidence, 0.95)
    elif matched_intent == "transaction_dispute" and predicted_intent != "transaction_dispute":
        predicted_intent = "transaction_dispute"
        confidence = max(confidence, 0.95)
    elif matched_intent == "loan_due_date" and (predicted_intent in ("out_of_scope", "balance_check") or confidence < 0.75):
        # Prevent "mera kcc loan kab bharna hai" from falling into balance_check
        predicted_intent = "loan_due_date"
        confidence = max(confidence, 0.95)
    elif matched_intent == "balance_check" and (predicted_intent in ("out_of_scope", "loan_due_date") or confidence < 0.75):
        predicted_intent = "balance_check"
        confidence = max(confidence, 0.95)
    elif predicted_intent == "out_of_scope" or confidence < 0.6:
        if matched_intent:
            predicted_intent = matched_intent
            confidence = max(confidence, 0.95)
        elif slots.get("account_type"):
            predicted_intent = "balance_check"
            confidence = max(confidence, 0.95)
        elif slots.get("loan_type"):
            predicted_intent = "loan_due_date"
            confidence = max(confidence, 0.95)

    # Normalize slots and purge cross-intent noise
    if predicted_intent == "crop_insurance_status":
        slots.pop("loan_type", None)
        slots.pop("account_type", None)
    elif predicted_intent == "balance_check":
        slots.pop("loan_type", None)
        slots.pop("claim_id", None)
        slots.pop("transaction_ref", None)
        # If "current" was extracted but text is "current balance" (not "current account"), remove it
        if re.search(r"\bcurrent\s+(?:balance|status|amount)\b", cleaned_text.lower()):
            if not re.search(r"\bcurrent\s+(?:account|acct|a/c)\b", cleaned_text.lower()):
                slots.pop("account_type", None)
    elif predicted_intent == "loan_due_date":
        if slots.get("account_type") == "kcc" and "loan_type" not in slots:
            slots["loan_type"] = "crop"
        slots.pop("account_type", None)
        slots.pop("claim_id", None)
    elif predicted_intent == "transaction_dispute":
        slots.pop("account_type", None)
        slots.pop("loan_type", None)

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

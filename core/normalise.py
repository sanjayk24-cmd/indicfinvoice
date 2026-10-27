#!/usr/bin/env python3
"""
core/normalise.py - Slot Normalisation Module

Normalises raw slot values extracted from text into standard formats:
  - account_type: savings, current, kcc
  - loan_type: home, crop, personal
  - claim_id: CLM-<digits> (handles spoken digits, separators, Hindi/Tamil script)
  - amount: integer rupees (e.g. 500, 1500, 22000, 75000)
  - date: ISO format YYYY-MM-DD (today, yesterday, specific dates)
  - transaction_ref: TXN-<digits>

Rule: If a value cannot be mapped or parsed with certainty, leave it out. Never guess.
"""

import datetime
import os
import re
from typing import Any, Dict, Optional
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "configs", "slot_values.yaml")


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


CONFIG = load_config()


def _clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def normalise_account_type(raw_val: Any) -> Optional[str]:
    text = _clean_str(raw_val).lower()
    if not text:
        return None

    # Strip common suffixes
    text = re.sub(r"\b(account|acct|खाता|கணக்கு)\b", "", text).strip()

    mapping = CONFIG.get("account_type", {})
    for target_key, synonyms in mapping.items():
        if text == target_key.lower():
            return target_key
        for syn in synonyms:
            if text == str(syn).strip().lower():
                return target_key
            # Substring match if full token
            if re.search(rf"\b{re.escape(str(syn).strip().lower())}\b", text):
                return target_key

    return None


def normalise_loan_type(raw_val: Any) -> Optional[str]:
    text = _clean_str(raw_val).lower()
    if not text:
        return None

    text = re.sub(r"\b(loan|ऋण|लोन|கடன்)\b", "", text).strip()

    mapping = CONFIG.get("loan_type", {})
    for target_key, synonyms in mapping.items():
        if text == target_key.lower():
            return target_key
        for syn in synonyms:
            if text == str(syn).strip().lower():
                return target_key
            if re.search(rf"\b{re.escape(str(syn).strip().lower())}\b", text):
                return target_key

    return None


def _convert_spoken_digits(text: str) -> str:
    """Converts words for digits (0-9) in en, hi, ta to ASCII digits."""
    spoken_dict = {}
    spoken_config = CONFIG.get("spoken_digits", {})
    for lang, d in spoken_config.items():
        spoken_dict.update(d)

    # Sort keys by length descending to match multi-char words first
    sorted_words = sorted(spoken_dict.keys(), key=lambda x: len(x), reverse=True)
    res = text
    for w in sorted_words:
        digit = spoken_dict[w]
        # Match as word boundary or surrounded by spaces/punctuation
        res = re.sub(rf"(?<!\w){re.escape(w)}(?!\w)", digit, res, flags=re.IGNORECASE)
    return res


def normalise_claim_id(raw_val: Any) -> Optional[str]:
    text = _clean_str(raw_val)
    if not text:
        return None

    # Replace spoken prefixes
    for prefix_syn in CONFIG.get("spoken_prefixes", {}).get("clm", []):
        text = re.sub(rf"(?<!\w){re.escape(prefix_syn)}(?!\w)", "CLM", text, flags=re.IGNORECASE)

    # Convert spoken digits
    converted = _convert_spoken_digits(text)
    # Collapse spaces between consecutive digits
    converted = re.sub(r"(?<=\d)\s+(?=\d)", "", converted)

    # Remove extra spaces/hyphens between letters and numbers
    m = re.search(r"CLM[\s\-_]*([0-9]{3,4})", converted, flags=re.IGNORECASE)
    if m:
        return f"CLM-{m.group(1)}"

    # If it is only 3-4 digits in context of a claim
    if re.fullmatch(r"[0-9]{3,4}", converted.strip()):
        return f"CLM-{converted.strip()}"

    return None


def normalise_transaction_ref(raw_val: Any) -> Optional[str]:
    text = _clean_str(raw_val)
    if not text:
        return None

    # Replace spoken prefixes
    for prefix_syn in CONFIG.get("spoken_prefixes", {}).get("txn", []):
        text = re.sub(rf"(?<!\w){re.escape(prefix_syn)}(?!\w)", "TXN", text, flags=re.IGNORECASE)

    converted = _convert_spoken_digits(text)
    # Collapse spaces between consecutive digits
    converted = re.sub(r"(?<=\d)\s+(?=\d)", "", converted)

    m = re.search(r"TXN[\s\-_]*([0-9]{4,6})", converted, flags=re.IGNORECASE)
    if m:
        return f"TXN-{m.group(1)}"

    if re.fullmatch(r"[0-9]{4,6}", converted.strip()):
        return f"TXN-{converted.strip()}"

    return None


def normalise_amount(raw_val: Any) -> Optional[int]:
    if raw_val is None:
        return None

    if isinstance(raw_val, (int, float)):
        return int(raw_val)

    text = _clean_str(raw_val).lower().replace(",", "")
    if not text:
        return None

    # Check direct integer
    if text.isdigit():
        return int(text)

    # Check "1.5k" or "22k"
    k_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*k", text)
    if k_match:
        return int(float(k_match.group(1)) * 1000)

    # Check config amount synonyms - exact match first
    amounts_config = CONFIG.get("amounts", {})
    for target_amt_str, synonyms in amounts_config.items():
        if text == target_amt_str:
            return int(target_amt_str)
        for syn in synonyms:
            if text == str(syn).strip().lower():
                return int(target_amt_str)

    # Check multi-word/partial synonyms sorted by length descending
    all_syns = []
    for target_amt_str, synonyms in amounts_config.items():
        for syn in synonyms:
            all_syns.append((str(syn).strip().lower(), int(target_amt_str)))
    all_syns.sort(key=lambda x: len(x[0]), reverse=True)

    for syn_str, amt in all_syns:
        if re.search(r"(?<!\S)" + re.escape(syn_str) + r"(?!\S)", text) or syn_str in text:
            return amt

    # Try extracting numbers from phrase like "1500 rupees" or "रु 1500"
    num_match = re.search(r"\b([0-9]+)\b", text)
    if num_match:
        return int(num_match.group(1))

    return None


def normalise_date(raw_val: Any) -> Optional[str]:
    text = _clean_str(raw_val).lower()
    if not text:
        return None

    today = datetime.date.today()

    # Relative dates
    rel_dates = CONFIG.get("relative_dates", {})
    for syn in rel_dates.get("today", []):
        if text == syn.lower() or syn.lower() in text.split():
            return today.isoformat()

    for syn in rel_dates.get("yesterday", []):
        if text == syn.lower() or syn.lower() in text.split():
            return (today - datetime.timedelta(days=1)).isoformat()

    # Check ISO format YYYY-MM-DD (fullmatch or search in text)
    iso_m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if iso_m:
        return iso_m.group(1)

    # Day + Month parsing (e.g., "12 October", "5 November", "12 अक्टूबर", "12 அக்டோபர்")
    months_config = CONFIG.get("months", {})
    # Month mapping
    month_name_to_num = {}
    for m_num, m_names in months_config.items():
        for name in m_names:
            month_name_to_num[name.lower()] = int(m_num)

    # Match "<day> <month>" or "<month> <day>"
    for m_name, m_num in sorted(month_name_to_num.items(), key=lambda x: len(x[0]), reverse=True):
        if m_name in text:
            # Extract day
            day_match = re.search(r"\b([0-9]{1,2})\b", text)
            if day_match:
                day = int(day_match.group(1))
                try:
                    return datetime.date(today.year, m_num, day).isoformat()
                except ValueError:
                    return None

    return None


def normalise_slots(slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalises all recognised slots in the input dictionary.
    Unknown or unparseable values are excluded from the output.
    """
    if not slots:
        return {}

    normalised = {}

    if "account_type" in slots:
        val = normalise_account_type(slots["account_type"])
        if val is not None:
            normalised["account_type"] = val

    if "loan_type" in slots:
        val = normalise_loan_type(slots["loan_type"])
        if val is not None:
            normalised["loan_type"] = val

    if "claim_id" in slots:
        val = normalise_claim_id(slots["claim_id"])
        if val is not None:
            normalised["claim_id"] = val

    if "transaction_ref" in slots:
        val = normalise_transaction_ref(slots["transaction_ref"])
        if val is not None:
            normalised["transaction_ref"] = val

    if "amount" in slots:
        val = normalise_amount(slots["amount"])
        if val is not None:
            normalised["amount"] = val

    if "date" in slots:
        val = normalise_date(slots["date"])
        if val is not None:
            normalised["date"] = val

    return normalised

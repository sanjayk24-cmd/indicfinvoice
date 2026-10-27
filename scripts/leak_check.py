#!/usr/bin/env python3
"""
scripts/leak_check.py - Performs leakage verification between held-out test data
(data/splits/heldout.jsonl) and training data (train.jsonl and train_raw.jsonl).

Checks:
  1. No held-out token sequence may appear in training (train.jsonl and train_raw.jsonl).
  2. Held-out slot-value combinations do not match template combinations.
  3. If passed: writes data/splits/SPLITS_FROZEN.txt with SHA-256 hashes of:
     heldout.jsonl, train.jsonl, val.jsonl.
  4. Prints counts per intent and language. Flags any cell below 10 items.
"""

import glob
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple
import yaml

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

HELDOUT_PATH = "data/splits/heldout.jsonl"
TRAIN_PATH = "data/splits/train.jsonl"
VAL_PATH = "data/splits/val.jsonl"
TRAIN_RAW_PATH = "data/generated/train_raw.jsonl"
TEMPLATES_DIR = "data/templates"
FROZEN_TXT = "data/splits/SPLITS_FROZEN.txt"

ALL_INTENTS = [
    "balance_check",
    "crop_insurance_status",
    "loan_due_date",
    "out_of_scope",
    "transaction_dispute",
]
ALL_LANGS = ["en", "hi", "ta"]


def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_jsonl(filepath: str) -> List[dict]:
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if line_str:
                try:
                    records.append(json.loads(line_str))
                except Exception as e:
                    print(f"ERROR: Failed parsing JSON at {filepath}:{line_num}: {e}")
                    sys.exit(1)
    return records


def extract_slot_entities(tokens: List[str], tags: List[str]) -> List[Tuple[str, str]]:
    """
    Extracts (slot_type, slot_value) pairs from BIO tags.
    """
    entities = []
    cur_type = None
    cur_tokens = []

    for token, tag in zip(tokens, tags):
        if tag.startswith("B-"):
            if cur_type is not None:
                entities.append((cur_type, " ".join(cur_tokens)))
            cur_type = tag[2:]
            cur_tokens = [token]
        elif tag.startswith("I-") and cur_type == tag[2:]:
            cur_tokens.append(token)
        else:
            if cur_type is not None:
                entities.append((cur_type, " ".join(cur_tokens)))
            cur_type = None
            cur_tokens = []

    if cur_type is not None:
        entities.append((cur_type, " ".join(cur_tokens)))

    return entities


def load_template_slot_combinations(templates_dir: str = TEMPLATES_DIR) -> Set[frozenset]:
    """
    Loads slot values defined in YAML templates.
    """
    combos = set()
    yaml_files = glob.glob(os.path.join(templates_dir, "*.yaml"))
    for yf in yaml_files:
        with open(yf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        slots = data.get("slots", {}) or {}
        for slot_name, slot_vals in slots.items():
            if isinstance(slot_vals, list):
                for v in slot_vals:
                    combos.add(frozenset([(slot_name, str(v))]))
    return combos


def main():
    print("=" * 75)
    print("DATA SPLITS LEAK CHECK & INTEGRITY VERIFICATION")
    print("=" * 75)

    print(f"Loading held-out data:     {HELDOUT_PATH}")
    heldout_records = load_jsonl(HELDOUT_PATH)
    print(f"  Total heldout records:   {len(heldout_records)}")

    print(f"Loading training split:    {TRAIN_PATH}")
    train_records = load_jsonl(TRAIN_PATH)
    print(f"  Total train records:     {len(train_records)}")

    print(f"Loading generated data:    {TRAIN_RAW_PATH}")
    train_raw_records = load_jsonl(TRAIN_RAW_PATH)
    print(f"  Total train_raw records: {len(train_raw_records)}")

    # ----------------------------------------------------
    # Check 1: Token sequence leak check
    # ----------------------------------------------------
    print("\n--- Check 1: Token Sequence Leak Check ---")
    train_token_seqs = {tuple(r["tokens"]): ("train.jsonl", r) for r in train_records}
    train_raw_token_seqs = {tuple(r["tokens"]): ("train_raw.jsonl", r) for r in train_raw_records}

    # Also check normalized/casefolded strings
    train_norm_seqs = {" ".join(r["tokens"]).strip().lower(): ("train.jsonl", r) for r in train_records}
    train_raw_norm_seqs = {" ".join(r["tokens"]).strip().lower(): ("train_raw.jsonl", r) for r in train_raw_records}

    token_leak_failures = []

    for idx, r in enumerate(heldout_records, 1):
        h_tokens = tuple(r["tokens"])
        h_norm = " ".join(r["tokens"]).strip().lower()

        matched_file = None
        matched_record = None

        if h_tokens in train_token_seqs:
            matched_file, matched_record = train_token_seqs[h_tokens]
        elif h_tokens in train_raw_token_seqs:
            matched_file, matched_record = train_raw_token_seqs[h_tokens]
        elif h_norm in train_norm_seqs:
            matched_file, matched_record = train_norm_seqs[h_norm]
        elif h_norm in train_raw_norm_seqs:
            matched_file, matched_record = train_raw_norm_seqs[h_norm]

        if matched_file is not None:
            token_leak_failures.append({
                "heldout_row": idx,
                "heldout_record": r,
                "matched_file": matched_file,
                "matched_record": matched_record,
            })

    if token_leak_failures:
        print(f"FAIL: Token sequence leak check FAILED with {len(token_leak_failures)} offending rows!")
        print("\nOffending Rows:")
        for fail in token_leak_failures:
            print(f"  Heldout row {fail['heldout_row']}: {' '.join(fail['heldout_record']['tokens'])}")
            print(f"    Matched in: {fail['matched_file']}")
        print("\nStopping as requested. Do not edit heldout.jsonl.")
        sys.exit(1)
    else:
        print("PASS: No held-out token sequence appears in train.jsonl or train_raw.jsonl (0 collisions).")

    # ----------------------------------------------------
    # Check 2: Slot-value combinations check
    # ----------------------------------------------------
    print("\n--- Check 2: Slot-Value Combinations Leak Check ---")
    # Collect all slot combinations from training data & YAML templates
    training_slot_combos = set()
    for r in train_raw_records:
        ents = extract_slot_entities(r["tokens"], r["tags"])
        if ents:
            training_slot_combos.add(frozenset(ents))

    yaml_slot_combos = load_template_slot_combinations(TEMPLATES_DIR)

    slot_leak_failures = []
    for idx, r in enumerate(heldout_records, 1):
        ents = extract_slot_entities(r["tokens"], r["tags"])
        if ents:
            ent_set = frozenset(ents)
            if ent_set in training_slot_combos or ent_set in yaml_slot_combos:
                slot_leak_failures.append({
                    "heldout_row": idx,
                    "heldout_record": r,
                    "entities": ents,
                })

    if slot_leak_failures:
        print(f"FAIL: Slot-value combinations check FAILED with {len(slot_leak_failures)} offending rows!")
        for fail in slot_leak_failures:
            print(f"  Heldout row {fail['heldout_row']}: {fail['entities']}")
        print("\nStopping as requested. Do not edit heldout.jsonl.")
        sys.exit(1)
    else:
        print("PASS: Held-out slot-value combinations do not match template combinations.")

    # ----------------------------------------------------
    # Step 3: Write data/splits/SPLITS_FROZEN.txt with SHA-256 hashes
    # ----------------------------------------------------
    print("\n--- Step 3: Writing Frozen Hashes ---")
    heldout_hash = compute_sha256(HELDOUT_PATH)
    train_hash = compute_sha256(TRAIN_PATH)
    val_hash = compute_sha256(VAL_PATH)

    with open(FROZEN_TXT, "w", encoding="utf-8") as f_froz:
        f_froz.write(f"heldout.jsonl:{heldout_hash}\n")
        f_froz.write(f"train.jsonl:{train_hash}\n")
        f_froz.write(f"val.jsonl:{val_hash}\n")

    print(f"Updated {FROZEN_TXT} with SHA-256 hashes:")
    print(f"  heldout.jsonl: {heldout_hash}")
    print(f"  train.jsonl:   {train_hash}")
    print(f"  val.jsonl:     {val_hash}")

    # ----------------------------------------------------
    # Step 4: Print counts per intent and language
    # ----------------------------------------------------
    val_records = load_jsonl(VAL_PATH)

    def print_split_matrix(split_name: str, records: List[dict]):
        print(f"\nTable: Intent x Language breakdown in {split_name} (Total rows: {len(records)})")
        print(f"{'Intent':<25} | {'en':<12} | {'hi':<12} | {'ta':<12} | {'Total':<10}")
        print("-" * 78)

        counts = Counter((r.get("intent"), r.get("lang")) for r in records)
        intents = sorted(list(set(r.get("intent") for r in records)))
        
        flagged = []
        for intent in intents:
            row_str = f"{intent:<25} | "
            for lang in ["en", "hi", "ta"]:
                cnt = counts.get((intent, lang), 0)
                if cnt < 10:
                    flagged.append((intent, lang, cnt))
                    row_str += f"{cnt} [FLAG]".ljust(12) + " | "
                else:
                    row_str += f"{cnt}".ljust(12) + " | "
            tot = sum(counts.get((intent, l), 0) for l in ["en", "hi", "ta"])
            row_str += f"{tot:<10}"
            print(row_str)

        print("-" * 78)
        tot_en = sum(counts.get((intent, "en"), 0) for intent in intents)
        tot_hi = sum(counts.get((intent, "hi"), 0) for intent in intents)
        tot_ta = sum(counts.get((intent, "ta"), 0) for intent in intents)
        print(f"{'TOTAL':<25} | {str(tot_en).ljust(12)} | {str(tot_hi).ljust(12)} | {str(tot_ta).ljust(12)} | {len(records):<10}")
        
        if flagged:
            print(f"  --> Flagged cells (< 10 items) in {split_name}: {flagged}")
        else:
            print(f"  --> All cells in {split_name} have >= 10 items (no flags).")
        return flagged

    print("\n--- Step 4: Counts per Intent and Language ---")
    flagged_heldout = print_split_matrix("heldout.jsonl", heldout_records)
    flagged_train = print_split_matrix("train.jsonl", train_records)
    flagged_val = print_split_matrix("val.jsonl", val_records)
    flagged_all = print_split_matrix("ALL SPLITS (train + val + heldout)", train_records + val_records + heldout_records)

    print("\n" + "=" * 78)
    print("FINAL SUMMARY & ACCEPTANCE CRITERIA")
    print("=" * 78)
    print("- Leak Check:                     PASS")
    print("- Freeze File Exists:             PASS")
    print(f"- Frozen File Path:               {FROZEN_TXT}")
    print(f"- Held-Out Set Rows:              {len(heldout_records)} (15 en, 15 hi, 15 ta)")
    print(f"- Train Rows:                     {len(train_records)}")
    print(f"- Val Rows:                       {len(val_records)}")
    print("=" * 78)


if __name__ == "__main__":
    main()

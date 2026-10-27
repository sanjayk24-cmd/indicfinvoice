#!/usr/bin/env python3
"""
data/split.py - Splits generated training data by template_id into train.jsonl and val.jsonl (85/15, seed 42).

Ensures strict template isolation: no template_id appears in both train and validation splits.
Writes:
  - data/splits/train.jsonl
  - data/splits/val.jsonl
  - data/splits/SPLITS_FROZEN.txt (SHA-256 hashes)
"""

import hashlib
import json
import os
import sys
from collections import Counter
from sklearn.model_selection import train_test_split

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

INPUT_PATH = "data/generated/train_raw.jsonl"
SPLITS_DIR = "data/splits"
TRAIN_OUTPUT = os.path.join(SPLITS_DIR, "train.jsonl")
VAL_OUTPUT = os.path.join(SPLITS_DIR, "val.jsonl")
FROZEN_TXT = os.path.join(SPLITS_DIR, "SPLITS_FROZEN.txt")


def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def split_data(
    input_path: str = INPUT_PATH,
    train_path: str = TRAIN_OUTPUT,
    val_path: str = VAL_OUTPUT,
    test_size: float = 0.15,
    seed: int = 42,
) -> None:
    print("=" * 60)
    print("STAGE 6: SPLITTING GENERATED DATA BY TEMPLATE_ID")
    print("=" * 60)

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    os.makedirs(SPLITS_DIR, exist_ok=True)

    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                records.append(json.loads(line_str))

    total_records = len(records)
    print(f"Loaded {total_records} records from {input_path}")

    # Gather unique templates and their attributes
    template_to_records = {}
    template_intents = {}
    template_langs = {}

    for r in records:
        tid = r["template_id"]
        if tid not in template_to_records:
            template_to_records[tid] = []
            template_intents[tid] = r["intent"]
            template_langs[tid] = r["lang"]
        template_to_records[tid].append(r)

    unique_templates = sorted(list(template_to_records.keys()))
    num_templates = len(unique_templates)
    print(f"Total unique template_ids: {num_templates}")

    # Deterministic split on unique templates (85/15, seed 42)
    train_templates, val_templates = train_test_split(
        unique_templates,
        test_size=test_size,
        random_state=seed,
    )
    train_templates_set = set(train_templates)
    val_templates_set = set(val_templates)

    # Strict leak check on templates
    overlap = train_templates_set.intersection(val_templates_set)
    if overlap:
        print(f"ERROR: Template leakage detected between train and val! Overlap: {overlap}")
        sys.exit(1)
    print("Template leak check: PASS (0 overlapping templates)")

    # Partition records
    train_records = []
    val_records = []

    for r in records:
        tid = r["template_id"]
        if tid in train_templates_set:
            train_records.append(r)
        elif tid in val_templates_set:
            val_records.append(r)
        else:
            print(f"ERROR: Unassigned template_id: {tid}")
            sys.exit(1)

    # Write train.jsonl
    with open(train_path, "w", encoding="utf-8") as f_train:
        for r in train_records:
            f_train.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Write val.jsonl
    with open(val_path, "w", encoding="utf-8") as f_val:
        for r in val_records:
            f_val.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nWritten {len(train_records)} records to {train_path} ({len(train_templates)} templates)")
    print(f"Written {len(val_records)} records to {val_path} ({len(val_templates)} templates)")

    # Data pair leak check (tokens, intent)
    train_pairs = set((tuple(r["tokens"]), r["intent"]) for r in train_records)
    val_pairs = set((tuple(r["tokens"]), r["intent"]) for r in val_records)
    pair_leak = train_pairs.intersection(val_pairs)
    if pair_leak:
        print(f"WARNING: {len(pair_leak)} (tokens, intent) pairs appear in both train and val due to slot collisions.")
    else:
        print("Data pair leak check: PASS (0 duplicate token-intent pairs between train and val)")

    # Print Distributions
    print("\n--- Distribution Summary ---")
    print(f"Split ratio: {len(train_records)/total_records*100:.1f}% Train / {len(val_records)/total_records*100:.1f}% Val")
    print("\nTrain Intent Distribution:")
    for intent, count in sorted(Counter(r["intent"] for r in train_records).items()):
        print(f"  {intent}: {count}")
    print("\nVal Intent Distribution:")
    for intent, count in sorted(Counter(r["intent"] for r in val_records).items()):
        print(f"  {intent}: {count}")
    print("\nTrain Language Distribution:")
    for lang, count in sorted(Counter(r["lang"] for r in train_records).items()):
        print(f"  {lang}: {count}")
    print("\nVal Language Distribution:")
    for lang, count in sorted(Counter(r["lang"] for r in val_records).items()):
        print(f"  {lang}: {count}")

    # Write SPLITS_FROZEN.txt with SHA-256 hashes
    train_hash = compute_sha256(train_path)
    val_hash = compute_sha256(val_path)

    with open(FROZEN_TXT, "w", encoding="utf-8") as f_froz:
        f_froz.write(f"train.jsonl:{train_hash}\n")
        f_froz.write(f"val.jsonl:{val_hash}\n")

    print(f"\nFrozen hashes written to {FROZEN_TXT}:")
    print(f"  train.jsonl: {train_hash}")
    print(f"  val.jsonl:   {val_hash}")
    print("=" * 60)


if __name__ == "__main__":
    split_data()

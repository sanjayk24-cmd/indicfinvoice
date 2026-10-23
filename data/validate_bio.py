#!/usr/bin/env python3
"""
data/validate_bio.py - Validates BIO tags and data integrity in generated JSONL files.

Checks:
1. tokens and tags have equal length and are non-empty.
2. No I-<slot> appears without an immediately preceding B-<slot> or I-<slot> of the same slot.
3. Every intent is one of the five allowed intents.
4. Every slot is one of the six allowed slots.
5. out_of_scope examples contain no B- or I- tags (all O).
6. Required fields (tokens, tags, intent, lang, template_id) are present.

Prints the total validated records, error count, and the first five failures.
Exits 0 on clean validation, 1 on any error.
"""

import json
import os
import sys

ALLOWED_INTENTS = {
    "balance_check",
    "loan_due_date",
    "crop_insurance_status",
    "transaction_dispute",
    "out_of_scope",
}

ALLOWED_SLOTS = {
    "account_type",
    "loan_type",
    "claim_id",
    "amount",
    "date",
    "transaction_ref",
}

ALLOWED_LANGUAGES = {"en", "hi", "ta"}


def validate_file(input_path: str = "data/generated/train_raw.jsonl") -> int:
    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        return 1

    total_records = 0
    errors = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            total_records += 1

            try:
                record = json.loads(line_str)
            except Exception as e:
                errors.append(f"Line {line_num}: JSON parse error: {e}")
                continue

            # Check required fields
            missing = [
                k
                for k in ["tokens", "tags", "intent", "lang", "template_id"]
                if k not in record
            ]
            if missing:
                errors.append(f"Line {line_num}: Missing required field(s): {missing}")
                continue

            tokens = record["tokens"]
            tags = record["tags"]
            intent = record["intent"]
            lang = record["lang"]
            template_id = record["template_id"]

            # Intent check
            if intent not in ALLOWED_INTENTS:
                errors.append(
                    f"Line {line_num}: Disallowed intent '{intent}' not in {ALLOWED_INTENTS}"
                )

            # Lang check
            if lang not in ALLOWED_LANGUAGES:
                errors.append(
                    f"Line {line_num}: Disallowed lang '{lang}' not in {ALLOWED_LANGUAGES}"
                )

            # Type checks
            if not isinstance(tokens, list) or not isinstance(tags, list):
                errors.append(f"Line {line_num}: 'tokens' and 'tags' must be lists")
                continue

            # Length check
            if len(tokens) == 0:
                errors.append(f"Line {line_num}: tokens list is empty")
                continue

            if len(tokens) != len(tags):
                errors.append(
                    f"Line {line_num}: tokens length ({len(tokens)}) != tags length ({len(tags)})"
                )
                continue

            # BIO tag sequence validation
            prev_tag = None
            for idx, tag in enumerate(tags):
                if tag == "O":
                    prev_tag = tag
                    continue

                if intent == "out_of_scope":
                    errors.append(
                        f"Line {line_num}: out_of_scope record has non-O tag '{tag}' at index {idx}"
                    )
                    break

                if tag.startswith("B-"):
                    slot = tag[2:]
                    if slot not in ALLOWED_SLOTS:
                        errors.append(
                            f"Line {line_num}: Disallowed slot '{slot}' in tag '{tag}'"
                        )
                    prev_tag = tag
                elif tag.startswith("I-"):
                    slot = tag[2:]
                    if slot not in ALLOWED_SLOTS:
                        errors.append(
                            f"Line {line_num}: Disallowed slot '{slot}' in tag '{tag}'"
                        )
                    # Must follow B-<slot> or I-<slot> of the same slot
                    if prev_tag is None or prev_tag not in (f"B-{slot}", f"I-{slot}"):
                        errors.append(
                            f"Line {line_num}: Invalid BIO transition at token {idx} ('{tokens[idx]}'): "
                            f"'{tag}' follows '{prev_tag}'"
                        )
                    prev_tag = tag
                else:
                    errors.append(
                        f"Line {line_num}: Invalid tag format '{tag}' at index {idx}"
                    )
                    prev_tag = tag

    print(f"Validation complete: {total_records} records checked.")
    print(f"Total errors: {len(errors)}")

    if errors:
        print("\n--- First 5 Failures ---")
        for err in errors[:5]:
            print(f"FAIL: {err}")
        return 1

    print("ALL CHECKS PASSED: 0 errors detected.")
    return 0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/generated/train_raw.jsonl"
    exit_code = validate_file(path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

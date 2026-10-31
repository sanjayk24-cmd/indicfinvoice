import glob
import json
import os
import sys
import yaml

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
ALLOWED_INTENTS = {
    "balance_check",
    "loan_due_date",
    "crop_insurance_status",
    "transaction_dispute",
    "out_of_scope",
}
for tf in glob.glob(os.path.join(templates_dir, "*.yaml")):
    try:
        with open(tf, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f)
            if d and "intent" in d:
                ALLOWED_INTENTS.add(d["intent"])
    except Exception:
        pass

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
                errors.append(f"Line {line_num}: Invalid JSON ({e})")
                continue

            # Check 6: Required fields
            req_fields = ["tokens", "tags", "intent", "lang", "template_id"]
            missing = [f for f in req_fields if f not in record]
            if missing:
                errors.append(f"Line {line_num}: Missing fields {missing}")
                continue

            tokens = record["tokens"]
            tags = record["tags"]
            intent = record["intent"]
            lang = record["lang"]

            # Check 1: Non-empty and equal length
            if not tokens or not tags:
                errors.append(f"Line {line_num}: Empty tokens or tags")
                continue

            if len(tokens) != len(tags):
                errors.append(
                    f"Line {line_num}: Length mismatch (tokens={len(tokens)}, tags={len(tags)})"
                )
                continue

            # Check 3: Intent validity
            if intent not in ALLOWED_INTENTS:
                errors.append(f"Line {line_num}: Invalid intent '{intent}'")
                continue

            # Check language
            if lang not in ALLOWED_LANGUAGES:
                errors.append(f"Line {line_num}: Invalid lang '{lang}'")
                continue

            # Check 2: BIO tag consistency
            prev_slot = None
            for idx, tag in enumerate(tags):
                if tag == "O":
                    prev_slot = None
                elif tag.startswith("B-"):
                    slot = tag[2:]
                    if slot not in ALLOWED_SLOTS:
                        errors.append(
                            f"Line {line_num}: Unknown slot '{slot}' at tag index {idx}"
                        )
                        break
                    prev_slot = slot
                elif tag.startswith("I-"):
                    slot = tag[2:]
                    if slot != prev_slot:
                        errors.append(
                            f"Line {line_num}: Invalid tag transition to '{tag}' at index {idx} (previous slot was '{prev_slot}')"
                        )
                        break
                else:
                    errors.append(f"Line {line_num}: Unknown tag format '{tag}' at index {idx}")
                    break

            # Check 5: out_of_scope examples contain no B- or I- tags
            if intent == "out_of_scope":
                has_entity = any(t != "O" for t in tags)
                if has_entity:
                    errors.append(
                        f"Line {line_num}: out_of_scope example has non-O tags: {tags}"
                    )

    print(f"Validation complete: {total_records} records checked.")
    print(f"Total errors: {len(errors)}")

    if errors:
        print("First 5 errors:")
        for err in errors[:5]:
            print(f"  - {err}")
        return 1

    print("ALL CHECKS PASSED: 0 errors detected.")
    return 0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/generated/train_raw.jsonl"
    sys.exit(validate_file(path))


if __name__ == "__main__":
    main()

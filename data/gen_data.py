#!/usr/bin/env python3
"""
data/gen_data.py - Generates training data from intent templates with BIO tags.

Reads all YAML files in data/templates/, generates 60 slot permutations per template,
and writes data/generated/train_raw.jsonl with tokens, tags, intent, lang, template_id.
"""

import glob
import json
import os
import random
import re
from pathlib import Path
import yaml


def load_settings(settings_path: str = "configs/settings.yaml") -> dict:
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def generate_data(
    templates_dir: str = "data/templates",
    output_path: str = "data/generated/train_raw.jsonl",
    n_examples_per_template: int = 60,
    seed: int = 42,
) -> int:
    random.seed(seed)
    template_files = sorted(glob.glob(os.path.join(templates_dir, "*.yaml")))
    if not template_files:
        raise FileNotFoundError(f"No template files found in {templates_dir}")

    records = []
    placeholder_pattern = re.compile(r"^\{([a-zA-Z_]+)\}$")

    for tf in template_files:
        with open(tf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        intent = data.get("intent")
        languages = data.get("languages", {})
        slots = data.get("slots", {}) or {}

        for lang, lang_block in languages.items():
            templates = lang_block.get("templates", [])
            for t_idx, template_str in enumerate(templates):
                template_id = f"{intent}_{lang}_{t_idx}"
                template_words = template_str.strip().split()

                for _ in range(n_examples_per_template):
                    tokens = []
                    tags = []

                    for word in template_words:
                        m = placeholder_pattern.match(word)
                        if m:
                            slot_name = m.group(1)
                            if (
                                slot_name in slots
                                and lang in slots[slot_name]
                                and slots[slot_name][lang]
                            ):
                                chosen_val = random.choice(slots[slot_name][lang])
                                val_words = str(chosen_val).strip().split()
                                for v_idx, vw in enumerate(val_words):
                                    tokens.append(vw)
                                    tags.append(
                                        f"B-{slot_name}"
                                        if v_idx == 0
                                        else f"I-{slot_name}"
                                    )
                            else:
                                # Placeholder with no slot values defined
                                tokens.append(word)
                                tags.append("O")
                        else:
                            tokens.append(word)
                            tags.append("O")

                    records.append(
                        {
                            "tokens": tokens,
                            "tags": tags,
                            "intent": intent,
                            "lang": lang,
                            "template_id": template_id,
                        }
                    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as out_f:
        for record in records:
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Generated {len(records)} examples across {len(template_files)} template files.")
    print(f"Saved to {output_path}")
    return len(records)


def main():
    settings = load_settings()
    seed = settings.get("seed", 42)
    count = generate_data(seed=seed)
    print(f"Total count: {count}")


if __name__ == "__main__":
    main()

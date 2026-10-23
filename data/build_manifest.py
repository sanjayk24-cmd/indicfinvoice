"""Manifest builder script for Stage 2 of IndicFinVoice.

Constructs dataset_manifest.csv from raw transcripts and converted 16 kHz WAV audio.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import yaml


TARGET_LANGUAGES = {"en", "hi", "ta"}


def load_label_map(config_path: str = "configs/label_map.yaml") -> Tuple[Dict, str]:
    """Load intent keyword rules and default intent from label_map.yaml."""
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        return {}, "out_of_scope"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("intent_rules", {}), cfg.get("default_intent", "out_of_scope")


def load_corrections(corrections_path: str = "data/manifests/corrections.csv") -> Dict[str, str]:
    """Load transcript corrections if any."""
    corr_path = Path(corrections_path)
    if not corr_path.exists():
        return {}
    try:
        df_corr = pd.read_csv(corr_path, encoding="utf-8")
        if "clip_id" in df_corr.columns and "corrected_ref" in df_corr.columns:
            return dict(zip(df_corr["clip_id"], df_corr["corrected_ref"]))
    except Exception as e:
        print(f"Warning: could not read corrections file {corrections_path}: {e}")
    return {}


def derive_intent(text: str, en_text: str, rules: Dict, default_intent: str) -> str:
    """Derive project intent from text and parallel English sentence using keyword rules."""
    combined = (text + " " + en_text).lower()
    for intent, data in rules.items():
        for kw in data.get("keywords", []):
            if kw.lower() in combined:
                return intent
    return default_intent


def build_manifest(
    raw_dir: str = "data/raw",
    wav_dir: str = "data/wav16k",
    output_path: str = "data/manifests/dataset_manifest.csv",
    corrections_path: str = "data/manifests/corrections.csv",
    label_map_path: str = "configs/label_map.yaml",
) -> pd.DataFrame:
    """Build the dataset manifest CSV file."""
    rules, default_intent = load_label_map(label_map_path)
    corrections = load_corrections(corrections_path)

    # Load English reference sentences for keyword cross-referencing
    eng_csv = Path(raw_dir) / "eng_textdata.csv"
    if eng_csv.exists():
        df_eng = pd.read_csv(eng_csv, header=None, encoding="utf-8")
        eng_sentences = [str(s).strip() for s in df_eng[0].tolist()]
    else:
        eng_sentences = []

    rows: List[Dict] = []
    dropped_counts: Dict[str, int] = {
        "unsupported_language": 0,
        "empty_reference": 0,
        "missing_audio_file": 0,
    }

    # Inspect all language directories in data/raw/data
    data_dir = Path(raw_dir) / "data"
    all_lang_dirs = [d for d in data_dir.iterdir() if d.is_dir()] if data_dir.exists() else []

    for lang_dir in sorted(all_lang_dirs):
        lang = lang_dir.name
        if lang not in TARGET_LANGUAGES:
            dropped_counts["unsupported_language"] += 100  # Each lang has 100 sentences
            continue

        text_file = lang_dir / f"{lang}_textdata.csv"
        if not text_file.exists():
            print(f"Warning: text file {text_file} not found.")
            continue

        df_text = pd.read_csv(text_file, header=None, encoding="utf-8")

        for idx, text_val in enumerate(df_text[0], 1):
            ref = str(text_val).strip() if pd.notna(text_val) else ""
            clip_id = f"{lang}_{idx:03d}"

            if not ref:
                dropped_counts["empty_reference"] += 1
                continue

            # Apply correction if present
            if clip_id in corrections:
                ref = corrections[clip_id]

            audio_rel_path = f"data/wav16k/{lang}/{lang}_voicedata/{idx}.wav"
            audio_full_path = Path(audio_rel_path)

            if not audio_full_path.exists():
                dropped_counts["missing_audio_file"] += 1
                continue

            en_ref = eng_sentences[idx - 1] if idx - 1 < len(eng_sentences) else ""
            intent = derive_intent(ref, en_ref, rules, default_intent)

            rows.append({
                "clip_id": clip_id,
                "path": audio_rel_path.replace("\\", "/"),
                "ref": ref,
                "lang": lang,
                "intent": intent,
                "slots_json": "{}",
                "speaker": "unknown",
                "noise": "unknown",
                "source_split": "dataset",
            })

    df_manifest = pd.DataFrame(rows, columns=[
        "clip_id", "path", "ref", "lang", "intent", "slots_json", "speaker", "noise", "source_split"
    ])

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df_manifest.to_csv(out_file, index=False, encoding="utf-8")

    print("\n" + "=" * 50)
    print("DATASET MANIFEST SUMMARY")
    print("=" * 50)
    print(f"Total manifest rows: {len(df_manifest)}")
    print("\nRows by language:")
    for lang, count in df_manifest["lang"].value_counts().items():
        print(f"  {lang}: {count}")
    print("\nRows by derived intent:")
    for intent, count in df_manifest["intent"].value_counts().items():
        print(f"  {intent}: {count}")
    print("\nDropped items:")
    for reason, count in dropped_counts.items():
        print(f"  {reason}: {count}")
    print(f"\nManifest saved to: {output_path}")

    return df_manifest


if __name__ == "__main__":
    build_manifest()

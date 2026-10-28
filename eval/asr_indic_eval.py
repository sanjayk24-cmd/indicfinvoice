#!/usr/bin/env python3
"""
eval/asr_indic_eval.py - AI4Bharat IndicConformer Speech Evaluation

Evaluates AI4Bharat IndicConformer on Hindi and Tamil clips from
data/manifests/speech_test.csv.
Imports normalization, repetition loop detection, and script error detection
directly from existing modules without reimplementing them.

Outputs:
  - eval/results/asr_indic_results.csv
  - eval/results/asr_indic_summary.json
  - eval/results/asr_comparison.csv
"""

import json
import os
import re
import statistics
import sys
import time
from typing import Any, Dict, List, Optional

import jiwer
import pandas as pd

# UTF-8 stdout configuration for Windows consoles
sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import existing functions from baseline modules without redefining them
from asr.transcribe_indicconformer import (
    free_model,
    load_asr,
    normalise_text,
    transcribe_fixed_language,
)
from eval.asr_eval import check_repetition_loop, detect_script_error

CHOSEN_MODEL_HI = "ai4bharat/indic-conformer-600m-multilingual"
CHOSEN_MODEL_TA = "ai4bharat/indic-conformer-600m-multilingual"


def main():
    manifest_path = os.path.join(PROJECT_ROOT, "data", "manifests", "speech_test.csv")
    speech_root = os.path.join(PROJECT_ROOT, "data", "raw", "speech")
    results_dir = os.path.join(PROJECT_ROOT, "eval", "results")
    os.makedirs(results_dir, exist_ok=True)

    whisper_summary_path = os.path.join(results_dir, "asr_summary.json")
    whisper_results_path = os.path.join(results_dir, "asr_results.csv")

    indic_results_csv_path = os.path.join(results_dir, "asr_indic_results.csv")
    indic_summary_json_path = os.path.join(results_dir, "asr_indic_summary.json")
    comparison_csv_path = os.path.join(results_dir, "asr_comparison.csv")

    print("=" * 80)
    print("AI4BHARAT INDICCONFORMER EVALUATION (HINDI & TAMIL)")
    print(f"Manifest:   {manifest_path}")
    print(f"Audio Root: {speech_root}")
    print(f"Hindi Model: {CHOSEN_MODEL_HI}")
    print(f"Tamil Model: {CHOSEN_MODEL_TA}")
    print("=" * 80)

    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    df_manifest = pd.read_csv(manifest_path)
    # Filter only rows with lang in {hi, ta}. Do not process en rows.
    df_indic = df_manifest[df_manifest["lang"].isin(["hi", "ta"])].copy()
    total_clips = len(df_indic)
    print(f"Filtered {total_clips} Indic clips (Hindi: {(df_indic['lang'] == 'hi').sum()}, Tamil: {(df_indic['lang'] == 'ta').sum()}).")
    print("English rows skipped as required.\n")

    # Load Whisper baseline numbers from existing asr_summary.json and asr_results.csv
    if not os.path.exists(whisper_summary_path):
        print(f"Error: Existing Whisper summary not found at {whisper_summary_path}")
        sys.exit(1)
    with open(whisper_summary_path, "r", encoding="utf-8") as f_w:
        whisper_summary = json.load(f_w)

    whisper_clean_wer: Dict[str, float] = {}
    if os.path.exists(whisper_results_path):
        df_whisper = pd.read_csv(whisper_results_path)
        for lang_code in ["hi", "ta"]:
            sub_w = df_whisper[df_whisper["lang"] == lang_code]
            c_refs, c_hyps = [], []
            for _, r in sub_w.iterrows():
                h_text = str(r["hyp"])
                r_text = str(r["ref"])
                is_lp = check_repetition_loop(h_text)
                is_sc, _ = detect_script_error(h_text, lang_code)
                if not is_lp and not is_sc:
                    c_refs.append(normalise_text(r_text))
                    c_hyps.append(normalise_text(h_text))
            whisper_clean_wer[lang_code] = round(float(jiwer.wer(c_refs, c_hyps)), 4) if c_refs else 1.0

    # Load IndicConformer model
    print(f"Loading IndicConformer model ({CHOSEN_MODEL_HI})...")
    pipe = load_asr(CHOSEN_MODEL_HI)
    print("Model loaded successfully.\n")

    results_data: List[Dict[str, Any]] = []
    durations: List[float] = []

    start_time = time.perf_counter()

    for idx, (_, row) in enumerate(df_indic.iterrows()):
        rel_path = str(row["path"])
        full_path = os.path.join(speech_root, rel_path)
        ref_text = str(row["ref"])
        lang = str(row["lang"])
        model_id = CHOSEN_MODEL_HI if lang == "hi" else CHOSEN_MODEL_TA

        t0 = time.perf_counter()
        hyp_text = transcribe_fixed_language(pipe, full_path, lang)
        elapsed = time.perf_counter() - t0

        is_loop = check_repetition_loop(hyp_text)
        is_script_err, script_type = detect_script_error(hyp_text, lang)

        results_data.append(
            {
                "path": rel_path,
                "ref": ref_text,
                "hyp": hyp_text,
                "lang": lang,
                "model_id": model_id,
                "seconds": round(elapsed, 4),
                "loop": is_loop,
                "script_error": is_script_err,
            }
        )
        durations.append(elapsed)

        if (idx + 1) % 25 == 0 or (idx + 1) == total_clips:
            avg_sec = sum(durations) / len(durations)
            print(
                f"  [{idx + 1:3d}/{total_clips}] Transcribed {rel_path} "
                f"({elapsed:.2f}s) | Avg: {avg_sec:.2f}s/clip"
            )

    total_eval_time = time.perf_counter() - start_time
    print(f"\nAll {total_clips} Indic clips transcribed in {total_eval_time:.2f} s.")

    # Free model memory
    free_model(pipe)

    # Save eval/results/asr_indic_results.csv
    # Columns: path, ref, hyp, lang, model_id, seconds, loop, script_error
    df_results = pd.DataFrame(results_data)
    df_results.to_csv(indic_results_csv_path, index=False, encoding="utf-8")
    print(f"Saved Indic results to: {indic_results_csv_path}")

    # Compute metrics per language
    summary_per_language: Dict[str, Any] = {}
    comparison_rows: List[Dict[str, Any]] = []

    for lang in ["hi", "ta"]:
        sub_df = df_results[df_results["lang"] == lang]
        count = len(sub_df)
        model_id = sub_df["model_id"].iloc[0]

        all_refs = [normalise_text(r) for r in sub_df["ref"]]
        all_hyps = [normalise_text(h) for h in sub_df["hyp"]]
        corpus_wer = float(jiwer.wer(all_refs, all_hyps))

        loop_count = int(sub_df["loop"].sum())
        loop_rate = float(loop_count / count)

        script_err_count = int(sub_df["script_error"].sum())
        script_err_rate = float(script_err_count / count)

        clean_sub = sub_df[(sub_df["loop"] == False) & (sub_df["script_error"] == False)]
        clips_kept = len(clean_sub)

        if clips_kept > 0:
            clean_refs = [normalise_text(r) for r in clean_sub["ref"]]
            clean_hyps = [normalise_text(h) for h in clean_sub["hyp"]]
            clean_wer = float(jiwer.wer(clean_refs, clean_hyps))
        else:
            clean_wer = 1.0

        median_sec = float(statistics.median(sub_df["seconds"]))

        summary_per_language[lang] = {
            "model_id": model_id,
            "clips": count,
            "corpus_wer": round(corpus_wer, 4),
            "clean_transcript_wer": round(clean_wer, 4),
            "clips_kept_for_clean_wer": clips_kept,
            "loop_rate": round(loop_rate, 4),
            "script_error_rate": round(script_err_rate, 4),
            "median_seconds": round(median_sec, 4),
        }

        # Whisper baseline numbers from asr_summary.json
        w_metrics = whisper_summary.get("per_language", {}).get(lang, {})
        w_wer = float(w_metrics.get("wer", 0.0))
        w_clean_wer = whisper_clean_wer.get(lang, w_wer)
        w_loop_rate = float(w_metrics.get("repetition_loops", {}).get("rate", 0.0))
        w_script_err_rate = float(w_metrics.get("script_errors", {}).get("rate", 0.0))

        comparison_rows.append(
            {
                "lang": lang,
                "whisper_medium_wer": round(w_wer, 4),
                "indic_wer": round(corpus_wer, 4),
                "whisper_medium_clean_wer": round(w_clean_wer, 4),
                "indic_clean_wer": round(clean_wer, 4),
                "whisper_medium_loop_rate": round(w_loop_rate, 4),
                "indic_loop_rate": round(loop_rate, 4),
                "whisper_medium_script_error_rate": round(w_script_err_rate, 4),
                "indic_script_error_rate": round(script_err_rate, 4),
            }
        )

    # Save eval/results/asr_indic_summary.json
    indic_summary_data = {
        "note": "English is not in this evaluation as IndicConformer is evaluated on Indic languages (Hindi and Tamil).",
        "per_language": summary_per_language,
    }
    with open(indic_summary_json_path, "w", encoding="utf-8") as f_out:
        json.dump(indic_summary_data, f_out, indent=2, ensure_ascii=False)
    print(f"Saved Indic summary to: {indic_summary_json_path}")

    # Save eval/results/asr_comparison.csv
    # Columns: lang, whisper_medium_wer, indic_wer, whisper_medium_clean_wer, indic_clean_wer, whisper_medium_loop_rate, indic_loop_rate, whisper_medium_script_error_rate, indic_script_error_rate
    df_comparison = pd.DataFrame(comparison_rows)
    df_comparison.to_csv(comparison_csv_path, index=False, encoding="utf-8")
    print(f"Saved comparison to: {comparison_csv_path}")

    # Print Report
    print("\n" + "=" * 80)
    print("ASR COMPARISON TABLE (Whisper-medium vs AI4Bharat IndicConformer)")
    print("English is not in this comparison; evaluated only on Indic languages (hi, ta).")
    print("=" * 80)

    header = (
        f"{'Language':<8} | {'Whisper WER':<11} | {'Indic WER':<10} | "
        f"{'Whisper Clean':<13} | {'Indic Clean':<11} | "
        f"{'Wh-Loop':<8} | {'Ind-Loop':<8} | {'Wh-ScriptErr':<12} | {'Ind-ScriptErr':<13}"
    )
    print(header)
    print("-" * len(header))
    for r in comparison_rows:
        row_str = (
            f"{r['lang']:<8} | "
            f"{r['whisper_medium_wer']:<11.4f} | "
            f"{r['indic_wer']:<10.4f} | "
            f"{r['whisper_medium_clean_wer']:<13.4f} | "
            f"{r['indic_clean_wer']:<11.4f} | "
            f"{r['whisper_medium_loop_rate']:<8.2%} | "
            f"{r['indic_loop_rate']:<8.2%} | "
            f"{r['whisper_medium_script_error_rate']:<12.2%} | "
            f"{r['indic_script_error_rate']:<13.2%}"
        )
        print(row_str)
    print("-" * len(header))


if __name__ == "__main__":
    main()

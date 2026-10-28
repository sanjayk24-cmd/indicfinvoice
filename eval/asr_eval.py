#!/usr/bin/env python3
"""
eval/asr_eval.py - Automatic Speech Recognition Evaluation

Evaluates openai/whisper-medium on data/manifests/speech_test.csv.
Measures Word Error Rate (WER) using jiwer, repetition loop rates,
script error rates, and median runtime per clip.
Saves:
  - eval/results/asr_results.csv (path, ref, hyp, lang, source, seconds)
  - eval/results/asr_summary.json (WER per language and per source, median seconds, loops, script errors)
"""

import json
import os
import re
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import jiwer
import pandas as pd

# UTF-8 stdout configuration for Windows consoles
sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from asr.transcribe import get_pipeline, normalise_text, transcribe


def check_repetition_loop(text: str, n_gram: int = 3, min_repeats: int = 3) -> bool:
    """
    Returns True if the normalised text contains any 3-word sequence
    repeated 3 or more times.
    """
    words = normalise_text(text).split()
    if len(words) < n_gram * min_repeats:
        return False
    counts: Dict[Tuple[str, ...], int] = {}
    for i in range(len(words) - n_gram + 1):
        gram = tuple(words[i : i + n_gram])
        counts[gram] = counts.get(gram, 0) + 1
        if counts[gram] >= min_repeats:
            return True
    return False


def detect_script_error(hyp: str, lang: str) -> Tuple[bool, Optional[str]]:
    """
    Detects if hypothesis is in the wrong script for the expected language.
    Returns (is_error: bool, wrong_script_name: Optional[str]).
    """
    clean_hyp = normalise_text(hyp)
    if not clean_hyp:
        return False, None

    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", hyp))
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", hyp))
    arabic_chars = len(
        re.findall(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",
            hyp,
        )
    )
    latin_chars = len(re.findall(r"[a-zA-Z]", hyp))

    if lang == "hi":
        if arabic_chars > 0:
            return True, "Urdu/Arabic"
        if devanagari_chars == 0:
            if latin_chars > 0:
                return True, "Latin"
            if tamil_chars > 0:
                return True, "Tamil"
            return True, "non-Devanagari"
        return False, None

    elif lang == "ta":
        if tamil_chars == 0:
            if devanagari_chars > 0:
                return True, "Devanagari"
            if latin_chars > 0:
                return True, "Latin"
            if arabic_chars > 0:
                return True, "Urdu/Arabic"
            return True, "non-Tamil"
        if devanagari_chars > tamil_chars:
            return True, "Devanagari (predominant)"
        return False, None

    elif lang == "en":
        if latin_chars == 0 and (
            devanagari_chars > 0 or tamil_chars > 0 or arabic_chars > 0
        ):
            return True, "non-Latin"
        return False, None

    return False, None


def main():
    manifest_path = os.path.join(PROJECT_ROOT, "data", "manifests", "speech_test.csv")
    speech_root = os.path.join(PROJECT_ROOT, "data", "raw", "speech")
    results_dir = os.path.join(PROJECT_ROOT, "eval", "results")
    os.makedirs(results_dir, exist_ok=True)

    results_csv_path = os.path.join(results_dir, "asr_results.csv")
    summary_json_path = os.path.join(results_dir, "asr_summary.json")

    print("=" * 80)
    print("AUTOMATIC SPEECH RECOGNITION (ASR) EVALUATION")
    print(f"Manifest:   {manifest_path}")
    print(f"Audio Root: {speech_root}")
    print(f"Model:      openai/whisper-medium (fp16, CUDA, auto-detect language)")
    print("=" * 80)

    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    df_manifest = pd.read_csv(manifest_path)
    total_clips = len(df_manifest)
    print(f"Loaded {total_clips} clips from manifest.")
    print("Breakdown by language:", df_manifest["lang"].value_counts().to_dict())
    print("Breakdown by source:  ", df_manifest["source"].value_counts().to_dict())
    print("-" * 80)

    # Pre-load Whisper model once
    print("Initializing Whisper pipeline...")
    pipe = get_pipeline()
    if pipe is None:
        print("Error: Could not initialize Whisper pipeline.")
        sys.exit(1)
    print("Whisper pipeline ready.\n")

    results_data: List[Dict[str, Any]] = []
    norm_refs: List[str] = []
    norm_hyps: List[str] = []
    loop_flags: List[bool] = []
    script_err_flags: List[bool] = []
    script_types: List[Optional[str]] = []
    durations: List[float] = []

    print(f"Starting transcription of {total_clips} clips...")
    start_total_time = time.perf_counter()

    for idx, row in df_manifest.iterrows():
        rel_path = str(row["path"])
        full_path = os.path.join(speech_root, rel_path)
        ref_text = str(row["ref"])
        lang = str(row["lang"])
        source = str(row["source"])

        t0 = time.perf_counter()
        hyp_text = transcribe(full_path)
        elapsed = time.perf_counter() - t0

        norm_ref = normalise_text(ref_text)
        norm_hyp = normalise_text(hyp_text)

        is_loop = check_repetition_loop(hyp_text)
        is_script_err, script_type = detect_script_error(hyp_text, lang)

        results_data.append(
            {
                "path": rel_path,
                "ref": ref_text,
                "hyp": hyp_text,
                "lang": lang,
                "source": source,
                "seconds": round(elapsed, 4),
            }
        )

        norm_refs.append(norm_ref)
        norm_hyps.append(norm_hyp)
        loop_flags.append(is_loop)
        script_err_flags.append(is_script_err)
        script_types.append(script_type)
        durations.append(elapsed)

        if (idx + 1) % 25 == 0 or (idx + 1) == total_clips:
            avg_sec = sum(durations) / len(durations)
            print(
                f"  [{idx + 1:3d}/{total_clips}] Transcribed {rel_path} "
                f"({elapsed:.2f}s) | Avg: {avg_sec:.2f}s/clip"
            )

    total_eval_time = time.perf_counter() - start_total_time
    print(f"\nAll {total_clips} clips transcribed in {total_eval_time:.2f} s.")

    # Save eval/results/asr_results.csv with required columns: (path, ref, hyp, lang, source, seconds)
    df_results = pd.DataFrame(results_data)
    df_results.to_csv(results_csv_path, index=False, encoding="utf-8")
    print(f"\nSaved clip results to: {results_csv_path}")

    # Compute Evaluation Metrics
    # 1. Overall WER
    overall_wer = float(jiwer.wer(norm_refs, norm_hyps))
    overall_median_sec = float(statistics.median(durations))

    # 2. Per-Language Metrics
    per_language: Dict[str, Any] = {}
    languages = sorted(df_manifest["lang"].unique())

    for lang in languages:
        indices = [i for i, r in enumerate(results_data) if r["lang"] == lang]
        sub_refs = [norm_refs[i] for i in indices]
        sub_hyps = [norm_hyps[i] for i in indices]
        sub_loops = [loop_flags[i] for i in indices]
        sub_script_errs = [script_err_flags[i] for i in indices]
        sub_types = [script_types[i] for i in indices if script_types[i] is not None]
        sub_secs = [durations[i] for i in indices]
        sub_source = results_data[indices[0]]["source"]

        lang_wer = float(jiwer.wer(sub_refs, sub_hyps))
        lang_median_sec = float(statistics.median(sub_secs))
        loop_count = sum(sub_loops)
        loop_rate = float(loop_count / len(indices))
        script_err_count = sum(sub_script_errs)
        script_err_rate = float(script_err_count / len(indices))

        type_counts: Dict[str, int] = {}
        for st in sub_types:
            type_counts[st] = type_counts.get(st, 0) + 1

        per_language[lang] = {
            "count": len(indices),
            "source": sub_source,
            "wer": round(lang_wer, 4),
            "median_seconds": round(lang_median_sec, 4),
            "repetition_loops": {
                "count": loop_count,
                "rate": round(loop_rate, 4),
            },
            "script_errors": {
                "count": script_err_count,
                "rate": round(script_err_rate, 4),
                "breakdown": type_counts,
            },
        }

    # 3. Per-Source Metrics
    per_source: Dict[str, Any] = {}
    sources = sorted(df_manifest["source"].unique())

    for source in sources:
        indices = [i for i, r in enumerate(results_data) if r["source"] == source]
        sub_refs = [norm_refs[i] for i in indices]
        sub_hyps = [norm_hyps[i] for i in indices]
        sub_loops = [loop_flags[i] for i in indices]
        sub_script_errs = [script_err_flags[i] for i in indices]
        sub_secs = [durations[i] for i in indices]
        sub_langs = sorted(list(set(results_data[i]["lang"] for i in indices)))

        source_wer = float(jiwer.wer(sub_refs, sub_hyps))
        source_median_sec = float(statistics.median(sub_secs))
        loop_count = sum(sub_loops)
        loop_rate = float(loop_count / len(indices))
        script_err_count = sum(sub_script_errs)
        script_err_rate = float(script_err_count / len(indices))

        per_source[source] = {
            "count": len(indices),
            "languages": sub_langs,
            "wer": round(source_wer, 4),
            "median_seconds": round(source_median_sec, 4),
            "loop_count": loop_count,
            "loop_rate": round(loop_rate, 4),
            "script_error_count": script_err_count,
            "script_error_rate": round(script_err_rate, 4),
        }

    # 4. Summary JSON Structure
    summary_data = {
        "note": "English is from FLEURS and Hindi/Tamil from IndicVoices, so these are not directly comparable.",
        "model": "openai/whisper-medium",
        "device": "cuda",
        "dtype": "fp16",
        "language_argument": None,
        "total_clips": total_clips,
        "overall_wer": round(overall_wer, 4),
        "overall_median_seconds": round(overall_median_sec, 4),
        "total_repetition_loops": sum(loop_flags),
        "total_repetition_loop_rate": round(sum(loop_flags) / total_clips, 4),
        "total_script_errors": sum(script_err_flags),
        "total_script_error_rate": round(sum(script_err_flags) / total_clips, 4),
        "per_language": per_language,
        "per_source": per_source,
    }

    with open(summary_json_path, "w", encoding="utf-8") as f_json:
        json.dump(summary_data, f_json, indent=2, ensure_ascii=False)
    print(f"Saved evaluation summary to: {summary_json_path}")

    # 5. Print Summary Tables
    print("\n" + "=" * 80)
    print("ASR EVALUATION RESULTS SUMMARY")
    print("=" * 80)

    print("\n--- PER-LANGUAGE METRICS ---")
    header_lang = f"{'Language':<10} | {'Source':<20} | {'Clips':<6} | {'WER':<8} | {'Median(s)':<10} | {'Loop Rate':<10} | {'Script Err Rate':<15}"
    print(header_lang)
    print("-" * len(header_lang))
    for lang, metrics in per_language.items():
        row_str = (
            f"{lang:<10} | "
            f"{metrics['source']:<20} | "
            f"{metrics['count']:<6} | "
            f"{metrics['wer']:<8.4f} | "
            f"{metrics['median_seconds']:<10.4f} | "
            f"{metrics['repetition_loops']['rate']:<10.2%} | "
            f"{metrics['script_errors']['rate']:<15.2%}"
        )
        print(row_str)
    print("-" * len(header_lang))

    print("\n--- PER-SOURCE METRICS ---")
    header_src = f"{'Source':<22} | {'Languages':<12} | {'Clips':<6} | {'WER':<8} | {'Median(s)':<10} | {'Loop Rate':<10} | {'Script Err Rate':<15}"
    print(header_src)
    print("-" * len(header_src))
    for source, metrics in per_source.items():
        row_str = (
            f"{source:<22} | "
            f"{', '.join(metrics['languages']):<12} | "
            f"{metrics['count']:<6} | "
            f"{metrics['wer']:<8.4f} | "
            f"{metrics['median_seconds']:<10.4f} | "
            f"{metrics['loop_rate']:<10.2%} | "
            f"{metrics['script_error_rate']:<15.2%}"
        )
        print(row_str)
    print("-" * len(header_src))

    print("\n--- OVERALL METRICS ---")
    print(f"Total Clips:               {total_clips}")
    print(f"Overall Corpus WER:        {overall_wer:.4f} ({overall_wer * 100:.2f}%)")
    print(f"Overall Median Latency:    {overall_median_sec:.4f} s/clip")
    print(f"Total Repetition Loops:    {sum(loop_flags)} / {total_clips} ({sum(loop_flags)/total_clips:.2%})")
    print(f"Total Script Errors:       {sum(script_err_flags)} / {total_clips} ({sum(script_err_flags)/total_clips:.2%})")

    print("\n--- SCRIPT ERROR DETAILS ---")
    for lang, metrics in per_language.items():
        err_info = metrics["script_errors"]
        print(f"  [{lang}] Script Errors: {err_info['count']}/{metrics['count']} ({err_info['rate']:.1%}) - Breakdown: {err_info['breakdown']}")

    print("\n--- COMPARABILITY NOTE ---")
    print(summary_data["note"])
    print("=" * 80)


if __name__ == "__main__":
    main()

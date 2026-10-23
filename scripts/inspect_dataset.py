"""Dataset inspection script for Stage 2 of IndicFinVoice."""

import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import soundfile as sf

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def print_file_tree(root_dir: str, max_depth: int = 3) -> None:
    """Print the directory file tree up to max_depth levels."""
    print("=" * 60)
    print(f"FILE TREE (up to depth {max_depth}): {root_dir}")
    print("=" * 60)
    root_path = Path(root_dir)
    if not root_path.exists():
        print(f"Directory {root_dir} does not exist.")
        return

    root_level = len(root_path.parts)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)
        depth = len(current_path.parts) - root_level
        if depth >= max_depth:
            dirnames.clear()
            continue
        indent = "  " * depth
        folder_name = current_path.name if depth > 0 else root_path.name
        print(f"{indent}[{folder_name}/]")
        sub_indent = "  " * (depth + 1)
        # Limit filenames display if too many
        if len(filenames) > 10:
            for f in filenames[:5]:
                print(f"{sub_indent}{f}")
            print(f"{sub_indent}... ({len(filenames) - 5} more files)")
        else:
            for f in filenames:
                print(f"{sub_indent}{f}")


def count_file_extensions(root_dir: str) -> Dict[str, int]:
    """Count and print all files by their extension under root_dir."""
    print("\n" + "=" * 60)
    print(f"FILE COUNTS BY EXTENSION: {root_dir}")
    print("=" * 60)
    counts: Counter[str] = Counter()
    for root, _, files in os.walk(root_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            counts[ext if ext else "[no extension]"] += 1

    for ext, count in sorted(counts.items()):
        print(f"  {ext:<15}: {count}")
    return dict(counts)


def inspect_tabular_files(root_dir: str) -> None:
    """Inspect the first 5 rows, types, and column statistics for CSV/JSON files."""
    print("\n" + "=" * 60)
    print(f"INSPECTING TABULAR (CSV/JSON) FILES: {root_dir}")
    print("=" * 60)
    tabular_files: List[Path] = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.endswith(".csv") or f.endswith(".json"):
                tabular_files.append(Path(root) / f)

    for file_path in sorted(tabular_files):
        print(f"\n--- FILE: {file_path} ---")
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8")
            else:
                df = pd.read_json(file_path, encoding="utf-8")
        except Exception as e:
            print(f"  Error reading {file_path}: {e}")
            continue

        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print("\nColumns and Data Types:")
        for col, dtype in df.dtypes.items():
            print(f"  {col}: {dtype}")

        print("\nFirst 5 Rows:")
        print(df.head(5).to_string())

        print("\nColumn Value Distributions:")
        for col in df.columns:
            unique_count = df[col].nunique(dropna=False)
            print(f"  Column '{col}': {unique_count} unique values")
            top_vals = df[col].value_counts(dropna=False).head(20)
            for val, cnt in top_vals.items():
                val_str = str(val)[:60]
                print(f"    - {val_str!r}: {cnt}")


def inspect_audio_files(root_dir: str) -> None:
    """Compute and print audio statistics (sample rate, channels, min, median, max duration)."""
    print("\n" + "=" * 60)
    print(f"INSPECTING AUDIO FILES: {root_dir}")
    print("=" * 60)
    audio_files: List[Path] = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg")):
                audio_files.append(Path(root) / f)

    print(f"Total audio files found: {len(audio_files)}")
    if not audio_files:
        return

    sample_rates: Counter[int] = Counter()
    channels: Counter[int] = Counter()
    durations: List[float] = []

    for af in audio_files:
        try:
            info = sf.info(str(af))
            sample_rates[info.samplerate] += 1
            channels[info.channels] += 1
            durations.append(info.duration)
        except Exception as e:
            print(f"Error reading audio file {af}: {e}")

    if durations:
        total_seconds = sum(durations)
        total_hours = total_seconds / 3600.0
        dur_array = np.array(durations)
        print("\nAudio Format Statistics:")
        print("  Sample rates:", dict(sample_rates))
        print("  Channels:", dict(channels))
        print(f"  Total audio duration: {total_seconds:.2f} s ({total_hours:.2f} hours)")
        print(f"  Duration stats (seconds):")
        print(f"    Min:    {dur_array.min():.3f} s")
        print(f"    Median: {np.median(dur_array):.3f} s")
        print(f"    Max:    {dur_array.max():.3f} s")


def main() -> None:
    """Run full dataset inspection on data/raw."""
    raw_dir = "data/raw"
    print_file_tree(raw_dir, max_depth=3)
    count_file_extensions(raw_dir)
    inspect_tabular_files(raw_dir)
    inspect_audio_files(raw_dir)


if __name__ == "__main__":
    main()

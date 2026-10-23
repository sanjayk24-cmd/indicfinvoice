"""Audio conversion script for Stage 2 of IndicFinVoice.

Converts target dataset audio files (en, hi, ta) to 16 kHz mono WAV format into data/wav16k/.
"""

import os
from pathlib import Path
from typing import List, Tuple
import numpy as np
import soundfile as sf

# Try librosa, fallback to soundfile + soxr if numba/librosa is blocked by OS policy
try:
    import librosa
    USE_LIBROSA = True
except Exception:
    import soxr
    USE_LIBROSA = False


TARGET_LANGUAGES = {"en", "hi", "ta"}


def load_audio_16k(audio_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """Load an audio file, convert to mono, and resample to target_sr."""
    if USE_LIBROSA:
        try:
            data, sr = librosa.load(audio_path, sr=target_sr, mono=True)
            return data, sr
        except Exception:
            pass

    # High-quality fallback using soundfile + soxr (librosa's backend)
    import soxr
    data, orig_sr = sf.read(audio_path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if orig_sr != target_sr:
        data = soxr.resample(data, orig_sr, target_sr)
    return data.astype(np.float32), target_sr


def find_audio_files(raw_dir: str) -> List[Path]:
    """Find all target audio files (.mp3, .wav) under raw_dir for target languages."""
    audio_paths: List[Path] = []
    data_dir = Path(raw_dir) / "data"
    if not data_dir.exists():
        data_dir = Path(raw_dir)

    for lang in TARGET_LANGUAGES:
        lang_dir = data_dir / lang
        if lang_dir.exists():
            for root, _, files in os.walk(lang_dir):
                for f in files:
                    if f.lower().endswith((".mp3", ".wav", ".m4a")):
                        audio_paths.append(Path(root) / f)
    return sorted(audio_paths)


def convert_audio_files(
    raw_dir: str = "data/raw",
    output_dir: str = "data/wav16k",
    error_log: str = "logs/audio_conversion_errors.txt",
    sample_rate: int = 16000,
) -> Tuple[int, int]:
    """Convert audio files to 16 kHz mono WAV and save to output_dir."""
    raw_path = Path(raw_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    log_path = Path(error_log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    files_to_convert = find_audio_files(raw_dir)
    print(f"Found {len(files_to_convert)} audio files to convert for languages {sorted(TARGET_LANGUAGES)}.")

    success_count = 0
    error_count = 0
    error_lines = []

    for idx, audio_file in enumerate(files_to_convert, 1):
        try:
            try:
                rel_path = audio_file.relative_to(raw_path / "data")
            except ValueError:
                rel_path = audio_file.relative_to(raw_path)

            dest_file = (out_path / rel_path).with_suffix(".wav")
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            audio_data, sr = load_audio_16k(str(audio_file), target_sr=sample_rate)
            sf.write(str(dest_file), audio_data, sr, subtype="PCM_16")
            success_count += 1
            if idx % 50 == 0 or idx == len(files_to_convert):
                print(f"[{idx}/{len(files_to_convert)}] Converted {audio_file.name} -> {dest_file}")
        except Exception as e:
            error_count += 1
            err_msg = f"{audio_file}: {type(e).__name__} - {e}\n"
            print(f"Error converting {audio_file}: {e}")
            error_lines.append(err_msg)

    if error_lines:
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(error_lines)
    else:
        log_path.write_text("", encoding="utf-8")

    print(f"\nAudio Conversion Summary:")
    print(f"  Successfully converted: {success_count}")
    print(f"  Failed / Skipped:        {error_count}")
    print(f"  Destination directory:  {output_dir}")
    return success_count, error_count


if __name__ == "__main__":
    convert_audio_files()

# scripts/fetch_indicvoices.py
"""Extract a fixed sample of IndicVoices clips from a cached parquet file.

Usage: python scripts/fetch_indicvoices.py <lang_code> <parquet_file> [more parquet files]
Example: python scripts/fetch_indicvoices.py hi hindi/valid-00000-of-00001.parquet
"""
import csv
import io
import random
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
import librosa
from huggingface_hub import hf_hub_download

REPO = "ai4bharat/IndicVoices"
N_CLIPS = 100
SEED = 42
MIN_SEC, MAX_SEC = 1.0, 20.0
SR = 16000

lang_code = sys.argv[1]
parquet_names = sys.argv[2:]
out_dir = Path("data/raw/speech/indicvoices") / lang_code
out_dir.mkdir(parents=True, exist_ok=True)

def clean(value):
    """Strip whitespace and remove non-printing characters."""
    if value is None:
        return ""
    return " ".join(str(value).split())

# 1. Read all rows from the requested parquet files
rows = []
for name in parquet_names:
    local = hf_hub_download(REPO, name, repo_type="dataset")
    table = pq.read_table(local, columns=[
        "audio_filepath", "normalized", "verbatim", "duration",
        "gender", "state", "speaker_id",
    ])
    rows.extend(table.to_pylist())
print(f"Read {len(rows)} rows from {len(parquet_names)} file(s)")

# 2. Filter
kept, dropped = [], {"empty_ref": 0, "duration": 0, "no_audio": 0}
for r in rows:
    ref = clean(r["normalized"])
    dur = float(r["duration"] or 0)
    if not ref:
        dropped["empty_ref"] += 1
    elif not (MIN_SEC <= dur <= MAX_SEC):
        dropped["duration"] += 1
    elif not r["audio_filepath"] or not r["audio_filepath"].get("bytes"):
        dropped["no_audio"] += 1
    else:
        kept.append(r)
print(f"Kept {len(kept)} rows; dropped: {dropped}")

# 3. Fixed sample
random.Random(SEED).shuffle(kept)
sample = kept[:N_CLIPS]

# 4. Decode, resample to 16 kHz mono, save
index = []
for i, r in enumerate(sample):
    audio, sr = sf.read(io.BytesIO(r["audio_filepath"]["bytes"]), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SR)
    name = f"{lang_code}_{i:03d}.wav"
    sf.write(out_dir / name, np.asarray(audio, dtype=np.float32), SR, subtype="PCM_16")
    index.append({
        "path": f"indicvoices/{lang_code}/{name}",
        "ref": clean(r["normalized"]),
        "verbatim": clean(r["verbatim"]),
        "lang": lang_code,
        "source": "IndicVoices valid",
        "gender": r["gender"] or "",
        "state": r["state"] or "",
        "duration": round(float(r["duration"]), 3),
    })

# 5. Write the index
index_path = Path("data/raw/speech/indicvoices") / f"{lang_code}_index.csv"
with open(index_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(index[0].keys()))
    w.writeheader()
    w.writerows(index)
print(f"Saved {len(index)} clips to {out_dir}")
print(f"Index written to {index_path}")
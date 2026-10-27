# scripts/fetch_fleurs_en.py
"""Extract a fixed sample of FLEURS English (en_us, test split) clips.

Usage: python scripts/fetch_fleurs_en.py
Reads parquet-data/en_us/test-00000-of-00001.parquet from google/fleurs.
"""
import csv
import io
import random
from pathlib import Path

import librosa
import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
from huggingface_hub import hf_hub_download

REPO = "google/fleurs"
PARQUET = "parquet-data/en_us/test-00000-of-00001.parquet"
N_CLIPS = 100
SEED = 42
MIN_SEC, MAX_SEC = 1.0, 20.0
SR = 16000

out_dir = Path("data/raw/speech/fleurs/en")
out_dir.mkdir(parents=True, exist_ok=True)
index_path = Path("data/raw/speech/fleurs/en_index.csv")

def clean(value):
    """Collapse whitespace; return empty string for None."""
    if value is None:
        return ""
    return " ".join(str(value).split())

local = hf_hub_download(REPO, PARQUET, repo_type="dataset")
table = pq.read_table(local, columns=[
    "id", "num_samples", "audio", "transcription", "raw_transcription", "gender",
])
rows = table.to_pylist()
print(f"Read {len(rows)} rows")

# Filter using num_samples (FLEURS audio is 16 kHz), so no decoding is needed here
kept, dropped = [], {"empty_ref": 0, "duration": 0, "no_audio": 0}
for r in rows:
    ref = clean(r["transcription"])
    dur = (r["num_samples"] or 0) / SR
    if not ref:
        dropped["empty_ref"] += 1
    elif not (MIN_SEC <= dur <= MAX_SEC):
        dropped["duration"] += 1
    elif not r["audio"] or not r["audio"].get("bytes"):
        dropped["no_audio"] += 1
    else:
        r["_dur"] = dur
        kept.append(r)
print(f"Kept {len(kept)} rows; dropped: {dropped}")

random.Random(SEED).shuffle(kept)
sample = kept[:N_CLIPS]

index = []
for i, r in enumerate(sample):
    raw = r["audio"]["bytes"]
    try:
        audio, sr = sf.read(io.BytesIO(raw), dtype="float32")
    except Exception as e:
        raise RuntimeError(
            f"Could not decode clip id={r['id']}; first bytes={raw[:4]!r}; error={e}"
        )
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SR)
    name = f"en_{i:03d}.wav"
    sf.write(out_dir / name, np.asarray(audio, dtype=np.float32), SR, subtype="PCM_16")
    index.append({
        "path": f"fleurs/en/{name}",
        "ref": clean(r["transcription"]),
        "verbatim": clean(r["raw_transcription"]),
        "lang": "en",
        "source": "FLEURS en_us test",
        "gender": r["gender"] if r["gender"] is not None else "",
        "state": "",
        "duration": round(r["_dur"], 3),
    })

with open(index_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(index[0].keys()))
    w.writeheader()
    w.writerows(index)
print(f"Saved {len(index)} clips to {out_dir}")
print(f"Index written to {index_path}")
# IndicFinVoice: Comprehensive Project & Evaluation Report

**Date:** October 28, 2026  
**Environment:** Conda `translate` (Python 3.10+, PyTorch CUDA, Hugging Face Transformers, ONNX Runtime)  
**Primary Baseline Workspace:** `indicfinvoice/`  
**Parallel Replica Workspace:** `indicfinvoice_indic/`  
**Test Suite Status:** 68/68 passed in both workspaces (`pytest -q`)

---

## 1. Executive Summary

**IndicFinVoice** is an end-to-end multilingual conversational AI banking assistant built to process spoken and written customer queries across **English (`en`)**, **Hindi (`hi`)**, and **Tamil (`ta`)**. The system integrates Speech-to-Text (ASR), Natural Language Understanding (intent detection across 15 banking intents and slot filling), and a safety-conscious core dialogue manager connected to a mock retail banking API (`mockbank`).

This report provides a full top-to-bottom accounting of the engineering progression, dataset audits, privacy safeguards, and speech recognition benchmarking conducted across both the primary repository (`indicfinvoice/`) and its parallel replica environment (`indicfinvoice_indic/`). It details the comparison between OpenAI's **Whisper-Medium** baseline and AI4Bharat's **IndicConformer** pipeline.

---

## 2. Dual-Repository Workspace Architecture

To ensure experimental rigor and prevent accidental modification of the frozen Whisper baseline, two complementary workspaces are maintained in parallel:

```
c:\Users\mouli\OneDrive\Desktop\NLP\
├── indicfinvoice/           # Baseline repository: hosts the untouched Whisper-medium evaluation
└── indicfinvoice_indic/     # Parallel replica repository: dedicated to the IndicConformer pipeline
```

1. **`indicfinvoice/` (Baseline Workspace):** Contains the original frozen evaluation pipeline, baseline Whisper STT code, baseline manifests, and original evaluation results.
2. **`indicfinvoice_indic/` (Parallel Workspace):** An isolated replica created to host the IndicConformer pipeline and run parallel evaluations without risking regressions or accidental overwrites in the baseline project. Audio files and heavy model weights are strictly git-ignored.

---

## 3. Environment & Dependency Specifications

All operations were executed inside the frozen `translate` Conda environment on a CUDA-enabled GPU system under strict non-destructive constraints (no upgrades or downgrades of `torch`, `transformers`, or `huggingface_hub`):

- **Python Version:** 3.10+
- **PyTorch:** GPU-accelerated with CUDA runtime
- **Audio Tooling:** `soundfile`, `librosa`, `jiwer`
- **Inference Runtimes:**
  - Hugging Face `transformers.pipeline` (for Whisper-medium FP16)
  - `onnxruntime` / PyTorch AutoModel (for IndicConformer CTC/RNNT)
  - `IndicTransToolkit` (for machine translation verification)

---

## 4. Dataset Audit & Data Integrity Verification

### 4.1 Split Counts & Cryptographic Hash Verification
All dataset splits under `data/splits/` were audited against cryptographic hashes recorded in `SPLITS_FROZEN.txt`. Direct recount confirmed exact row counts:

| Split File | Row Count | Languages Covered | Purpose |
|:---|:---:|:---|:---|
| `data/splits/train.jsonl` | **7,620** | `en` (2,540), `hi` (2,540), `ta` (2,540) | NLU Model Training |
| `data/splits/val.jsonl` | **1,380** | `en` (460), `hi` (460), `ta` (460) | Hyperparameter tuning & model selection |
| `data/splits/heldout.jsonl` | **45** | `en` (15), `hi` (15), `ta` (15) | Held-out sanity testing |
| **Combined Total** | **9,045** | Balanced 3-way split across 15 intents | Full NLU Dataset |

*Note: The actual row total across files is 9,045, rectifying an earlier documentation typo stating 9,040.*

### 4.2 Audit Findings & Validation Zero-Cells
1. **Zero-Cells in Validation:** Analysis revealed that the validation split contained 0 samples for `crop_insurance_status` (Hindi) and 0 samples for `out_of_scope` (English). This occurred as an artifact of synthetic template-grouped splitting implemented to prevent template overlap between train and validation.
2. **Selection Verification:** Review of `training_history.json` confirmed that checkpoint selection was strictly governed by validation intent macro-F1 during training, with zero leakage from the test or heldout partitions.

---

## 5. Privacy & PII Scrubbing

To prevent accidental simulation of real telephone numbers, an audit identified invented helpline numbers (`1800-123-4567`) across responses and rule definitions.

1. **Scrubbing Scope:**
   - Modified `core/responses.json`
   - Modified `core/rules.py`
   - Updated unit assertions in `tests/test_rules.py` and `tests/test_dialogue.py`
2. **Standardization:**
   - All phone strings were replaced with the canonical placeholder:
     `[BANK_HELPLINE_NUMBER]`
   - Policy logged in `DATA_SOURCES.md`: *"Helpline number is a placeholder [BANK_HELPLINE_NUMBER]. Replace with the real bank helpline before any real use."*
3. **Verification:** Test suite re-run confirmed 100% pass rate across all 68 tests.

---

## 6. Test 1: Speech-to-Text Baseline (Whisper-Medium)

### 6.1 Speech Manifest & Cross-Source Structure
The speech test set comprises exactly 300 real-speaker clips defined in `data/manifests/speech_test.csv` (16 kHz mono WAV):
- **English (`en`):** 100 clips from **FLEURS** (`en_us`, `test` split).
- **Hindi (`hi`):** 100 clips from **IndicVoices** (`valid` split).
- **Tamil (`ta`):** 100 clips from **IndicVoices** (`valid` split).

*Benchmark Note:* Because English clips originate from FLEURS and Indic clips originate from IndicVoices, acoustic environments, noise profiles, and recording devices differ. English and Indic WER represent distinct benchmark distributions.

### 6.2 Conditioning Policy & Pre-Run Decisions
To eliminate post-hoc cherry-picking:
- **Primary Benchmark Policy:** Pure auto-detection with no language argument passed (`generate_kwargs={"task": "transcribe"}`).
- **Diagnostic Finding:** A 10-clip Hindi diagnostic revealed that auto-detection frequently suffered from language misidentification, producing hallucination loops and non-Devanagari scripts. However, adhering to the project protocol, auto-detection remained the primary evaluation standard.

### 6.3 Baseline Architecture & Normalisation
- **File:** `asr/transcribe.py`
- **Model:** `openai/whisper-medium` loaded once at module import in FP16 on CUDA.
- **Normalisation (`normalise_text`):** Lowercases text, removes ASCII punctuation and Indic dandas (`।`, `॥`), strips quotes and dashes, and normalizes spacing. Applied identically to references and hypotheses.

### 6.4 Baseline Evaluation Metrics & Outputs
- **Corpus WER:** Standard Word Error Rate via `jiwer`.
- **Repetition Loop Detector:** Flags transcripts where any 3-word n-gram repeats 3 or more consecutive times.
- **Script Error Detector:** Uses Unicode character block inspection to flag transcripts produced in the wrong script (e.g., Latin or Perso-Arabic scripts in Hindi/Tamil).
- **Clean-Transcript WER:** Evaluates WER exclusively on the subset of clips free of loops and script errors.
- **Output Files:**
  - `eval/results/asr_results.csv` (SHA-256: `1863b88881721ee5b990e0bab586d52dc705783b41a509200ae5727bb89d3ead`)
  - `eval/results/asr_summary.json` (SHA-256: `04e71103055d57a9ef2a059815bfe37d7d27a7747ca3a3e47cc82bed514c074c`)

---

## 7. Parallel IndicConformer Evaluation (AI4Bharat)

### 7.1 Step 0: Model Search, Candidates & Selection

Hugging Face was queried for AI4Bharat IndicConformer checkpoints:

| Model ID | Parameters | Licence | Description / Architecture | IndicVoices Mention | Language-Specific | Access Status |
|:---|:---:|:---:|:---|:---:|:---:|:---:|
| `ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large` | ~120M | MIT | Conformer-Large encoder with hybrid CTC-RNNT decoder (NeMo) | No explicit mention | Yes (`hi`) | Gated (HTTP 403 Forbidden) |
| `ai4bharat/indicconformer_stt_ta_hybrid_ctc_rnnt_large` | ~120M | MIT | Conformer-Large encoder with hybrid CTC-RNNT decoder (NeMo) | No explicit mention | Yes (`ta`) | Gated (HTTP 403 Forbidden) |
| `ai4bharat/indic-conformer-600m-multilingual` | ~600M | MIT | Multilingual Conformer Hybrid CTC + RNNT across 22 Indic languages (ONNX) | Yes (links to IndicVoices tokenizers) | No (Multilingual, 22 langs) | **Public (Open)** |
| `ai4bharat/IndicConformer` | ~120M | CC-BY-4.0 | NeMo Conformer model template repository | No mention | No | Public |
| `OpenVoiceOS/ai4bharat-indicconformer-hi-onnx` | ~120M | MIT | Community ONNX export of AI4Bharat Hindi Conformer | No mention | Yes (`hi`) | Public (Community) |
| `OpenVoiceOS/ai4bharat-indicconformer-ta-onnx` | ~120M | MIT | Community ONNX export of AI4Bharat Tamil Conformer | No mention | Yes (`ta`) | Public (Community) |

**Selection Rule Applied:** Prefer an AI4Bharat-published checkpoint over a community checkpoint; among AI4Bharat checkpoints, prefer one whose licence permits research use and open publication.

**Chosen Checkpoint:**
- **Hindi (`hi`):** `ai4bharat/indic-conformer-600m-multilingual`
- **Tamil (`ta`):** `ai4bharat/indic-conformer-600m-multilingual`
- **Justification:** Published officially by AI4Bharat under the MIT License, publicly downloadable without gated restrictions, and natively supports 22 Indian languages.

### 7.2 Contamination Analysis & Disclosure
Documented in `DATA_SOURCES.md` *prior* to running evaluation:
- **Hindi (`hi`): Contaminated (High Risk).** The model card explicitly points to IndicVoices tokenizers (`AI4Bharat/IndicVoices/tree/master/artifacts/tokenizers`), and the training data incorporates large IndicVoices partitions. Test clips from IndicVoices `valid` overlap with training speaker and acoustic distributions.
- **Tamil (`ta`): Contaminated (High Risk).** Identical contamination vector; training corpora and tokenizers originate from the IndicVoices corpus.

### 7.3 Step 1 & 2: Implementation & Evaluation Script
- **Module:** `asr/transcribe_indicconformer.py` (additive only; `asr/transcribe.py` left 100% untouched).
  - `load_asr(model_id)`: Loads model once per script execution with GPU memory management.
  - `transcribe_fixed_language(pipe, path, language)`: Uses RNNT decoding with robust `soundfile` audio ingestion.
  - Reuses `normalise_text` imported directly from `asr.transcribe`.
- **Evaluation Runner:** `eval/asr_indic_eval.py`
  - Evaluated only `hi` and `ta` rows from `data/manifests/speech_test.csv` (100 clips each, 200 total; English excluded).
  - Uses identical WER calculation, repetition loop detection, and script error detection.

---

## 8. Comparative Results & Evaluation Metrics

### 8.1 Side-by-Side Comparison Table (`eval/results/asr_comparison.csv`)

```csv
lang,whisper_medium_wer,indic_wer,whisper_medium_clean_wer,indic_clean_wer,whisper_medium_loop_rate,indic_loop_rate,whisper_medium_script_error_rate,indic_script_error_rate
hi,0.9035,0.1378,0.5053,0.1378,0.11,0.0,0.14,0.0
ta,0.9638,0.3187,0.7665,0.3187,0.06,0.0,0.08,0.0
```

### 8.2 Full Metrics Comparison

| Metric | Hindi (`hi`) - Whisper | Hindi (`hi`) - IndicConformer | Tamil (`ta`) - Whisper | Tamil (`ta`) - IndicConformer |
|:---|:---:|:---:|:---:|:---:|
| **Model ID** | `openai/whisper-medium` | `ai4bharat/indic-conformer-600m-multilingual` | `openai/whisper-medium` | `ai4bharat/indic-conformer-600m-multilingual` |
| **Clips Evaluated** | 100 | 100 | 100 | 100 |
| **Corpus WER** | **90.35%** | **13.78%** | **96.38%** | **31.87%** |
| **Clean-Transcript WER** | **50.53%** | **13.78%** | **76.65%** | **31.87%** |
| **Clips Kept for Clean WER** | 75 / 100 | 100 / 100 | 86 / 100 | 100 / 100 |
| **Repetition Loop Rate** | 11.00% (11 clips) | **0.00% (0 clips)** | 6.00% (6 clips) | **0.00% (0 clips)** |
| **Script Error Rate** | 14.00% (14 clips) | **0.00% (0 clips)** | 8.00% (8 clips) | **0.00% (0 clips)** |
| **Median Latency (s/clip)** | 1.35 s | **0.36 s** | 1.11 s | **0.34 s** |

*(English is evaluated in the Whisper baseline at 5.97% WER on FLEURS, but excluded from IndicConformer evaluation.)*

---

## 9. Verification & System Quality Checks

| Verification Item | Requirement / Expected Value | Observed Output | Result |
|:---|:---|:---|:---:|
| `eval/results/asr_summary.json` Hash | `04e71103055d57a9ef2a059815bfe37d7d27a7747ca3a3e47cc82bed514c074c` | Exact Match | **PASS** |
| `eval/results/asr_results.csv` Hash | `1863b88881721ee5b990e0bab586d52dc705783b41a509200ae5727bb89d3ead` | Exact Match | **PASS** |
| `asr/transcribe.py` Hash | `6e822455f0ea6ab9b44aa7bf6a4ba425236c686fd5d94d0e8ceb90a2a4827a19` | Exact Match | **PASS** |
| Indic Results Clip Count | Exactly 100 `hi` and 100 `ta` rows | 100 `hi`, 100 `ta` (200 total) | **PASS** |
| Non-empty Model ID Matching Choice | All rows match `indic-conformer-600m-multilingual` | 200 / 200 match | **PASS** |
| Comparison File Row Count | Exactly 2 rows (`hi`, `ta`) | Exactly 2 rows | **PASS** |
| English Isolation in New Files | Zero `en` occurrences in Indic outputs | 0 `en` rows in all 3 files | **PASS** |
| Unit & Regression Test Suite | 68 passed | 68 passed in 21.32s | **PASS** |

---

## 10. Comprehensive `indicfinvoice_indic/` Folder Report (Top-to-Bottom)

### 10.1 Origin, Purpose & Architectural Motivation
The `indicfinvoice_indic/` repository was established under explicit user instruction to maintain complete separation between the existing baseline and the new parallel pipeline:
> *"indicfinvoice/ (existing baseline, unchanged)*  
> *indicfinvoice_indic/ (new pipeline, copy of the project)*  
> *Copy the project, don’t edit the original. Then the Whisper baseline stays intact, and you can show both pipelines side by side in the report. Don’t commit the new folder’s audio or model weights to Git."*

By maintaining `indicfinvoice_indic/` as an isolated replica:
1. The original baseline (`indicfinvoice/`) remains cryptographically verified and immutable.
2. The parallel pipeline operates in an environment identical in configuration, dependency resolution, and test harness execution.
3. Git history for production stays lightweight by preventing large binary speech models or audio datasets from entering the commit graph.

---

### 10.2 Complete Directory Structure & Inventory

```
indicfinvoice_indic/
├── .git/                                # Independent Git version control repository
├── .gitignore                           # Strict exclusion configuration for weights & audio
├── .gitkeep                             # Root tracking placeholder
├── .pytest_cache/                       # Pytest test execution metadata
├── .vscode/                             # Workspace configuration
├── DATA_SOURCES.md                      # Synchronized data source lineages & contamination logs (16,826 B)
├── FULL_REPORT.md                       # Synchronized comprehensive engineering report (13,844 B)
├── README.md                            # Comprehensive system documentation and architecture spec (54,255 B)
├── pipeline.py                          # End-to-end multi-turn dialogue & banking execution pipeline (14,509 B)
├── plot.py                              # Visualization script for training curves and evaluation metrics (7,985 B)
├── requirements.txt                     # Core Python dependency manifest (120 B)
├── setup_check.py                       # Environment and CUDA availability diagnostic script (1,279 B)
├── asr/                                 # Speech-to-Text Subsystem
│   ├── .gitkeep                         # Subdirectory marker
│   ├── transcribe.py                    # Whisper-Medium baseline STT engine (2,458 B)
│   └── transcribe_indicconformer.py     # AI4Bharat IndicConformer STT engine (1,643 B)
├── configs/                             # Model hyperparameter and pipeline configurations
├── core/                                # Core Dialogue Management & Business Logic
│   ├── rules.py                         # Rule-based fallback handlers & safety policies
│   ├── responses.json                   # Multi-turn response templates with [BANK_HELPLINE_NUMBER]
│   └── normalise.py                     # Canonical text and entity normalizer
├── data/                                # Data Repository
│   ├── external/                        # Banking77 translated corpora (en, hi, ta)
│   ├── generated/                       # Synthetic templates and interim manifests
│   ├── manifests/
│   │   └── speech_test.csv              # Speech evaluation manifest (300 clips: en, hi, ta)
│   ├── raw/
│   │   └── speech/                      # Evaluated real audio clips (git-ignored)
│   │       ├── fleurs/en/               # 100 FLEURS English WAV clips
│   │       ├── indicvoices/hi/          # 100 IndicVoices Hindi WAV clips
│   │       └── indicvoices/ta/          # 100 IndicVoices Tamil WAV clips
│   └── splits/                          # NLU Train, Validation, and Heldout Partitions
│       ├── train.jsonl                  # 7,620 rows
│       ├── val.jsonl                    # 1,380 rows
│       ├── heldout.jsonl                # 45 rows
│       └── SPLITS_FROZEN.txt            # SHA-256 frozen split checksums
├── docs/                                # Documentation assets and evaluation notes
├── eval/                                # Evaluation Suite
│   ├── asr_eval.py                      # Whisper baseline evaluation script
│   ├── asr_indic_eval.py                # IndicConformer parallel evaluation script
│   └── results/                         # Evaluation Deliverables
│       ├── .gitkeep                     # Directory marker
│       ├── asr_results.csv              # Whisper clip-level predictions (160,974 B)
│       ├── asr_summary.json             # Whisper summary metrics (2,203 B)
│       ├── asr_indic_results.csv        # IndicConformer clip-level predictions (129,472 B)
│       ├── asr_indic_summary.json       # IndicConformer summary metrics (758 B)
│       └── asr_comparison.csv           # Side-by-side comparison table (274 B)
├── logs/                                # Execution and diagnostic runtime logs
├── mockbank/                            # Simulated Retail Core Banking Engine
│   ├── api.py                           # Banking REST and transaction handling interface
│   └── db.json                          # In-memory account database and balance state
├── models/                              # Local model checkpoints (git-ignored)
├── nlu/                                 # Intent Classification & Slot Extraction Modules
├── scripts/                             # Utility scripts (leak detection, OOS selection)
└── tests/                               # Comprehensive Automated Test Suite (68 tests)
    ├── test_dialogue.py                 # Multi-turn conversational flow tests
    ├── test_nlu.py                      # Intent and entity parsing tests
    └── test_rules.py                    # Safety, boundary, and helpline placeholder tests
```

---

### 10.3 Git Configuration & Binary Asset Exclusion (`.gitignore`)

To ensure that neither large audio files (WAV) nor deep learning model weights enter the version control history, `indicfinvoice_indic/.gitignore` contains strict exclusion patterns:

```gitignore
# Python and Virtual Environment
venv/
__pycache__/
.env
.vscode/
logs/

# Audio Data & Manifest Directories (Excluded from Git)
data/raw/
data/wav16k/
*.wav
*.m4a
*.mp3

# Model Checkpoints & Large Binary Weights (Excluded from Git)
models/
data/hf_cache/
*.bin
*.safetensors
*.pt
*.pth
*.onnx
```

**Git Audit Status:** Confirmed via `git status` that all `.wav` audio files and `.onnx` / `.bin` model weights remain untracked and excluded from staging.

---

### 10.4 ASR Subsystem & Script Implementation in Replica

The replica repository houses both ASR implementations side-by-side:

1. **`asr/transcribe.py` (Whisper Baseline):**
   - Singleton pattern caching `openai/whisper-medium` in FP16 on CUDA.
   - Pure auto-detection with no language argument passed (`generate_kwargs={"task": "transcribe"}`).
   - Text normalization with `normalise_text`.

2. **`asr/transcribe_indicconformer.py` (IndicConformer Engine):**
   - `load_asr(model_id: str)`: Loads `ai4bharat/indic-conformer-600m-multilingual` using ONNX runtime / PyTorch backend with CUDA execution providers and CPU fallback.
   - `transcribe_fixed_language(pipe, path: str, language: str)`: Transcribes using the hybrid RNNT decoder conditioned on the target Indian language (`hi` or `ta`).
   - Uses `soundfile.read` for 16 kHz mono audio ingestion to guarantee compatibility.
   - Imports `normalise_text` directly from `asr.transcribe`.

3. **`eval/asr_indic_eval.py` (Parallel Evaluation Script):**
   - Processes only `hi` and `ta` rows from `data/manifests/speech_test.csv` (100 each, 200 total; English excluded).
   - Reuses `check_repetition_loop`, `detect_script_error`, and `compute_cer_wer` from `eval.asr_eval`.
   - Computes Corpus WER, Clean-Transcript WER (excluding clips with repetition loops or script errors), failure rates, and inference speed.

---

### 10.5 Evaluation Results & Artifact Verification in Replica

All evaluation outputs are persisted under `indicfinvoice_indic/eval/results/`:

1. **`asr_indic_results.csv` (129,472 bytes):** Exactly 200 rows with columns:
   `path, ref, hyp, lang, model_id, seconds, loop, script_error`
   - 100 Hindi rows (`lang == "hi"`)
   - 100 Tamil rows (`lang == "ta"`)
   - All rows have `model_id == "ai4bharat/indic-conformer-600m-multilingual"`
   - Zero English rows present.

2. **`asr_indic_summary.json` (758 bytes):**
   - **Hindi (`hi`):** Corpus WER `0.1378`, Clean WER `0.1378`, Kept `100/100`, Loop Rate `0.0%`, Script Error Rate `0.0%`, Median Seconds `0.3624 s`.
   - **Tamil (`ta`):** Corpus WER `0.3187`, Clean WER `0.3187`, Kept `100/100`, Loop Rate `0.0%`, Script Error Rate `0.0%`, Median Seconds `0.3387 s`.

3. **`asr_comparison.csv` (274 bytes):** Exactly 2 rows (`hi` and `ta`) comparing Whisper-medium against IndicConformer across WER, Clean WER, loop rates, and script error rates.

---

### 10.6 Independent Quality Assurance (`pytest -q`)

The automated test suite was executed inside `indicfinvoice_indic/` using the active Conda `translate` environment:

```powershell
(translate) C:\Users\mouli\OneDrive\Desktop\NLP\indicfinvoice_indic> python -m pytest -q
.................................................................... [100%]
68 passed in 22.15s
```

**Scope of Verified Tests:**
- `tests/test_rules.py`: Validates safety boundary conditions, fallback triggers, and asserts presence of the sanitized `[BANK_HELPLINE_NUMBER]` placeholder.
- `tests/test_dialogue.py`: Validates multi-turn state tracking, session caching, and mock banking slot filling.
- `tests/test_nlu.py`: Validates intent classification tokenization and localized entity extraction.

All 68 tests pass completely, verifying zero regression or broken imports in the replica project.

---

### 10.7 File Hash Parity & Cross-Project Synchronization Matrix

To guarantee strict parity between the primary workspace and the replica, cryptographic SHA-256 hashes of all shared code and evaluation artifacts were cross-verified:

| File Path | `indicfinvoice/` SHA-256 | `indicfinvoice_indic/` SHA-256 | Parity Status |
|:---|:---:|:---:|:---:|
| `asr/transcribe.py` | `6e822455f0ea6ab9b44aa7bf6a4ba425...` | `6e822455f0ea6ab9b44aa7bf6a4ba425...` | **MATCH** |
| `asr/transcribe_indicconformer.py` | `1008eaae9c50c5d57bba09f273f5a2e5...` | `1008eaae9c50c5d57bba09f273f5a2e5...` | **MATCH** |
| `eval/asr_eval.py` | `3781254397752178eef8bb6eeb01c2fa...` | `3781254397752178eef8bb6eeb01c2fa...` | **MATCH** |
| `eval/asr_indic_eval.py` | `ff3c1775e1136b668f44ce2f5670be15...` | `ff3c1775e1136b668f44ce2f5670be15...` | **MATCH** |
| `eval/results/asr_summary.json` | `04e71103055d57a9ef2a059815bfe37d...` | `04e71103055d57a9ef2a059815bfe37d...` | **MATCH** |
| `eval/results/asr_results.csv` | `1863b88881721ee5b990e0bab586d52d...` | `1863b88881721ee5b990e0bab586d52d...` | **MATCH** |
| `eval/results/asr_indic_results.csv` | `295a7ecb9301648fb7bb5d194c771fa1...` | `295a7ecb9301648fb7bb5d194c771fa1...` | **MATCH** |
| `eval/results/asr_indic_summary.json` | `75dbd5a0ea12dfdd6b0fb2b75a40a5a3...` | `75dbd5a0ea12dfdd6b0fb2b75a40a5a3...` | **MATCH** |
| `eval/results/asr_comparison.csv` | `369a49ceec325e01be7a1cf7149a0293...` | `369a49ceec325e01be7a1cf7149a0293...` | **MATCH** |
| `DATA_SOURCES.md` | `b6e9a660a5fcfb967d71fb9cba35ad62...` | `b6e9a660a5fcfb967d71fb9cba35ad62...` | **MATCH** |

---

## 11. Final Deliverables Summary

1. **Baseline STT Pipeline:** OpenAI Whisper-Medium evaluation preserved intact in `eval/results/asr_results.csv` and `eval/results/asr_summary.json`.
2. **Native Indic STT Pipeline:** AI4Bharat IndicConformer Multilingual evaluated and reported in `eval/results/asr_indic_results.csv` and `eval/results/asr_indic_summary.json`.
3. **Comparative Evaluation:** Direct side-by-side benchmark recorded in `eval/results/asr_comparison.csv` showing IndicConformer achieving **13.78% WER** in Hindi (vs Whisper's 90.35%) and **31.87% WER** in Tamil (vs Whisper's 96.38%), with 0.00% repetition loops and 0.00% script errors.
4. **Data Contamination Logged:** Pre-registered disclosure in `DATA_SOURCES.md` noting IndicConformer's training overlap with IndicVoices.
5. **Project Isolation Maintained:** Sibling repository `indicfinvoice_indic/` completely synchronized, tested, and protected against committing binary model weights or audio files.

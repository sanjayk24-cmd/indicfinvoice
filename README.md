# IndicFinVoice: Multilingual Voice Banking for Rural India

A voice and text banking assistant for three languages: **English**, **Hindi (हिंदी)**, and **Tamil (தமிழ்)**. A user speaks or types a banking question, the system identifies the intent and slots, queries a rich 24-persona mock bank core, and replies in text in the same language.

> **Quick Links:**
> - [🚀 Complete Execution Guide & How to Run](#13-complete-execution-guide--system-workflow)
> - [🔄 End-to-End Workflow Architecture](#132-full-workflow-architecture)
> - [🧪 Comprehensive 23-Category Example Questions (EN, HI, TA)](#134-comprehensive-list-of-example-questions-by-category)
> - [📡 REST API Reference](#135-api-specification-reference)

---

This README is the build guide. It is written so that an AI coding agent (for example, Antigravity) can follow it stage by stage from an empty folder to a working, tested application. Each stage has:

- **Goal**: what this stage delivers
- **Inputs**: what must exist before starting
- **Tasks**: what to build
- **Acceptance criteria**: checks that must pass before moving on
- **Do not**: things the agent must avoid in this stage

**Rule for the agent:** do not start a stage until the previous stage's acceptance criteria all pass. If a check fails, fix it in the current stage. Do not skip ahead.

---

## 0. Ground Rules

### 0.1 Scope

| Item | Decision |
|---|---|
| Languages | `en` (English), `hi` (Hindi, Devanagari), `ta` (Tamil, Tamil script). Only these three. Romanised code-mixed Hinglish and Tanglish are out of scope for v1, because the dataset has no audio for them. The dataset's other languages (bn, gu, kn, ml, mr, te, ur) are also out of scope and excluded from the manifest. |
| Intents | `balance_check`, `loan_due_date`, `crop_insurance_status`, `transaction_dispute`, `out_of_scope` |
| Slots (BIO tags) | `account_type` (savings, current, kcc), `loan_type` (home, crop, personal), `claim_id`, `amount`, `date`, `transaction_ref` |
| Speech input | Audio files and microphone via Gradio |
| Speech output | Text only in v1. Text-to-speech is optional and out of scope for the core build. |
| Backend | Mock bank API with JSON data. No real accounts, no real money. |
| Authentication | Simulated 4-digit PIN, required only for `transaction_dispute` |

### 0.2 Hardware

- One NVIDIA RTX 5060, 8 GB VRAM.
- Use a PyTorch build for CUDA 12.8 (required for RTX 50-series GPUs).
- All models must run for inference within 8 GB. Fine-tune only IndicBERT. Whisper is used zero-shot.

### 0.3 Models

| Role | Model | Mode |
|---|---|---|
| Speech to text | `openai/whisper-medium` | Zero-shot, fp16, CUDA |
| Understanding | `ai4bharat/indic-bert` | Fine-tuned, two heads |

### 0.4 Data Rules (must never be broken)

1. **Training data** comes only from the template generator (Stage 3) and from the dataset's training split, if the dataset has labels (Stage 2).
2. **Test data** is never used for training, tuning, or choosing hyperparameters. This includes the external dataset's test clips, the unseen text set, and the scripted scenarios.
3. **Splits are frozen** after Stage 6. Do not regenerate them later.
4. **No personal data** in any committed file: no real names, account numbers, phone numbers, or Aadhaar/PAN-like numbers.
5. **Audio files and raw dataset files are never committed to Git.** Only manifests (CSV or JSONL) and scripts are committed.
6. **Record the licence** of every dataset in `DATA_SOURCES.md` before using it.

### 0.5 Coding Standards

- Python 3.10 or newer.
- Type hints and a one-line docstring on every public function.
- Load models once at process start, never per request.
- Set `random.seed(42)`, `numpy` seed, and `torch.manual_seed(42)` in every script that uses randomness.
- Every script that produces a result writes it to a file under `eval/results/` or `models/`, and prints a clear `PASS` or `FAIL` summary where a check applies.
- Use `pytest` for tests. Tests go in `tests/`.

### 0.6 Final Repository Layout

The agent must create this exact layout in Stage 1 and fill it in over later stages.

```
indicfinvoice/
├── README.md                       # build guide; final sections updated at Stage 12
├── DATA_SOURCES.md                 # dataset name, URL, licence, case chosen, counts, freeze dates (Stage 2)
├── requirements.txt                # pinned at Stage 11
├── setup_check.py                  # GPU and environment check (Stage 1)
├── pipeline.py                     # BankingAssistant: end-to-end pipeline (Stage 8)
├── app.py                          # Gradio UI (Stage 9)
├── .gitignore
├── .gitkeep                        # placeholder in any empty folder
│
├── configs/
│   ├── settings.yaml               # thresholds, paths, model names, seed (Stage 1)
│   ├── label_map.yaml              # dataset labels → project intents and slots (Stage 2)
│   └── slot_values.yaml            # normalisation tables for slot values (Stage 6A)
│
├── data/
│   ├── raw/                        # downloaded Kaggle dataset (NOT committed)
│   ├── wav16k/                     # 16 kHz mono WAV conversions (NOT committed)
│   ├── manifests/
│   │   ├── dataset_manifest.csv    # one row per clip (committed)
│   │   └── corrections.csv         # transcript corrections, if any (committed)
│   ├── templates/                  # one YAML per intent, five language blocks (Stage 3)
│   │   ├── balance_check.yaml
│   │   ├── loan_due_date.yaml
│   │   ├── crop_insurance_status.yaml
│   │   ├── transaction_dispute.yaml
│   │   └── out_of_scope.yaml
│   ├── generated/
│   │   └── train_raw.jsonl         # generated, BIO-tagged training text (Stage 3)
│   ├── splits/
│   │   ├── train.jsonl             # Stage 6
│   │   ├── val.jsonl               # Stage 6
│   │   ├── external_test.jsonl     # dataset's labelled rows, if any (Stage 6)
│   │   ├── unseen_test.jsonl       # written by the developer by hand (section 0.7)
│   │   └── SPLITS_FROZEN.txt       # SHA-256 hashes, written at freeze (Stage 6)
│   ├── prepare_audio.py            # convert dataset audio to 16 kHz mono (Stage 2)
│   ├── build_manifest.py           # build dataset manifest (Stage 2)
│   ├── gen_data.py                 # template generator (Stage 3)
│   ├── validate_bio.py             # BIO tag validator (Stage 3)
│   └── split.py                    # splits and leak check (Stage 6)
│
├── docs/
│   ├── TEMPLATES_FROZEN.txt        # SHA-256 of template files (Stage 3)
│   └── limitations.md              # limitations write-up (Stage 12)
│
├── scripts/
│   ├── inspect_dataset.py          # dataset inspection report (Stage 2)
│   └── clean_install_test.sh       # fresh-environment test (Stage 11)
│
├── mockbank/
│   ├── db.json                     # seeded fake customers (Stage 4)
│   └── api.py                      # FastAPI service (Stage 4)
│
├── asr/
│   └── transcribe.py               # Whisper wrapper and normalise() (Stage 5)
│
├── nlu/
│   ├── model.py                    # JointNLU: intent and slot heads (Stage 6)
│   ├── train.py                    # training loop (Stage 6)
│   └── predict.py                  # predict(text) (Stage 6)
│
├── core/
│   ├── lang_id.py                  # identify_language(): en, hi, ta (Stage 8)
│   ├── normalise.py                # normalise_slots(): slot value mapping (Stage 6A)
│   ├── dialogue.py                 # DialogueState: pending requests across turns (Stage 6A)
│   ├── rules.py                    # next_action(): decides the next step (Stage 7)
│   └── responses.json              # reply templates in five languages (Stage 7)
│
├── eval/
│   ├── asr_eval.py                 # WER evaluation (Stage 5)
│   ├── nlu_eval.py                 # intent and slot evaluation (Stage 6)
│   ├── e2e_eval.py                 # end-to-end evaluation (Stage 10)
│   ├── summarise.py                # builds SUMMARY.md from results (Stage 12)
│   ├── scenarios.jsonl             # scripted test cases, with changelog at top (Stage 10)
│   └── results/                    # every reported number comes from here
│       ├── asr_results.csv
│       ├── asr_summary.json
│       ├── nlu_results.json
│       ├── confusion_val.csv
│       ├── confusion_unseen.csv
│       ├── confusion_external.csv
│       ├── e2e_results.json
│       └── SUMMARY.md
│
├── models/                         # trained weights (NOT committed)
│   └── indicfinvoice_v1/           # model weights, tokenizer files, label_maps.json (Stage 6)
│
├── logs/                           # requests.jsonl, conversion errors (NOT committed)
│
└── tests/
    ├── test_db.py                  # Stage 4
    ├── test_api.py                 # Stage 4
    ├── test_gen.py                 # Stage 3
    ├── test_predict.py             # Stage 6
    ├── test_normalise.py           # Stage 6A
    ├── test_dialogue.py            # Stage 6A
    ├── test_rules.py               # Stage 7
    ├── test_lang_id.py             # Stage 8
    └── test_pipeline.py            # Stage 8
```

**Committed to Git:** code, configs, templates, manifests, splits, `docs/`, `eval/results/`, `scenarios.jsonl`, `DATA_SOURCES.md`.
**Not committed:** `data/raw/`, `data/wav16k/`, `models/`, `logs/`, `venv/`, and any audio or personal data.

---

### 0.7 Solo Build Protocol

The project is built by one person. A team would normally provide two safeguards that a solo developer must apply manually:

1. **Separate test writing from template writing.** The unseen test set must not come from the same mind and the same sentences as the training templates.
   - Finish the templates in Stage 3, then write `docs/TEMPLATES_FROZEN.txt`.
   - Wait at least 24 hours.
   - Write the unseen test set from the intent descriptions in section 0.1 and from realistic customer situations. Do not look at the templates while writing it, and do not copy sentences from the dataset's text.
   - Record the date you wrote the templates and the date you wrote the unseen set in `DATA_SOURCES.md`.
2. **Get an outside check for Tamil.** If the developer is not a native Tamil speaker, Tamil templates and replies need checking by a native speaker outside the project. If no one is available, mark those templates and replies `"verified": false` in their files and say so in the report. Do not present unverified Tamil results as validated.

The agent must not write `data/splits/unseen_test.jsonl` itself, because it is generated from the same process as the templates.

**Time planning:** Stages 5 and 6 need long GPU runs, so start them early in the day and run them in the background while working on Stages 4, 7, and 9.

## Stage 1: Environment and Repository

**Goal:** a working Python environment with CUDA, the repository skeleton, and project settings.

**Inputs:** an empty folder `indicfinvoice/`.

**Tasks**

1. Create the folder layout in section 0.6. Create every folder, and add a `.gitkeep` in empty folders.
2. Activate the conda environment `medvqa` and check it:
   ```bash
   conda activate medvqa
   python --version                  # must be 3.10 or newer
   which python pip                  # both must point inside the medvqa environment
   python -c "import torch; print(torch.__version__, torch.version.cuda)"
   ```
   The environment must use Python 3.10 or newer. If it is older, stop and tell the team; do not create a new environment without asking.
   
   Existing packages in `medvqa` may conflict with the requirements (for example, a different `transformers` or `numpy` version). Do not uninstall packages that other projects need. If a conflict appears in Stage 11 and cannot be resolved cleanly, create a separate environment named `indicfinvoice` with `conda create -n indicfinvoice python=3.11` and repeat this stage there.
3. Create `requirements.txt` (versions unpinned at first; pin them in Stage 11):
   ```
   transformers
   datasets
   accelerate
   gradio
   soundfile
   librosa
   jiwer
   fastapi
   uvicorn
   httpx
   pyyaml
   pandas
   scikit-learn
   pytest
   ```
4. Install PyTorch for CUDA 12.8 first, then the rest. Run both inside the activated `medvqa` environment, and use `pip` (not `conda install`) for PyTorch so the CUDA 12.8 wheel is used:
   ```bash
   conda activate medvqa
   pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
   pip install -r requirements.txt
   ```
   Then confirm the GPU is visible:
   ```bash
   python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
   ```
   If the first value is `False`, the installed PyTorch is the CPU build or a CUDA version older than 12.8. Re-run the install line above before going further.
5. Write `setup_check.py` at the repo root. It must:
   - print the torch version, CUDA availability, and GPU name
   - print total and free GPU memory
   - exit with code `1` if CUDA is not available, printing the install command above
   - exit with code `0` otherwise
6. Write `configs/settings.yaml` with:
   ```yaml
   asr_model: openai/whisper-medium
   nlu_base_model: ai4bharat/indic-bert
   confidence_threshold: 0.6
   sample_rate: 16000
   seed: 42
   mockbank_url: http://127.0.0.1:8000
   ```
7. Write `.gitignore` containing at least:
   ```
   venv/
   data/raw/
   data/wav16k/
   models/
   logs/
   __pycache__/
   *.wav
   *.m4a
   *.mp3
   .env
   ```
8. Initialise Git: `git init`, and commit the skeleton.

**Acceptance criteria**

- [ ] `python setup_check.py` exits `0` and prints `CUDA available: True` with the RTX 5060 name.
- [ ] Every folder in section 0.6 exists.
- [ ] `git status` shows no `.wav` or `.m4a` files.

**Do not**

- Do not install TensorFlow or any other deep learning framework.
- Do not download any model yet. Models are downloaded in the stage that first uses them.

---

## Stage 2: Dataset Acquisition, Inspection, and Conversion

**Goal:** the external dataset is downloaded, inspected, licensed, and converted into a common manifest format.

**Inputs:** the Kaggle dataset `nagmanikumar/indilang-voice-dataset` (metadata: "Text and Voice datasets with terms related to Banks & Loans"). A Kaggle account and the Kaggle API token (`~/.kaggle/kaggle.json`).

**Tasks**

**2.1 Download**

```bash
pip install kaggle
kaggle datasets download -d nagmanikumar/indilang-voice-dataset -p data/raw --unzip
```

If the CLI is not set up, download the ZIP from the Kaggle website and extract it into `data/raw/`.

**2.2 Inspect (write the findings into DATA_SOURCES.md)**

Write `scripts/inspect_dataset.py` that prints:

- the full file tree (first 3 levels) under `data/raw/`
- counts by file extension
- the first 5 rows of every CSV or JSON file, with column names and types
- for audio: sample rate, channels, and duration statistics (min, median, max) using `soundfile`
- for each text or label column: number of unique values and the 20 most common values

Then answer these questions and record each answer in `DATA_SOURCES.md`:

| Question | Recorded answer |
|---|---|
| Which languages are present? | |
| Are there audio files? How many, total hours? | |
| Are transcripts provided for the audio? Where? | |
| Are there intent or category labels? What are the values? | |
| Are there slot or entity labels? | |
| Which of the five target languages have audio: en, hi, ta? Are romanised Hinglish or Tanglish clips present, or only native-script ones? | |
| Are the text rows and audio rows the same sentences, or separate sets? | |
| How many speakers? Is speaker ID provided? | |
| What is the licence? (copy the exact text from the Kaggle page) | |
| Is there any personal data (names, account numbers, phone numbers)? | |

**2.3 Choose the case**

Based on the answers, the agent must select exactly one case and record it in `DATA_SOURCES.md`:

- **Case A: audio plus intent labels.** Use the audio for ASR evaluation and the labelled rows for the end-to-end test. Map labels in `configs/label_map.yaml`.
- **Case B: audio plus transcripts, no intent labels.** Use the audio for ASR evaluation. Derive intents by keyword rules in `configs/label_map.yaml`, then have a human check a random sample of at least 50 items and record the agreement rate.
- **Case C: text with labels, no usable audio.** Use the labelled text as the unseen NLU test set. Use Whisper evaluation only on the separate Hindi or Hinglish public clip set if one is found, and report that the banking audio test was not possible.
- **Case D: nothing usable.** Stop and report to the team. Do not proceed.

**2.4 Convert audio**

Write `data/prepare_audio.py` that:

- reads the dataset's audio files
- converts each to 16 kHz mono WAV into `data/wav16k/`, using `librosa.load(path, sr=16000, mono=True)` and `soundfile.write`
- skips and logs any file that fails to decode, into `logs/audio_conversion_errors.txt`

**2.5 Build the manifest**

Write `data/build_manifest.py` that produces `data/manifests/dataset_manifest.csv` with these columns, one row per clip:

```
clip_id, path, ref, lang, intent, slots_json, speaker, noise, source_split
```

- `path`: relative path to `data/wav16k/...`
- `ref`: transcript, unchanged from the dataset
- `lang`: one of `en`, `hi`, `ta`. Use the dataset's own language field or folder name as the primary source. Do not detect language from the script alone: romanised Hindi, romanised Tamil, and English all use Latin letters, so script detection cannot separate them. Romanised Hinglish and Tanglish are out of scope for v1 and must not appear in the manifest.
- `intent`: project intent, after mapping through `configs/label_map.yaml`, or `out_of_scope` for unmapped items if the dataset is Case A and the item is clearly unrelated
- `slots_json`: JSON string of slot values if available; empty otherwise
- `speaker`: speaker ID if provided, otherwise `unknown`
- `noise`: `unknown` unless the dataset says otherwise
- `source_split`: the dataset's own split name if it has one

Drop any row whose `ref` is empty, whose audio file is missing, or whose language is not one of the three in section 0.1. Log the number dropped per reason.

**2.6 Licence and attribution**

Add a section to `DATA_SOURCES.md` with the dataset name, URL, licence text, download date, the number of clips used, and the citation (if the Kaggle page gives one).

**Acceptance criteria**

- [ ] `DATA_SOURCES.md` answers every row of the table in 2.2.
- [ ] One case (A, B, C, or D) is recorded, with the reason.
- [ ] `data/wav16k/` contains only 16 kHz mono WAV files.
- [ ] `data/manifests/dataset_manifest.csv` exists, and `build_manifest.py` prints the row count and the number dropped.
- [ ] A random sample of 20 manifest rows has been listened to or read by a human, and any errors are recorded in `DATA_SOURCES.md`.
- [ ] The dataset licence allows the intended use. If the licence is unclear, stop and ask the team.

**Do not**

- Do not commit `data/raw/` or `data/wav16k/`.
- Do not edit transcripts in place. If a transcript is wrong, record the correction in a separate file, `data/manifests/corrections.csv`, and apply it in `build_manifest.py`.

---

## Stage 3: Training Text Generation (Templates)

**Goal:** a labelled training set for the NLU model, generated from templates, with valid BIO tags.

**Inputs:** the intent and slot definitions in section 0.1.

**Why templates:** the dataset may not contain enough labelled text for all four intents and all slot values. Templates give controlled, correctly labelled data. The dataset itself is still used for ASR and as an external test.

**Tasks**

1. Write one YAML file per intent in `data/templates/`: `balance_check.yaml`, `loan_due_date.yaml`, `crop_insurance_status.yaml`, `transaction_dispute.yaml`, `out_of_scope.yaml`. Structure:
   ```yaml
   intent: balance_check
   languages:
     hi:
       templates:
         - "{account_type} खाते का बैलेंस बताइए"
         - "मेरे {account_type} खाते में कितने पैसे हैं"
         # about 10 in total
     hinglish:
       templates:
         - "{account_type} account ka balance batao"
         - "mere {account_type} account mein kitne paise hain"
         # about 10 in total
   slots:
     account_type:
       hi: ["बचत", "चालू", "केसीसी"]
       hinglish: ["savings", "current", "KCC"]
   ```
   Use these slot values: `account_type` (savings, current, KCC), `loan_type` (home, crop, personal), `claim_id` (CLM-771, CLM-402, CLM-930), `amount` (500, 1500, 22000, 75000), `date` (today, yesterday, 12 October, 5 November), `transaction_ref` (TXN-9001, TXN-9002). Write the Devanagari and romanised values in the YAML files.

   Each intent YAML must have three language blocks: `en`, `hi`, and `ta`, with about 10 templates each. Do not write `hinglish` or `tanglish` blocks, even if an example elsewhere shows them.
   - `en`: plain English banking phrases.
   - `hi`: Devanagari Hindi.
   - `ta`: Tamil script. Slot values in Tamil script, for example savings = சேமிப்பு, current = நடப்பு, KCC = கேசிசி.
   
   Tamil templates must be checked by a native Tamil speaker from outside the project if the developer is not a native speaker. Record the reviewer's description (for example, "native speaker, Tamil Nadu") in `DATA_SOURCES.md`, without a name. If no reviewer is available, mark those templates `"verified": false` and say so in the report. Do not use machine translation without review.
2. Templates for `out_of_scope` contain no slots. They cover greetings, weather, sports, and unsupported products.
3. Write `data/gen_data.py`:
   - reads every YAML file in `data/templates/`
   - for each template and language, generates 60 examples by filling slots randomly
   - produces BIO tags: first word of a slot value gets `B-<slot>`, following words get `I-<slot>`, other words get `O`
   - writes `data/generated/train_raw.jsonl` with fields `tokens`, `tags`, `intent`, `lang`, `template_id`
   - `template_id` is the index of the template in its YAML file, plus the intent name
   - prints the total count
4. Write `data/validate_bio.py`: checks that tokens and tags have equal length, no `I-x` appears without a preceding `B-x` or `I-x`, and every intent is one of the five allowed. Prints the error count and the first five failures. Exits `1` on any error.

**Acceptance criteria**

- [ ] `python data/gen_data.py` prints a count above 800.
- [ ] `python data/validate_bio.py` reports 0 errors.
- [ ] Five randomly chosen generated examples are printed and read by a human for naturalness. Record the result.
- [ ] `out_of_scope` examples contain no `B-` or `I-` tags.
- [ ] `docs/TEMPLATES_FROZEN.txt` is written with the SHA-256 hash of every file in `data/templates/`. From this point, templates may change only with a recorded reason in `DATA_SOURCES.md`.

**Do not**

- Do not write templates by copying sentences from the dataset. The dataset's text is for testing.
- Do not split the file here. Splitting happens in Stage 6.

---

## Stage 4: Mock Bank API

**Goal:** a FastAPI service with fake banking data that the rules layer can call.

**Inputs:** the slot definitions from section 0.1.

**Tasks**

1. Write `mockbank/db.json` with three customers `C001`, `C002`, `C003`. Each has:
   - `pin`: a 4-digit string
   - `accounts`: `savings` and `kcc`, each with `balance`
   - `loans`: `home`, `crop`, or `personal`, each with `due_date` (ISO format) and `outstanding`
   - `claims`: keyed by `claim_id` (for example `CLM-771`), each with `status` and `amount`
   - `transactions`: keyed by `transaction_ref` (for example `TXN-9001`), each with `amount`, `date`, and `status`
   
   `C001` must have a crop loan, a claim `CLM-771`, and a transaction `TXN-9001`.
2. Write `mockbank/api.py`. Load the JSON once at startup. Endpoints:
   - `GET /balance?customer_id=&account_type=`
   - `GET /loan/due?customer_id=&loan_type=`
   - `GET /claim/status?customer_id=&claim_id=`
   - `POST /dispute` with body `{customer_id, transaction_ref, amount, date, pin}`
3. Error rules:
   - unknown `customer_id`: 404
   - missing required field: 400, naming the field
   - unknown `account_type` or `loan_type`: 400, listing valid values
   - wrong PIN on `/dispute`: 401
   - unknown `transaction_ref`: 404
   - success on `/dispute`: `{"status": "dispute_registered", "reference": "DSP-" + 4 random digits}`
4. Disputes are stored in memory only. Do not write to `db.json`.
5. No model or language processing in this service. Plain lookups only.
6. Write `tests/test_api.py` with `fastapi.testclient`. Test each endpoint's success case and at least one error case.

**Acceptance criteria**

- [ ] `uvicorn mockbank.api:app --port 8000` starts without errors.
- [ ] `pytest tests/test_api.py` passes.
- [ ] `tests/test_db.py` checks that every customer has the required keys and the PIN is 4 digits; it passes.

**Do not**

- Do not add authentication beyond the PIN check.
- Do not return any field not listed above.

---

## Stage 5: Speech Recognition (ASR) and ASR Evaluation

**Goal:** a Whisper wrapper that transcribes audio, and a measured Word Error Rate (WER) on the dataset's audio.

**Inputs:** Stage 2 manifest with audio clips.

**Tasks**

1. Write `asr/transcribe.py`:
   - loads `openai/whisper-medium` once at module import, with `torch_dtype=torch.float16` and `device="cuda"`, via `transformers.pipeline("automatic-speech-recognition", ...)`
   - `transcribe(path: str) -> str`: loads audio at 16 kHz mono with librosa, passes it to the pipeline with `generate_kwargs={"task": "transcribe"}`, returns the stripped text. Do not pass a language argument: let Whisper auto-detect, and record the detected language in `asr_results.csv` if the pipeline returns it. Forcing one language hides errors such as Tamil speech being transcribed as Hindi
   - `normalise(text: str) -> str`: lowercase, remove punctuation (including Devanagari danda `।`), collapse whitespace; apply the same function to references and hypotheses
2. Write `eval/asr_eval.py`:
   - reads `data/manifests/dataset_manifest.csv`
   - transcribes every clip, timing each call
   - computes WER with `jiwer`, overall, per `lang`, and per `noise` (if known)
   - writes `eval/results/asr_results.csv` with columns `clip_id, ref, hyp, lang, noise, seconds`
   - writes `eval/results/asr_summary.json` with WER values and median time per clip
   - prints a table
3. Report the number of clips and the language breakdown in the summary.

**Acceptance criteria**

- [ ] `python eval/asr_eval.py` runs end to end on the full manifest, or on a 200-clip subset if the full set is too slow, with the subset size recorded.
- [ ] Both result files exist.
- [ ] WER is reported per language.
- [ ] The Whisper model loads once: confirm by checking that `asr/transcribe.py` has no load call inside `transcribe()`.

**Do not**

- Do not fine-tune Whisper.
- Do not change the normalisation function after seeing results. If it must change for a real reason, record the change and re-run.
- Do not fix individual transcripts to improve WER.

**Note for the report:** Use the same normalisation for all three languages, and state it in the report. Whisper-medium is weaker on Tamil than on Hindi and English, so always report WER per language rather than one average.

---

## Stage 6: NLU Model (Intent and Slot), Splits, and NLU Evaluation

**Goal:** a trained JointNLU model with two heads, frozen train, validation, and test splits, and measured NLU results.

**Inputs:** Stage 3 generated data; Stage 2 manifest (for Case A, used as the external test).

**Tasks**

1. **Splits** — write `data/split.py`:
   - reads `data/generated/train_raw.jsonl`
   - splits 85/15 into `data/splits/train.jsonl` and `data/splits/val.jsonl` **by `template_id`**, so no template appears in both
   - reads the dataset's labelled text (Case A or C) and writes it to `data/splits/external_test.jsonl`, in the same token and tag format, using the BIO tags from `configs/label_map.yaml`. If the dataset has no slot labels, write intent only and mark `tags` as all `O`. Report slot F1 for that set as not applicable, and say so in the report.
   - `data/splits/unseen_test.jsonl` is written by the developer under the solo protocol in section 0.7, after templates are frozen. The agent must not write this file itself. If it is missing, the rest of Stage 6 still runs, and the NLU results report that set as not available.
   - runs a leak check: no `(tokens, intent)` pair appears in both train and any test file. Prints the result. Exits `1` on any overlap.
   - writes `data/splits/SPLITS_FROZEN.txt` with the file hashes (SHA-256). From this point, these files may not change.
2. **Model** — write `nlu/model.py`, class `JointNLU(nn.Module)`:
   - encoder: `AutoModel.from_pretrained(nlu_base_model)`. Check the model card to confirm English, Hindi, and Tamil are in its pretraining languages, and record this in the report. IndicBERT is pretrained on native scripts, so check its results per language.
   - dropout 0.1
   - `intent_head`: `Linear(hidden, n_intents)` on the first token (`[CLS]`)
   - `slot_head`: `Linear(hidden, n_tags)` on every token
   - `forward(input_ids, attention_mask)` returns `(intent_logits, slot_logits)`
3. **Training** — write `nlu/train.py`:
   - builds label maps from the training split only, saved to `models/indicfinvoice_v1/label_maps.json`
   - tokenises with `is_split_into_words=True`
   - labels only the first sub-word of each word; other sub-words get `-100`
   - loss = cross-entropy(intent) + cross-entropy(slots, `ignore_index=-100`)
   - AdamW, learning rate `3e-5`, batch size 32, 8 epochs
   - after each epoch, evaluates on validation; keeps the checkpoint with best intent macro-F1
   - uses `torch.autocast` (float16) to stay within 8 GB
   - saves model weights, tokenizer, and label maps to `models/indicfinvoice_v1/`
   - prints per-epoch intent macro-F1 and slot F1
4. **Prediction** — write `nlu/predict.py`:
   - `predict(text: str) -> dict` returns `{"intent": str, "slots": dict, "confidence": float}`
   - decodes slots from BIO tags by joining consecutive tokens of the same type
   - `confidence` is the softmax maximum of the intent logits
   - loads the model once at module import
5. **Evaluation** — write `eval/nlu_eval.py`:
   - for `val`, `unseen_test` (if present), and `external_test` (if present), reports intent accuracy, intent macro-F1, slot F1 (token level over non-`O` tags)
   - writes a per-intent confusion matrix per set to `eval/results/confusion_<set>.csv`
   - writes all numbers to `eval/results/nlu_results.json`
   - if a set file is missing, prints a clear skip message and continues

**Acceptance criteria**

- [ ] `SPLITS_FROZEN.txt` exists, with hashes for train, val, and external test.
- [ ] Leak check passes.
- [ ] `nlu/train.py` completes on the GPU and saves the model.
- [ ] `pytest tests/test_predict.py` passes: for three sentences from the templates, predict returns the expected intent.
- [ ] `eval/results/nlu_results.json` contains results for every available set, with intent accuracy broken down by `lang` (en, hi, ta).

**Do not**

- Do not train on `external_test`, `unseen_test`, or anything derived from them.
- Do not tune hyperparameters using `external_test` or `unseen_test`. Use `val` only.
- Do not regenerate splits after `SPLITS_FROZEN.txt` is written. If a split is wrong, record the problem in `DATA_SOURCES.md`, stop, and ask the team.

**If IndicBERT does not converge** (intent macro-F1 below 0.5 after 8 epochs): lower the learning rate to `2e-5`, train 12 epochs, and check the label alignment with a printed example. Only then change the architecture. If still failing, fall back to a keyword matcher in `nlu/predict.py` and keep the transformer result in the report as a comparison.

---

## Stage 6A: Slot Normalisation and Dialogue State

**Goal:** convert the NLU's raw slot text into the exact values the mock bank expects, and keep a pending request open across turns so a short reply like "savings" completes the earlier question.

**Inputs:** Stage 6 predictions (intent, slot text, confidence).

**Tasks**

1. **Value mapping.** Write `configs/slot_values.yaml` with the mapping tables. Write `core/normalise.py` with `normalise_slots(slots: dict) -> dict` that reads them. Mappings:
   - `account_type`: "savings", "बचत", "சேமிப்பு" → `savings`; "current", "चालू", "நடப்பு" → `current`; "kcc", "KCC", "केसीसी", "கேசிசி" → `kcc`
   - `loan_type`: "home", "होम", "வீடு" → `home`; "crop", "फसल", "பயிர்" → `crop`; "personal", "पर्सनल", "தனிநபர்" → `personal`
   - `claim_id`: normalise separators and case, and convert spoken digits to numerals. "CLM 771", "clm-771", and "सी एल एम सात सात एक" all become `CLM-771`. Digit words are mapped for Hindi (एक to नौ, शून्य), Tamil (ஒன்று to ஒன்பது, பூஜ்ஜியம்), and English.
   - `amount`: convert to integer rupees. "1500", "1.5k", "15 सौ", "पंद्रह सौ" → `1500`. Only the number words used in the templates are mapped; anything else is treated as missing.
   - `date`: "today", "आज", "இன்று" → today's date; "yesterday", "kal", "कल", "நேற்று" → yesterday's date; "12 October" → ISO date in the current year. Use `datetime.date.today()`.
   - `transaction_ref`: "TXN 9001", "txn9001" → `TXN-9001`.
   
   **Rule:** if a value is not in the tables and cannot be parsed, leave the slot out. Never guess.

2. **Dialogue state.** Write `core/dialogue.py` with `DialogueState` holding `intent`, `slots`, `awaiting` (the slot name the system asked for, or `None`), and `last_active` (timestamp). Rules:
   - If `awaiting` is set and the new input provides a value for that slot, fill it, keep the pending intent, and clear `awaiting` once all required slots are filled.
   - If `awaiting` is set and the new input is a new banking request with a different intent, discard the old state and start the new request.
   - Cancel words ("cancel", "रद्द", "ரத்து") clear the state.
   - State expires after 5 minutes without input, so an old pending request cannot be completed later.

3. **Tests.** `tests/test_normalise.py` with at least 5 examples per slot type, covering Hindi, Tamil, and English forms. `tests/test_dialogue.py` covering the two-turn case, cancel, expiry, and a new intent overriding a pending one.

**Acceptance criteria**

- [ ] `pytest tests/test_normalise.py tests/test_dialogue.py` passes.
- [ ] After "KCC ka balance batao" (no account type given) and then "savings", the second turn fills `account_type = savings` and returns the balance.
- [ ] An unrecognised value is left out of the slots, not guessed.

**Do not**

- Do not call the bank API from `normalise.py` or `dialogue.py`.
- Do not use a language model for normalisation. Use the reviewed mapping tables.

---

## Stage 7: Rules Layer and Response Templates

**Goal:** a deterministic layer that decides the next action from the NLU output, plus language-specific replies.

**Inputs:** Stage 6 prediction output.

**Tasks**

1. Write `core/rules.py` with `next_action(intent, slots, confidence) -> dict`:
   - if `confidence < 0.6`: return `{"action": "repeat"}`
   - if `intent == "out_of_scope"`: return `{"action": "help"}`
   - required slots:
     - `balance_check`: `account_type`
     - `loan_due_date`: `loan_type`
     - `crop_insurance_status`: `claim_id`
     - `transaction_dispute`: `transaction_ref`, `amount`, `date`
   - if a required slot is missing or empty: return `{"action": "ask", "slot": <name>, "question": <text>}`. Questions in romanised Hinglish, stored in a `QUESTIONS` dict in the file.
   - if `intent == "transaction_dispute"` and all slots are present: return `{"action": "need_pin"}`
   - otherwise: return `{"action": "call_api", "intent": intent, "slots": slots}`
2. Write `core/responses.json` with templates for each intent in all three languages (`en`, `hi`, `ta`), plus `repeat`, `help`, `ask`, `need_pin`, and `error`. Placeholders are named, such as `{balance}`, `{due_date}`, `{status}`, `{reference}`.
3. Write `tests/test_rules.py` with one test per branch, plus a test that an empty-string slot counts as missing.

**Acceptance criteria**

- [ ] `pytest tests/test_rules.py` passes.
- [ ] `python -m json.tool core/responses.json` succeeds.
- [ ] Every intent and every reply type has templates in all three languages. A native Tamil speaker has checked the `ta` replies.

**Do not**

- Do not call the bank API from `rules.py`. It only decides the action.

---

## Stage 8: End-to-End Pipeline

**Goal:** one function that takes audio or text and returns the reply, connecting every stage.

**Inputs:** Stages 4 to 7.

**Tasks**

1. Write `pipeline.py` with a class `BankingAssistant` that loads the ASR and NLU models once at construction.
2. Language identification: write `core/lang_id.py` with `identify_language(text: str) -> str` returning one of `en`, `hi`, `ta`.
   - Tamil script → `ta`; Devanagari → `hi`.
   - Latin script → `en`. Romanised Hindi and Tamil are out of scope for v1, so no word lists are needed.
   - Test it on at least 10 examples per language in `tests/test_lang_id.py`.
   - The reply language is the detected language of the input.
3. Method `handle_text(text: str, customer_id: str, pending: dict | None, pin: str | None) -> dict`:
   - runs `predict(text)`
   - runs `next_action(...)`
   - if the action is `ask`, returns the question and stores the pending intent and slots, so the next input fills the missing slot
   - if the action is `need_pin` and `pin` is empty, asks for the PIN
   - if the action is `call_api`, calls the bank API through `httpx` at `mockbank_url`, maps the response to the reply template in `core/responses.json`
   - handles API errors by returning the `error` template, never by raising
   - returns `{"reply": str, "intent": str, "confidence": float, "slots": dict, "action": str, "pending": dict | None}`
4. Method `handle_audio(path: str, ...) -> dict`: calls `transcribe()`, then `handle_text()`, and adds the transcript to the result.
5. Write `tests/test_pipeline.py`:
   - a two-turn dialogue: "KCC ka balance batao" with no account type, then "savings" as the next reply, where the second turn fills the slot
   - a dispute without a PIN, then with the PIN

**Acceptance criteria**

- [ ] `pytest tests/test_pipeline.py` passes.
- [ ] A text request for a loan due date returns a due date from the mock bank.

**Do not**

- Do not let the NLU output reach the bank API without passing through `next_action()`.
- Do not write any state to disk inside the pipeline.

---

## Stage 9: Gradio Application

**Goal:** a browser interface that accepts audio, microphone input, or typed text.

**Inputs:** Stage 8 `BankingAssistant`.

**Tasks**

1. Write `app.py` with Gradio Blocks:
   - `gr.Audio(sources=["microphone", "upload"], type="filepath")`
   - `gr.Textbox` for typed input
   - `gr.Dropdown` for customer ID: `C001`, `C002`, `C003` (default `C001`)
   - `gr.Textbox(type="password")` for the PIN
   - read-only outputs: transcript, detected intent and confidence (as JSON), slots (as JSON), reply
   - a button labelled "Ask"
   - `gr.State` for the pending dialogue state
2. Logic:
   - if audio is provided, use `handle_audio`; otherwise use `handle_text`
   - show the reply and keep the pending state
   - never crash: catch exceptions and show a friendly error in the reply box
3. Logging: append one line per request to `logs/requests.jsonl` with timestamp, input text (or "audio"), intent, action, and outcome. Never log audio content, PIN, or the reply's account details.
4. Update `README.md` with the run instructions in section 13.

**Acceptance criteria**

- [ ] Start the API in one terminal: `uvicorn mockbank.api:app --port 8000`.
- [ ] Start the app in another: `python app.py`.
- [ ] Typing "mera crop loan kab due hai" returns a due date.
- [ ] A dispute without a PIN asks for the PIN; with the correct PIN it registers.
- [ ] An audio file from the dataset returns a reply.
- [ ] `logs/requests.jsonl` contains the entries and no PIN values.

---

## Stage 10: End-to-End Evaluation

**Goal:** measured task success for the full system, plus latency.

**Inputs:** Stage 8 pipeline and Stage 2 manifest.

**Tasks**

1. Write `eval/scenarios.jsonl` with at least 50 scripted cases: 10 per intent (five intents), with at least 2 cases per language (`en`, `hi`, `ta`) for each intent. Include phrasings not in the templates. Tamil cases must be written or checked by a native Tamil speaker. Each line:
   ```json
   {"text": "...", "expected_intent": "...", "expected_action": "...", "customer_id": "C001", "expected_api_status": 200}
   ```
   For multi-turn cases, add `"followup": "..."`.
2. Write `eval/e2e_eval.py`:
   - runs every scenario through `BankingAssistant.handle_text`, and reports task success and intent accuracy per `lang`, not only overall
   - records whether intent, action, and API status match expectations
   - runs the dataset's labelled audio clips (if Case A or B) through `handle_audio` on a fixed random sample of 100 clips, and records intent accuracy on audio
   - records NLU latency, median and 95th percentile, and total pipeline latency
   - writes `eval/results/e2e_results.json`
3. Print the overall task success, per-intent success, and latency.

**Acceptance criteria**

- [ ] `python eval/e2e_eval.py` runs and writes results.
- [ ] Task success is reported overall and per intent.
- [ ] Latency is reported as median and 95th percentile. Targets (report whether each is met, do not force a change): NLU under 100 ms per utterance on the RTX 5060; end-to-end under 2 seconds per text request, excluding Whisper; under 5 seconds per audio request.

**Do not**

- Do not edit `scenarios.jsonl` after looking at the failures. If a scenario is wrong, record the change in a changelog section at the top of the file, with the reason.

---

## Stage 11: Testing, Packaging, and Clean Install

**Goal:** all tests pass, dependencies are pinned, and a new machine can run the project by following the README.

**Tasks**

1. Run `pytest -q` and fix every failure.
2. Pin dependency versions in `requirements.txt` using `pip freeze` from the working environment, keeping `torch` on the cu128 build with a comment.
3. Write `scripts/clean_install_test.sh`:
   - creates a fresh virtual environment in a temporary folder
   - copies the repository, excluding `data/raw/`, `data/wav16k/`, `models/`, `logs/`, and `venv/`
   - installs the requirements
   - runs `setup_check.py`, `pytest -q`, and starts the API and the app briefly to confirm they launch
   - prints PASS or FAIL for each step
4. Run the clean install test. Fix any failing step, then re-run.

**Acceptance criteria**

- [ ] `pytest -q` reports all tests passing.
- [ ] `scripts/clean_install_test.sh` prints PASS for every step.
- [ ] The trained model can be reloaded from `models/indicfinvoice_v1/` without retraining.

---

## Stage 12: Results Summary and Documentation

**Goal:** every number in the report comes from a results file, and the documentation matches what was built.

**Tasks**

1. Write `eval/summarise.py`. It reads `eval/results/*.json` and `*.csv`, and writes `eval/results/SUMMARY.md` with these tables:
   - **ASR:** WER overall, per language (en, hi, ta), per noise condition (if known), with the transcription policy stated
   - **NLU:** intent accuracy and macro-F1, and slot F1, for val, unseen, and external test
   - **End-to-end:** task success overall and per intent, audio intent accuracy, NLU latency median and 95th percentile, total pipeline latency
   - **Tests:** number passing
   No number may be typed by hand. Every value is read from a results file.
2. Update `README.md`:
   - replace the project description with a three-sentence summary
   - section 13 (run instructions)
   - section 14 (limitations)
3. Update `DATA_SOURCES.md` with the final clip counts used, the case chosen in Stage 2, and the licence text.
4. Write `docs/limitations.md` covering at least:
   - templates limit linguistic variety, so the unseen and external sets are the realistic measure
   - Whisper is used without fine-tuning
   - the bank is simulated, and the PIN check is a demonstration only
   - only English, Hindi, and Tamil are covered; romanised Hinglish and Tanglish are out of scope
   - the dataset's licence and any known gaps
   - Tamil results are weaker than Hindi and English, and must be reported per language
5. Tag the release in Git: `git tag v1.0`.

**Acceptance criteria**

- [ ] `eval/results/SUMMARY.md` exists and every number traces to a results file.
- [ ] `README.md` run instructions work on a clean machine.
- [ ] `docs/limitations.md` exists.

---

## 13. Complete Execution Guide & System Workflow

### 13.1 Prerequisites & System Requirements
- **Python:** 3.10 or 3.11 (tested on Windows & Linux with Conda / Python venv).
- **Node.js:** v18.0+ and `npm`.
- **GPU (Optional / Recommended):** NVIDIA GPU with CUDA 12.8 for fast fp16 neural speech transcription and NLU inference; runs cleanly on CPU with float32 fallbacks.

---

### 13.2 Full Workflow Architecture
The application supports both spoken audio and text queries, routing through language identification, neural speech recognition, joint intent/slot understanding, dialogue management, and a mock banking core:

```
                              [ User Interaction ]
                               /                \
                     (Spoken Voice Audio)      (Typed Text)
                             /                    \
            [ Web Audio API (16kHz Mono PCM) ]     \
                            │                       \
            [ POST /transcribe or /voice ]           \
                            │                         \
               [ Script / Lang Detection ]             \
                /                       \               \
        (English: 'en')            (Indic: 'hi' / 'ta')  \
               │                               │          │
     [ openai/whisper-medium ]     [ ai4bharat/indic-     │
                                     conformer-600m ]     │
               │                               │          │
               └───────────────┬───────────────┘          │
                               │                          │
                     Transcribed Plain Text               │
                               │                          │
                               └───────────────┬──────────┘
                                               │
                                 [ JointNLU Model ]
                             (models/indicfinvoice_v1)
                                      /        \
                           (Intent Detection) (BIO Slot Filling)
                                      \        /
                              [ Dialogue State Tracker ]
                            (core/dialogue.py, core/rules.py)
                                               │
                                  [ Mock Banking Core ]
                                (24 Personas, 700+ Txns)
                                               │
                                [ Multilingual Response ]
                               (English / हिंदी / தமிழ்)
                                               │
                                [ Modern React / Vite UI ]
                       (Sound Waveforms, Metallic Card, Feeds)
```

---

### 13.3 Step-by-Step Execution

#### Step 1: Clone and Set Up Python Environment
```bash
git clone https://github.com/sanjayk24-cmd/indicfinvoice.git
cd indicfinvoice

# Create or activate Conda environment
conda create -n translate python=3.11 -y
conda activate translate

# Install PyTorch with CUDA 12.8 (or CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Model Training & Verification (Optional)
The pre-trained production model weights are packaged under `models/indicfinvoice_v1`. To retrain the 23-intent JointNLU model from scratch:
```bash
python scripts/train_joint_nlu.py
```
To run the automated regression test suite:
```bash
pytest tests/ -q
# Expected: 174 passed
```

#### Step 3: Run the FastAPI Backend Server
The backend service hosts the REST and speech endpoints, runs model inferences as singletons, and connects to the expanded 24-persona mock database:
```bash
# From repository root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- **API Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check Endpoint:** `http://127.0.0.1:8000/health`

#### Step 4: Run the Modern React / Vite Frontend
The frontend features real-time audio wave visualization, language selector pills, an interactive visual debit card, customer persona switching, and embedded banking cards:
```bash
# In a second terminal window
cd frontend
npm install
npm run dev
```
- **Web Application URL:** `http://localhost:5173`

---

### 13.4 Comprehensive List of Example Questions by Category

Test the system by copying any query below into the chat composer, or by clicking the microphone button and speaking aloud in **English**, **Hindi (हिंदी)**, or **Tamil (தமிழ்)**:

#### 1. Account Closure (`account_closure`)
* **[EN]** *"I have shifted abroad and need to close down my salary account permanently."*
* **[EN]** *"Kindly guide me through closing my secondary current account."*
* **[EN]** *"Is there an exit penalty if I shut down my account after 8 months?"*
* **[HI]** *"मुझे अपना बैंक खाता हमेशा के लिए बंद करवाना है क्योंकि मैं शहर छोड़ रहा हूँ"*
* **[TA]** *"என் வங்கிக் கணக்கை நிரந்தரமாக முடித்துவிட்டு மீதிப் பணத்தை எப்படி பெறுவது"*

#### 2. Account Discovery (`account_discovery`)
* **[EN]** *"Could you list all the savings and deposit accounts linked to my customer ID?"*
* **[EN]** *"How many total active accounts do I currently operate with this bank?"*
* **[EN]** *"Please display the branch IFSC and masked numbers for all my accounts."*
* **[HI]** *"मेरे सीआईएफ नंबर से जुड़े सभी बैंक खातों का विवरण दिखाइए"*
* **[TA]** *"எனது வாடிக்கையாளர் எண்ணில் எத்தனை வங்கிக் கணக்குகள் உள்ளன என்பதை காட்டுங்கள்"*

#### 3. App Troubleshooting (`app_troubleshooting`)
* **[EN]** *"The application keeps crashing every time I reach the biometric scan screen."*
* **[EN]** *"I am not receiving the 6-digit login OTP on my mobile network."*
* **[EN]** *"My session expired unexpectedly while I was reviewing my account details."*
* **[HI]** *"मोबाइल ऐप बार-बार क्रैश हो रहा है और लॉगिन स्क्रीन नहीं खुल रही"*
* **[TA]** *"மொபைல் பேங்கிங் செயலியில் கைரேகை உள்நுழைவு வேலை செய்யவில்லை"*

#### 4. Balance Check (`balance_check`)
* **[EN]** *"What is the current available ledger balance in my main savings account?"*
* **[EN]** *"How much spendable cash is left in my primary account right now?"*
* **[EN]** *"Could you verify the available funds in my current account after today's debits?"*
* **[HI]** *"मेरे मुख्य बचत खाते में इस समय कुल कितना बैलेंस बाकी है"*
* **[TA]** *"இன்றைய நிலவரப்படி எனது சேமிப்பு கணக்கில் எவ்வளவு பணம் உள்ளது"*

#### 5. Card Controls (`card_controls`)
* **[EN]** *"Please enable contactless NFC tap payments on my Platinum debit card."*
* **[EN]** *"Turn off international online transactions on my Visa credit card right now."*
* **[EN]** *"I want to lower my daily ATM cash withdrawal limit to five thousand rupees."*
* **[HI]** *"मेरे वीजा डेबिट कार्ड पर ऑनलाइन इंटरनेशनल पेमेंट्स बंद कर दीजिए"*
* **[TA]** *"எனது டெபிட் கார்டில் ஏடிஎம் பணம் எடுக்கும் வரம்பை மாற்ற முடியுமா"*

#### 6. Cheque Services (`cheque_services`)
* **[EN]** *"Can I issue an immediate stop payment order on cheque number 458921?"*
* **[EN]** *"I need a fresh 25-leaf chequebook delivered to my registered home address."*
* **[EN]** *"Has the clearance for high-value cheque 782103 gone through yet?"*
* **[HI]** *"चेक संख्या 654321 का भुगतान तुरंत रोकने के लिए आवेदन कैसे करें"*
* **[TA]** *"எனது புதிய காசோலை புத்தகம் தபாலில் எப்போது வந்து சேரும்"*

#### 7. Credit Card Billing (`credit_card_billing`)
* **[EN]** *"Can you split my total outstanding credit card bill into easy 6-month EMIs?"*
* **[EN]** *"Why is there an unbilled foreign currency markup charge on my credit card?"*
* **[EN]** *"How much minimum payment is mandatory for my credit card before the due date?"*
* **[HI]** *"मेरे क्रेडिट कार्ड के कुल बिल को 6 महीने की किस्तों में बदलें"*
* **[TA]** *"எனது கிரெடிட் கார்டு பில்லில் இந்த மாதம் குறைந்தபட்சம் எவ்வளவு செலுத்த வேண்டும்"*

#### 8. Fees & Penalties (`fees_and_penalties`)
* **[EN]** *"Why was an annual debit card maintenance charge deducted from my balance?"*
* **[EN]** *"Please explain the penalty levied for not keeping the minimum average quarterly balance."*
* **[EN]** *"Can you reverse the surcharge fee debited for non-home branch ATM usage?"*
* **[HI]** *"खाते में न्यूनतम बैलेंस न रखने पर कितना जुर्माना काटा गया है"*
* **[TA]** *"என் கணக்கிலிருந்து எஸ்எம்எஸ் கட்டணம் ஏன் பிடித்தம் செய்யப்பட்டது"*

#### 9. Fixed Deposits (`fixed_deposits`)
* **[EN]** *"What interest rate will I earn if I book a 1-year cumulative fixed deposit?"*
* **[EN]** *"Can I break my term deposit early and what would be the penalty rate?"*
* **[EN]** *"When is the exact maturity date for my fixed deposit account 998877?"*
* **[HI]** *"एक साल की फिक्स्ड डिपॉजिट पर बैंक कितना ब्याज दे रहा है"*
* **[TA]** *"எனது நிலையான வைப்பு நிதி எப்போது முதிர்வடையும் மற்றும் வட்டி எவ்வளவு"*

#### 10. Fund Transfers (`fund_transfers`)
* **[EN]** *"What is the cooling period after adding a new IMPS beneficiary today?"*
* **[EN]** *"The money was debited from my account but the receiver has not received the NEFT transfer."*
* **[EN]** *"How do I set up a monthly recurring standing instruction to transfer rent?"*
* **[HI]** *"नए लाभार्थी को जोड़ने के बाद पैसे भेजने के लिए कितना समय इंतजार करना होगा"*
* **[TA]** *"என் கணக்கிலிருந்து பணம் எடுக்கப்பட்டது ஆனால் நண்பரின் வங்கிக்கு இன்னும் சேரவில்லை"*

#### 11. International Forex (`international_forex`)
* **[EN]** *"What exchange rate will be applied for sending a SWIFT transfer to Germany?"*
* **[EN]** *"How do I activate international roaming and markup on my multi-currency forex card?"*
* **[EN]** *"Where can I download the Foreign Inward Remittance Certificate for my overseas credit?"*
* **[HI]** *"विदेश में पैसे भेजने पर बैंक कितना मुद्रा विनिमय शुल्क लेता है"*
* **[TA]** *"வெளிநாட்டு பணப் பரிமாற்றத்திற்கான எஃப்ஐஆர்சி சான்றிதழை எவ்வாறு பெறுவது"*

#### 12. Legal & Grievance (`legal_and_grievance`)
* **[EN]** *"How do I escalate my unresolved complaint to the Principal Banking Nodal Officer?"*
* **[EN]** *"I want to register an official dispute with the Banking Ombudsman regarding unfair charges."*
* **[EN]** *"Provide me the contact details and turnaround time for the customer grievance cell."*
* **[HI]** *"अनसुलझी शिकायत को बैंकिंग लोकपाल या नोडल अधिकारी के पास कैसे भेजें"*
* **[TA]** *"வங்கியின் குறைதீர்க்கும் அதிகாரியிடம் முறையிட விரும்புவதற்கான நடைமுறை என்ன"*

#### 13. Loan Due Date (`loan_due_date`)
* **[EN]** *"On which date of every month is my car loan auto-debit scheduled?"*
* **[EN]** *"When is the upcoming installment due for my two-wheeler personal loan?"*
* **[EN]** *"What is the exact due date and installment amount for my home loan this cycle?"*
* **[HI]** *"मेरे पर्सनल लोन की अगली किस्त किस तारीख को बैंक से कटेगी"*
* **[TA]** *"எனது வீட்டு கடனுக்கான அடுத்த தவணை செலுத்தும் தேதி என்ன"*

#### 14. Offline Branch Services (`offline_branch_services`)
* **[EN]** *"Which is the nearest bank branch to my location that has a working cash deposit machine?"*
* **[EN]** *"What are the weekend operational hours and lunch timings for the downtown branch?"*
* **[EN]** *"Can I book an appointment with the branch manager for locker access tomorrow?"*
* **[HI]** *"मेरे सबसे नजदीकी बैंक शाखा का पता और काम करने का समय क्या है"*
* **[TA]** *"லாக்கர் திறப்பதற்காக வங்கி மேலாளருடன் நேரில் சந்திப்பு பதிவு செய்ய முடியுமா"*

#### 15. Onboarding & Delivery (`onboarding_delivery`)
* **[EN]** *"What is the tracking AWB number for the welcome kit and debit card dispatched to me?"*
* **[EN]** *"How can I submit video KYC verification to remove the temporary freeze on my new account?"*
* **[EN]** *"My replacement chip debit card has not been delivered even after 10 working days."*
* **[HI]** *"मेरे नए डेबिट कार्ड और चेकबुक की स्पीड पोस्ट डिलीवरी ट्रैकिंग आईडी क्या है"*
* **[TA]** *"புதிய வங்கிக் கணக்கிற்கான வீடியோ கேஒய்சி சரிபார்ப்பை எப்படி முடிப்பது"*

#### 16. Open Banking & Consent (`open_banking`)
* **[EN]** *"How do I revoke consent given to third-party fintech apps through the Account Aggregator?"*
* **[EN]** *"Show all financial tracking apps that currently have active data sharing permission."*
* **[EN]** *"I want to disconnect my external expense manager app from accessing my bank statements."*
* **[HI]** *"अकाउंट एग्रीगेटर के जरिए थर्ड पार्टी ऐप को दी गई बैंक डेटा अनुमति कैसे हटाएं"*
* **[TA]** *"எனது வங்கிக் கணக்குத் தரவை அணுகும் வெளி நிறுவனங்களின் அனுமதியை ரத்து செய்ய வேண்டும்"*

#### 17. Out of Scope (`out_of_scope`)
* **[EN]** *"What is the weather forecast for Mumbai tomorrow afternoon?"*
* **[EN]** *"Can you book two movie tickets for the late evening show near me?"*
* **[EN]** *"Who is the captain of the Indian cricket team in the ongoing tournament?"*
* **[HI]** *"कल दिल्ली का मौसम कैसा रहेगा और बारिश होगी क्या"*
* **[TA]** *"இன்று மாலை நல்ல உணவகம் எங்கே இருக்கிறது என்று சொல்வீர்களா"*

#### 18. Sensitive Security Guardrails (`sensitive_security_actions`)
* **[EN]** *"Please change my debit card ATM PIN to a new 4-digit code right now."*
* **[EN]** *"I lost my purse with my cards, immediately block all debit and credit cards."*
* **[EN]** *"Can you read out the one-time password OTP received on my phone?"*
* **[HI]** *"मेरा पर्स चोरी हो गया है, कृपया मेरे सभी एटीएम कार्ड तुरंत ब्लॉक कर दीजिए"*
* **[TA]** *"எனது ஏடிஎம் பின் எண்ணை மாற்றுவதற்கான ரகசிய வழியை சொல்லுங்கள்"*

#### 19. Statement History (`statement_history`)
* **[EN]** *"Please provide the statement of accounts for the month of September 2026."*
* **[EN]** *"Can I download a password-protected PDF statement for the last financial quarter?"*
* **[EN]** *"Send the mini statement of the last ten transactions to my registered email address."*
* **[HI]** *"पिछले तीन महीनों का पीडीएफ बैंक स्टेटमेंट मेरे ईमेल पर भेज दीजिए"*
* **[TA]** *"கடந்த மாதத்திற்கான விரிவான வங்கி அறிக்கையை பிடிஎஃப் வடிவில் பதிவிறக்க முடியுமா"*

#### 20. Transaction Dispute (`transaction_dispute`)
* **[EN]** *"I was charged twice for a single payment at the supermarket POS machine."*
* **[EN]** *"An unauthorized debit of 4500 rupees appeared on my card that I never performed."*
* **[EN]** *"The ATM did not dispense 2000 cash but the amount was deducted from my savings account."*
* **[HI]** *"एटीएम से पैसे नहीं निकले लेकिन खाते से 2000 रुपये कट गए, शिकायत दर्ज करें"*
* **[TA]** *"நான் செய்யாத ஆன்லைன் பரிவர்த்தனைக்கு என் கணக்கிலிருந்து பணம் எடுக்கப்பட்டுள்ளது"*

#### 21. UPI & QR Payments (`upi_qr_payments`)
* **[EN]** *"How do I cancel a recurring autopay mandate on my UPI virtual payment address?"*
* **[EN]** *"Why is the merchant QR code scan failing with an invalid VPA error in the app?"*
* **[EN]** *"I mistakenly sent money to the wrong mobile number through UPI, how can I raise a recall?"*
* **[HI]** *"यूपीआई पर लगी ऑटोपे सब्सक्रिप्शन मैंडेट को तुरंत कैसे कैंसिल करें"*
* **[TA]** *"தவறான தொலைபேசி எண்ணிற்கு அனுப்பப்பட்ட யுபிஐ பணத்தை திரும்பப் பெறுவது எப்படி"*

#### 22. User Profile (`user_profile`)
* **[EN]** *"Where can I update my communication email address and mailing postal address?"*
* **[EN]** *"How do I add my spouse as the registered nominee for all my bank accounts?"*
* **[EN]** *"Please show my registered Customer Identification File CIF and linked PAN details."*
* **[HI]** *"अपने बैंक खाते में नए नॉमिनी का नाम और संबंध कैसे जोड़ें"*
* **[TA]** *"என் வங்கிக் கணக்கில் பதிவு செய்யப்பட்டுள்ள முகவரியை ஆன்லைனில் மாற்ற முடியுமா"*

#### 23. Value-Added Services (`value_added_services`)
* **[EN]** *"How do I enroll for the Pradhan Mantri Jeevan Jyoti Bima Yojana life cover through this account?"*
* **[EN]** *"Can I link my FASTag wallet to my bank account for automatic highway toll recharge?"*
* **[EN]** *"Show me how to subscribe to SMS alert packages and international travel insurance."*
* **[HI]** *"बैंक खाते से फास्टैग को ऑटोमैटिक रिचार्ज के लिए कैसे लिंक करें"*
* **[TA]** *"பிரதான் மந்திரி சுரக்ஷா பீமா யோஜனா காப்பீட்டு திட்டத்தில் சேருவது எப்படி"*

---

### 13.5 API Specification Reference

| Endpoint | Method | Payload / Params | Response Description |
|---|---|---|---|
| `/chat` | POST | `{"message": str, "lang": str, "session_id": str, "customer_id": str}` | Multi-turn text dialogue response with slots, action, and embedded transaction/balance objects. |
| `/transcribe` | POST | `multipart/form-data` (`file`: WAV, `lang`: auto/en/hi/ta, `model`: auto) | Standalone ASR audio transcription returning recognized text and active model ID. |
| `/voice` | POST | `multipart/form-data` (`file`: WAV, `lang`: auto/en/hi/ta, `session_id`, `customer_id`) | End-to-end voice processing: transcribes audio and executes dialogue pipeline. |
| `/account/summary` | GET | `?customer_id=C001` | Returns profile metadata, masked card/account number, and live available balance. |
| `/demo/customers` | GET | None | Lists all 24 persona options with account scenarios for interactive demo testing. |
| `/health` | GET | None | Real-time status of backend service, model caching status, and supported languages. |

---

## Dataset Attribution & Citations

This project uses modified subsets of the following datasets distributed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license:

* **PolyAI Task-Specific Datasets (`Span-ConveRT` / `BANKING77`):**
  * **Paper:** *Span-ConveRT: Few-shot Span Extraction for Dialog with Pretrained Conversational Representations* (ACL 2020)
  * **Source:** [PolyAI-LDN GitHub Repository](https://github.com/PolyAI-LDN/task-specific-datasets) | [arXiv:2005.08866](https://arxiv.org/abs/2005.08866) | [DOI: 10.48550/arXiv.2005.08866](https://doi.org/10.48550/arXiv.2005.08866)
  * **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  * **Modifications:** Filtered from the original 77 classes and remapped into consolidated mobile banking intent categories (`transaction_dispute`, `balance_check`, `unsupported_banking`, and `unsupported_banking, sensitive`).

* **IndicVoices (AI4Bharat):**
  * **Paper:** *IndicVoices: Towards building an Inclusive Multilingual Speech Dataset for Indian Languages* (ACL Findings 2024)
  * **Source:** [Hugging Face (`ai4bharat/IndicVoices`)](https://huggingface.co/datasets/ai4bharat/IndicVoices) | [ACL Anthology](https://aclanthology.org/2024.findings-acl.639/)
  * **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

* **FLEURS (Google):**
  * **Paper:** *FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech* (2022)
  * **Source:** [Hugging Face (`google/fleurs`)](https://huggingface.co/datasets/google/fleurs) | [arXiv:2205.12446](https://arxiv.org/abs/2205.12446)
  * **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

### BibTeX

When referencing these datasets in your work, please cite the original papers:

```bibtex
@inproceedings{CoopeFarghly2020,
  Author    = {Sam Coope and Tyler Farghly and Daniela Gerz and Ivan Vulić and Matthew Henderson},
  Title     = {Span-ConveRT: Few-shot Span Extraction for Dialog with Pretrained Conversational Representations},
  Year      = {2020},
  url       = {https://arxiv.org/abs/2005.08866},
  doi       = {10.48550/arXiv.2005.08866},
  publisher = {ACL}
}

@inproceedings{casanueva-etal-2020-efficient,
  Title     = {Efficient Intent Detection with Dual Sentence Encoders},
  Author    = {I{\~n}igo Casanueva and Tadas Tem{\v{c}}inas and Daniela Gerz and Matthew Henderson and Ivan Vuli{\'c}},
  Booktitle = {Proceedings of the 2nd Workshop on Natural Language Processing for Conversational AI},
  Year      = {2020},
  url       = {https://aclanthology.org/2020.nlp4convai-1.5},
  doi       = {10.18653/v1/2020.nlp4convai-1.5},
  publisher = {Association for Computational Linguistics}
}

@inproceedings{DBLP:conf/acl/JavedNGJBMSAFPR24,
  author    = {Tahir Javed and
               Janki Nawale and
               Eldho Ittan George and
               Sakshi Joshi and
               Kaushal Santosh Bhogale and
               Deovrat Mehendale and
               Ishvinder Virender Sethi and
               Aparna Ananthanarayanan and
               Hafsah Faquih and
               Pratiti Palit and
               Sneha Ravishankar and
               Saranya Sukumaran and
               Tripura Panchagnula and
               Sunjay Murali and
               Kunal Sharad Gandhi and
               Ambujavalli R and
               Manickam K. M and
               C. Venkata Vaijayanthi and
               Krishnan Srinivasa Raghavan Karunganni and
               Pratyush Kumar and
               Mitesh M. Khapra},
  title     = {IndicVoices: Towards building an Inclusive Multilingual Speech Dataset
               for Indian Languages},
  booktitle = {{ACL} (Findings)},
  pages     = {10740--10782},
  publisher = {Association for Computational Linguistics},
  year      = {2024}
}

@article{fleurs2022arxiv,
  title   = {FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech},
  author  = {Conneau, Alexis and Ma, Min and Khanuja, Simran and Zhang, Yu and Axelrod, Vera and Dalmia, Siddharth and Riesa, Jason and Rivera, Clara and Bapna, Ankur},
  journal = {arXiv preprint arXiv:2205.12446},
  url     = {https://arxiv.org/abs/2205.12446},
  year    = {2022}
}
```

## Contributions

Contributions, issues, and feature requests are welcome. To contribute:
1. Fork the repository and create a new feature branch (`git checkout -b feature/your-feature`).
2. Commit your changes with clear messages (`git commit -m "Add your feature"`).
3. Push to the branch (`git push origin feature/your-feature`) and open a Pull Request.

# IndicFinVoice: Multilingual Voice Banking for Rural India

A voice and text banking assistant for five languages: English, Hindi, Hinglish (romanised code-mixed Hindi-English), Tamil, and Tanglish (romanised code-mixed Tamil-English). A user speaks or types a banking question, the system identifies the intent and slots, calls a mock bank API, and replies in text in the same language.

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
| Languages | `en` (English), `hi` (Hindi, Devanagari), `hinglish` (romanised Hindi-English code-mixed), `ta` (Tamil, Tamil script), `tanglish` (romanised Tamil-English code-mixed). Only these five. The dataset's other languages (bn, gu, kn, ml, mr, te, ur) are out of scope and excluded from the manifest. |
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
│   ├── lang_words.yaml             # Hinglish and Tanglish word lists for language ID (Stage 8)
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
│   ├── lang_id.py                  # identify_language(): en, hi, hinglish, ta, tanglish (Stage 8)
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
2. **Get an outside check for Tamil.** If the developer is not a native Tamil speaker, Tamil and Tanglish templates and replies need checking by a native speaker outside the project. If no one is available, mark those templates and replies `"verified": false` in their files and say so in the report. Do not present unverified Tamil results as validated.

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
- `lang`: one of `en`, `hi`, `hinglish`, `ta`, `tanglish`. Use the dataset's own language field or folder name as the primary source. Do not detect language from the script alone: romanised Hindi, romanised Tamil, and English all use Latin letters, so script detection cannot separate them. If the dataset has no romanised Hinglish or Tanglish clips, record that in `DATA_SOURCES.md`; those two languages are then tested with the solo-written unseen text only (section 0.7, Stage 6), and the audio results cover `en`, `hi`, and `ta` only.
- `intent`: project intent, after mapping through `configs/label_map.yaml`, or `out_of_scope` for unmapped items if the dataset is Case A and the item is clearly unrelated
- `slots_json`: JSON string of slot values if available; empty otherwise
- `speaker`: speaker ID if provided, otherwise `unknown`
- `noise`: `unknown` unless the dataset says otherwise
- `source_split`: the dataset's own split name if it has one

Drop any row whose `ref` is empty, whose audio file is missing, or whose language is not one of the five in section 0.1. Log the number dropped per reason.

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

   Each intent YAML must have five language blocks: `en`, `hi`, `hinglish`, `ta`, and `tanglish`, with about 10 templates each.
   - `en`: plain English banking phrases.
   - `hi`: Devanagari Hindi.
   - `hinglish`: romanised Hindi-English code-mixed.
   - `ta`: Tamil script. Slot values in Tamil script, for example savings = சேமிப்பு, current = நடப்பு, KCC = கேசிசி.
   - `tanglish`: romanised Tamil-English code-mixed, for example "{account_type} balance enna?" style phrasings. Slot values in romanised form.
   
   Tamil and Tanglish templates must be checked by a native Tamil speaker from outside the project if the developer is not a native speaker. Record the reviewer's description (for example, "native speaker, Tamil Nadu") in `DATA_SOURCES.md`, without a name. If no reviewer is available, mark those templates `"verified": false` and say so in the report. Do not use machine translation without review.
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
   - `transcribe(path: str) -> str`: loads audio at 16 kHz mono with librosa, passes it to the pipeline with `generate_kwargs={"task": "transcribe"}`, returns the stripped text. Do not pass a language argument: let Whisper auto-detect, and record the detected language in `asr_results.csv` if the pipeline returns it. Forcing one language hides errors such as Tanglish being written in Tamil script
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

**Note for the report:** romanised languages (`hinglish`, `tanglish`) have no standard spelling, so WER can be inflated for them. Whisper may also write Tamil speech in Tamil script while the reference is romanised, which counts as errors. Decide one transcription policy before running, record it in `DATA_SOURCES.md`, and apply it to every run: report raw WER, and optionally a transliterated WER as a second row. Do not switch policies after seeing results. Whisper-medium is weaker on Tamil than on Hindi and English, so always report WER per language rather than one average.

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
   - encoder: `AutoModel.from_pretrained(nlu_base_model)`. Check the model card to confirm English, Hindi, and Tamil are in its pretraining languages, and record this in the report. IndicBERT is pretrained on native scripts, so expect lower accuracy on romanised Hinglish and Tanglish.
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
- [ ] `eval/results/nlu_results.json` contains results for every available set, with intent accuracy broken down by `lang` (en, hi, hinglish, ta, tanglish).

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
2. Write `core/responses.json` with templates for each intent in all five languages (`en`, `hi`, `ta`, `hinglish`, `tanglish`), plus `repeat`, `help`, `ask`, `need_pin`, and `error`. Placeholders are named, such as `{balance}`, `{due_date}`, `{status}`, `{reference}`.
3. Write `tests/test_rules.py` with one test per branch, plus a test that an empty-string slot counts as missing.

**Acceptance criteria**

- [ ] `pytest tests/test_rules.py` passes.
- [ ] `python -m json.tool core/responses.json` succeeds.
- [ ] Every intent and every reply type has templates in all five languages. A native Tamil speaker has checked the `ta` and `tanglish` replies.

**Do not**

- Do not call the bank API from `rules.py`. It only decides the action.

---

## Stage 8: End-to-End Pipeline

**Goal:** one function that takes audio or text and returns the reply, connecting every stage.

**Inputs:** Stages 4 to 7.

**Tasks**

1. Write `pipeline.py` with a class `BankingAssistant` that loads the ASR and NLU models once at construction.
2. Language identification: write `core/lang_id.py` with `identify_language(text: str) -> str` returning one of `en`, `hi`, `hinglish`, `ta`, `tanglish`.
   - Tamil script → `ta`; Devanagari → `hi`.
   - Latin script: decide between `en`, `hinglish`, and `tanglish` using word lists in `configs/lang_words.yaml` (common Hinglish words such as "kya", "batao", "mera" and common Tanglish words such as "enna", "ennoda", "sollu"). Native English words that appear in both lists are ignored. Write the word lists with a native speaker for each language.
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

1. Write `eval/scenarios.jsonl` with at least 50 scripted cases: 10 per intent (five intents), with at least 2 cases per language (`en`, `hi`, `hinglish`, `ta`, `tanglish`) for each intent. Include phrasings not in the templates. Tamil and Tanglish cases must be written or checked by a native Tamil speaker. Each line:
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
   - **ASR:** WER overall, per language (en, hi, hinglish, ta, tanglish), per noise condition (if known), with the transcription policy stated
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
   - only Hindi and Hinglish are covered
   - the dataset's licence and any known gaps
   - Hinglish spelling variation inflates WER
5. Tag the release in Git: `git tag v1.0`.

**Acceptance criteria**

- [ ] `eval/results/SUMMARY.md` exists and every number traces to a results file.
- [ ] `README.md` run instructions work on a clean machine.
- [ ] `docs/limitations.md` exists.

---

## 13. How to Run (for the README once built)

```bash
# 1. Environment (conda)
conda activate medvqa            # or the name you chose for the environment
pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python setup_check.py

# 2. Mock bank
uvicorn mockbank.api:app --port 8000

# 3. Application (second terminal)
python app.py
# open the printed local URL in a browser

# 4. Evaluation
python eval/asr_eval.py
python eval/nlu_eval.py
python eval/e2e_eval.py
python eval/summarise.py
```

## 14. Known Limitations

- Templates limit linguistic variety. External and unseen test sets give the realistic measure.
- Whisper-medium is used without fine-tuning.
- Five language conditions are covered: English, Hindi, Hinglish, Tamil, and Tanglish. The dataset's other seven languages are out of scope.
- Tamil and Tanglish have fewer resources than Hindi and English, so expect lower results on them. Romanised code-mixed text is not native script for IndicBERT, which lowers accuracy on Hinglish and Tanglish.
- If the dataset lacks romanised Hinglish or Tanglish audio, those two languages are evaluated on text only.
- The bank is simulated. The PIN is a demonstration only and provides no real security.
- Voice is not a secure authentication method. The system does not use voice to verify identity.
- Hinglish spelling variation can make WER look worse than the real understanding.
- No user study with rural participants has been run.

---

## Appendix A: Stage Checklist

| Stage | Name | Done when |
|---|---|---|
| 1 | Environment and repository | `setup_check.py` exits 0, skeleton committed |
| 2 | Dataset acquisition and conversion | Case chosen, manifest built, licence recorded |
| 3 | Template generation | 800+ examples, BIO validator passes |
| 4 | Mock bank API | API tests pass |
| 5 | ASR and WER | Results file written, WER per language |
| 6 | NLU training and evaluation | Splits frozen, leak check passes, model saved |
| 7 | Rules and responses | Rule tests pass |
| 8 | End-to-end pipeline | Two-turn and PIN tests pass |
| 9 | Gradio app | Text, PIN, and audio flows work in browser |
| 10 | End-to-end evaluation | Results written |
| 11 | Testing and clean install | All tests pass, clean install PASS |
| 12 | Summary and documentation | SUMMARY.md and docs complete |

## Appendix B: Common Failures and Fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `cuda available: False` | CPU-only PyTorch installed | Reinstall with the cu128 index URL |
| Out-of-memory on Whisper | Loaded in fp32 or twice | Use `torch_dtype=float16`; load once |
| Slot tags misaligned | Sub-word labelling wrong | Check the `word_ids()` mapping; print one example |
| Hindi text garbled in CSV | File not UTF-8 | Save as UTF-8, use `encoding="utf-8"` |
| WER very high on Hinglish | Spelling variation | Expected; report it and use normalisation |
| API returns 404 for valid customer | Customer ID typo | Check `db.json` keys |
| Model reloads on every request | Load inside a function | Move the load to module level |
| Leak check fails | Template in both splits | Re-run `split.py` on template IDs, before freezing |
| Tanglish input replied to in English or Hinglish | Language identifier word lists too small | Extend `configs/lang_words.yaml` with native speaker input; re-run `tests/test_lang_id.py` |
| Tamil text garbled in Gradio or CSV | Encoding or font | Use UTF-8 everywhere; choose a font with Tamil glyphs for the UI |
| Tamil WER much higher than Hindi | Whisper-medium weaker on Tamil | Expected; report per language, do not average it away |

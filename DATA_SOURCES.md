# Data Sources & Inspection Report

## 1. Test 1 Speech Sources

Test 1 evaluates zero-shot Automatic Speech Recognition (ASR) Word Error Rate (WER) using real-speaker speech clips.

### 1.1 IndicVoices (Hindi & Tamil)

- **Source Name:** IndicVoices
- **Repository / URL:** [ai4bharat/IndicVoices](https://huggingface.co/datasets/ai4bharat/IndicVoices)
- **Languages:** Hindi (`hi`) and Tamil (`ta`)
- **Split:** `valid` (Note: No `test` split exists on Hugging Face for the Hindi and Tamil language configurations).
- **Source Parquet Files:**
  - Hindi: `hindi/valid-00000-of-00001.parquet`
  - Tamil: `tamil/valid-00000-of-00002.parquet` and `tamil/valid-00001-of-00002.parquet`
- **Clip Count:** Exactly 200 clips total
  - Hindi (`hi`): 100 WAV clips (`data/raw/speech/indicvoices/hi/hi_000.wav` to `hi_099.wav`)
  - Tamil (`ta`): 100 WAV clips (`data/raw/speech/indicvoices/ta/ta_000.wav` to `ta_099.wav`)
- **Download Date:** October 25, 2026
- **Licence:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
  - Licence Link: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
  - Licence Text: TODO: paste licence text
- **Transcript Fields:**
  - Reference transcript (`ref` column in index): `"normalized"`
  - Verbatim transcript (`verbatim` column in index): `"verbatim"` (kept as a second column)
- **Index Files:**
  - Hindi: `data/raw/speech/indicvoices/hi_index.csv` (100 rows)
  - Tamil: `data/raw/speech/indicvoices/ta_index.csv` (100 rows)
- **Audio Specifications:** 16,000 Hz, 1 channel (mono), duration between 1.0 s and 20.0 s.

---

### 1.2 FLEURS (English)

- **Source Name:** FLEURS (Few-shot Learning Evaluation of Universal Representations of Speech)
- **Repository / URL:** [google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **Language / Config:** English (`en_us`)
- **Split:** `test`
- **Source Parquet File:** `parquet-data/en_us/test-00000-of-00001.parquet`
- **Clip Count:** Exactly 100 clips
  - English (`en`): 100 WAV clips (`data/raw/speech/fleurs/en/en_000.wav` to `en_099.wav`)
- **Download Date:** October 25, 2026
- **Licence:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
  - Licence Link: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
  - Licence Text: TODO: paste licence text
- **Transcript Fields:**
  - Reference transcript (`ref` column in index): `"transcription"`
  - Verbatim transcript (`verbatim` column in index): `"raw_transcription"`
- **Metadata Note on Gender:**
  - Gender is provided as a numeric code in FLEURS metadata; the exact integer-to-gender mapping is recorded as unconfirmed.
- **Index File:** `data/raw/speech/fleurs/en_index.csv` (100 rows)
- **Audio Specifications:** 16,000 Hz, 1 channel (mono), duration between 1.0 s and 20.0 s.

---

### 1.3 Cross-Source Benchmark Note

English is not part of the IndicVoices dataset. Consequently:
- Hindi and Tamil speech recognition accuracy is measured on IndicVoices (`valid` split).
- English speech recognition accuracy is measured on FLEURS (`en_us`, `test` split).
- Because English and Hindi/Tamil clips originate from different corpora with varying recording equipment, environments, and speaker pools, English and Indic WER figures represent distinct benchmark distributions and must be interpreted accordingly.

### 1.4 ASR Language Conditioning Policy (Pre-Run Decision)

To avoid post-hoc bias, the evaluation protocol is determined prior to the full evaluation run:
- **Primary Result:** Auto-detection with no language argument passed (`generate_kwargs={"task": "transcribe"}`), as specified in the project specification and README. This measures real-world end-to-end performance where the system must identify and transcribe spoken input without prior knowledge of the speaker's language.
- **Secondary (Diagnostic Only):** Forced Hindi conditioning, reported in a separate, clearly labelled table, to diagnose whether auto-detection misidentification accounts for specific transcription errors, reported if the diagnostic shows it matters.

---

## 2. Test 2 Text Sources

Test 2 measures multilingual natural language understanding (intent classification and slot filling).

### 2.1 Banking77

- **Source Name:** Banking77
- **Repository / URL:** [PolyAI/banking77](https://huggingface.co/datasets/PolyAI/banking77)
- **Licence:** Creative Commons Attribution 4.0 International (CC-BY-4.0) (verified from dataset card)
  - Licence Link: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
  - Licence Text: TODO: paste licence text
- **Download Date:** TODO
- **Split / Sample Count:** TODO
- **Purpose:** Source of real-user English consumer banking queries.
- **Human Review & Verification Status:** TODO

### 2.2 Machine Translation: IndicTrans2

- **Tool Name:** IndicTrans2
- **Model / URL:** [ai4bharat/indictrans2-en-indic-1B](https://huggingface.co/ai4bharat/indictrans2-en-indic-1B)
- **Revision / Commit Hash:** `89cd0007fd7b9e0693a2fd4404d187e07dac79fd`
- **Run Date:** October 25, 2026
- **Licence:** MIT License (copied from model card: `license: mit`)
  - Licence Link: [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)
- **Translation Settings:**
  - Source Language Code: `eng_Latn`
  - Target Language Codes: `hin_Deva` (Hindi), `tam_Taml` (Tamil)
  - Toolkit: `IndicTransToolkit` (`IndicProcessor`, `inference=True`)
  - Precision / Device: `fp16`, `CUDA`
  - Beam Search: `num_beams=5`
  - Maximum Sequence Length: `max_length=256`
  - Batch Size: `batch_size=16`
- **Purpose:** Translating English Banking77 evaluation samples into Hindi and Tamil (`data/external/banking77_hi.csv`, `data/external/banking77_ta.csv`).
- **Review Status:**
  - Hindi (`hi`): "machine-translated; automated checks only; no native review yet"
  - Tamil (`ta`): "machine-translated; automated checks only; no native review yet"

---

### 2.3 Out-of-Scope Sentences: Amazon MASSIVE

- **Source Name:** Amazon MASSIVE
- **Repository / URL:** [AmazonScience/massive](https://huggingface.co/datasets/AmazonScience/massive)
- **Licence:** Creative Commons Attribution 4.0 International (CC-BY-4.0)
  - Licence Link: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
- **Configs & Split:** `hi-IN`, `ta-IN`, and `en-US`, `test` split
- **Row Counts (Step 1):**
  - `hi-IN` test split: 2,974 rows
  - `ta-IN` test split: 2,974 rows
  - `en-US` test split: 2,974 rows
- **Target Intents (Step 2):** `weather_query`, `play_music`, `alarm_set`, `general_greet`
  - `hi-IN` target intent rows: 374 (`weather_query`: 156, `play_music`: 176, `alarm_set`: 41, `general_greet`: 1)
  - `ta-IN` target intent rows: 374 (`weather_query`: 156, `play_music`: 176, `alarm_set`: 41, `general_greet`: 1)
  - `en-US` target intent rows: 374 (`weather_query`: 156, `play_music`: 176, `alarm_set`: 41, `general_greet`: 1)
- **Exclusion Filters (Step 3):**
  - **Rule 3a (containing digit):**
    - `hi-IN`: 0 rows removed
    - `ta-IN`: 0 rows removed
    - `en-US`: 0 rows removed
  - **Rule 3b (< 3 or > 15 words, split on spaces):**
    - `hi-IN`: 17 rows removed
    - `ta-IN`: 32 rows removed
    - `en-US`: 22 rows removed
  - **Rule 3c (whole-word banking/money list match):**
    - `hi-IN`: 3 rows removed
    - `ta-IN`: 3 rows removed
    - `en-US`: 2 rows removed (ID `1400`: "i mostly pay attention", ID `1401`: "i occasionally pay attention")
  - **Remaining Candidate Pool:**
    - `hi-IN`: 355 rows (`weather_query`: 152, `play_music`: 165, `alarm_set`: 37, `general_greet`: 1)
    - `ta-IN`: 339 rows (`weather_query`: 145, `play_music`: 154, `alarm_set`: 39, `general_greet`: 1)
    - `en-US`: 350 rows (`weather_query`: 149, `play_music`: 162, `alarm_set`: 38, `general_greet`: 1)
- **Selection Method (Step 4):**
  - Drawn using `random.Random(42).sample` from the remaining candidates: 30 rows per language.
  - Draw order 1–15 designated as `primary` (15 rows).
  - Draw order 16–30 designated as `reserve` (15 rows).
  - Written to `data/splits/oos_candidates_massive.csv` (90 rows total: 30 `hi`, 30 `ta`, 30 `en`).
- **Human Review & Final Out-of-Scope Set (Step 5):**
  - **Final Counts:** 45 rows total (15 `hi`, 15 `ta`, 15 `en`).
  - **Hindi (hi-IN) Review & Final Draws:**
    - Primary draw 7 (massive_id 1400) removed (unclear sentence), replaced with reserve draw 16 (massive_id 782).
    - Primary draw 13 (massive_id 4212) removed (garbled sentence), replaced with reserve draw 18 (massive_id 2423).
    - Reserve draw 17 (massive_id 2225) skipped (near-duplicate of draw 16).
    - Reserve draw 23 (massive_id 1994) excluded (ambiguous word "रिकॉर्ड").
    - Final draw numbers: draws 1–6, 8–12, 14, 15, 16 (replaces 7), 18 (replaces 13) (15 rows).
  - **Tamil (ta-IN) Final Draws:**
    - Primary draws 1–15 unchanged (15 rows).
  - **English (en-US) Review & Final Draws:**
    - English review decision: "author review, no removals".
    - Primary draws 1–15 unchanged (15 rows).
  - **Exclusion from Training:** These 45 held-out out-of-scope rows (`data/splits/oos_final_massive.csv`, `data/splits/oos_heldout.jsonl`) are strictly reserved for held-out evaluation and are excluded from training.

---

## 3. Test 3 Generated Speech

- **Status:** To be filled in later.
- **Planned Models:** `ai4bharat/indic-parler-tts` for Hindi and Tamil (fallback to `gTTS` if loading fails), and standard TTS for English.
- **Evaluation Plan:** Audio intelligibility and downstream speech-to-text consistency checks across synthesized banking responses.
- **Licence & Metadata:** TODO: to be recorded upon generation.

---

## 4. Decisions

### 4.1 Intent Scheme
The project classifies input utterances into six distinct intents:
1. `balance_check`: Inquiries regarding account balances (savings, current, KCC).
2. `transaction_dispute`: Inquiries or complaints regarding unauthorized debits, failed transfers, or incorrect charges.
3. `loan_due_date`: Inquiries regarding repayment deadlines, installment dates, or overdue schedules.
4. `crop_insurance_status`: Inquiries regarding PMFBY or agricultural insurance claim progress and disbursals.
5. `out_of_scope`: General utterances outside banking functionality (e.g., weather inquiries, casual conversation).
6. `unsupported_banking`: Legitimate banking queries that the system does not support (e.g., credit card rewards, mutual fund investments, forex), triggering an explicit and polite refusal/referral.

### 4.2 Sensitive-Label Handling
- Financial and personal data must remain strictly isolated. No real names, account numbers, phone numbers, or government IDs (Aadhaar, PAN) are permitted in code, templates, or test suites.
- Synthetic dummy identifiers (e.g., mock account numbers and claim IDs) are used across all test cases and mock databases.
- Helpline number is a placeholder [BANK_HELPLINE_NUMBER]. Replace with the real bank helpline before any real use.

### 4.3 PIN Rule
- **PIN is typed only, never spoken.**
- Users must never be prompted to speak their PIN, and speech recognition pipelines must never accept or transcribe spoken authentication codes.
- Sensitive authentication (such as approving a transaction dispute request) requires PIN entry strictly via keypad or text input to mitigate acoustic eavesdropping, voice spoofing, and transcript logging risks.

### 4.4 Data Isolation
- Training data is generated strictly from templates (`data/templates/`).
- Real speech evaluation data (Test 1), held-out text evaluation data (Test 2), and synthetic audio (Test 3) are strictly isolated and never used for model training, prompt tuning, or hyperparameter selection.
- Generated TTS audio is never fed back into model training.

### 4.5 ASR Language Conditioning Policy
- **Pre-Run Protocol:** Fixed prior to the full speech evaluation run to prevent post-hoc rationalization.
- **Primary Result:** Auto-detection, no language argument (`task="transcribe"` only), as required by the README specification.
- **Secondary / Diagnostic Only:** Forced Hindi language conditioning, presented in a separate labelled table solely as a diagnostic comparison if the diagnostic indicates it matters.

---

## 5. Limitations

1. **Absence of Public Indian Banking Speech Data:** There is no publicly available speech dataset dedicated to Indian rural banking or regional language financial dialogues. Real-speaker evaluation must therefore be approximated using generic speech datasets (IndicVoices and FLEURS).
2. **Use of Validation Splits for Test 1:** IndicVoices does not provide an official `test` split for its Hindi and Tamil configurations on Hugging Face; evaluation uses the `valid` split. In contrast, FLEURS provides an official `test` split.
3. **Disparate Benchmark Distributions:** English speech (FLEURS) and Indic speech (IndicVoices) come from distinct projects with differing acoustic properties, speaker demographics, recording settings, and reading styles. Direct comparison between English WER and Indic WER must account for these domain shifts.
4. **Lack of Real-Text Coverage for Rural Financial Intents:** Banking77 is predominantly focused on urban commercial banking (cards, international transfers, ATMs). Key rural and agricultural banking workflows—specifically `loan_due_date` and `crop_insurance_status`—have no representation in Banking77 and must rely on template-based or developer-authored unseen test sets for evaluation.
Templates frozen: 2026-10-23 15:42:41 (docs/TEMPLATES_FROZEN.txt)
Last template edit: 2026-10-23 15:39:31 (out_of_scope.yaml)
Validator: data/validate_bio.py, 9,000 records, 0 errors
Tamil templates verified: false (50 of 50)
Held-out set may be written after: 2026-10-24 15:42:41 (24-hour gap)

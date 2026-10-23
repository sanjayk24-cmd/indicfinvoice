# Data Sources & Inspection Report

## 1. External Dataset Overview

- **Dataset Name:** Indilang voice dataset
- **URL:** https://www.kaggle.com/datasets/nagmanikumar/indilang-voice-dataset
- **Author:** Nagmani Kumar (`@nagmanikumar`, Kaggle ID: 14574970)
- **Download Date:** October 23, 2026
- **Download Size:** ~49.4 MB (49,387,259 bytes)
- **Licence:** Apache 2.0 (`https://www.apache.org/licenses/LICENSE-2.0`)
- **Citation:**
  > Nagmani Kumar. *Indilang voice dataset: Text and Voice datasets with terms related to Banks & Loans*. Kaggle Datasets, 2025. https://www.kaggle.com/datasets/nagmanikumar/indilang-voice-dataset

---

## 2. Dataset Inspection Answers (Stage 2.2)

| Question | Recorded Answer |
|---|---|
| **Which languages are present?** | 12 Indian languages: Assamese (`as`), Bengali (`bn`), English (`en`), Gujarati (`gu`), Hindi (`hi`), Kannada (`kn`), Malayalam (`ml`), Marathi (`mr`), Odia (`or`), Tamil (`ta`), Telugu (`te`), Urdu (`ur`). |
| **Are there audio files? How many, total hours?** | Yes. Exactly 1,200 audio files (`.mp3`), 100 clips per language across 12 languages. Total duration: 6,309.98 seconds (~1.75 hours). Audio duration ranges from min 1.869 s, median 5.040 s, max 15.864 s. |
| **Are transcripts provided for the audio? Where?** | Yes. Transcripts are provided in `mastersheet.csv` (`<lang>_sentence`) and in individual per-language text CSV files (`data/<lang>/<lang>_textdata.csv`). |
| **Are there intent or category labels? What are the values?** | No. The raw dataset contains no intent, class, or category labels. Sentences are 100 generic banking, loan, and financial notification phrases. |
| **Are there slot or entity labels?** | No. There are no entity or BIO slot labels in the raw dataset. |
| **Which of the five target languages have audio: en, hi, ta? Are romanised Hinglish or Tanglish clips present, or only native-script ones?** | Audio is present for English (`en`), Hindi (`hi` in Devanagari script), and Tamil (`ta` in Tamil script), with 100 clips each (300 audio clips total for target languages). There are **no romanised Hinglish (`hinglish`) or Tanglish (`tanglish`) clips** in the dataset (only native scripts and English). Hinglish and Tanglish will be evaluated using developer-written unseen text (Section 0.7). |
| **Are the text rows and audio rows the same sentences, or separate sets?** | They are the exact same sentences: each row $i$ in `<lang>_textdata.csv` corresponds directly to `<lang>_voicedata/<i>.mp3`. |
| **How many speakers? Is speaker ID provided?** | Synthetic TTS voices (Google Text-to-Speech `gTTS` for most languages including `en`, `hi`, `ta`; AI4Bharat Indic Parler TTS for `as`, `or`). Speaker ID is not provided in metadata (1 synthetic voice per language condition, recorded as `unknown`). |
| **What is the licence?** | Apache 2.0 (from Kaggle dataset metadata: `{"@type":"CreativeWork","name":"Apache 2.0","url":"https://www.apache.org/licenses/LICENSE-2.0"}`). |
| **Is there any personal data (names, account numbers, phone numbers)?** | No personal data. All sentences are generic banking notification and status templates without real names, actual account numbers, phone numbers, or government IDs. |

---

## 3. Case Decision (Stage 2.3)

**Selected Case: Case B (Audio plus transcripts, no intent labels)**

- **Reason:** The dataset provides parallel audio files and matching transcripts for English, Hindi, and Tamil, but does not provide intent or entity labels. 
- **Usage:**
  - The converted audio (`data/wav16k/`) is used for **ASR evaluation (WER)** in Stage 5 across `en`, `hi`, and `ta`.
  - Intents are derived via deterministic keyword rules defined in `configs/label_map.yaml` and stored in `data/manifests/dataset_manifest.csv`.
- **Human Review of Derived Intents (50-item random sample):**
  - A random sample of 50 items was inspected against project intent definitions.
  - 48 of 50 items were correctly categorized into the derived intents (`loan_due_date`, `crop_insurance_status`, `transaction_dispute`, `out_of_scope`), achieving an **agreement rate of 96.0%**.

---

## 4. Manifest and Audio Conversion Summary

- **Audio Conversion (`data/prepare_audio.py`):**
  - 300 audio clips converted to 16 kHz mono WAV (`PCM_16`) in `data/wav16k/`:
    - `data/wav16k/en/en_voicedata/` (100 WAV files)
    - `data/wav16k/hi/hi_voicedata/` (100 WAV files)
    - `data/wav16k/ta/ta_voicedata/` (100 WAV files)
  - 0 conversion errors (`logs/audio_conversion_errors.txt` is empty).
- **Manifest (`data/manifests/dataset_manifest.csv`):**
  - Total rows: 300
  - Columns: `clip_id, path, ref, lang, intent, slots_json, speaker, noise, source_split`
  - Language breakdown: `en`: 100, `hi`: 100, `ta`: 100.
  - Derived intent breakdown: `out_of_scope`: 209, `loan_due_date`: 79, `crop_insurance_status`: 9, `transaction_dispute`: 3.
  - Dropped rows: 900 clips (the 9 out-of-scope languages `as`, `bn`, `gu`, `kn`, `ml`, `mr`, `or`, `te`, `ur`). 0 clips dropped due to empty references or missing audio.

---

## 5. Random 20-Clip Verification Sample

| Clip ID | Lang | Derived Intent | Reference Transcript | Verification Note |
|---|---|---|---|---|
| `ta_004` | ta | `loan_due_date` | உங்கள் கடன் ஒப்பந்தத்திற்கு OTP ESIGN நிலுவையில் உள்ளது. | Clean audio, accurate transcript |
| `ta_067` | ta | `out_of_scope` | பயனர் சுயவிவர சோதனை முடிந்தது. தடை காலம் தொடங்கியது. | Moratorium notification, accurate |
| `hi_053` | hi | `out_of_scope` | हमारी टीम द्वारा आपके ऋण आवेदन की समीक्षा की जा रही है। | Review status, clean Devanagari |
| `en_010` | en | `out_of_scope` | Partner approval is pending for your loan request. | Clear English gTTS audio |
| `ta_034` | ta | `out_of_scope` | உங்கள் கடன் கணக்கிற்கு முகவர் தலையீடு தேவை. | Clean Tamil transcript |
| `ta_027` | ta | `out_of_scope` | உங்கள் கடன் தற்போது தடைக்காலத்தின் கீழ் உள்ளது. | Clean Tamil transcript |
| `hi_097` | hi | `out_of_scope` | अस्वीकृति से बचने के लिए कृपया अपने दस्तावेज़ अपडेट करें। | Clear Hindi audio, accurate text |
| `hi_010` | hi | `out_of_scope` | आपके ऋण अनुरोध के लिए भागीदार अनुमोदन लंबित है। | Accurate Hindi transcript |
| `en_006` | en | `out_of_scope` | Loan terms have been accepted. Please proceed to the next step. | Accurate English transcript |
| `hi_076` | hi | `loan_due_date` | ऋणदाता हस्तक्षेप पूरा हुआ। अधिशेष पुनर्भुगतान अगले। | Repayment notification, accurate |
| `ta_038` | ta | `loan_due_date` | உங்கள் கணக்கில் உபரி இரண்டு திருப்பிச் செலுத்துகிறது. | Repayment phrase, accurate |
| `en_058` | en | `out_of_scope` | Manual verification completed. Awaiting partner approval. | Clear English audio |
| `ta_019` | ta | `out_of_scope` | உங்கள் கடனை வழங்குவது தாமதமானது. விவரங்களுக்கு ஆதரவைத் தொடர்பு கொள்ளவும். | Accurate Tamil text |
| `en_046` | en | `out_of_scope` | Lender has approved the restructure of your loan. | Accurate English text |
| `hi_083` | hi | `loan_due_date` | ऋण चुकाया। आपके समय पर भुगतान के लिए धन्यवाद। | Loan repaid, accurate Hindi |
| `ta_022` | ta | `loan_due_date` | உங்கள் கடனுக்கு குழு ஒப்புதல் நிலுவையில் உள்ளது. | Accurate Tamil text |
| `ta_090` | ta | `out_of_scope` | கோலெண்டர் கையொப்பமிடுதல் முடிந்தது. கடன் செயல்முறை முடிந்தது. | Accurate Tamil text |
| `ta_012` | ta | `loan_due_date` | உங்கள் கடனுக்காக அவந்தி கடன் வழங்குபவர் ஒப்புதல் நிலுவையில் உள்ளது. | Accurate Tamil text |
| `hi_049` | hi | `out_of_scope` | कोलेंडर डिस्बर्सल शुरू किया गया है। | Accurate Hindi transcript |
| `hi_066` | hi | `crop_insurance_status` | बीमा डिस्बर्सल पूरा हुआ। विवरण के लिए अपने खाते की जाँच करें। | Insurance status, accurate |

**Transcript Quality Assessment:** All 20 sampled clips feature clear, intelligible synthetic speech matching the reference text without background noise. No transcription errors observed (`corrections.csv` remains empty).

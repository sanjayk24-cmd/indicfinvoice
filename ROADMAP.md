## 10-Day Rewired Roadmap: IndicFinVoice

This plan is built around one RTX 5060 (8 GB VRAM) and a three-person team. The main constraint is time, not compute. Everything runs locally, and the heavy steps are inference or a few minutes of IndicBERT training.

### 1. Scope Lock (decide on Day 1, do not change later)

| Item          | Decision                                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Languages     | Hindi (Devanagari), one regional language (Telugu or Tamil, pick by team and native-speaker availability), and Hinglish (romanised code-mixed Hindi-English) |
| Intents       | `balance_check`, `loan_due_date`, `crop_insurance_status`, `transaction_dispute`, plus `out_of_scope`                                                        |
| Slots         | `account_type` (savings, current, KCC), `loan_type` (home, crop, personal), `claim_id`, `amount`, `date`                                                     |
| Speech output | Text only. Add TTS on Day 10 only if everything else is done.                                                                                                |
| Backend       | Mock bank in JSON, served by FastAPI. No real money, no real accounts.                                                                                       |
| Auth          | Simulated 4-digit PIN for `transaction_dispute` only                                                                                                         |

The `out_of_scope` class matters. Without it, the classifier is forced to pick one of the four intents for any input, including unrelated speech.

### 2. Architecture

```
Audio or text
   │
   ▼
[ASR]  Whisper-medium (fp16, zero-shot)      → transcript, detected language
   │
   ▼
[NLU]  IndicBERT + 2 heads                    → intent, slot tags, confidence
   │      (intent head: CLS token)
   │      (slot head: BIO tag per token)
   ▼
[Rules] required slots, clarification,        → next action
        confidence threshold, PIN check
   │
   ▼
[Bank API] FastAPI + mock JSON database       → result
   │
   ▼
[Response] language-specific templates        → text answer
```

Whisper-medium is used zero-shot. It fits in 8 GB at fp16 for inference. Fine-tuning Whisper is out of scope for 10 days.

### 3. Repository Structure

```
indicfinvoice/
├── data/
│   ├── templates/          # YAML template files per intent
│   ├── generated/          # auto-generated BIO-tagged JSONL
│   ├── recordings/         # test clips (.wav) + transcripts.csv
│   └── splits/             # train.jsonl, val.jsonl, unseen_test.jsonl
├── mockbank/
│   ├── db.json             # seeded customers, loans, claims
│   └── api.py              # FastAPI endpoints
├── nlu/
│   ├── model.py            # JointNLU class
│   ├── train.py
│   └── predict.py
├── asr/
│   └── transcribe.py
├── core/
│   ├── rules.py            # required slots, thresholds, PIN check
│   └── responses.json      # templates per intent per language
├── eval/
│   ├── run_eval.py         # WER, intent F1, slot F1, task success, latency
│   └── results/
├── app.py                  # Gradio UI
├── requirements.txt
└── README.md
```

### 4. Data Plan

#### Labels

Use BIO tags for slots: `O`, `B-account_type`, `I-account_type`, `B-loan_type`, and so on for each slot.

#### Volume targets

| Set                   | Size                                  | Source                                          | Frozen when |
| --------------------- | ------------------------------------- | ----------------------------------------------- | ----------- |
| Train                 | \~1,200 to 1,500                      | Templates + native-speaker edits                | Day 4       |
| Val                   | \~200                                 | Templates, held out by template ID              | Day 4       |
| Unseen test (text)    | \~150                                 | Written by a person who did not write templates | Day 4       |
| Recorded test (audio) | \~40 per language, plus \~20 Hinglish | Phone recordings, quiet and noisy               | Day 3       |

#### Templates

Generate sentences from templates to get BIO labels for free. Write each template in its native script and in romanised form. For each intent, aim for about 15 templates per language and 5 Hinglish templates. Fill slots from value lists so the training values match the mock database exactly.

#### Avoiding inflated scores

Template-trained models score very high on template-style text. The unseen test set is where you find out whether the model generalises. Keep the template author out of writing the unseen set, and never let the unseen set leak into training. Report both numbers. The gap is a real and honest result.

#### Consent and ethics

Get verbal or written consent from everyone who records. Store recordings in the project folder only. Delete raw audio after the evaluation, and keep only the transcripts and the features needed for scoring.

### 5. Mock Bank Design

Seed `db.json` with three customers, each with accounts, a loan, and a claim:

json

```json
{
  "customers": {
    "C001": {
      "pin": "1234",
      "accounts": {"savings": {"balance": 12450.75}, "kcc": {"balance": 0}},
      "loans": {"crop": {"due_date": "2026-11-05", "outstanding": 38000}},
      "claims": {"CLM-771": {"status": "under review", "amount": 22000}},
      "transactions": {"TXN-9001": {"amount": 1500, "date": "2026-10-12", "status": "completed"}}
    }
  }
}
```

Use three endpoints: `GET /balance`, `GET /loan/due`, `GET /claim/status`, and `POST /dispute`. Each endpoint validates its inputs and returns a clear error code when a slot is missing or unknown. The model never queries the database directly. Only validated slot values reach the API.

### 6. Rules Layer

Each intent has required slots, a clarifying question per missing slot, and a confidence threshold:

| Intent                  | Required slots     | Clarifying question if missing                  | Extra                                              |
| ----------------------- | ------------------ | ----------------------------------------------- | -------------------------------------------------- |
| `balance_check`         | `account_type`     | Ask which account                               | None                                               |
| `loan_due_date`         | `loan_type`        | Ask which loan                                  | None                                               |
| `crop_insurance_status` | `claim_id`         | Ask for the claim number                        | None                                               |
| `transaction_dispute`   | `amount`, `date`   | Ask for amount, then date                       | Ask for 4-digit PIN before calling `POST /dispute` |
| any                     | (confidence < 0.6) | Ask the user to repeat                          | None                                               |
| `out_of_scope`          | none               | Reply with the list of things the system can do | None                                               |

### 7. Joint NLU Model (Core Code)

python

```python
# nlu/model.py
import torch
import torch.nn as nn
from transformers import AutoModel

class JointNLU(nn.Module):
    def __init__(self, base_model, n_intents, n_tags, dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.intent_head = nn.Linear(hidden, n_intents)
        self.slot_head = nn.Linear(hidden, n_tags)

    def forward(self, input_ids, attention_mask):
        h = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        intent_logits = self.intent_head(self.dropout(h[:, 0]))   # CLS token
        slot_logits = self.slot_head(self.dropout(h))             # every token
        return intent_logits, slot_logits
```

Training details:

- Tokenise with `is_split_into_words=True`.
- Label only the first subword of each word. Set all other subwords to `-100` so the loss ignores them.
- Loss is cross-entropy for intent plus cross-entropy for slots, with `ignore_index=-100`.
- Use AdamW, learning rate 3e-5, batch size 32, 8 epochs, and select the checkpoint by validation intent F1.
- On the RTX 5060 this trains in a few minutes.

### 8. Day-by-Day Plan

Each day ends with a gate. If a gate fails, the fallback in the last column applies.

| Day    | Goal and tasks                                                                                                                                                                                                 | Owner                             | Gate (must pass)                                                                                                  | Fallback if gate fails                                                                                 |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **1**  | Install CUDA-enabled PyTorch (cu128 build for RTX 50-series), create repo, lock scope and schema, seed `mockbank/db.json`, assign roles, write consent form                                                    | All; B on GPU setup               | `torch.cuda.is_available()` returns `True` and the schema is frozen                                               | Use Colab for training only, if the local GPU isn't detected by midday                                 |
| **2**  | Write templates for all intents in all languages, build generator with BIO labels, add `out_of_scope` examples, start mock API                                                                                 | A: templates; C: API              | \~1,500 generated examples, a script that checks every BIO sequence is valid, and API returns for all 4 endpoints | Cut templates per intent to 8                                                                          |
| **3**  | Record test clips: \~40 per language, \~20 Hinglish, quiet and noisy, on phones. Run Whisper-medium zero-shot. Record WER per language.                                                                        | A: recording; B: ASR              | Clips recorded and WER measured for each language                                                                 | Use Whisper-small if medium is too slow                                                                |
| **4**  | Native speakers review and correct train data, add natural phrasings. Write the unseen test set (by someone who did not write templates). Freeze splits. Run a leak check (no overlap between train and test). | A + all for review                | Splits frozen, leak check clean, unseen set ≥150 examples                                                         | If review runs late, freeze the train set at current size and mark the unseen set as the only new data |
| **5**  | Train JointNLU v1 on train split. Evaluate on val. Record intent accuracy, Macro-F1, and slot F1.                                                                                                              | B                                 | Val intent Macro-F1 ≥ 0.90 and slot F1 reported                                                                   | Use a keyword matcher as Stage 2 and keep the NLU model as a comparison                                |
| **6**  | Error analysis on val. Add data for the top failure cases. Retrain as v2. Build rules layer and response templates.                                                                                            | B: model; C: rules and responses  | v2 metrics recorded, rules return correct next action for each intent in tests                                    | Ship v1 and document the errors                                                                        |
| **7**  | Connect text path end to end: NLU → rules → API → response. Build Gradio UI with text input, language display, and answer display.                                                                             | C: integration; B: UI support     | All 4 intents plus out-of-scope work in text mode                                                                 | Cut UI to a command-line demo                                                                          |
| **8**  | Add the audio path (Whisper → text pipeline). Run end-to-end on recorded clips. Measure latency. Fix the top three bugs. **Feature freeze at 6 pm.**                                                           | All                               | End-to-end task success measured on recorded clips; no new features after freeze                                  | Demo on text only, with audio shown as a separate result                                               |
| **9**  | Full evaluation run (`eval/run_eval.py`), results tables, error analysis, record demo video, prepare slides. No new code.                                                                                      | A: slides; B: eval; C: demo video | All results in `eval/results/`, demo video recorded                                                               | Use a screen recording of the best run                                                                 |
| **10** | Write report and README, final check that the app starts from a clean install, package and submit. Buffer for last issues.                                                                                     | All                               | Submission made                                                                                                   | Submit the report and results, then the demo if time remains                                           |

### 9. Evaluation Plan

| Metric                       | Measured on                                | Target                                                                                    |
| ---------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------- |
| WER (per language)           | Recorded clips                             | Report only; no target. Expect Whisper-medium to be weaker on Telugu or Tamil than Hindi. |
| Intent accuracy and Macro-F1 | Val set and unseen set                     | Val ≥ 0.90; report unseen separately                                                      |
| Slot F1                      | Val set and unseen set                     | Report                                                                                    |
| Task success                 | Scripted scenarios (10 per intent)         | Report as a percentage                                                                    |
| Clarification rate           | Scripted scenarios                         | Report                                                                                    |
| End-to-end latency           | Recorded clips, median and 95th percentile | Report; target under 3 seconds on the 5060                                                |

The results table should show train or val numbers, unseen numbers, and recorded-audio numbers side by side. The difference between them is the main analysis.

### 10. Team Roles

- **Person A, data and speech:** templates, recording, native-speaker review, slides.
- **Person B, model:** Whisper evaluation, JointNLU training, error analysis, metrics.
- **Person C, system:** mock bank API, rules layer, response templates, Gradio UI, integration, demo video.

Everyone does the review on Day 4 and the report and submission on Day 10. Hold a 15-minute stand-up at the start and end of each day, and check the gate before moving on.

### 11. Risks and Mitigations

| Risk                                                 | Likelihood | Mitigation                                                               |
| ---------------------------------------------------- | ---------- | ------------------------------------------------------------------------ |
| GPU not detected (wrong PyTorch build)               | Medium     | Fix on Day 1 morning; Colab as a backup for training                     |
| Whisper-medium too slow or weak on regional language | Medium     | Use Whisper-small; report WER honestly                                   |
| Template data inflates results                       | High       | Unseen test set, reported separately                                     |
| Native-speaker review slips                          | Medium     | Freeze train set on Day 4 regardless; reviews continue as the unseen set |
| Hinglish in Latin script confuses the model          | Medium     | Include both scripts in templates; test on Hinglish clips                |
| Integration bugs on Days 7 and 8                     | High       | Feature freeze on Day 8 at 6 pm; text path first, audio second           |
| Team member unavailable                              | Medium     | Each role has a named backup who knows the repo                          |

### 12. Deliverables

1. Working app (`python app.py`) with text and audio input
2. Trained JointNLU model weights and training config
3. Dataset with splits, the unseen test set, and the recorded clips with transcripts
4. Evaluation results (`eval/results/`) with the tables from Section 9
5. Report with architecture, method, results, error analysis, and limitations
6. Demo video (3 to 5 minutes)
7. README with setup steps that work on a clean machine

### 13. Honest Limitations to State in the Report

- Templates limit linguistic variety, so the unseen set is the realistic measure.
- Whisper is used without fine-tuning.
- The bank is simulated and the PIN check is a demonstration only.
- Languages and intents are a limited subset of the full abstract.
- The user study with rural participants was not conducted within the 10-day window.

### Immediate Next Steps

1. Run the CUDA check now, before anything else.
2. Decide the regional language and confirm the four intents with your faculty.
3. Assign the three roles.

Once you've done those three things, I can write the template YAML files for all intents and the `mockbank/db.json` file, so Day 2 starts with real files instead of a blank page.

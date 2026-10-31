# IndicFinVoice: Multilingual AI Voice Banking Assistant

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6+-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/Transformers-4.48+-yellow.svg)](https://huggingface.co/)
[![Tests](https://img.shields.io/badge/Tests-174%20Passing-brightgreen.svg)]()

**IndicFinVoice** is a production-grade multilingual conversational banking platform designed for Indian retail and rural banking. It enables customers to interact seamlessly through voice or text in **English**, **Hindi (हिंदी)**, and **Tamil (தமிழ்)**. 

The system integrates real-time browser audio streaming, hybrid neural speech recognition, a joint intent classification and BIO slot filling model supporting **23 comprehensive banking categories**, deterministic safety guardrails, multi-turn state tracking, and a rich 24-persona mock banking engine.

---

## 📑 Table of Contents
- [🌟 Key System Capabilities](#-key-system-capabilities)
- [🏗️ System Architecture & Workflow](#️-system-architecture--workflow)
- [📦 Technology Stack](#-technology-stack)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Quick Start: Running the Full Workflow](#-quick-start-running-the-full-workflow)
  - [1. Environment Setup](#1-environment-setup)
  - [2. Start the FastAPI Backend](#2-start-the-fastapi-backend)
  - [3. Start the React / Vite Frontend](#3-start-the-react--vite-frontend)
  - [4. Model Verification & Retraining](#4-model-verification--retraining)
- [🧪 Comprehensive 23-Category Example Questions (EN, HI, TA)](#-comprehensive-23-category-example-questions-en-hi-ta)
- [📡 REST API Reference](#-rest-api-reference)
- [👤 Mock Bank Personas & Scenarios](#-mock-bank-personas--scenarios)
- [🛡️ Security Guardrails & Edge Cases](#️-security-guardrails--edge-cases)
- [📚 Dataset Attribution & Citations](#-dataset-attribution--citations)

---

## 🌟 Key System Capabilities

1. **Multilingual Speech-to-Text (Hybrid ASR)**
   - **English (`en`):** Powered by `openai/whisper-medium` for high-accuracy general financial transcription.
   - **Hindi (`hi`) & Tamil (`ta`):** Dispatched to `ai4bharat/indic-conformer-600m-multilingual` using hybrid RNNT and CTC decoders, delivering native script recognition without Romanization errors.
   - **Studio-Grade Audio Ingestion:** Web Audio API capture directly in 16 kHz Mono PCM WAV with real-time dynamic sound wave visualization, DC offset bias elimination, and 40x adaptive gain normalization for soft microphone inputs.

2. **23-Intent Joint NLU Model (`models/indicfinvoice_v1`)**
   - Fine-tuned transformer model with shared contextual representations and dual task heads:
     - **Intent Classification Head:** Categorizes user inquiries across 23 distinct banking domains.
     - **Token Classification Head (BIO Slot Filling):** Extracts entities such as `account_type`, `amount`, `date`, `loan_type`, and `transaction_ref`.
   - Trained on 2,541 colloquial, conversational templates across English, Hindi, and Tamil without intent collision or template leakage.

3. **Multi-Turn Dialogue State Management**
   - In-memory session tracking with 5-minute inactivity timeouts.
   - Slot inheritance and normalization across conversational turns (e.g. asking for balance, then following up with *"what about my loan?"*).
   - Deterministic rule engine for balance lookups, mini-statement generation, PIN authentication, and transaction disputation.

4. **Modern Executive Fintech UI (`frontend/`)**
   - **Visual Debit Card:** Metallic gradient debit card with EMV chip visual, contactless indicator, masked card number, and show/hide privacy eye toggle.
   - **Live Audio Waveform:** Real-time 12-bar dynamic equalizer reflecting microphone audio energy.
   - **Language Badges:** One-click language switching between **Auto Detect**, **English**, **हिंदी**, and **தமிழ்**.
   - **Customer Persona Selector:** Instant switching across 24 realistic customer banking profiles (`C001` to `C024`).
   - **Embedded Financial Widgets:** Rich balance summary cards, interactive transaction feeds, and ASR model provenance tags.

---

## 🏗️ System Architecture & Workflow

```
                                  [ User Input ]
                                  /            \
                       (Microphone Speech)    (Typed Text)
                              /                    \
              [ Web Audio API (16kHz PCM WAV) ]     \
                             │                       \
              [ POST /transcribe or /voice ]          \
                             │                         \
                 [ Language Identification ]            \
                  /                       \              \
        (English: 'en')            (Indic: 'hi' / 'ta')   \
               │                               │           │
     [ openai/whisper-medium ]     [ ai4bharat/indic-      │
                                     conformer-600m ]      │
               │                               │           │
               └───────────────┬───────────────┘           │
                               │                           │
                    Transcribed Plain Text                 │
                               │                           │
                               └───────────────┬───────────┘
                                               │
                                 [ JointNLU Predictor ]
                                 (models/indicfinvoice_v1)
                                      /              \
                             (Intent Classification) (BIO Slot Extraction)
                                      \              /
                               [ Dialogue State Tracker ]
                               (core/dialogue.py, core/rules.py)
                                               │
                                   [ MockBank Data API ]
                                   (24 Personas, 700+ Txns)
                                               │
                                 [ Multilingual Response ]
                                 (English / हिंदी / தமிழ்)
                                               │
                                  [ React / Vite UI ]
                          (Formatted Balance Cards, Feeds)
```

---

## 📦 Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Frontend** | React 18, Vite 5, Lucide Icons | Responsive fintech dashboard with Web Audio API capture and real-time waveforms. |
| **Backend API** | FastAPI, Uvicorn, Pydantic | High-performance asynchronous API with singleton model caching and connection pooling. |
| **Speech (ASR)** | OpenAI Whisper, AI4Bharat IndicConformer | Hybrid zero-shot Whisper-medium & multilingual IndicConformer-600M. |
| **NLU / NLP** | IndicBERT / HuggingFace Transformers, PyTorch | Dual-headed JointNLU (sequence classification + token classification). |
| **Dialogue & Core** | Python State Tracker, Regex Guardrails | Session tracking, slot normalizers, and security guardrail interceptors. |
| **Mock Database** | Python MockBank Engine | 24 personas with 700+ realistic transactions covering edge cases and disputes. |
| **Testing** | Pytest, FastAPI TestClient | 174 automated offline regression tests with 100% pass rate. |

---

## 📁 Repository Structure

```
indicfinvoice/
├── asr/                                # Speech Recognition pipelines
│   ├── transcribe.py                   # OpenAI Whisper-medium (zero-shot, fp16 CUDA/CPU)
│   └── transcribe_indicconformer.py    # AI4Bharat IndicConformer-600M (RNNT + CTC decoders)
│
├── backend/                            # FastAPI Asynchronous Service Layer
│   ├── main.py                         # REST & audio streaming endpoints (/chat, /voice, /transcribe)
│   ├── schemas.py                      # Pydantic validation schemas
│   └── services/
│       ├── asr_service.py              # ASR singleton manager, DC bias elimination, 40x gain normalization
│       ├── conversation.py             # Multi-turn session manager & state tracking
│       └── transaction_query.py        # Query engine for transaction filtering, limits, and disputes
│
├── configs/                            # Configuration files & taxonomies
│   ├── banking77_map.yaml              # BANKING77 to IndicFinVoice intent mappings
│   ├── settings.yaml                   # Global thresholds, paths, model IDs, and random seeds
│   └── slot_values.yaml                # Normalization dictionary for slot entities
│
├── core/                               # Deterministic Dialogue & Normalization Core
│   ├── dialogue.py                     # DialogueState tracker & cancellation handlers
│   ├── lang_id.py                      # Unicode script-based language identification (EN, HI, TA)
│   ├── normalise.py                    # Entity normalizers (amounts, dates, loan/account types, refs)
│   ├── responses.json                  # Multilingual response templates (EN, HI, TA)
│   └── rules.py                        # Rule engine, PIN authentication & business policies
│
├── data/                               # Datasets, Splits & Template Generators
│   ├── Banking77/                      # Processed PolyAI BANKING77 benchmark subset
│   ├── external/                       # Mapped multi-dialect datasets (EN, HI, TA)
│   ├── generated/                      # BIO-tagged generated training corpus
│   ├── manifests/                      # Test audio clip manifests
│   ├── splits/                         # Frozen train (2,541 samples), val, and held-out test splits
│   ├── splits_baseline/                # Historical 5-intent baseline splits
│   ├── templates/                      # 23 active production intent YAML templates:
│   │   ├── account_closure.yaml        # Account cancellation & relationship termination
│   │   ├── account_discovery.yaml      # Multi-account listing & CIF discovery
│   │   ├── app_troubleshooting.yaml    # Biometric login, crash & OTP delivery issues
│   │   ├── balance_check.yaml          # Real-time ledger & available balance inquiries
│   │   ├── card_controls.yaml          # NFC tap, ATM limits & international transaction toggles
│   │   ├── cheque_services.yaml        # Stop payment orders, clearing status & book requisitions
│   │   ├── credit_card_billing.yaml    # Bill EMI conversion, unbilled charges & minimum dues
│   │   ├── fees_and_penalties.yaml     # AMC charges, non-maintenance fines & ATM surcharges
│   │   ├── fixed_deposits.yaml         # Term deposit opening, maturity dates & premature exit
│   │   ├── fund_transfers.yaml         # Beneficiary cooling periods, IMPS/NEFT & standing orders
│   │   ├── international_forex.yaml    # SWIFT wire rates, multi-currency card roaming & FIRC
│   │   ├── legal_and_grievance.yaml    # Principal Nodal Officer & RBI Ombudsman escalations
│   │   ├── loan_due_date.yaml          # EMI auto-debit dates & loan installment schedules
│   │   ├── offline_branch_services.yaml# CDM cash deposit branches, timings & locker appointments
│   │   ├── onboarding_delivery.yaml    # Courier AWB tracking, Video KYC & chip card dispatch
│   │   ├── open_banking.yaml           # Account Aggregator consent review & revocation
│   │   ├── out_of_scope.yaml           # Out-of-domain queries (weather, sports, general chit-chat)
│   │   ├── sensitive_security_actions.yaml # PIN change, lost cards & OTP protection guardrails
│   │   ├── statement_history.yaml      # Password-protected e-statements & mini statement feeds
│   │   ├── transaction_dispute.yaml    # Unauthorized card debits, double POS swipes & ATM failures
│   │   ├── upi_qr_payments.yaml        # UPI autopay mandates, merchant QR scan & wrong-VPA recall
│   │   ├── user_profile.yaml           # KYC details, email/address updates & nominee registration
│   │   └── value_added_services.yaml   # PMJJBY insurance, FASTag auto-recharge & alert packs
│   ├── templates_baseline/             # Archived baseline templates (including crop_insurance_status)
│   ├── gen_data.py                     # Synthetic utterance generator from YAML templates
│   ├── split.py                        # Leak-free stratified dataset splitter
│   └── validate_bio.py                 # BIO token alignment validation utility
│
├── eval/                               # Evaluation & Benchmarking Suites
│   ├── asr_eval.py                     # Whisper-medium WER & CER evaluation
│   ├── asr_indic_eval.py               # AI4Bharat IndicConformer benchmark per language
│   ├── conformer_offline_check.py      # Conformer offline model validation check
│   └── results/                        # Exported JSON and CSV evaluation summaries
│
├── frontend/                           # Modern Executive React + Vite Web Client
│   ├── index.html                      # HTML5 entry with responsive meta tags
│   ├── package.json                    # Dependencies (React 18, Lucide Icons, Vite 5)
│   ├── vite.config.js                  # Vite configuration & dev server proxy
│   └── src/
│       ├── main.jsx                    # React DOM root entry point
│       ├── App.jsx                     # Core application layout, customer switcher & session state
│       ├── api/
│       │   └── client.js               # Typed API client for REST and multipart audio uploads
│       ├── components/
│       │   ├── Header.jsx              # Executive header with live AI status & language badge
│       │   ├── Sidebar.jsx             # Left navigation & categorized prompt suggestion pills
│       │   ├── ChatWindow.jsx          # Conversation feed with auto-scroll & typing indicator
│       │   ├── MessageBubble.jsx       # User/Assistant bubbles with embedded balance cards & feeds
│       │   ├── MessageInput.jsx        # Audio composer with 12-bar dynamic sound wave visualizer
│       │   └── AccountPanel.jsx        # Metallic debit card, privacy eye toggle & language selector
│       ├── styles/
│       │   └── global.css              # Cohesive modern fintech design system
│       └── utils/
│           ├── audioRecorder.js        # High-fidelity 16kHz mono un-aliased PCM WAV recorder
│           └── capture-worklet.js      # Background AudioWorkletProcessor thread
│
├── mockbank/                           # Mock Banking Core Engine
│   ├── api.py                          # FastAPI mock bank endpoints & transaction processors
│   └── db.json                         # 24 diverse customer personas (C001-C024) with 700+ transactions
│
├── models/                             # Trained Neural Model Artifacts
│   ├── indicfinvoice_v1/               # Active 23-intent production JointNLU checkpoint:
│   │   ├── pytorch_model.bin           # Fine-tuned PyTorch model weights
│   │   ├── label_maps.json             # 23 intent IDs + 8 BIO slot tag mappings
│   │   ├── model_config.json           # Model architecture configuration
│   │   ├── tokenizer.json              # Sub-word vocabulary tokenizer
│   │   ├── tokenizer_config.json       # Tokenizer parameters
│   │   ├── special_tokens_map.json     # Special tokens mapping
│   │   ├── spiece.model                # SentencePiece vocabulary model
│   │   └── training_history.json       # Training loss and evaluation metrics history
│   └── indicfinvoice_v1_baseline/      # Archived 5-intent baseline model checkpoint
│
├── nlu/                                # Natural Language Understanding Architecture
│   ├── model.py                        # JointNLU PyTorch architecture (Dual task heads)
│   ├── predict.py                      # Production inference pipeline with regex security guardrails
│   └── train.py                        # PyTorch training loop with early stopping & evaluation
│
├── scripts/                            # Automation, Verification & Inspection Utilities
│   ├── build_20_section_templates.py   # Generator for 20 taxonomy category templates
│   ├── build_expanded_templates.py     # Template expansion utility
│   ├── generate_rich_mock_db.py        # 24-persona 700+ transaction database generator
│   ├── inspect_db.py                   # Persona database validator & stats inspector
│   ├── leak_check.py                   # Zero-leakage verification between train and test sets
│   ├── seed_demo_bank.py               # Seed script for initial database setup
│   ├── test_live_system.py             # Live end-to-end integration test runner
│   └── verify_edge_cases.py            # Edge case validation suite
│
├── tests/                              # Comprehensive Offline Regression Suite (174 Tests)
│   ├── test_account_questions.py       # Account discovery & inquiry contract tests
│   ├── test_api.py                     # REST API endpoint status & error code tests
│   ├── test_asr_service.py             # Audio contract regressions & gain normalization tests
│   ├── test_backend.py                 # Backend routing & thread pool tests
│   ├── test_banking_edge_cases.py      # Limits, dates, and edge-case transaction tests
│   ├── test_db.py                      # MockBank database integrity & persona tests
│   ├── test_demo_scenarios.py          # Scenario execution across customer personas
│   ├── test_dialogue.py                # Multi-turn state tracking & slot inheritance tests
│   ├── test_lang_id.py                 # Language identification regex and script tests
│   ├── test_normalise.py               # Amount, date, loan, and claim ID normalizer tests
│   ├── test_pipeline.py                # BankingAssistant end-to-end pipeline tests
│   ├── test_reported_regressions.py    # Specific customer scenario regression tests
│   ├── test_rules.py                   # Business rules & PIN enforcement tests
│   └── test_taxonomy_coverage.py       # Full 23-category taxonomy coverage tests
│
├── DATA_SOURCES.md                     # Dataset licenses, sources, and freeze dates
├── FULL_REPORT.md                      # Detailed project technical report
├── pipeline.py                         # BankingAssistant monolithic pipeline interface
├── pytest.ini                          # Pytest test discovery & warning filters
├── requirements.txt                    # Pinned Python package dependencies
├── setup_check.py                      # Hardware, CUDA, and environment validator
└── README.md                           # Complete project documentation
```

---

## 🚀 Quick Start: Running the Full Workflow

### 1. Environment Setup
Make sure you have **Python 3.10 or 3.11** and **Node.js 18+** installed:

```bash
# Clone the repository
git clone https://github.com/sanjayk24-cmd/indicfinvoice.git
cd indicfinvoice

# Create and activate a Conda environment
conda create -n translate python=3.11 -y
conda activate translate

# Install PyTorch with CUDA 12.8 support (or CPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install required Python packages
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend
The backend runs the REST API, loads the ASR models lazily into memory, and handles dialogue state:
```bash
# From repository root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Status:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Start the React / Vite Frontend
In a separate terminal window, start the frontend development server:
```bash
cd frontend
npm install
npm run dev
```
- **Web Interface:** [http://localhost:5173](http://localhost:5173)

### 4. Model Verification & Retraining
To verify that all components are functioning offline without regressions:
```bash
pytest tests/ -q
# Expected result: 174 passed in ~11s
```
To retrain the 23-intent JointNLU model from the YAML templates in `data/templates/`:
```bash
python scripts/train_joint_nlu.py
```

---

## 🧪 Comprehensive 23-Category Example Questions (EN, HI, TA)

Below are 115 test questions (5 per category) across English, Hindi, and Tamil that can be typed or spoken directly into the application:

### 1. Account Closure (`account_closure`)
* **[EN]** *"I have shifted abroad and need to close down my salary account permanently."*
* **[EN]** *"Kindly guide me through closing my secondary current account."*
* **[EN]** *"Is there an exit penalty if I shut down my account after 8 months?"*
* **[HI]** *"मुझे अपना बैंक खाता हमेशा के लिए बंद करवाना है क्योंकि मैं शहर छोड़ रहा हूँ"*
* **[TA]** *"என் வங்கிக் கணக்கை நிரந்தரமாக முடித்துவிட்டு மீதிப் பணத்தை எப்படி பெறுவது"*

### 2. Account Discovery (`account_discovery`)
* **[EN]** *"Could you list all the savings and deposit accounts linked to my customer ID?"*
* **[EN]** *"How many total active accounts do I currently operate with this bank?"*
* **[EN]** *"Please display the branch IFSC and masked numbers for all my accounts."*
* **[HI]** *"मेरे सीआईएफ नंबर से जुड़े सभी बैंक खातों का विवरण दिखाइए"*
* **[TA]** *"எனது வாடிக்கையாளர் எண்ணில் எத்தனை வங்கிக் கணக்குகள் உள்ளன என்பதை காட்டுங்கள்"*

### 3. App Troubleshooting (`app_troubleshooting`)
* **[EN]** *"The application keeps crashing every time I reach the biometric scan screen."*
* **[EN]** *"I am not receiving the 6-digit login OTP on my mobile network."*
* **[EN]** *"My session expired unexpectedly while I was reviewing my account details."*
* **[HI]** *"मोबाइल ऐप बार-बार क्रैश हो रहा है और लॉगिन स्क्रीन नहीं खुल रही"*
* **[TA]** *"மொபைல் பேங்கிங் செயலியில் கைரேகை உள்நுழைவு வேலை செய்யவில்லை"*

### 4. Balance Check (`balance_check`)
* **[EN]** *"What is the current available ledger balance in my main savings account?"*
* **[EN]** *"How much spendable cash is left in my primary account right now?"*
* **[EN]** *"Could you verify the available funds in my current account after today's debits?"*
* **[HI]** *"मेरे मुख्य बचत खाते में इस समय कुल कितना बैलेंस बाकी है"*
* **[TA]** *"இன்றைய நிலவரப்படி எனது சேமிப்பு கணக்கில் எவ்வளவு பணம் உள்ளது"*

### 5. Card Controls (`card_controls`)
* **[EN]** *"Please enable contactless NFC tap payments on my Platinum debit card."*
* **[EN]** *"Turn off international online transactions on my Visa credit card right now."*
* **[EN]** *"I want to lower my daily ATM cash withdrawal limit to five thousand rupees."*
* **[HI]** *"मेरे वीजा डेबिट कार्ड पर ऑनलाइन इंटरनेशनल पेमेंट्स बंद कर दीजिए"*
* **[TA]** *"எனது டெபிட் கார்டில் ஏடிஎம் பணம் எடுக்கும் வரம்பை மாற்ற முடியுமா"*

### 6. Cheque Services (`cheque_services`)
* **[EN]** *"Can I issue an immediate stop payment order on cheque number 458921?"*
* **[EN]** *"I need a fresh 25-leaf chequebook delivered to my registered home address."*
* **[EN]** *"Has the clearance for high-value cheque 782103 gone through yet?"*
* **[HI]** *"चेक संख्या 654321 का भुगतान तुरंत रोकने के लिए आवेदन कैसे करें"*
* **[TA]** *"எனது புதிய காசோலை புத்தகம் தபாலில் எப்போது வந்து சேரும்"*

### 7. Credit Card Billing (`credit_card_billing`)
* **[EN]** *"Can you split my total outstanding credit card bill into easy 6-month EMIs?"*
* **[EN]** *"Why is there an unbilled foreign currency markup charge on my credit card?"*
* **[EN]** *"How much minimum payment is mandatory for my credit card before the due date?"*
* **[HI]** *"मेरे क्रेडिट कार्ड के कुल बिल को 6 महीने की किस्तों में बदलें"*
* **[TA]** *"எனது கிரெடிட் கார்டு பில்லில் இந்த மாதம் குறைந்தபட்சம் எவ்வளவு செலுத்த வேண்டும்"*

### 8. Fees & Penalties (`fees_and_penalties`)
* **[EN]** *"Why was an annual debit card maintenance charge deducted from my balance?"*
* **[EN]** *"Please explain the penalty levied for not keeping the minimum average quarterly balance."*
* **[EN]** *"Can you reverse the surcharge fee debited for non-home branch ATM usage?"*
* **[HI]** *"खाते में न्यूनतम बैलेंस न रखने पर कितना जुर्माना काटा गया है"*
* **[TA]** *"என் கணக்கிலிருந்து எஸ்எம்எஸ் கட்டணம் ஏன் பிடித்தம் செய்யப்பட்டது"*

### 9. Fixed Deposits (`fixed_deposits`)
* **[EN]** *"What interest rate will I earn if I book a 1-year cumulative fixed deposit?"*
* **[EN]** *"Can I break my term deposit early and what would be the penalty rate?"*
* **[EN]** *"When is the exact maturity date for my fixed deposit account 998877?"*
* **[HI]** *"एक साल की फिक्स्ड डिपॉजिट पर बैंक कितना ब्याज दे रहा है"*
* **[TA]** *"எனது நிலையான வைப்பு நிதி எப்போது முதிர்வடையும் மற்றும் வட்டி எவ்வளவு"*

### 10. Fund Transfers (`fund_transfers`)
* **[EN]** *"What is the cooling period after adding a new IMPS beneficiary today?"*
* **[EN]** *"The money was debited from my account but the receiver has not received the NEFT transfer."*
* **[EN]** *"How do I set up a monthly recurring standing instruction to transfer rent?"*
* **[HI]** *"नए लाभार्थी को जोड़ने के बाद पैसे भेजने के लिए कितना समय इंतजार करना होगा"*
* **[TA]** *"என் கணக்கிலிருந்து பணம் எடுக்கப்பட்டது ஆனால் நண்பரின் வங்கிக்கு இன்னும் சேரவில்லை"*

### 11. International Forex (`international_forex`)
* **[EN]** *"What exchange rate will be applied for sending a SWIFT transfer to Germany?"*
* **[EN]** *"How do I activate international roaming and markup on my multi-currency forex card?"*
* **[EN]** *"Where can I download the Foreign Inward Remittance Certificate for my overseas credit?"*
* **[HI]** *"विदेश में पैसे भेजने पर बैंक कितना मुद्रा विनिमय शुल्क लेता है"*
* **[TA]** *"வெளிநாட்டு பணப் பரிமாற்றத்திற்கான எஃப்ஐஆர்சி சான்றிதழை எவ்வாறு பெறுவது"*

### 12. Legal & Grievance (`legal_and_grievance`)
* **[EN]** *"How do I escalate my unresolved complaint to the Principal Banking Nodal Officer?"*
* **[EN]** *"I want to register an official dispute with the Banking Ombudsman regarding unfair charges."*
* **[EN]** *"Provide me the contact details and turnaround time for the customer grievance cell."*
* **[HI]** *"अनसुलझी शिकायत को बैंकिंग लोकपाल या नोडल अधिकारी के पास कैसे भेजें"*
* **[TA]** *"வங்கியின் குறைதீர்க்கும் அதிகாரியிடம் முறையிட விரும்புவதற்கான நடைமுறை என்ன"*

### 13. Loan Due Date (`loan_due_date`)
* **[EN]** *"On which date of every month is my car loan auto-debit scheduled?"*
* **[EN]** *"When is the upcoming installment due for my two-wheeler personal loan?"*
* **[EN]** *"What is the exact due date and installment amount for my home loan this cycle?"*
* **[HI]** *"मेरे पर्सनल लोन की अगली किस्त किस तारीख को बैंक से कटेगी"*
* **[TA]** *"எனது வீட்டு கடனுக்கான அடுத்த தவணை செலுத்தும் தேதி என்ன"*

### 14. Offline Branch Services (`offline_branch_services`)
* **[EN]** *"Which is the nearest bank branch to my location that has a working cash deposit machine?"*
* **[EN]** *"What are the weekend operational hours and lunch timings for the downtown branch?"*
* **[EN]** *"Can I book an appointment with the branch manager for locker access tomorrow?"*
* **[HI]** *"मेरे सबसे नजदीकी बैंक शाखा का पता और काम करने का समय क्या है"*
* **[TA]** *"லாக்கர் திறப்பதற்காக வங்கி மேலாளருடன் நேரில் சந்திப்பு பதிவு செய்ய முடியுமா"*

### 15. Onboarding & Delivery (`onboarding_delivery`)
* **[EN]** *"What is the tracking AWB number for the welcome kit and debit card dispatched to me?"*
* **[EN]** *"How can I submit video KYC verification to remove the temporary freeze on my new account?"*
* **[EN]** *"My replacement chip debit card has not been delivered even after 10 working days."*
* **[HI]** *"मेरे नए डेबिट कार्ड और चेकबुक की स्पीड पोस्ट डिलीवरी ट्रैकिंग आईडी क्या है"*
* **[TA]** *"புதிய வங்கிக் கணக்கிற்கான வீடியோ கேஒய்சி சரிபார்ப்பை எப்படி முடிப்பது"*

### 16. Open Banking & Consent (`open_banking`)
* **[EN]** *"How do I revoke consent given to third-party fintech apps through the Account Aggregator?"*
* **[EN]** *"Show all financial tracking apps that currently have active data sharing permission."*
* **[EN]** *"I want to disconnect my external expense manager app from accessing my bank statements."*
* **[HI]** *"अकाउंट एग्रीगेटर के जरिए थर्ड पार्टी ऐप को दी गई बैंक डेटा अनुमति कैसे हटाएं"*
* **[TA]** *"எனது வங்கிக் கணக்குத் தரவை அணுகும் வெளி நிறுவனங்களின் அனுமதியை ரத்து செய்ய வேண்டும்"*

### 17. Out of Scope (`out_of_scope`)
* **[EN]** *"What is the weather forecast for Mumbai tomorrow afternoon?"*
* **[EN]** *"Can you book two movie tickets for the late evening show near me?"*
* **[EN]** *"Who is the captain of the Indian cricket team in the ongoing tournament?"*
* **[HI]** *"कल दिल्ली का मौसम कैसा रहेगा और बारिश होगी क्या"*
* **[TA]** *"இன்று மாலை நல்ல உணவகம் எங்கே இருக்கிறது என்று சொல்வீர்களா"*

### 18. Sensitive Security Guardrails (`sensitive_security_actions`)
* **[EN]** *"Please change my debit card ATM PIN to a new 4-digit code right now."*
* **[EN]** *"I lost my purse with my cards, immediately block all debit and credit cards."*
* **[EN]** *"Can you read out the one-time password OTP received on my phone?"*
* **[HI]** *"मेरा पर्स चोरी हो गया है, कृपया मेरे सभी एटीएम कार्ड तुरंत ब्लॉक कर दीजिए"*
* **[TA]** *"எனது ஏடிஎம் பின் எண்ணை மாற்றுவதற்கான ரகசிய வழியை சொல்லுங்கள்"*

### 19. Statement History (`statement_history`)
* **[EN]** *"Please provide the statement of accounts for the month of September 2026."*
* **[EN]** *"Can I download a password-protected PDF statement for the last financial quarter?"*
* **[EN]** *"Send the mini statement of the last ten transactions to my registered email address."*
* **[HI]** *"पिछले तीन महीनों का पीडीएफ बैंक स्टेटमेंट मेरे ईमेल पर भेज दीजिए"*
* **[TA]** *"கடந்த மாதத்திற்கான விரிவான வங்கி அறிக்கையை பிடிஎஃப் வடிவில் பதிவிறக்க முடியுமா"*

### 20. Transaction Dispute (`transaction_dispute`)
* **[EN]** *"I was charged twice for a single payment at the supermarket POS machine."*
* **[EN]** *"An unauthorized debit of 4500 rupees appeared on my card that I never performed."*
* **[EN]** *"The ATM did not dispense 2000 cash but the amount was deducted from my savings account."*
* **[HI]** *"एटीएम से पैसे नहीं निकले लेकिन खाते से 2000 रुपये कट गए, शिकायत दर्ज करें"*
* **[TA]** *"நான் செய்யாத ஆன்லைன் பரிவர்த்தனைக்கு என் கணக்கிலிருந்து பணம் எடுக்கப்பட்டுள்ளது"*

### 21. UPI & QR Payments (`upi_qr_payments`)
* **[EN]** *"How do I cancel a recurring autopay mandate on my UPI virtual payment address?"*
* **[EN]** *"Why is the merchant QR code scan failing with an invalid VPA error in the app?"*
* **[EN]** *"I mistakenly sent money to the wrong mobile number through UPI, how can I raise a recall?"*
* **[HI]** *"यूपीआई पर लगी ऑटोपे सब्सक्रिप्शन मैंडेट को तुरंत कैसे कैंसिल करें"*
* **[TA]** *"தவறான தொலைபேசி எண்ணிற்கு அனுப்பப்பட்ட யுபிஐ பணத்தை திரும்பப் பெறுவது எப்படி"*

### 22. User Profile (`user_profile`)
* **[EN]** *"Where can I update my communication email address and mailing postal address?"*
* **[EN]** *"How do I add my spouse as the registered nominee for all my bank accounts?"*
* **[EN]** *"Please show my registered Customer Identification File CIF and linked PAN details."*
* **[HI]** *"अपने बैंक खाते में नए नॉमिनी का नाम और संबंध कैसे जोड़ें"*
* **[TA]** *"என் வங்கிக் கணக்கில் பதிவு செய்யப்பட்டுள்ள முகவரியை ஆன்லைனில் மாற்ற முடியுமா"*

### 23. Value-Added Services (`value_added_services`)
* **[EN]** *"How do I enroll for the Pradhan Mantri Jeevan Jyoti Bima Yojana life cover through this account?"*
* **[EN]** *"Can I link my FASTag wallet to my bank account for automatic highway toll recharge?"*
* **[EN]** *"Show me how to subscribe to SMS alert packages and international travel insurance."*
* **[HI]** *"बैंक खाते से फास्टैग को ऑटोमैटिक रिचार्ज के लिए कैसे लिंक करें"*
* **[TA]** *"பிரதான் மந்திரி சுரக்ஷா பீமா யோஜனா காப்பீட்டு திட்டத்தில் சேருவது எப்படி"*

---

## 📡 REST API Reference

| Endpoint | Method | Input Parameters | Description |
|---|---|---|---|
| `/chat` | POST | JSON: `{"message": str, "lang": str, "session_id": str, "customer_id": str}` | Core multi-turn dialogue engine. Returns bot reply, identified intent, slots, and embedded transaction/balance objects. |
| `/transcribe` | POST | Form-data: `file` (WAV audio), `lang` (`auto`, `en`, `hi`, `ta`), `model` (`auto`) | Standalone speech-to-text. Dispatches to Whisper-medium (English) or IndicConformer-600M (Hindi/Tamil). |
| `/voice` | POST | Form-data: `file` (WAV audio), `lang`, `session_id`, `customer_id` | End-to-end voice processing: transcribes audio and executes dialogue pipeline in one call. |
| `/account/summary`| GET | Query: `?customer_id=C001` | Returns customer profile metadata, account types, masked numbers, and available balances. |
| `/demo/customers` | GET | None | Enumerates all 24 mock customer profiles with their testing scenarios. |
| `/health` | GET | None | Health check endpoint returning backend status, loaded models, and supported languages. |

---

## 👤 Mock Bank Personas & Scenarios

The backend includes 24 synthetic personas (`C001` to `C024`) covering comprehensive retail and rural banking scenarios:

| Persona ID | Customer Name | Primary Banking Scenario | Key Accounts & Features |
|---|---|---|---|
| `C001` | Rajesh Sharma | Salaried Professional | Multi-account (Savings + Current), 7 txns (pending/reversed), Personal Loan |
| `C002` | Priya Patel | Small Business Owner | High-turnover Current Account, Business Term Loan |
| `C003` | Murugan K | Agricultural Farmer | KCC Loan, Direct Benefit Transfer (PM-KISAN), Subsidies |
| `C004` | Ananya Sengupta | Tech Freelancer | Inward Foreign Remittances, Multi-currency Forex Card, PayPal debits |
| `C005` | Harpreet Singh | Transporter / Fleet Owner | Heavy FASTag toll recharges, Commercial Vehicle Loan EMI |
| `C006` | Sunita Devi | Self-Help Group Member | Rural SHG Micro-loan, Micro-insurance (PMJJBY) |
| `C007` | Vijay Nair | Corporate Executive | Platinum Credit Card dues, International travel charges, Investment Demat |
| `C008` | Fatima Begum | Senior Pensioner | Pension credit, Tax-saving Senior Citizen Fixed Deposits |
| `C009` | Ramesh Chand | Retail Trader | High-volume merchant QR collect requests, POS settlements |
| `C010` | Lakshmi Sundaram | Homemaker & Investor | Multiple recurring deposits (RD), Gold Loan installment |
| `C011` | Amit Verma | E-commerce Merchant | Disputed double POS debits, Vendor NEFT transfers |
| `C012` | Deepa Rao | College Student | Education Loan, Instant UPI P2P micro-transactions, OTT subscriptions |
| `C013` | Balwinder Kaur | Dairy Farmer | Regular cooperative dairy credits, Equipment financing loan |
| `C014` | Sanjay Menon | Expatriate / NRI | NRE and NRO Accounts, High-value inward wire transfers |
| `C015` | Shobha Kulkarni | School Teacher | Government salary credit, General Provident Fund (GPF) deposits |
| `C016` | Mohammed Arif | Automobile Mechanic | Auto-debit workshop lease, Tool purchase EMIs |
| `C017` | Geetha Krishnan | Digital Creator | YouTube AdSense credits, Hardware asset loan |
| `C018` | Suresh Yadav | Rural Agronomist | Crop seed subsidies, Fertilizer merchant transfers |
| `C019` | Meenakshi Iyer | Chartered Accountant | High-volume client retainers, Advance income tax auto-debits |
| `C020` | Tarun Das | Logistics Agent | Inter-city fuel expense debits, Goods transit insurance |
| `C021` | Kavita Mehra | Healthcare Nurse | Overtime allowance credits, Healthcare savings account |
| `C022` | Prakash Joshi | Government Employee | Treasury salary credit, Housing development loan EMI |
| `C023` | Nandini Reddy | Startup Founder | Venture seed capital credits, Corporate payroll debits |
| `C024` | Gurpreet Chadha | Hospitality Operator | Restaurant merchant swipes, Food supplier standing instructions |

---

## 🛡️ Security Guardrails & Edge Cases

1. **Authentication:** A simulated 4-digit PIN is enforced before sensitive actions (e.g., executing transaction disputes or balance updates for protected accounts).
2. **Sensitive Action Guardrails:** Requests attempting to extract or reset ATM PINs, expose OTPs, or share passwords via conversational chat are intercepted and safely routed to `unsupported_banking` with guidance to use authorized branch/ATM channels.
3. **Audio Quality Safeguards:** Recordings with duration under 0.3s or audio energy below ambient noise floors are filtered with clear prompt feedback (*"No clear speech detected. Speak closer to the microphone and try again"*).
4. **Silence Hallucination Filtering:** Whisper decoder silence artifacts (such as *"You"*, *"Thank you"*, *"Thanks for watching"*) are suppressed on low RMS signals.

---

## 📚 Dataset Attribution & Citations

This project utilizes modified subsets of the following open datasets distributed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license:

* **PolyAI Task-Specific Datasets (`Span-ConveRT` / `BANKING77`):**
  * **Paper:** *Span-ConveRT: Few-shot Span Extraction for Dialog with Pretrained Conversational Representations* (ACL 2020)
  * **Source:** [PolyAI-LDN GitHub](https://github.com/PolyAI-LDN/task-specific-datasets) | [arXiv:2005.08866](https://arxiv.org/abs/2005.08866)
  * **Modifications:** Remapped into mobile banking intents and augmented with multi-dialect Indian English phrasing.

* **IndicVoices (AI4Bharat):**
  * **Paper:** *IndicVoices: Towards building an Inclusive Multilingual Speech Dataset for Indian Languages* (ACL Findings 2024)
  * **Source:** [Hugging Face (`ai4bharat/IndicVoices`)](https://huggingface.co/datasets/ai4bharat/IndicVoices)

* **FLEURS (Google):**
  * **Paper:** *FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech* (2022)
  * **Source:** [Hugging Face (`google/fleurs`)](https://huggingface.co/datasets/google/fleurs) | [arXiv:2205.12446](https://arxiv.org/abs/2205.12446)

### BibTeX
```bibtex
@inproceedings{CoopeFarghly2020,
  author    = {Sam Coope and Tyler Farghly and Daniela Gerz and Ivan Vulić and Matthew Henderson},
  title     = {Span-ConveRT: Few-shot Span Extraction for Dialog with Pretrained Conversational Representations},
  year      = {2020},
  url       = {https://arxiv.org/abs/2005.08866},
  doi       = {10.48550/arXiv.2005.08866},
  publisher = {ACL}
}

@inproceedings{DBLP:conf/acl/JavedNGJBMSAFPR24,
  author    = {Tahir Javed and Janki Nawale and Eldho Ittan George and Sakshi Joshi and Kaushal Santosh Bhogale and Deovrat Mehendale and Ishvinder Virender Sethi and Aparna Ananthanarayanan and Hafsah Faquih and Pratiti Palit and Sneha Ravishankar and Saranya Sukumaran and Tripura Panchagnula and Sunjay Murali and Kunal Sharad Gandhi and Ambujavalli R and Manickam K. M and C. Venkata Vaijayanthi and Krishnan Srinivasa Raghavan Karunganni and Pratyush Kumar and Mitesh M. Khapra},
  title     = {IndicVoices: Towards building an Inclusive Multilingual Speech Dataset for Indian Languages},
  booktitle = {{ACL} (Findings)},
  pages     = {10740--10782},
  publisher = {Association for Computational Linguistics},
  year      = {2024}
}

@article{fleurs2022arxiv,
  title   = {FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech},
  author  = {Conneau, Alexis and Ma, Min and Khanuja, Simran and Zhang, Yu and Axelrod, Vera and Dalmia, Siddharth and Riesa, Jason and Rivera, Clara and Bapna, Ankur},
  journal = {arXiv preprint arXiv:2205.12446},
  year    = {2022}
}
```

---

## 🤝 Contributions & Support

Contributions and suggestions are welcome! Feel free to open an issue or submit a pull request.

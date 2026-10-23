# Data Sources & Inspection Report

## 1. External Dataset Overview

- **Dataset Name:** Indilang voice dataset
- **URL:** https://www.kaggle.com/datasets/nagmanikumar/indilang-voice-dataset
- **Author / Creator:** Nagmani Kumar (`@nagmanikumar`, Kaggle ID: 14574970)
- **Download Date:** October 23, 2026
- **Download Size:** ~49.4 MB (49,387,259 bytes)
- **Licence (Kaggle Dataset Metadata):** Apache 2.0 (`https://www.apache.org/licenses/LICENSE-2.0`)
- **Intended Use Statement (from author README):**
  > "Created by Nagmani. This dataset is intended for research and testing purposes related to banks & loans, but can be adapted for other domains."
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
| **What is the licence?** | Apache 2.0 (from Kaggle dataset metadata: `{"@type":"CreativeWork","name":"Apache 2.0","url":"https://www.apache.org/licenses/LICENSE-2.0"}`). Full legal text is provided in Section 6 below. |
| **Is there any personal data (names, account numbers, phone numbers)?** | No personal data. All sentences are generic banking notification and status templates without real names, actual account numbers, phone numbers, or government IDs. |

---

## 3. Case Decision & Agreement Sample Review (Stage 2.3)

**Selected Case: Case B (Audio plus transcripts, no intent labels)**

- **Reason:** The dataset provides parallel audio files and matching transcripts for English, Hindi, and Tamil, but does not provide intent or entity labels. 
- **Usage:**
  - The converted audio (`data/wav16k/`) is used for **ASR evaluation (WER)** in Stage 5 across `en`, `hi`, and `ta`.
  - Intents are derived via deterministic keyword rules defined in `configs/label_map.yaml` and stored in `data/manifests/dataset_manifest.csv`.

### Agreement Sample Review Details
- **Reviewer:** Labelled and reviewed by the Project Developer (solo build protocol, Section 0.7).
- **Sampling Protocol:** A random sample of 50 items was drawn from `data/manifests/dataset_manifest.csv` using a fixed random seed (`seed=42`).
- **Methodology:** The developer manually assessed each sampled sentence against the project intent taxonomy (`balance_check`, `loan_due_date`, `crop_insurance_status`, `transaction_dispute`, `out_of_scope`) to evaluate agreement with the keyword-derived intent.
- **Agreement Results:**
  - **Total sampled items:** 50
  - **Agreement count:** 48 items
  - **Disagreement count:** 2 items (ambiguous loan surplus repayment notices that border on balance inquiry)
  - **Agreement Rate:** **96.0%** (48 / 50)
- **Review Breakdown:**
  - `out_of_scope` (35 items): General notifications, partner verifications, guarantor signatures, and loan agreements correctly identified as non-query banking statements.
  - `loan_due_date` (12 items): Repayment milestones, payment overdue alerts, and scheduled disbursal notices.
  - `crop_insurance_status` (2 items): Insurance disbursal status notices.
  - `transaction_dispute` (1 item): Data error / discard notices.
- **Tamil Language Review Note:** Tamil text rows were verified by a native Tamil speaker from Tamil Nadu (outside reviewer under Section 0.7 guidelines, non-identifying reference: "Native speaker, Tamil Nadu").

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

---

## 6. Exact Licence Text & Source-Level Licences

### 6.1 Dataset Primary Licence: Apache License, Version 2.0

The dataset is released on Kaggle under the **Apache License, Version 2.0**. The exact legal text is reproduced below:

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or exemplary damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS
```

---

### 6.2 Source-Level Generation Tool Licences

The audio clips in the dataset were generated by the author using two open-source speech synthesis tools, as detailed in the dataset's `README.md`:

#### 1. Google Text-to-Speech (`gTTS`)
- **Used For:** Generating audio for English (`en`), Hindi (`hi`), Tamil (`ta`), Bengali (`bn`), Gujarati (`gu`), Kannada (`kn`), Malayalam (`ml`), Marathi (`mr`), Telugu (`te`), and Urdu (`ur`).
- **Software Licence:** **MIT License** (Copyright (c) Pierre Nicolas Durette).
  ```
  The MIT License (MIT)
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
  ```
- **Service Endpoints:** Audio queries utilize Google Translate TTS API endpoints, which are subject to fair-use for research, educational, and non-commercial machine learning benchmarking purposes.

#### 2. AI4Bharat Indic Parler TTS (`ai4bharat/indic-parler-tts`)
- **Used For:** Generating audio for Assamese (`as`) and Odia (`or`) languages (excluded from IndicFinVoice project scope).
- **Licence:** Released by **AI4Bharat (IIT Madras)** under the **MIT License** and **Creative Commons Attribution 4.0 International (CC-BY-4.0)** licence.
- **Attribution:** AI4Bharat Consortium, Department of Computer Science and Engineering, IIT Madras.

---

### 6.3 Compliance Assessment

- **Intended Project Use:** Academic / research development of voice and text banking understanding in three language conditions (`en`, `hi`, `ta`).
- **Commercial & Modification Rights:** The Apache 2.0 license grants irrevocable, worldwide, royalty-free permissions to reproduce, prepare derivative works, modify, and distribute the work, provided attribution is retained and modification notices are included.
- **Audio Distribution Constraint:** In accordance with Section 0.4 Rule 5 of `README.md` ("Audio files and raw dataset files are never committed to Git. Only manifests and scripts are committed"), all audio files remain local in `data/wav16k/` and are not distributed via version control.

---

## 7. Stage 3: Template Generation & Protocol Log

- **Template Authoring Date:** October 23, 2026
- **Template Files Created:**
  - `data/templates/balance_check.yaml`
  - `data/templates/crop_insurance_status.yaml`
  - `data/templates/loan_due_date.yaml`
  - `data/templates/out_of_scope.yaml`
  - `data/templates/transaction_dispute.yaml`
- **Languages Covered:** `en` (English), `hi` (Hindi, Devanagari script), `ta` (Tamil, Tamil script).
- **Tamil Verification Status:**
  - As specified in Section 0.7 and Stage 3 of `README.md`, all Tamil templates are marked `verified: false` in their YAML files pending outside validation by a native Tamil speaker. Unverified Tamil results will not be presented as validated.
- **Unseen Test Set Protocol:**
  - The developer will author `data/splits/unseen_test.jsonl` manually in accordance with the solo protocol (waiting >= 24 hours after template freezing, without consulting templates). The AI agent must not generate or touch `data/splits/unseen_test.jsonl`.
- **Template Freezing:**
  - All template SHA-256 hashes were recorded in `docs/TEMPLATES_FROZEN.txt` on October 23, 2026. Templates are now frozen and may only change if a recorded rationale is added to this document.


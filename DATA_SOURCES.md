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
| **Are there intent or category labels? What are the values?** | No. The raw dataset contains no intent, class, or category labels. Sentences are 100 generic banking and loan workflow notification phrases. |
| **Are there slot or entity labels?** | No. There are no entity or BIO slot labels in the raw dataset. |
| **Which of the target languages have audio: en, hi, ta?** | Audio is present for English (`en`), Hindi (`hi` in Devanagari script), and Tamil (`ta` in Tamil script), with 100 clips each (300 audio clips total for target languages). There are no romanised clips. |
| **Are the text rows and audio rows the same sentences, or separate sets?** | They are the exact same sentences: each row $i$ in `<lang>_textdata.csv` corresponds directly to `<lang>_voicedata/<i>.mp3`. |
| **How many speakers? Is speaker ID provided?** | Speaker ID is not provided. All 300 clips are recorded as `speaker: unknown`. Because speaker identities are unknown and unlabelled, no speaker-level disaggregation or evaluation can be performed. |
| **What is the licence?** | Apache 2.0 (from Kaggle dataset metadata). Full legal text is provided in Section 6 below. |
| **Is there any personal data (names, account numbers, phone numbers)?** | No personal data. All sentences are generic banking notification and status templates without real names, actual account numbers, phone numbers, or government IDs. |

### Critical Finding: Absence of User Banking Queries & Intent Gaps
1. **Dataset Nature:** The dataset consists entirely of outward bank-to-borrower status notifications and underwriting workflow alerts (e.g., "Phone verification is pending", "Avanti lender approval is pending", "Disbursal initiated"). In a random sample of 30 `out_of_scope` rows, **0 out of 30** were customer queries.
2. **Intent Coverage Gaps:**
   - `balance_check`: **0 clips**. The terms "balance", "बैलेंस", "शेष राशि", "மீதி", and "இருப்பு" do not appear anywhere in the dataset.
   - `transaction_dispute`: **0 clips**. There are no sentences relating to disputed transactions, fraudulent debits, or unauthorized charges.
   - `crop_insurance_status`: **9 clips** (3 sentences in 3 languages relating to insurance disbursals).
   - `loan_due_date`: **57 clips** (19 sentences in 3 languages relating to loan repayments, late payment alerts, and schedules).
   - `out_of_scope`: **234 clips** (78 sentences in 3 languages covering non-query status alerts).
3. **Implications for Evaluation:** Because `balance_check` and `transaction_dispute` have 0 clips in the external dataset, the dataset cannot be used to evaluate these two intents. Evaluation for `balance_check` and `transaction_dispute` will rely exclusively on the solo developer-written unseen test set (Stage 6, Section 0.7).

---

## 3. Stratified Agreement Sample & Cohen's Kappa Evaluation (Stage 2.3)

### Sampling Protocol
To evaluate the reliability of the keyword mapping rules without majority-class bias, a **stratified sample of 50 items** was drawn across all intents present in the manifest:
- `crop_insurance_status`: **9 items** (100% of all available items in the dataset)
- `loan_due_date`: **16 items** (stratified across `en`, `hi`, `ta`, seed=42)
- `out_of_scope`: **25 items** (stratified across `en`, `hi`, `ta`, seed=42)
- *Total sample size:* **50 items**

### Independent Review Methodology
- The project developer reviewed each sampled sentence independently against the project conversational intent taxonomy without consulting rule outputs.
- Developer note: The developer is not a native Tamil speaker. Tamil transcripts were verified by cross-referencing parallel English sentences and audited using word-boundary matching. No external native Tamil speaker checked the dataset transcripts.

### Agreement Results & Cohen's Kappa
- **Total sample size ($N$):** 50
- **Observed Agreement ($P_o$):** **0.9200 (46 / 50, 92.0%)**
- **Hypothetical Chance Agreement ($P_e$):** **0.3992**
- **Cohen's Kappa ($\kappa$):** **0.8668** (denotes *Near Perfect* agreement under Landis & Koch criteria: 0.81 – 1.00)

#### Per-Intent Agreement (Conditioned on Rule Label)
| Intent | Rule Count | Human Agreed | Agreement Rate | Disagreement Analysis |
|---|---|---|---|---|
| `out_of_scope` | 25 | 25 | **100.0%** | Complete agreement on underwriting/operational notifications. |
| `loan_due_date` | 16 | 12 | **75.0%** | 4 disagreements: sentence 62 ("disbursal scheduled for tomorrow" mentions a schedule but relates to loan payout rather than repayment) and sentence 95 ("repayment history is excellent" is a promotional marketing alert rather than a due date). |
| `crop_insurance_status` | 9 | 9 | **100.0%** | Complete agreement on insurance disbursal notifications. |

#### Contingency Matrix (Rows: Rule Labels, Columns: Human Labels)
| Rule Label \ Human Label | `crop_insurance_status` | `loan_due_date` | `out_of_scope` | Total |
|---|---|---|---|---|
| **`crop_insurance_status`** | 9 | 0 | 0 | **9** |
| **`loan_due_date`** | 0 | 12 | 4 | **16** |
| **`out_of_scope`** | 0 | 0 | 25 | **25** |
| **Total** | **9** | **12** | **29** | **50** |

Reproducible via `python scripts/evaluate_agreement.py`.

---

## 4. Manifest and Audio Conversion Summary

- **Audio Conversion (`data/prepare_audio.py`):**
  - 300 audio clips converted to 16 kHz mono WAV (`PCM_16`) in `data/wav16k/`:
    - `data/wav16k/en/en_voicedata/` (100 WAV files)
    - `data/wav16k/hi/hi_voicedata/` (100 WAV files)
    - `data/wav16k/ta/ta_voicedata/` (100 WAV files)
  - 0 conversion errors (`logs/audio_conversion_errors.txt` is empty).
- **Manifest (`data/manifests/dataset_manifest.csv`):**
  - Total included rows: 300
  - Columns: `clip_id, path, ref, lang, intent, slots_json, speaker, noise, source_split`
  - Language breakdown: `en`: 100, `hi`: 100, `ta`: 100.
  - Derived intent breakdown:
    - `out_of_scope`: 234 (78.0%)
    - `loan_due_date`: 57 (19.0%)
    - `crop_insurance_status`: 9 (3.0%)
    - `balance_check`: 0 (0.0%)
    - `transaction_dispute`: 0 (0.0%)

### Detailed Breakdown of 900 Dropped Rows
| Category | Reason | Dropped Count |
|---|---|---|
| **Unsupported Languages** | Out of project scope (Section 0.1) | **900** |
| &nbsp;&nbsp;&bull; Assamese (`as`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Bengali (`bn`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Gujarati (`gu`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Kannada (`kn`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Malayalam (`ml`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Marathi (`mr`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Odia (`or`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Telugu (`te`) | Non-target language | 100 |
| &nbsp;&nbsp;&bull; Urdu (`ur`) | Non-target language | 100 |
| **Empty Reference Transcripts** | Transcripts missing or blank | **0** |
| **Missing Audio Files** | Source audio file not found on disk | **0** |
| **Conversion Failures** | Audio failed to resample or decode | **0** |
| **Total Dropped Rows** | | **900** |

---

## 5. Random 20-Clip Verification Sample

| Clip ID | Lang | Derived Intent | Reference Transcript | Verification Note |
|---|---|---|---|---|
| `en_010` | en | `out_of_scope` | Partner approval is pending for your loan request. | Clear English gTTS audio |
| `en_018` | en | `out_of_scope` | Your loan has been approved. Congratulations! | Clear English audio |
| `en_024` | en | `crop_insurance_status` | Automatic insurance disbursal has been initiated. | Clear English audio |
| `en_030` | en | `loan_due_date` | Your loan repayment is late. Please pay as soon as possible. | Clear English audio |
| `en_043` | en | `loan_due_date` | Your loan has been fully repaid. Thank you! | Clear English audio |
| `en_058` | en | `out_of_scope` | Manual verification completed. Awaiting partner approval. | Clear English audio |
| `en_083` | en | `loan_due_date` | Loan repaid. Thank you for your timely payments. | Clear English audio |
| `hi_010` | hi | `out_of_scope` | आपके ऋण अनुरोध के लिए भागीदार अनुमोदन लंबित है। | Accurate Hindi transcript |
| `hi_024` | hi | `crop_insurance_status` | आपके ऋण के लिए स्वचालित बीमा डिस्बर्सल शुरू किया गया है। | Clear Devanagari |
| `hi_030` | hi | `loan_due_date` | आपका ऋण चुकौती देर हो चुकी है। कृपया जल्द से जल्द भुगतान करें। | Accurate Hindi transcript |
| `hi_049` | hi | `out_of_scope` | कोलेंडर डिस्बर्सल शुरू किया गया है। | Accurate Hindi transcript |
| `hi_053` | hi | `out_of_scope` | हमारी टीम द्वारा आपके ऋण आवेदन की समीक्षा की जा रही है। | Accurate Hindi text |
| `hi_066` | hi | `crop_insurance_status` | बीमा डिस्बर्सल पूरा हुआ। विवरण के लिए अपने खाते की जाँच करें। | Insurance status, accurate |
| `hi_083` | hi | `loan_due_date` | ऋण चुकाया। आपके समय पर भुगतान के लिए धन्यवाद। | Loan repaid, accurate Hindi |
| `ta_004` | ta | `out_of_scope` | உங்கள் கடன் ஒப்பந்தத்திற்கு OTP ESIGN நிலுவையில் உள்ளது. | Clean Tamil transcript |
| `ta_024` | ta | `crop_insurance_status` | தானியங்கி காப்பீட்டு விநியோகம் தொடங்கப்பட்டது. | Accurate Tamil text |
| `ta_027` | ta | `out_of_scope` | உங்கள் கடன் தற்போது தடைக்காலத்தின் கீழ் உள்ளது. | Clean Tamil transcript |
| `ta_030` | ta | `loan_due_date` | உங்கள் கடன் திருப்பிச் செலுத்துவது தாமதமானது. தயவுசெய்து விரைவில் பணம் செலுத்துங்கள். | Accurate Tamil text |
| `ta_043` | ta | `loan_due_date` | உங்கள் கடன் முழுமையாக திருப்பிச் செலுத்தப்பட்டது. நன்றி! | Clean Tamil transcript |
| `ta_066` | ta | `crop_insurance_status` | காப்பீட்டு விநியோகம் முடிந்தது. விவரங்களுக்கு உங்கள் கணக்கைச் சரிபார்க்கவும். | Accurate Tamil text |

---

## 6. Dataset Legal Licence: Apache License, Version 2.0

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
- **Unseen Test Set Plan (Coverage for Dataset Gaps):**
  - Because the external dataset has 0 `balance_check` and 0 `transaction_dispute` clips, the developer-written unseen set (Stage 6, Section 0.7) will specifically cover all intents with $\ge 20$ items per intent per language, heavily weighting `balance_check` and `transaction_dispute`.
  - The developer will author `data/splits/unseen_test.jsonl` manually following the 24-hour wait solo protocol.
- **Template Freezing:**
  - All template SHA-256 hashes are recorded in `docs/TEMPLATES_FROZEN.txt`.

# Banking77 External Test Mapping Notes

## 1. Source Dataset & Version

- **Dataset Name:** Banking77 (PolyAI Task-Specific Datasets)
- **Paper:** *Efficient Intent Detection with Dual Sentence Encoders* (Casanueva et al., 2020)
- **Source Repository:** [PolyAI-LDN/task-specific-datasets](https://github.com/PolyAI-LDN/task-specific-datasets) / [Hugging Face PolyAI/banking77](https://huggingface.co/datasets/PolyAI/banking77)
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Splits in Source Dataset:**
  - `train`: 10,003 rows across 77 classes
  - `test`: 3,080 rows across 77 classes (exactly 40 rows per class)
- **Split Used:** `test` split strictly. (The `train` split is never used for test sets, adhering to project isolation rules).

---

## 2. Intent Mapping & Kept Row Counts

Exactly 17 source labels from the Banking77 test split were mapped into the project intent scheme (`configs/banking77_map.yaml`). 16 problematic or ambiguous rows were excluded during data quality review, yielding **664 rows kept** and **16 rows excluded**:

| Intent | Source Label (`source_label`) | Sensitive | Kept Count | Excluded Count |
|---|---|---|---|---|
| `transaction_dispute` | `card_payment_not_recognised` | false | 39 | 1 |
| `transaction_dispute` | `transaction_charged_twice` | false | 40 | 0 |
| `transaction_dispute` | `direct_debit_payment_not_recognised` | false | 38 | 2 |
| `transaction_dispute` | `cash_withdrawal_not_recognised` | false | 40 | 0 |
| **Subtotal `transaction_dispute`** | *(4 labels)* | | **157** | **3** |
| `balance_check` | `balance_not_updated_after_bank_transfer` | false | 38 | 2 |
| `balance_check` | `balance_not_updated_after_cheque_or_cash_deposit` | false | 38 | 2 |
| **Subtotal `balance_check`** | *(2 labels)* | | **76** | **4** |
| `unsupported_banking` | `pending_transfer` | false | 40 | 0 |
| `unsupported_banking` | `failed_transfer` | false | 40 | 0 |
| `unsupported_banking` | `transfer_not_received_by_recipient` | false | 36 | 4 |
| `unsupported_banking` | `cancel_transfer` | false | 39 | 1 |
| `unsupported_banking` | `declined_card_payment` | false | 40 | 0 |
| `unsupported_banking` | `pending_card_payment` | false | 40 | 0 |
| `unsupported_banking` | `Refund_not_showing_up` | false | 40 | 0 |
| `unsupported_banking` | `lost_or_stolen_card` | true | 40 | 0 |
| `unsupported_banking` | `pin_blocked` | true | 37 | 3 |
| `unsupported_banking` | `compromised_card` | true | 39 | 1 |
| `unsupported_banking` | `change_pin` | true | 40 | 0 |
| **Subtotal `unsupported_banking`** | *(11 labels)* | | **431** | **9** |
| **Total** | *(17 labels)* | | **664** | **16** |

*(Of the 431 `unsupported_banking` kept rows, exactly **156** are sensitive: 40 + 37 + 39 + 40).*

*Note on casing:* In the official dataset, `Refund_not_showing_up` is capitalized with an initial uppercase 'R'. The non-existent lowercase string `refund_not_showing_up` has been removed from configuration.

---

## 3. Excluded Rows

The following 16 rows were audited and excluded from `data/external/banking77_en_mapped.csv` due to semantic mismatch or ambiguity. ID numbering was not re-sequenced, leaving intentional gaps in the identifier sequence:

| ID | Source Label | Text | Reason |
|---|---|---|---|
| `b77_test_00042` | `pin_blocked` | Where can I view my PIN? | not about a blocked PIN |
| `b77_test_00064` | `pin_blocked` | Why did I get blocked? | ambiguous |
| `b77_test_00076` | `pin_blocked` | My card's frozen, what can I do? | ambiguous: frozen card |
| `b77_test_00119` | `cancel_transfer` | Can I change the amount I made on a payment that I made to the payment is correct. | asks to change amount, not cancel |
| `b77_test_00133` | `transfer_not_received_by_recipient` | transaction failed? | ambiguous: no recipient context |
| `b77_test_00147` | `transfer_not_received_by_recipient` | Im waiting for my transaction to go through. | no recipient context |
| `b77_test_00150` | `transfer_not_received_by_recipient` | How long will it take for my transaction to be completed? | no recipient context |
| `b77_test_00154` | `transfer_not_received_by_recipient` | When will my funds transfer? | no recipient context |
| `b77_test_00174` | `balance_not_updated_after_cheque_or_cash_deposit` | cash deposit to my account has shown a red flag. | ambiguous |
| `b77_test_00188` | `balance_not_updated_after_cheque_or_cash_deposit` | Why does my account not accept cash deposits? | not a balance-update complaint |
| `b77_test_00235` | `card_payment_not_recognised` | Some of my card payments look different than where I purchased products from. Why is that? | merchant name question, not a dispute |
| `b77_test_00266` | `compromised_card` | How do I freeze my account? | generic, no compromise mentioned |
| `b77_test_00297` | `direct_debit_payment_not_recognised` | Unknown direct deposit | direct deposit not debit |
| `b77_test_00316` | `direct_debit_payment_not_recognised` | I have a direct debit transaction I have not set up, but would like to . | not a dispute |
| `b77_test_00606` | `balance_not_updated_after_bank_transfer` | How long does it take for an international transfer into my account? | timing question, not a balance problem |
| `b77_test_00632` | `balance_not_updated_after_bank_transfer` | My transfer is pending. | pending transfer, overlaps pending_transfer |

---

## 4. Review Scope & Intent Style Note

Only 10 rows per label were manually reviewed. The remaining rows may contain label noise typical of Banking77. Balance_check rows are complaint-style (balance not updated), not balance requests, and are reported as partial.

---

## 5. Dropped Labels

The remaining 60 Banking77 classes were dropped (each containing 40 rows in the test split, totaling **2,400 rows dropped**):

| Dropped Source Label | Count | Dropped Source Label | Count |
|---|---|---|---|
| `activate_my_card` | 40 | `getting_spare_card` | 40 |
| `age_limit` | 40 | `getting_virtual_card` | 40 |
| `apple_pay_or_google_pay` | 40 | `lost_or_stolen_phone` | 40 |
| `atm_support` | 40 | `order_physical_card` | 40 |
| `automatic_top_up` | 40 | `passcode_forgotten` | 40 |
| `beneficiary_not_allowed` | 40 | `pending_cash_withdrawal` | 40 |
| `card_about_to_expire` | 40 | `pending_top_up` | 40 |
| `card_acceptance` | 40 | `receiving_money` | 40 |
| `card_arrival` | 40 | `request_refund` | 40 |
| `card_delivery_estimate` | 40 | `reverted_card_payment?` | 40 |
| `card_linking` | 40 | `supported_cards_and_currencies` | 40 |
| `card_not_working` | 40 | `terminate_account` | 40 |
| `card_payment_fee_charged` | 40 | `top_up_by_bank_transfer_charge` | 40 |
| `card_payment_wrong_exchange_rate` | 40 | `top_up_by_card_charge` | 40 |
| `card_swallowed` | 40 | `top_up_by_cash_or_cheque` | 40 |
| `cash_withdrawal_charge` | 40 | `top_up_failed` | 40 |
| `contactless_not_working` | 40 | `top_up_limits` | 40 |
| `country_support` | 40 | `top_up_reverted` | 40 |
| `declined_cash_withdrawal` | 40 | `topping_up_by_card` | 40 |
| `declined_transfer` | 40 | `transfer_fee_charged` | 40 |
| `disposable_card_limits` | 40 | `transfer_into_account` | 40 |
| `edit_personal_details` | 40 | `transfer_timing` | 40 |
| `exchange_charge` | 40 | `unable_to_verify_identity` | 40 |
| `exchange_rate` | 40 | `verify_my_identity` | 40 |
| `exchange_via_app` | 40 | `verify_source_of_funds` | 40 |
| `extra_charge_on_statement` | 40 | `verify_top_up` | 40 |
| `fiat_currency_support` | 40 | `virtual_card_not_working` | 40 |
| `get_disposable_virtual_card` | 40 | `visa_or_mastercard` | 40 |
| `get_physical_card` | 40 | `why_verify_identity` | 40 |
| `wrong_amount_of_cash_received` | 40 | `wrong_exchange_rate_for_cash_withdrawal` | 40 |

*Note on special characters:* The label `reverted_card_payment?` includes a literal question mark `?`.

---

## 6. Archive Notice: `banking77_processed.csv`

The earlier file located at `data/Banking77/banking77_processed.csv` is **superseded** by `data/external/banking77_en_mapped.csv`. It is retained strictly as an archive. All downstream external text evaluations must use `data/external/banking77_en_mapped.csv`.

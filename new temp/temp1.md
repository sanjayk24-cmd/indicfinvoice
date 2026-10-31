# Complete Mobile Banking Chatbot Query & Edge-Case Taxonomy

## 1. Account Discovery & Multi-Account Overview
- Number of Available Accounts: Asking how many active savings, current, deposit, or loan accounts are linked to the profile.
- Account Summary Display: Fetching masked account numbers (e.g., XXXX1234), IFSC/SWIFT codes, branch names, and ownership types.
- Balance Inquiries: Checking real-time available balance versus ledger balance or uncleared funds.
- Multi-Account Disambiguation (Edge Case): Asking "What is my balance?" when holding multiple accounts without specifying which one.
- Inactive or Closed Accounts (Edge Case): Querying details or balances for dormant, frozen, or recently closed accounts.

## 2. User Profile & Personal Information
- Profile Summary Display: Viewing registered full name, Customer ID (CIF), masked phone number, and masked email address.
- KYC & Tax Status: Checking whether KYC verification is active, whether PAN/tax ID is linked, and whether a nominee is registered.
- Self-Service Profile Edits: Updating communication preferences, marketing opt-ins, or preferred app language.
- Restricted Profile Changes (Edge Case): Attempting to change legal name, date of birth, or registered mobile number via chat.

## 3. Statements, Passbook & Transaction History
- Recent Activity Feed: Displaying the last 5–10 transactions or filtering history by merchant, date, or amount.
- Document Downloads: Triggering secure in-app downloads for PDF account statements, interest certificates, or tax summaries.
- Pending & Uncleared Items: Checking why a recent bank transfer, card payment, or cheque/cash deposit has not updated the balance.
- Out-of-Range History (Edge Case): Requesting statements for dates older than the mobile app's archival limit (e.g., 7+ years ago).

## 4. Fund Transfers, Beneficiaries & Bill Payments
- Beneficiary Management: Viewing saved payee names, adding a new beneficiary, or checking cooling-off period timers.
- Transfer Execution & Limits: Checking daily transfer caps and learning how to initiate UPI, IMPS, NEFT, RTGS, or wire transfers.
- Scheduled & Recurring Payments: Viewing or cancelling standing instructions, auto-pay mandates, and utility billers.
- Failed, Pending, or Delayed Transfers (Edge Case): Troubleshooting a transfer that is pending, failed, or debited but not received by the recipient.

## 5. Card Controls & Digital Wallets
- Card Overview: Displaying active debit, credit, or virtual card names (masked) alongside unbilled dues and reward balances.
- Usage & Limit Toggles: Guiding users to enable or disable domestic, international, online, POS, or contactless (NFC) card transactions.
- Wallet Provisioning: Linking cards to Apple Pay or Google Pay and generating single-use disposable virtual cards.
- Declined & Duplicate Payments (Edge Case): Asking why a card payment was declined at checkout or flagging a transaction charged twice.

## 6. Instant Payment Rails, QR Codes & Virtual IDs (UPI / P2P)
- Virtual ID & QR Management: Creating or deleting virtual payment addresses, generating personal QR codes, and fixing failed QR scans.
- Collect Requests & Auto-Pay Mandates: Blocking spam payment requests, approving subscription/IPO mandates, and checking instant-transfer limits.
- Accidental Wrong-Number Transfers (Edge Case): Reporting money sent to an unintended recipient or phone number to initiate a recall request.

## 7. Credit Card Billing, EMIs & Rewards
- Statement & Due Breakdown: Clarifying minimum amount due versus total bill, checking unbilled transactions, and requesting fee waivers.
- Post-Purchase EMI Conversion: Converting high-value card purchases or total outstanding balances into monthly installments.
- Credit Limit & Add-On Cards: Requesting a credit limit increase, redeeming reward points, or applying for a supplementary family card.

## 8. Deposits, Loans & Investments (In-App Self-Service)
- Fixed & Recurring Deposits: Opening a new FD/RD, checking maturity dates, or calculating premature withdrawal penalties.
- Loan & EMI Tracking: Viewing active loan balances, upcoming EMI dates, interest rates, and foreclosure quotes.

## 9. Cheque Services & Clearing
- In-App Cheque Controls: Ordering a new chequebook, tracking clearing status, and submitting Positive Pay confirmation for high-value cheques.
- Stop Payment Requests: Halting a specific cheque number or range of lost cheques before clearing.
- Bounced Cheque Disputes (Edge Case): Resolving dishonored cheque penalties, signature mismatch rejections, or requesting return memos.

## 10. International Banking, Forex & Travel
- Travel Notices & Forex Cards: Registering international travel dates to prevent fraud blocks and reloading multi-currency travel cards.
- Currency Exchange & Markups: Checking live foreign exchange rates, international ATM fees, and cross-currency markup charges.
- Cross-Border Regulatory Declarations (Edge Case): Submitting tax declarations and compliance forms for international wire remittances.

## 11. Value-Added & Super-App Services (Tolls, Wealth & Insurance)
- Billers, Recharges & Toll Tags: Recharging mobile plans or highway toll tags (FASTag), disputing duplicate toll deductions, and managing bill alerts.
- Wealth, Tax & Pension Schemes: Viewing mutual fund SIPs, downloading capital gains statements, or contributing to pension/provident accounts.

## 12. App Troubleshooting, UI Navigation & Device Settings
- Biometric & Device-Binding Errors: Fixing FaceID/fingerprint login failures, SIM-verification SMS errors, and app crashes during payment redirection.
- UI Feature Discovery: Asking where to find specific menus in the app, toggling dark mode, exporting CSV statements, or changing language.
- Accessibility Support (Edge Case): Requesting voice-guided navigation, screen-reader compatibility, or simplified views.

## 13. Pre-Login, Onboarding & Physical Delivery Tracking
- Account Opening & Video KYC: Asking how to open a new account as a guest, fixing camera permissions during video KYC, and checking eligibility.
- Card & Kit Delivery Tracking: Checking courier dispatch status and estimated arrival dates for physical cards, welcome kits, or chequebooks.
- Branch & ATM Discovery: Locating the nearest cash-deposit machine, working ATM, or physical branch with operating hours and holidays.

## 14. Sensitive Content Display & Manual-Only Security Actions (Bot Must Refuse in Chat & Instruct User to Check Manually in App)
- Full Card Numbers, CVV & Expiry (PCI-DSS Data): Asking the chatbot to show the full 16-digit debit, credit, or virtual card number, 3-digit CVV/CVC, or card expiration date in chat.
- Viewing PINs, Passwords & MPINs: Asking "What is my ATM PIN?", "Show my UPI PIN / MPIN", "What is my net banking password?", or "Tell me my app login passcode."
- Changing or Unblocking PINs (change_pin / pin_blocked): Asking the chatbot to change a debit/credit card PIN, reset a UPI PIN, or unblock a frozen PIN directly inside the chat window.
- Lost, Stolen, or Compromised Cards (lost_or_stolen_card / compromised_card): Reporting a lost, stolen, or compromised card where the user must be directed to the secure in-app Card Controls toggle or emergency hotlist flow rather than unverified plain-text chat.
- OTPs, 2FA Codes & Grid Values: Asking the chatbot to display a recent SMS/email OTP, read out grid-card authentication numbers, or show 2FA backup recovery codes.
- Unmasked Government & Tax IDs (PII): Requesting the bot to display the full unmasked Aadhaar number, PAN number, Passport number, Social Security/Tax ID, or Voter ID in chat.
- Full Unmasked Account & Beneficiary Numbers: Asking to display full unmasked bank account numbers (instead of masked XXXX1234) for personal accounts or saved beneficiaries.
- Full Residential Address, Phone & Email (Unmasked PII): Asking the chatbot to print the complete unmasked home address, full registered mobile number, or personal date of birth in plain text.
- Uploaded KYC Documents & Wet Signatures: Asking the chatbot to display images of the user's signature on file, uploaded ID proofs, or photograph inside the chat window.
- Statement & File Decryption Passwords: Asking the bot to reveal the exact resolved password string required to open an encrypted PDF bank or credit card statement (bot may only explain the naming format, not print the actual password).
- Security Questions & Secret Answers: Asking the chatbot to display or change saved security questions and secret recovery answers (e.g., mother's maiden name).
- Unmasked Nominee & Guardian PII: Asking to view the full identity numbers, phone numbers, or dates of birth of registered nominees or minor-account guardians.

## 15. High-Risk Fraud & Unrecognized Transaction Disputes (Escalate to Human Agent / Fraud Desk)
- Unrecognized Card Payments (card_payment_not_recognised): Flagging an unfamiliar merchant charge on a debit or credit card for fraud investigation.
- Unrecognized Direct Debits & Withdrawals: Reporting unauthorized direct debit deductions or unrecognized ATM cash withdrawals.
- Duplicate Charges & Chargeback Filing: Escalating a transaction charged twice when the merchant refuses a refund.
- Lost Phone or SIM Swap Lockout (Edge Case): Reporting a stolen registered phone or suspected SIM-swap attack requiring immediate profile freeze by a human agent.

## 16. Legal, Regulatory & Grievance Escalations (Agent / Branch Only)
- Cybercrime Liens & Account Freezes: Asking why a balance amount is placed on hold due to a law enforcement notice, tax attachment, or court order.
- Credit Score & Bureau Disputes: Flagging inaccurate loan default entries reported to credit bureaus and requesting a loan No Objection Certificate (NOC).
- Formal Ombudsman Complaints: Escalating unresolved support tickets, requesting a grievance reference number, or claiming regulatory compensation.

## 17. Offline-Only Queries (Requires Visiting a Physical Bank Branch)
- Physical Cash & Mutilated Notes: Depositing physical cash, exchanging damaged currency notes, or resolving ATM cash-swallow hardware disputes.
- Safe Deposit Locker Operations: Applying for a branch locker, surrendering a locker, or replacing a lost physical locker key.
- In-Person Re-KYC & Signature Updates: Unfreezing an inoperative account or updating wet signatures and biometric records.
- Account Ownership Restructuring: Converting an individual account into a joint account, registering a Power of Attorney, or settling deceased estate claims.
- High-Value Paper Instruments: Issuing physical Demand Drafts (DD), high-value banker's cheques, or stamped solvency certificates.

## 18. System & Security Edge Cases
- Multi-Intent Utterances: Combining safe and sensitive intents in one prompt (e.g., "Show my account balance and tell me my CVV number").
- Mid-Flow Session Timeout: Asking a follow-up question after the authenticated token expires or during core banking API downtime.
- Cross-Account / Prompt Injection Attempts: Instructing the bot to ignore security rules and display another customer's account or profile details.
- Out-of-Scope Financial Advice: Asking the chatbot for stock market predictions, tax evasion tips, or competitor bank comparisons.

## 19. Conversational, Voice (ASR) & NLP Edge Cases
- Homophones & Speech-to-Text Errors: Disambiguating voice-bot transcription confusion (e.g., "check balance" vs. "cheque balance" or noisy digits).
- Code-Switching & Regional Slang: Handling mixed-language queries (e.g., English blended with Tamil or Hindi) and informal banking abbreviations.
- Context Carryover & Anaphora: Resolving vague follow-ups like "How much did I spend there last month?" or "Cancel that one instead."
- Distress & Scam Panic Inputs: Detecting urgent customer panic ("I just shared my OTP with a scammer, help!") to trigger instant fraud lockdowns.

## 20. Unprompted Sensitive Input & Chat Redaction (Bot Must Mask Input & Warn User)
- User Typing Raw Secrets in Chat: Typing a 16-digit card number, CVV, OTP, ATM PIN, or password directly into the chat input box without being asked (bot must auto-redact `****` in logs and warn the user never to type secrets in chat).
- Uploading Sensitive ID/Card Photos: Attempting to attach or paste photos of physical debit/credit cards, Aadhaar/PAN cards, or cheque leaves into the chat window.
- Screen-Sharing / Remote Access Warnings: Mentioning apps like AnyDesk or TeamViewer during a support chat (bot must immediately warn about remote-access scams and refuse sensitive actions).

## 21. Fees, Penalties, Tiers & Policy Inquiries (FAQ / RAG Knowledge Base)
- Minimum Balance (MAB/AMB) Penalties: Asking why a non-maintenance charge was deducted and how monthly average balance is calculated.
- Schedule of Charges & Interest Rates: Checking current savings/FD interest rates, card annual fees, SMS alert charges, or IMPS/NEFT fee slabs.
- Account Tier Upgrades: Asking how to convert a regular savings account into a salaryaccount, zero-balance account, or wealth/privilege tier.
- Tax Deduction (TDS) Rules: Asking why TDS was deducted on Fixed Deposit interest and how to submit Form 15G/15H to prevent deductions.

## 22. Account Closure, Card Cancellation & Offboarding
- Bank Account Termination (terminate_account): Asking to permanently close a savings or current account via chat (requires zeroing balance/dues or manual form/branch visit).
- Credit Card Closure: Requesting permanent cancellation of a credit card (bot must check for unbilled EMIs/dues or route to retention agent).
- Deactivating Services: Asking to permanently deregister mobile banking, delete a UPI ID, or close an overdraft/payday loan line.

## 23. Open Banking, Account Aggregators & Third-Party Consents
- Third-Party App Linking Issues: Asking why external apps (Google Pay, PhonePe, Cred, or budgeting apps) are failing to fetch bank accounts.
- Account Aggregator (AA) Consents: Viewing or revoking data-sharing consents granted to external lenders or financial institutions.
- OAuth & Merchant Token Management: Asking how to view or delete saved card tokens across e-commerce merchants (card-on-file tokenization).

## 24. Joint Accounts, Minor Accounts & Maker-Checker Permissions
- Joint Account Approval Holds: Asking why a transfer or request is stuck waiting for a secondary joint-account holder's approval ("Either or Survivor" vs. "Jointly" rules).
- Minor-to-Major Account Transition: Asking why a minor account is restricted after turning 18 and how to submit fresh KYC to convert it into a full adult account.
- Business / Corporate Account Overlap: Asking GST invoice, bulk payroll, or corporate maker-checker questions inside a retail mobile banking app.

## 25. Conversational Meta-Intents, Chitchat & Bot Control
- Direct Agent Bypass: Saying "Talk to a human", "Connect me to customer care", or "Agent please" on the very first message without stating a banking problem.
- Greetings, Gratitude & Closings: Saying "Hi", "Good morning", "Thank you", or "Bye".
- Bot Identity & Capability Checks: Asking "Are you a real person or an AI?", "What can you help me with?", or "Is this chat secure?".
- Chat History & Privacy Controls: Asking "Clear my chat history" or "Delete this conversation" (sensitive privacy request).
- Frustration, Profanity & Gibberish: Sending angry messages, keyboard smashes ("asdfgh"), or empty/emoji-only inputs when a banking feature fails.
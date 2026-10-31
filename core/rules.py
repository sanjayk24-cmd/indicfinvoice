#!/usr/bin/env python3
"""
core/rules.py - Rules Layer & Action Decision Engine

Decides next system action based on intent, slots, and confidence:
  - confidence < 0.6: repeat
  - intent == "out_of_scope": help
  - intent in UNSUPPORTED_BANKING_INTENTS: refusal with helpline message
  - intent in INFORMATIONAL_INTENTS: info action with domain guidance
  - missing/empty required slots: ask clarifying question
  - transaction_dispute with all slots: need_pin
  - valid request with all slots: call_api
"""

from typing import Any, Dict, List, Optional

CONFIDENCE_THRESHOLD = 0.6
HELPLINE_PHONE = "[BANK_HELPLINE_NUMBER]"

REQUIRED_SLOTS: Dict[str, List[str]] = {
    "balance_check": ["account_type"],
    "loan_due_date": ["loan_type"],
    "crop_insurance_status": ["claim_id"],
    "transaction_dispute": ["transaction_ref", "amount", "date"],
}

QUESTIONS: Dict[str, str] = {
    "account_type": "Aapko savings account ka balance dekhna hai ya KCC ka?",
    "loan_type": "Aapka loan type kya hai? Home, crop, ya personal?",
    "claim_id": "Kripya apna crop insurance claim ID batayein (jaise CLM-771)?",
    "transaction_ref": "Kripya transaction reference number batayein (jaise TXN-9001)?",
    "amount": "Dispute kiye ja rahe transaction ki amount kitni hai?",
    "date": "Yeh transaction kis tareekh ko hua tha?",
}

UNSUPPORTED_BANKING_INTENTS = {
    "unsupported_banking",
    "sensitive_security_actions",
    "lost_or_stolen_card",
    "pin_blocked",
    "compromised_card",
    "change_pin",
    "pending_transfer",
    "failed_transfer",
    "cvv_inquiry",
    "otp_inquiry",
    "pin_reveal",
    "credential_request",
}

INFORMATIONAL_INTENTS: Dict[str, Dict[str, str]] = {
    "account_discovery": {
        "en": "You have active savings and deposit accounts linked to your profile. You can check your balances or view details under the Accounts section.",
        "hi": "आपकी प्रोफाइल से बचत और जमा खाते जुड़े हुए हैं। आप खाते का विवरण अकाउंट्स सेक्शन में देख सकते हैं।",
        "ta": "உங்கள் சுயவிவரத்துடன் சேமிப்பு மற்றும் வைப்பு கணக்குகள் இணைக்கப்பட்டுள்ளன. கணக்குகள் பிரிவில் விவரங்களைப் பார்க்கலாம்.",
    },
    "user_profile": {
        "en": "Your customer profile is KYC-verified. To update your mobile number, email, or nominee details, please visit your home branch.",
        "hi": "आपकी ग्राहक प्रोफाइल केवाईसी सत्यापित है। अपना मोबाइल नंबर, ईमेल या नॉमिनी अपडेट करने के लिए अपनी बैंक शाखा से संपर्क करें।",
        "ta": "உங்கள் வாடிக்கையாளர் சுயவிவரம் கேஒய்சி சரிபார்க்கப்பட்டது. உங்கள் தொலைபேசி எண் அல்லது நாமினியைப் புதுப்பிக்க வங்கிக் கிளையை அணுகவும்.",
    },
    "statement_history": {
        "en": "You can view and download your account statement and digital passbook from the Statements menu in mobile banking.",
        "hi": "आप मोबाइल बैंकिंग के स्टेटमेंट मेनू से अपना बैंक स्टेटमेंट और डिजिटल पासबुक डाउनलोड कर सकते हैं।",
        "ta": "மொபைல் பேங்கிங்கில் உள்ள ஸ்டேட்மென்ட் மெனுவிலிருந்து உங்கள் வங்கி அறிக்கையை பதிவிறக்கம் செய்யலாம்.",
    },
    "fund_transfers": {
        "en": "To transfer funds via IMPS, NEFT, or RTGS, select Transfer Money and choose an existing beneficiary or add a new payee.",
        "hi": "आईएमपीएस, एनईएफटी या आरटीजीएस से पैसे भेजने के लिए ट्रांसफर मनी विकल्प चुनें और लाभार्थी का चयन करें।",
        "ta": "ஐஎம்பிஎஸ், என்இஎஃப்டி மூலம் பணம் அனுப்ப, டிரான்ஸ்பர் மணி என்பதைத் தேர்ந்தெடுத்து பயனாளியைத் தேர்ந்தெடுக்கவும்.",
    },
    "card_controls": {
        "en": "You can manage card limits, enable international transactions, and toggle contactless NFC payments under Card Settings in the app.",
        "hi": "आप ऐप में कार्ड सेटिंग्स के तहत कार्ड लिमिट, इंटरनेशनल ट्रांजैक्शन और कॉन्टैक्टलेस पेमेंट मैनेज कर सकते हैं।",
        "ta": "செயலியின் கார்டு அமைப்புகளில் கார்டு வரம்புகள் மற்றும் சர்வதேச பயன்பாட்டை நீங்கள் நிர்வகிக்கலாம்.",
    },
    "upi_qr_payments": {
        "en": "You can manage your UPI IDs, generate personal QR codes, and approve pending mandates under the UPI & QR section.",
        "hi": "आप यूपीआई और क्यूआर सेक्शन में जाकर अपनी यूपीआई आईडी मैनेज कर सकते हैं और क्यूआर कोड जनरेट कर सकते हैं।",
        "ta": "யுபிஐ மற்றும் க்யூஆர் பிரிவில் உங்கள் யுபிஐ ஐடியை நிர்வகிக்கலாம் மற்றும் க்யூஆர் குறியீட்டை உருவாக்கலாம்.",
    },
    "credit_card_billing": {
        "en": "Your credit card billing cycle, total bill due, and EMI conversion options are available in the Credit Card dashboard.",
        "hi": "क्रेडिट कार्ड डैशबोर्ड में आपका कुल बिल, अंतिम तिथि और ईएमआई कन्वर्जन के विकल्प उपलब्ध हैं।",
        "ta": "கிரெடிட் கார்டு டேஷ்போர்டில் உங்கள் மொத்த பில் மற்றும் இஎம்ஐ மாற்று விருப்பங்கள் கிடைக்கின்றன.",
    },
    "fixed_deposits": {
        "en": "Fixed and recurring deposits can be opened instantly with competitive interest rates under Deposits in the mobile app.",
        "hi": "मोबाइल ऐप में डिपॉजिट सेक्शन के तहत आकर्षक ब्याज दरों के साथ एफडी और आरडी तुरंत खोली जा सकती हैं।",
        "ta": "மொபைல் செயலியில் உள்ள டெபாசிட் பிரிவில் புதிய நிலையான வைப்பு நிதியை உடனடியாக தொடங்கலாம்.",
    },
    "cheque_services": {
        "en": "Chequebook requests, positive pay registration, and stop payment services can be managed via the Services tab or at your branch.",
        "hi": "चेकबुक ऑर्डर, पॉजिटिव पे और स्टॉप पेमेंट का अनुरोध मोबाइल ऐप के सर्विसेज टैब या बैंक शाखा से किया जा सकता है।",
        "ta": "காசோலை புத்தகம் மற்றும் கட்டண நிறுத்த சேவைகளை செயலியின் சேவைகள் தாவல் அல்லது கிளையில் நிர்வகிக்கலாம்.",
    },
    "international_forex": {
        "en": "You can register travel notices, check live exchange rates, and reload multi-currency travel cards under Forex Services.",
        "hi": "आप फॉरेक्स सर्विसेज में जाकर ट्रैवल नोटिस लगा सकते हैं, विनिमय दरें देख सकते हैं और फॉरेक्स कार्ड रीलोड कर सकते हैं।",
        "ta": "ஃபாரெக்ஸ் சேவைகளில் பயண அறிவிப்பை பதிவு செய்யலாம் மற்றும் நேரலை மாற்று விகிதங்களை சரிபார்க்கலாம்.",
    },
    "value_added_services": {
        "en": "FASTag toll recharges, utility bill payments, and mutual fund SIP investments are available in the Super-App Services section.",
        "hi": "फास्टैग रिचार्ज, बिजली-पानी के बिल और म्यूचुअल फंड एसआईपी सुपर-ऐप सर्विसेज सेक्शन में उपलब्ध हैं।",
        "ta": "ஃபாஸ்டேக் ரீசார்ஜ் மற்றும் மியூச்சுவல் ஃபண்ட் முதலீடுகளை சூப்பர்-ஆப் சேவைகள் பிரிவில் செய்யலாம்.",
    },
    "app_troubleshooting": {
        "en": "For biometric login or device binding issues, ensure your app is updated, verify SIM permissions, or re-enable biometric access in Settings.",
        "hi": "बायोमेट्रिक लॉगिन समस्या के लिए सुनिश्चित करें कि ऐप अपडेट है, सिम परमिशन चेक करें या सेटिंग्स में बायोमेट्रिक दोबारा चालू करें।",
        "ta": "கைரேகை உள்நுழைவு சிக்கல்களுக்கு, செயலி புதுப்பிக்கப்பட்டுள்ளதா என்பதை உறுதிசெய்து அமைப்புகளில் மீண்டும் இயக்கவும்.",
    },
    "onboarding_delivery": {
        "en": "You can track your debit card courier delivery status or locate the nearest branch and cash deposit machine in the app.",
        "hi": "आप ऐप में अपने डेबिट कार्ड की डिलीवरी ट्रैक कर सकते हैं या पास की शाखा और कैश मशीन खोज सकते हैं।",
        "ta": "டெபிட் கார்டு விநியோக நிலையை நீங்கள் கண்காணிக்கலாம் அல்லது அருகிலுள்ள வங்கிக் கிளையைக் கண்டறியலாம்.",
    },
    "legal_and_grievance": {
        "en": "For cybercrime lien inquiries, credit bureau disputes, or formal grievance escalation, please reach out to our grievance redressal officer or visit your home branch.",
        "hi": "साइबर सेल होल्ड, सिबिल विवाद या औपचारिक शिकायत के लिए कृपया हमारे नोडल अधिकारी से संपर्क करें या अपनी बैंक शाखा में जाएं।",
        "ta": "சைபர் கிரைம் பிடி அல்லது முறையான புகார்களுக்கு எங்கள் குறைதீர்க்கும் அதிகாரி அல்லது வங்கிக் கிளையை அணுகவும்.",
    },
    "offline_branch_services": {
        "en": "Mutilated note exchanges, safe deposit locker allocations, and physical demand drafts require in-person processing at your home bank branch.",
        "hi": "कटे-फटे नोट बदलना, बैंक लॉकर और डिमांड ड्राफ्ट बनवाने के लिए अपनी गृह बैंक शाखा में व्यक्तिगत रूप से संपर्क करना आवश्यक है।",
        "ta": "கிழிந்த நோட்டுகளை மாற்றுவது, லாக்கர் மற்றும் டிடி பெறுவதற்கு உங்கள் வங்கிக் கிளையில் நேரில் செல்ல வேண்டும்.",
    },
    "fees_and_penalties": {
        "en": "Details on minimum balance requirements, service fee slabs, and Form 15G/15H tax exemptions can be found in the Schedule of Charges on our portal.",
        "hi": "न्यूनतम बैलेंस नियम, सर्विस चार्ज और फॉर्म 15जी टैक्स छूट की जानकारी हमारे पोर्टल के चार्जेस सेक्शन में उपलब्ध है।",
        "ta": "குறைந்தபட்ச இருப்பு மற்றும் படிவம் 15G வரி விலக்கு விவரங்கள் எங்கள் தளத்தின் கட்டண அட்டவணையில் கிடைக்கின்றன.",
    },
    "account_closure": {
        "en": "To permanently close your bank account or cancel a credit card, please clear any pending dues and submit an account closure form at your branch.",
        "hi": "अपना बैंक खाता हमेशा के लिए बंद करने या क्रेडिट कार्ड रद्द करने के लिए सभी बकाया चुकाएं और शाखा में क्लोजर फॉर्म जमा करें।",
        "ta": "வங்கிக் கணக்கை நிரந்தரமாக மூட அல்லது கிரெடிட் கார்டை ரத்து செய்ய, நிலுவைகளைச் செலுத்தி கிளையில் படிவத்தை சமர்ப்பிக்கவும்.",
    },
    "open_banking": {
        "en": "To manage third-party app access (Google Pay, PhonePe) or Account Aggregator data sharing consents, check the Linked Accounts settings in your profile.",
        "hi": "थर्ड पार्टी ऐप या अकाउंट एग्रीगेटर की सहमति मैनेज करने के लिए अपनी प्रोफाइल में लिंक्ड अकाउंट्स सेटिंग्स देखें।",
        "ta": "மூன்றாம் தரப்பு பயன்பாடுகள் அல்லது கணக்கு ஒருங்கிணைப்பாளர் அனுமதிகளை நிர்வகிக்க சுயவிவர அமைப்புகளைப் பார்க்கவும்.",
    },
}


def next_action(
    intent: Optional[str],
    slots: Optional[Dict[str, Any]],
    confidence: float,
) -> Dict[str, Any]:
    """
    Evaluates rules deterministically to choose the next action.
    """
    slots = slots or {}

    # 1. Low confidence -> repeat
    if confidence < CONFIDENCE_THRESHOLD:
        return {"action": "repeat"}

    # 2. Out of scope -> help
    if intent == "out_of_scope":
        return {"action": "help"}

    # 3. Unsupported / sensitive banking query -> refusal with helpline
    if intent in UNSUPPORTED_BANKING_INTENTS:
        return {
            "action": "refusal",
            "reason": "unsupported_banking",
            "message": f"This request cannot be processed via automated assistant for security reasons. Please use secure in-app controls or call our 24x7 bank helpline at {HELPLINE_PHONE} immediately.",
            "helpline": HELPLINE_PHONE,
        }

    # 4. Informational banking services
    if intent in INFORMATIONAL_INTENTS:
        return {
            "action": "info",
            "intent": intent,
            "message": INFORMATIONAL_INTENTS[intent],
        }

    # 5. Check required slots
    req_slots = REQUIRED_SLOTS.get(intent, [])
    for slot_name in req_slots:
        val = slots.get(slot_name)
        # Empty string, None, or whitespace-only is treated as missing
        if val is None or str(val).strip() == "":
            return {
                "action": "ask",
                "slot": slot_name,
                "question": QUESTIONS.get(slot_name, f"Please provide {slot_name}."),
            }

    # 6. Transaction dispute requires PIN authentication
    if intent == "transaction_dispute":
        return {
            "action": "need_pin",
            "intent": intent,
            "slots": slots,
        }

    # 7. All required slots present -> call bank API
    return {
        "action": "call_api",
        "intent": intent,
        "slots": slots,
    }

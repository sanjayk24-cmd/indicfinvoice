"""
backend/services/conversation.py - Multi-Turn Session & Dialogue Management Service
"""

import os
import re
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline import BankingAssistant
from backend.services.transaction_query import query_transactions
from datetime import datetime
from zoneinfo import ZoneInfo
from core.lang_id import identify_language
from mockbank.api import BANK_DB

EXPIRY_SECONDS = 300.0  # 5-minute session timeout


# Default realistic mock transactions aligned with reference UI
DEFAULT_MOCK_TRANSACTIONS = [
    {
        "date": "25 Oct 2026",
        "description": "UPI Payment",
        "amount": 500.00,
        "type": "debit",
        "status": "completed",
    },
    {
        "date": "24 Oct 2026",
        "description": "Salary Credit",
        "amount": 40000.00,
        "type": "credit",
        "status": "completed",
    },
    {
        "date": "22 Oct 2026",
        "description": "Electricity Bill",
        "amount": 1200.00,
        "type": "debit",
        "status": "completed",
    },
    {
        "date": "20 Oct 2026",
        "description": "Online Shopping",
        "amount": 2499.00,
        "type": "debit",
        "status": "completed",
    },
    {
        "date": "18 Oct 2026",
        "description": "Mobile Recharge",
        "amount": 299.00,
        "type": "debit",
        "status": "completed",
    },
]


class SessionManager:
    """
    Manages in-memory dialogue states indexed by session_id.
    Each session is isolated and automatically cleared after 5 minutes of inactivity.
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create(self, session_id: Optional[str]) -> tuple[str, Optional[Dict[str, Any]]]:
        now = time.time()
        self._cleanup(now)

        if not session_id or session_id not in self._sessions:
            new_id = session_id or str(uuid.uuid4())
            self._sessions[new_id] = {
                "pending": None,
                "last_active": now,
            }
            return new_id, None

        session = self._sessions[session_id]
        if now - session["last_active"] > EXPIRY_SECONDS:
            session["pending"] = None
        session["last_active"] = now
        return session_id, session.get("pending")

    def save(self, session_id: str, pending: Optional[Dict[str, Any]]) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["pending"] = pending
            self._sessions[session_id]["last_active"] = time.time()

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["pending"] = None
            self._sessions[session_id]["last_active"] = time.time()

    def _cleanup(self, now: float) -> None:
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data.get("last_active", 0) > (EXPIRY_SECONDS * 2)
        ]
        for sid in expired:
            del self._sessions[sid]


class ConversationService:
    """
    Integrates existing BankingAssistant with session tracking and rich UI components.
    """

    def __init__(self):
        self.assistant = BankingAssistant()
        self.session_manager = SessionManager()

    def is_transaction_query(self, text: str) -> bool:
        t = text.lower()
        keywords = [
            "transaction", "transactions", "statement", "passbook",
            "लेनदेन", "ट्रांजैक्शन", "लेन-देन", "स्टेटमेंट",
            "பரிவர்த்தனை", "பரிவர்த்தனைகள்", "ஸ்டேட்மென்ட்"
        ]
        return any(k in t for k in keywords)

    def process_message(
        self,
        message: str,
        lang: Optional[str] = None,
        session_id: Optional[str] = None,
        customer_id: str = "C001",
        pin: Optional[str] = None,
    ) -> Dict[str, Any]:
        sid, pending_state = self.session_manager.get_or_create(session_id)

        # Detect or use selected language
        detected_lang = identify_language(message)
        effective_lang = lang if lang in ("en", "hi", "ta") else detected_lang

        # Profile questions are independent of a pending balance/loan slot.
        # The demo database has no real account numbers or bank identity.
        text = message.lower().strip()
        profile_replies = {
            "account_number": {
                "en": "This demo does not store your actual account number. The XXXX number shown in the interface is a sample display, not a verified account number. Check your bank statement or banking app for your account number.",
                "hi": "इस डेमो में आपका वास्तविक खाता नंबर नहीं है। स्क्रीन पर XXXX वाला नंबर केवल नमूना है। अपना खाता नंबर बैंक स्टेटमेंट या बैंक ऐप में देखें।",
                "ta": "இந்த டெமோவில் உங்கள் உண்மையான கணக்கு எண் இல்லை. திரையில் உள்ள XXXX எண் மாதிரி மட்டுமே. உங்கள் வங்கி அறிக்கை அல்லது வங்கி செயலியில் கணக்கு எண்ணைப் பார்க்கவும்.",
            },
            "bank_name": {
                "en": "You are using IndicFinVoice, a demo banking assistant connected to MockBank. Your real bank name is not configured in this project.",
                "hi": "आप IndicFinVoice का उपयोग कर रहे हैं, जो MockBank से जुड़ा डेमो सहायक है। आपके वास्तविक बैंक का नाम इस प्रोजेक्ट में दर्ज नहीं है।",
                "ta": "நீங்கள் MockBank உடன் இணைந்த IndicFinVoice டெமோ உதவியாளரைப் பயன்படுத்துகிறீர்கள். உங்கள் உண்மையான வங்கியின் பெயர் இந்த திட்டத்தில் இல்லை.",
            },
        }
        profile_intent = None
        if any(word in text for word in ("account number", "account no", "a/c no", "खाता नंबर", "खाता संख्या", "கணக்கு எண்")):
            profile_intent = "account_number"
        elif any(word in text for word in ("bank name", "name of my bank", "which bank", "बैंक का नाम", "வங்கியின் பெயர்", "வங்கி பெயர்")):
            profile_intent = "bank_name"
        if profile_intent:
            self.session_manager.save(sid, None)
            reply = profile_replies[profile_intent][effective_lang]
            if profile_intent == 'bank_name':
                bank = BANK_DB.get(customer_id, {}).get('profile', {}).get('bank_name')
                if bank:
                    reply = {'en': f'Your synthetic demo bank is {bank} (MockBank).', 'hi': f'आपका डेमो बैंक {bank} (MockBank) है।', 'ta': f'உங்கள் டெமோ வங்கி {bank} (MockBank).'}[effective_lang]
            return {"reply": reply,
                    "intent": profile_intent, "action": "account_information",
                    "session_id": sid, "lang": effective_lang, "pending": None}

        # Check for explicit transaction history request (matching reference UI mockup)
        if self.is_transaction_query(message) and not any(word in text for word in (
            "dispute", "wrong", "unauthorized", "शिकायत", "आपत्ति", "புகார்", "சர்ச்சை"
        )):
            self.session_manager.clear(sid)
            txns = self.get_transactions(customer_id)
            try:
                txns, order = query_transactions(txns, text, datetime.now(ZoneInfo('Asia/Kolkata')).date())
            except ValueError as error:
                return {'reply': str(error), 'intent': 'transactions', 'action': 'ask',
                        'session_id': sid, 'lang': effective_lang, 'transactions': None}
            if effective_lang == "hi":
                reply = "यह आपके पिछले 5 लेनदेन हैं:\n\nWould you like to see more transactions or do you need help with anything else?"
            elif effective_lang == "ta":
                reply = "இவை உங்கள் கடந்த 5 பரிவர்த்தனைகள் ஆகும்:\n\nWould you like to see more transactions or do you need help with anything else?"
            else:
                reply = "Here are your recent transactions:\n\nWould you like to see more details or do you need help with anything else?"

            reply = {'en': f"Showing {len(txns)} matching transactions, {order}.",
                     'hi': f"{len(txns)} मिलते-जुलते लेनदेन, सबसे नए पहले।",
                     'ta': f"பொருந்தும் {len(txns)} பரிவர்த்தனைகள், புதியவை முதலில்."}[effective_lang]
            if not txns:
                reply = {"en": "No transactions match your filters for this demo customer.", "hi": "इस डेमो ग्राहक के लिए कोई लेनदेन नहीं है।", "ta": "இந்த டெமோ வாடிக்கையாளருக்கு பரிவர்த்தனைகள் இல்லை."}[effective_lang]
            return {
                "reply": reply,
                "intent": "transactions",
                "confidence": 0.98,
                "slots": {},
                "action": "show_transactions",
                "session_id": sid,
                "lang": effective_lang,
                "pending": None,
                "account_data": None,
                "transactions": txns,
            }

        if text.rstrip('!. ') in ('thank you', 'thanks', 'धन्यवाद', 'நன்றி', 'hello', 'hi', 'नमस्ते', 'வணக்கம்'):
            reply = {'en': "You’re welcome. How can I help with your banking?", 'hi': 'मैं आपकी बैंकिंग में कैसे मदद कर सकता हूँ?', 'ta': 'உங்கள் வங்கி தேவைகளுக்கு எப்படி உதவலாம்?'}[effective_lang]
            return {'reply': reply, 'intent': 'greeting', 'action': 'reply', 'session_id': sid, 'lang': effective_lang, 'pending': pending_state}

        # Run through existing NLU & Dialogue Pipeline
        pipeline_res = self.assistant.handle_text(
            text=message,
            customer_id=customer_id,
            pending=pending_state,
            pin=pin,
        )

        new_pending = pipeline_res.get("pending")
        self.session_manager.save(sid, new_pending)

        account_data = None
        # If balance check was executed, supply structured card data matching reference UI
        if pipeline_res.get("action") == "call_api" and pipeline_res.get("intent") == "balance_check":
            cust_info = BANK_DB.get(customer_id, {})
            accts = cust_info.get("accounts", {})
            acct_type = pipeline_res.get("slots", {}).get("account_type", "savings")
            bal = accts.get(acct_type, {}).get("balance", 0)
            account_data = {
                "account_type": "Savings Account" if acct_type == "savings" else "KCC Account",
                "masked_account": accts.get(acct_type, {}).get("masked_account", "Unavailable"),
                "balance": float(bal),
                "currency": "INR",
            }

        return {
            "reply": pipeline_res.get("reply", "Request processed."),
            "intent": pipeline_res.get("intent"),
            "confidence": pipeline_res.get("confidence"),
            "slots": pipeline_res.get("slots"),
            "action": pipeline_res.get("action"),
            "session_id": sid,
            "lang": effective_lang,
            "pending": new_pending,
            "account_data": account_data,
            "transactions": None,
        }

    def get_transactions(self, customer_id):
        records = BANK_DB.get(customer_id, {}).get("transactions", {})
        return [{"reference": ref, "date": txn["date"],
                 "description": txn.get("description", ref), "amount": txn["amount"],
                 "type": txn.get("type", "debit"), "status": txn.get("status", "completed")}
                for ref, txn in sorted(records.items(), key=lambda item: item[1]["date"], reverse=True)]

    def get_account_summary(self, customer_id: str = "C001") -> Dict[str, Any]:
        cust = BANK_DB.get(customer_id)
        if cust is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Customer not found")
        savings = cust.get("accounts", {}).get("savings", {})
        balance = savings.get("balance", 0)
        return {
            "customer_id": customer_id,
            "account_type": "Savings Account",
            "masked_account": savings.get("masked_account", "Unavailable"),
            "balance": float(balance),
            "currency": "INR",
            "transactions": self.get_transactions(customer_id),
        }


# Singleton conversation service instance
conversation_service = ConversationService()

"""
backend/schemas.py - Pydantic Request & Response Models for IndicFinVoice API
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User query in English, Hindi, or Tamil")
    lang: Optional[str] = Field("en", description="Selected language code: 'en', 'hi', or 'ta'")
    session_id: Optional[str] = Field(None, description="Unique session ID for multi-turn state tracking")
    customer_id: Optional[str] = Field("C001", description="Mock bank customer ID")
    pin: Optional[str] = Field(None, description="Customer PIN if required for authentication")
    voice_gender: Optional[str] = Field("female", description="Voice gender: 'female' or 'male'")
    tts_enabled: Optional[bool] = Field(True, description="Whether to synthesize speech for the reply")


class TransactionItem(BaseModel):
    reference: Optional[str] = None
    date: str
    description: str
    amount: float
    type: str  # "credit" or "debit"
    status: str = "completed"


class AccountSummaryResponse(BaseModel):
    customer_id: str
    account_type: str
    masked_account: str
    balance: float
    currency: str = "INR"
    transactions: Optional[List[TransactionItem]] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    slots: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    session_id: str
    lang: str
    pending: Optional[Dict[str, Any]] = None
    account_data: Optional[Dict[str, Any]] = None
    transactions: Optional[List[TransactionItem]] = None
    audio_base64: Optional[str] = None
    voice_persona: Optional[str] = None


class TranscribeResponse(BaseModel):
    transcript: str
    lang: str
    model_id: str
    status: str = "success"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize")
    lang: Optional[str] = Field("en", description="Language code: 'en', 'hi', or 'ta'")
    gender: Optional[str] = Field("female", description="Voice gender: 'female' or 'male'")


class HealthResponse(BaseModel):
    status: str
    service: str = "IndicFinVoice API"
    models_loaded: Dict[str, bool]
    supported_languages: List[str] = ["en", "hi", "ta"]

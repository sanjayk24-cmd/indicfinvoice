"""
backend/main.py - IndicFinVoice FastAPI Application
"""

import os
import sys
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.schemas import (
    AccountSummaryResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    TranscribeResponse,
    TTSRequest,
)
from backend.services.asr_service import asr_service
from backend.services.conversation import conversation_service
from backend.services.tts_service import synthesize_speech, synthesize_speech_base64
from mockbank.api import app as mockbank_app

app = FastAPI(
    title="IndicFinVoice API",
    description="Multilingual Voice & Text Banking Assistant API (English, Hindi, Tamil)",
    version="1.0.0",
)

# Seamlessly include mockbank routes so /balance, /loan/due, /claim/status, /dispute are live
for route in mockbank_app.routes:
    if hasattr(route, "path") and route.path not in [r.path for r in app.routes if hasattr(r, "path")]:
        app.routes.append(route)


# CORS Middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_AUDIO_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


@app.get('/demo/customers')
def demo_customers():
    from mockbank.api import BANK_DB
    return [{'id': key, 'name': value.get('profile', {}).get('name', key),
             'scenario': value.get('profile', {}).get('scenario', 'standard')}
            for key, value in BANK_DB.items()]


@app.get("/health", response_model=HealthResponse)
def health_endpoint():
    """
    Checks the status of the API and which ASR models are loaded.
    """
    return HealthResponse(
        status="ok",
        service="IndicFinVoice API",
        models_loaded=asr_service.is_loaded(),
        supported_languages=["en", "hi", "ta"],
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Processes a multi-turn text banking query across English, Hindi, or Tamil,
    and optionally synthesizes spoken audio using Microsoft Neural TTS.
    """
    if not payload.message or not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    lang = (payload.lang or "en").lower().strip()
    from mockbank.api import BANK_DB
    if (payload.customer_id or "C001") not in BANK_DB:
        raise HTTPException(status_code=404, detail="Customer not found")
    if lang not in ("auto", "en", "hi", "ta"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{payload.lang}'. Supported: 'en', 'hi', 'ta'."
        )

    try:
        res = conversation_service.process_message(
            message=payload.message.strip(),
            lang=lang,
            session_id=payload.session_id,
            customer_id=payload.customer_id or "C001",
            pin=payload.pin,
        )

        # Synthesize spoken voice output if enabled
        if payload.tts_enabled and res.get("reply"):
            audio_uri, voice_id = await synthesize_speech_base64(
                res["reply"],
                lang=res.get("lang", lang),
                gender=payload.voice_gender or "female",
            )
            res["audio_base64"] = audio_uri
            res["voice_persona"] = voice_id

        return ChatResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing dialogue: {str(e)}"
        )


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(
    file: UploadFile = File(...),
    lang: str = Form("auto"),
    model: str = Form("auto"),
):
    """
    Transcribes audio using IndicConformer (default) or Whisper.
    """
    lang = (lang or "hi").lower().strip()
    if lang not in ("auto", "en", "hi", "ta"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{lang}'. Must be 'en', 'hi', or 'ta'."
        )

    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty."
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds maximum allowed size of {MAX_AUDIO_SIZE_BYTES // (1024*1024)}MB."
        )

    try:
        res = await run_in_threadpool(asr_service.transcribe_audio_bytes, audio_bytes, lang=lang, model=model)
        return TranscribeResponse(**res)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/voice")
async def voice_endpoint(
    file: UploadFile = File(...),
    lang: str = Form("auto"),
    session_id: Optional[str] = Form(None),
    customer_id: str = Form("C001"),
    pin: Optional[str] = Form(None),
    model: str = Form("auto"),
    gender: str = Form("female"),
    tts_enabled: bool = Form(True),
):
    """
    End-to-end voice endpoint: transcribes audio using AI4Bharat IndicConformer (default),
    passes through dialogue pipeline, synthesizes speech reply, and returns transcript and audio.
    """
    lang = (lang or "hi").lower().strip()
    if lang not in ("auto", "en", "hi", "ta"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{lang}'. Must be 'en', 'hi', or 'ta'."
        )

    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty."
        )

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds {MAX_AUDIO_SIZE_BYTES // (1024*1024)}MB limit."
        )

    # 1. Transcribe audio with IndicConformer (default)
    try:
        asr_res = await run_in_threadpool(asr_service.transcribe_audio_bytes, audio_bytes, lang=lang, model=model)
        transcript = asr_res.get("transcript", "")
        effective_lang = asr_res.get("lang", lang)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ASR error: {str(e)}")

    if not transcript or not transcript.strip():
        silence_reply = {
            "en": "I could not detect any clear speech in the audio. Please speak closer to the microphone and try again.",
            "hi": "मुझे कोई स्पष्ट आवाज़ नहीं सुनाई दी। कृपया माइक्रोफ़ोन के पास आकर पुनः बोलें।",
            "ta": "தெளிவான குரல் எதுவும் கேட்கவில்லை. தயவுசெய்து மைக் அருகே வந்து மீண்டும் பேசவும்.",
        }.get(effective_lang, "मुझे कोई स्पष्ट आवाज़ नहीं सुनाई दी। कृपया माइक्रोफ़ोन के पास आकर पुनः बोलें।")

        silence_audio, silence_voice = None, None
        if tts_enabled:
            silence_audio, silence_voice = await synthesize_speech_base64(
                silence_reply,
                lang=effective_lang,
                gender=gender or "female",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "reply": silence_reply,
                "transcript": "",
                "status": asr_res.get("status", "no_speech"),
                "intent": "repeat",
                "session_id": session_id,
                "lang": effective_lang,
                "asr_model": asr_res.get("model_id", "ai4bharat/indic-conformer-600m-multilingual"),
                "audio_base64": silence_audio,
                "voice_persona": silence_voice,
            }
        )

    # 2. Process transcript in dialogue manager
    chat_res = conversation_service.process_message(
        message=transcript,
        lang=effective_lang,
        session_id=session_id,
        customer_id=customer_id,
        pin=pin,
    )
    chat_res["transcript"] = transcript
    chat_res["asr_model"] = asr_res.get("model_id", "ai4bharat/indic-conformer-600m-multilingual")

    # 3. Synthesize speech for the reply
    if tts_enabled and chat_res.get("reply"):
        audio_uri, voice_id = await synthesize_speech_base64(
            chat_res["reply"],
            lang=chat_res.get("lang", effective_lang),
            gender=gender or "female",
        )
        chat_res["audio_base64"] = audio_uri
        chat_res["voice_persona"] = voice_id

    return chat_res


@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    """
    Synthesizes arbitrary text into speech using Microsoft Neural TTS (edge-tts).
    """
    audio_bytes = await synthesize_speech(req.text, lang=req.lang or "en", gender=req.gender or "female")
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed."
        )
    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.get("/account/summary", response_model=AccountSummaryResponse)
def get_account_summary_endpoint(customer_id: str = "C001"):
    """
    Returns mock account summary for the right sidebar.
    """
    summary = conversation_service.get_account_summary(customer_id=customer_id)
    return AccountSummaryResponse(**summary)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

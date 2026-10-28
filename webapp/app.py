"""Local IndicConformer diagnostic UI. No NLU or training changes."""
import asyncio
import io
import json
import logging
import re
import shutil
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from asr.transcribe_indicconformer import load_asr

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / 'webapp/tmp'
MODEL_ID = 'ai4bharat/indic-conformer-600m-multilingual'
RMS_MIN = 0.0001
MAX_BYTES = 25 * 1024 * 1024
TIMEOUT = 30
log = logging.getLogger('conformer_webapp')
log.setLevel(logging.INFO)
(ROOT / 'logs').mkdir(exist_ok=True)
if not log.handlers:
    log.addHandler(logging.FileHandler(ROOT / 'logs/webapp.log', encoding='utf-8'))

class Problem(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status

def clean():
    TMP.mkdir(exist_ok=True)
    for file in TMP.glob('*.wav'):
        if time.time() - file.stat().st_mtime > 3600:
            file.unlink(missing_ok=True)

def decode(raw, ffmpeg):
    try:
        audio, sr = sf.read(io.BytesIO(raw), dtype='float32')
    except Exception:
        if ffmpeg:
            try:
                result = subprocess.run([ffmpeg, '-v', 'error', '-i', 'pipe:0', '-t', '31',
                    '-f', 'f32le', '-ac', '1', '-ar', '16000', 'pipe:1'], input=raw,
                    capture_output=True, timeout=20, check=True)
                audio, sr = np.frombuffer(result.stdout, dtype='<f4').copy(), 16000
            except Exception:
                raise Problem('DECODE_FAILED', 'Audio could not be decoded. Upload a WAV file.')
        else:
            try:
                import torchaudio
                tensor, sr = torchaudio.load(io.BytesIO(raw))
                audio = tensor.mean(dim=0).numpy().astype('float32')
            except Exception:
                raise Problem('DECODE_FAILED', 'Audio could not be decoded. FFmpeg is unavailable; use WAV or browser recording conversion.')
    if len(audio) / sr < 0.5 or len(audio) / sr > 30:
        raise Problem('DURATION', 'Audio must be between 0.5 and 30 seconds.')
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if sr != 16000:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    audio = np.asarray(audio, dtype=np.float32)
    if not np.isfinite(audio).all():
        raise Problem('INVALID_AUDIO', 'Audio contains invalid samples.')
    rms = float(np.sqrt(np.mean(audio * audio)))
    if rms < RMS_MIN:
        raise Problem('SILENCE', f'Audio is silent or too quiet (minimum RMS {RMS_MIN}).')
    return audio, rms

@asynccontextmanager
async def lifespan(app):
    clean()
    app.state.model = None
    app.state.ffmpeg = shutil.which('ffmpeg')
    app.state.mode = json.loads((ROOT / 'webapp/config.json').read_text())['decoding_mode']
    app.state.executor = ThreadPoolExecutor(max_workers=1)
    app.state.lock = Lock()
    app.state.assistant = None
    try:
        app.state.model = await asyncio.to_thread(load_asr, MODEL_ID)
        # This checkpoint executes float32 ONNX graphs; .half() cannot convert them.
        log.info('startup loaded mode=%s providers=%s', app.state.mode,
                 app.state.model.models['encoder'].get_providers())
    except Exception:
        log.exception('Model initialization failed')
    yield
    app.state.executor.shutdown(wait=False, cancel_futures=True)

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Problem)
async def problem_handler(request, error):
    log.info('request rejected endpoint=%s code=%s', request.url.path, error.code)
    return JSONResponse({'error_code': error.code, 'message': error.message}, status_code=error.status)

@app.exception_handler(RequestValidationError)
async def validation_handler(request, error):
    return JSONResponse({'error_code': 'INVALID_REQUEST', 'message': 'Invalid request fields.'}, status_code=400)

@app.middleware('http')
async def protect(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        log.exception('Unhandled request failure')
        return JSONResponse({'error_code':'INTERNAL_ERROR', 'message':'Request failed. See the local server log.'}, status_code=500)

@app.get('/')
def index():
    return FileResponse(ROOT / 'webapp/index.html')

@app.get('/health')
def health():
    model = app.state.model
    providers = model.models['encoder'].get_providers() if model else []
    return {'model_id': MODEL_ID, 'loaded': model is not None,
            'device': ('cuda' if 'CUDAExecutionProvider' in providers else 'cpu'),
            'preprocessor_device': str(model.d) if model else None,
            'precision': 'float32 (checkpoint ONNX inputs)', 'decoding_mode':app.state.mode,
            'ffmpeg': bool(app.state.ffmpeg), 'rms_threshold':RMS_MIN,
            'supported_languages':['hi','ta']}

def infer(audio, language):
    try:
        with torch.inference_mode():
            return app.state.model(torch.from_numpy(audio).unsqueeze(0), language, app.state.mode)
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        app.state.lock.release()

@app.post('/transcribe')
async def transcribe(request: Request):
    start = time.monotonic()
    # Bound the entire multipart request before parsing (including oversized fields).
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_BYTES + 65536:
            raise Problem('FILE_TOO_LARGE', 'Maximum audio size is 25 MB.')
    request._body = bytes(body)
    try:
        form = await request.form()
    except Exception:
        raise Problem('INVALID_REQUEST', 'Provide a multipart file and language.')
    language, upload = form.get('language'), form.get('file')
    if language not in ('en','hi','ta'):
        raise Problem('UNSUPPORTED_LANGUAGE', 'Select en, hi, or ta.')
    if language == 'en':
        raise Problem('MODEL_LANGUAGE_UNSUPPORTED', 'This IndicConformer checkpoint has no English head. Select Hindi or Tamil.')
    if upload is None or not hasattr(upload, 'read'):
        raise Problem('MISSING_FILE', 'Select an audio file.')
    raw = await upload.read(MAX_BYTES + 1)
    await upload.close()
    if len(raw) > MAX_BYTES:
        raise Problem('FILE_TOO_LARGE', 'Maximum audio size is 25 MB.')
    audio, rms = await asyncio.to_thread(decode, raw, app.state.ffmpeg)
    if app.state.model is None:
        raise Problem('MODEL_UNAVAILABLE', 'Model is not loaded. Check server startup logs.', 503)
    if not app.state.lock.acquire(blocking=False):
        raise Problem('BUSY', 'An inference is running. Please retry shortly.', 503)
    clean()
    identifier = uuid.uuid4().hex
    try:
        sf.write(TMP / f'{identifier}.wav', audio, 16000, subtype='FLOAT')
        task = app.state.executor.submit(infer, audio, language)
    except Exception:
        app.state.lock.release()
        raise
    try:
        transcript = await asyncio.wait_for(asyncio.shield(asyncio.wrap_future(task)), TIMEOUT)
    except asyncio.TimeoutError:
        # Native ONNX inference cannot safely be interrupted in a thread. Keep the
        # lock until infer() finishes; cache is freed there, not under active kernels.
        task.add_done_callback(lambda future: future.exception())
        raise Problem('INFERENCE_TIMEOUT', 'Inference exceeded 30 seconds. Retry when the model is ready.', 503)
    except torch.cuda.OutOfMemoryError:
        raise Problem('OUT_OF_MEMORY', 'GPU memory exhausted. Try a shorter recording.', 503)
    log.info('transcribe id=%s language=%s duration=%.3f rms=%.6f', identifier, language, len(audio)/16000, rms)
    return {'transcript': transcript, 'language':language, 'duration_s':len(audio)/16000,
            'rms':rms, 'sample_rate_used':16000, 'decoding_mode':app.state.mode,
            'seconds_taken':time.monotonic()-start, 'debug_audio_url':f'/debug-audio/{identifier}'}

@app.get('/debug-audio/{identifier}')
def debug_audio(identifier: str):
    clean()
    if not re.fullmatch('[0-9a-f]{32}', identifier) or not (TMP / f'{identifier}.wav').exists():
        raise Problem('NOT_FOUND', 'Debug recording expired or does not exist.', 404)
    return FileResponse(TMP / f'{identifier}.wav', media_type='audio/wav')

@app.post('/assist')
async def assist(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise Problem('INVALID_REQUEST', 'Provide a JSON request.')
    if not isinstance(data, dict) or not isinstance(data.get('transcript'), str) or not data['transcript'].strip():
        raise Problem('INVALID_TEXT', 'Transcript text is required.')
    if len(data['transcript']) > 4000 or not isinstance(data.get('customer_id'), str):
        raise Problem('INVALID_REQUEST', 'Provide a customer ID and at most 4000 text characters.')
    pin = data.get('pin')
    if pin is not None and not isinstance(pin, str):
        raise Problem('INVALID_PIN', 'PIN must be typed as text.')
    # Only this separate explicit text field is passed as PIN, never ASR output.
    def run():
        from pipeline import BankingAssistant
        from mockbank.api import BANK_DB
        if data['customer_id'] not in BANK_DB:
            raise Problem('UNKNOWN_CUSTOMER', 'Unknown demo customer.')
        if app.state.assistant is None:
            app.state.assistant = BankingAssistant()
        return app.state.assistant.handle_text(data['transcript'], customer_id=data['customer_id'], pin=pin)
    result = await asyncio.to_thread(run)
    return {key: result.get(key) for key in ('reply','intent','slots','action')}

"""Fixed-setting diagnostics. Writes logs only, not eval/results."""
import io
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import soundfile as sf
import librosa
from fastapi.testclient import TestClient
from asr.transcribe import normalise_text
from webapp.app import app, decode

def wav(audio, sr):
    stream = io.BytesIO(); sf.write(stream, audio, sr, format='WAV', subtype='FLOAT')
    return stream.getvalue()

def main():
    lines = []
    def check(label, passed, detail=''):
        line = f'{"PASS" if passed else "FAIL"} {label}: {detail}'
        lines.append(line); print(line, flush=True)
    source = ROOT / 'data/raw/speech/indicvoices/hi/hi_005.wav'
    raw = source.read_bytes()
    audio, sr = sf.read(source, dtype='float32')
    records = [json.loads(line) for line in (ROOT/'logs/conformer_offline_check.txt').read_text(encoding='utf-8').splitlines()]
    baseline = next(r for r in records if r.get('clip')=='hi_005.wav')
    with TestClient(app, raise_server_exceptions=False) as client:
        check('health loaded', client.get('/health').json()['loaded'], json.dumps(client.get('/health').json()))
        def post(content=raw, language='hi'):
            return client.post('/transcribe', files={'file':('clip.wav',content)}, data={'language':language})
        # STEP 2: current old endpoint, explicit IndicConformer, no old-app edits.
        from backend.main import app as old_app
        from backend.services.asr_service import asr_service
        asr_service._indic_pipe = app.state.model
        with TestClient(old_app) as old:
            old_response = old.post('/transcribe', files={'file':('hi_005.wav',raw,'audio/wav')}, data={'lang':'hi','model':'indicconformer'})
        info = sf.info(io.BytesIO(raw))
        received = {'container':info.format, 'codec':info.subtype, 'sample_rate':sr,
                    'channels':info.channels, 'duration':len(audio)/sr,
                    'rms':float(np.sqrt(np.mean(audio**2)))}
        old_hyp = old_response.json().get('transcript','')
        similarity = SequenceMatcher(None,normalise_text(old_hyp),normalise_text(baseline['rnnt']['hyp'])).ratio()
        check('old upload path vs offline RNNT', old_response.status_code==200 and similarity>=.95,
              json.dumps({'received':received,'hyp':old_hyp,'offline':baseline['rnnt']['hyp'],'similarity':similarity},ensure_ascii=False))
        lines.append('STEP 2 conclusion: inconclusive — unchanged uploaded WAV reaches the old route; upload transcript compared above; old service peak-normalizes before inference. Live microphone/Bluetooth capture was not reproduced.')
        response = post(); result=response.json()
        check('known WAV equals offline CTC', response.status_code==200 and result.get('transcript')==baseline['ctc']['hyp'], json.dumps(result,ensure_ascii=False))
        if response.status_code==200:
            heard = client.get(result['debug_audio_url'])
            processed, rate = sf.read(io.BytesIO(heard.content),dtype='float32')
            check('debug playback preserves waveform', rate==16000 and np.allclose(processed,audio,atol=1e-6))
        for rate, channels in [(44100,2),(48000,1)]:
            converted=librosa.resample(audio,orig_sr=sr,target_sr=rate)
            if channels==2: converted=np.column_stack([converted,converted])
            res=post(wav(converted,rate)); hyp=res.json().get('transcript','')
            similarity=SequenceMatcher(None,normalise_text(hyp),normalise_text(baseline['ctc']['hyp'])).ratio()
            check(f'{rate}Hz {channels}ch',res.status_code==200 and similarity>=.90,f'similarity={similarity:.4f}')
        ffmpeg=app.state.ffmpeg
        if ffmpeg:
            import subprocess
            encoded=subprocess.run([ffmpeg,'-v','error','-i','pipe:0','-f','webm','-c:a','libopus','pipe:1'],input=raw,capture_output=True,check=True).stdout
            res=post(encoded); similarity=SequenceMatcher(None,normalise_text(res.json().get('transcript','')),normalise_text(baseline['ctc']['hyp'])).ratio()
            check('WebM/Opus',res.status_code==200 and similarity>=.90,f'similarity={similarity:.4f}')
        else:
            check('WebM/Opus','' == 'unavailable','Not executed: no FFmpeg encoder installed; compressed input decoder support is environment-dependent.')
        for name,content,lang in [('silence',wav(np.zeros(16000),16000),'hi'),('short',wav(np.ones(3200)*.1,16000),'hi'),
             ('long',wav(np.ones(640000)*.1,16000),'hi'),('bad language',raw,'xx'),('English',raw,'en'),('non-audio',b'not audio','hi'),('oversize',b'x'*(25*1024*1024+1),'hi')]:
            res=post(content,lang)
            check(name,res.status_code==400 and set(res.json())=={'error_code','message'},str(res.json()))
        with ThreadPoolExecutor(max_workers=5) as pool:
            responses=list(pool.map(lambda _:post(),range(5)))
        check('5 parallel requests',all(r.status_code in (200,503) for r in responses) and any(r.status_code==200 for r in responses),str([r.status_code for r in responses]))
        with patch('webapp.app.decode',side_effect=RuntimeError('forced diagnostic error')):
            forced=post()
        check('forced error sanitized',forced.status_code==500 and set(forced.json())=={'error_code','message'})
        check('recovers after forced error',post().status_code==200)
        pin='DIAGNOSTIC_PIN_SENTINEL'
        client.post('/assist',json={'transcript':'my savings balance','customer_id':'C001','pin':pin})
        log=(ROOT/'logs/webapp.log').read_text(encoding='utf-8')
        check('log excludes PIN/audio',pin not in log and 'RIFF' not in log and "b'" not in log)
    (ROOT/'logs/webapp_checks.txt').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()

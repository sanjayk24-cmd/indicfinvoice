"""Bounded diagnostic, not a full-manifest evaluation. Writes only logs/."""
import csv
import json
import sys
from pathlib import Path
from difflib import SequenceMatcher
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import soundfile as sf
import torch
from asr.transcribe import normalise_text
from asr.transcribe_indicconformer import load_asr

MODEL_ID = 'ai4bharat/indic-conformer-600m-multilingual'

def main():
    (ROOT / 'logs').mkdir(exist_ok=True)
    with (ROOT / 'logs/conformer_offline_check.txt').open('w', encoding='utf-8') as log:
        def emit(record):
            line = json.dumps(record, ensure_ascii=False)
            print(line, flush=True)
            log.write(line + '\n'); log.flush()
        model = load_asr(MODEL_ID)
        emit({'model': MODEL_ID, 'device': str(model.d),
              'encoder_providers': model.models['encoder'].get_providers(),
              'precision': 'float32 ONNX graph; not converted to fp16'})
        scores = {}
        for lang in ('hi', 'ta'):
            with (ROOT / f'data/raw/speech/indicvoices/{lang}_index.csv').open(encoding='utf-8-sig') as f:
                rows = list(csv.DictReader(f))[:20]
            assert len(rows) == 20
            for row in rows:
                path = ROOT / 'data/raw/speech' / row['path']
                audio, sr = sf.read(path, dtype='float32')
                assert sr == 16000 and audio.ndim == 1 and str(audio.dtype) == 'float32', path
                result = {'clip': path.name, 'lang': lang, 'ref': row['ref']}
                for mode in ('ctc', 'rnnt'):
                    with torch.inference_mode():
                        hyp = model(torch.from_numpy(audio).unsqueeze(0), lang, mode)
                    score = SequenceMatcher(None, normalise_text(row['ref']), normalise_text(hyp)).ratio()
                    result[mode] = {'hyp': hyp, 'similarity': score}
                    scores.setdefault((lang, mode), []).append(score)
                emit(result)
        means = {f'{lang}/{mode}': mean(values) for (lang, mode), values in scores.items()}
        selected = max(('ctc', 'rnnt'), key=lambda mode: mean(means[f'{lang}/{mode}'] for lang in ('hi', 'ta')))
        emit({'means': means, 'selected': selected, 'criterion': 'macro mean across hi and ta; CTC wins exact ties'})

if __name__ == '__main__':
    main()

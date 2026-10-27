import os
import sys
import random
import unicodedata
import pandas as pd
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit import IndicProcessor

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

INPUT_CSV = "data/external/banking77_en_mapped.csv"
OUTPUT_HI_CSV = "data/external/banking77_hi.csv"
OUTPUT_TA_CSV = "data/external/banking77_ta.csv"
MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
TRANSLATION_DATE = "2026-10-25"

BATCH_SIZE = 16
NUM_BEAMS = 5
MAX_LENGTH = 256

def is_target_script(c, lang):
    code = ord(c)
    if lang == 'hi':
        return 0x0900 <= code <= 0x097F
    elif lang == 'ta':
        return 0x0B80 <= code <= 0x0BFF
    return False

def check_script_percentage(text, lang):
    # Total letters: alphabetic characters or characters in the script range (including combining marks)
    letters = [c for c in text if c.isalpha() or is_target_script(c, lang)]
    if not letters:
        return 0.0
    target_letters = [c for c in letters if is_target_script(c, lang)]
    return len(target_letters) / len(letters)

def run_translation(df, target_lang, target_code, model, tokenizer, ip):
    print(f"\n--- Translating to {target_lang} ({target_code}) ---")
    translations = []
    texts = df['text'].tolist()
    total = len(texts)
    
    for i in range(0, total, BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_pre = ip.preprocess_batch(batch_texts, src_lang="eng_Latn", tgt_lang=target_code, visualize=False)
        inputs = tokenizer(batch_pre, padding="longest", truncation=True, max_length=MAX_LENGTH, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            outputs = model.generate(**inputs, num_beams=NUM_BEAMS, max_length=MAX_LENGTH)
        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        batch_post = ip.postprocess_batch(decoded, lang=target_code)
        translations.extend(batch_post)
        if (i // BATCH_SIZE + 1) % 5 == 0 or (i + BATCH_SIZE) >= total:
            print(f"Processed {min(i + BATCH_SIZE, total)} / {total} rows")
            
    assert len(translations) == total, f"Expected {total} translations, got {len(translations)}"
    return translations

def perform_checks(df_result, df_en, lang):
    print(f"\n==========================================")
    print(f"Automatic Checks for {lang.upper()}:")
    print(f"==========================================")
    
    flagged = {
        'row_count_or_id_mismatch': [],
        'empty_translation': [],
        'identical_to_english': [],
        'script_under_60_percent': [],
        'length_ratio_out_of_bounds': []
    }
    
    # 1. Row count and IDs match
    if len(df_result) != 664:
        flagged['row_count_or_id_mismatch'].append(f"Row count is {len(df_result)}, expected 664")
    if list(df_result['id']) != list(df_en['id']):
        mismatched_ids = [f"{r_id} != {e_id}" for r_id, e_id in zip(df_result['id'], df_en['id']) if r_id != e_id]
        flagged['row_count_or_id_mismatch'].extend(mismatched_ids)
        
    for idx, row in df_result.iterrows():
        r_id = row['id']
        trans = str(row['text']) if pd.notna(row['text']) else ""
        eng = str(row['text_en']) if pd.notna(row['text_en']) else ""
        
        # 2. No empty translation
        if len(trans.strip()) == 0:
            flagged['empty_translation'].append((r_id, eng, trans))
            
        # 3. Differs from English source
        if trans.strip() == eng.strip():
            flagged['identical_to_english'].append((r_id, eng, trans))
            
        # 4. At least 60% of letters are in target script
        script_pct = check_script_percentage(trans, lang)
        if script_pct < 0.60:
            flagged['script_under_60_percent'].append((r_id, f"{script_pct:.1%}", eng, trans))
            
        # 5. Length ratio between 0.4 and 3.0
        len_trans = len(trans)
        len_eng = len(eng)
        ratio = (len_trans / len_eng) if len_eng > 0 else 0
        if ratio < 0.4 or ratio > 3.0:
            flagged['length_ratio_out_of_bounds'].append((r_id, f"{ratio:.2f}", eng, trans))

    # Print summary counts
    print(f"Total rows evaluated: {len(df_result)}")
    print(f"Row count == 664 and IDs match English exactly: {'PASS' if not flagged['row_count_or_id_mismatch'] else 'FAIL'}")
    print(f"Empty translations: {len(flagged['empty_translation'])}")
    print(f"Identical to English: {len(flagged['identical_to_english'])}")
    print(f"Script percentage < 60%: {len(flagged['script_under_60_percent'])}")
    print(f"Length ratio out of bounds (<0.4 or >3.0): {len(flagged['length_ratio_out_of_bounds'])}")
    
    # List flagged rows if any
    for check_name, items in flagged.items():
        if items:
            print(f"\n--- Flagged rows for {check_name} (Count: {len(items)}) ---")
            for item in items:
                print(item)
        else:
            print(f"Flagged rows for {check_name}: None")

def sample_and_print(df_result, lang_name, n=15, seed=42):
    print(f"\n==========================================")
    print(f"15 Sample Rows for {lang_name} (id | English | translation):")
    print(f"==========================================")
    random.seed(seed)
    indices = sorted(random.sample(range(len(df_result)), n))
    for idx in indices:
        row = df_result.iloc[idx]
        print(f"{row['id']} | {row['text_en']} | {row['text']}")

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} does not exist.")
        sys.exit(1)
        
    df_en = pd.read_csv(INPUT_CSV, encoding='utf-8')
    if len(df_en) != 664:
        print(f"Error: Expected 664 rows, found {len(df_en)}.")
        sys.exit(1)
    print(f"Successfully loaded {INPUT_CSV} with {len(df_en)} rows.")

    print(f"Loading model {MODEL_NAME} and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        torch_dtype=torch.float16
    ).to("cuda")
    print("Model and tokenizer loaded onto CUDA fp16.")

    ip = IndicProcessor(inference=True)

    # 1. Hindi Translation
    hi_translations = run_translation(df_en, "Hindi", "hin_Deva", model, tokenizer, ip)
    df_hi = pd.DataFrame({
        'id': df_en['id'],
        'text': hi_translations,
        'text_en': df_en['text'],
        'source_label': df_en['source_label'],
        'intent': df_en['intent'],
        'sensitive': df_en['sensitive'],
        'split': df_en['split'],
        'lang': 'hi',
        'translation_model': MODEL_NAME,
        'translation_date': TRANSLATION_DATE
    })
    df_hi.to_csv(OUTPUT_HI_CSV, index=False, encoding='utf-8')
    print(f"Saved Hindi translations to {OUTPUT_HI_CSV}")

    # 2. Tamil Translation
    ta_translations = run_translation(df_en, "Tamil", "tam_Taml", model, tokenizer, ip)
    df_ta = pd.DataFrame({
        'id': df_en['id'],
        'text': ta_translations,
        'text_en': df_en['text'],
        'source_label': df_en['source_label'],
        'intent': df_en['intent'],
        'sensitive': df_en['sensitive'],
        'split': df_en['split'],
        'lang': 'ta',
        'translation_model': MODEL_NAME,
        'translation_date': TRANSLATION_DATE
    })
    df_ta.to_csv(OUTPUT_TA_CSV, index=False, encoding='utf-8')
    print(f"Saved Tamil translations to {OUTPUT_TA_CSV}")

    # 3. Automatic Checks
    perform_checks(df_hi, df_en, 'hi')
    perform_checks(df_ta, df_en, 'ta')

    # 4. Print 15 samples per language
    sample_and_print(df_hi, "Hindi", n=15, seed=42)
    sample_and_print(df_ta, "Tamil", n=15, seed=42)

if __name__ == '__main__':
    main()

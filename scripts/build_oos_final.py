import os
import sys
import json
import re
import regex
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CANDIDATES_CSV = "data/splits/oos_candidates_massive.csv"
FINAL_CSV = "data/splits/oos_final_massive.csv"
HELDOUT_JSONL = "data/splits/oos_heldout.jsonl"
REVIEW_LOG_CSV = "data/splits/oos_review_log.csv"

HI_BANKING_WORDS = [
    'बैंक', 'खाता', 'खाते', 'कार्ड', 'लोन', 'ऋण', 'भुगतान', 'पैसे', 'पैसा', 'रुपये', 'रुपए', 'रुपया', 
    'कीमत', 'दाम', 'खर्च', 'बैलेंस', 'लेनदेन', 'ट्रांसफर', 'बीमा', 'बिल', 'पे', 'भुगतान करो', 
    'खरीद', 'खरीदो', 'बेच', 'दुकान', 'टैक्स', 'वेतन'
]

TA_BANKING_WORDS = [
    'வங்கி', 'கணக்கு', 'அட்டை', 'கடன்', 'பணம்', 'ரூபாய்', 'கட்டணம்', 'விலை', 'செலவு', 
    'பரிவர்த்தனை', 'பரிமாற்ற', 'காப்பீடு', 'பில்', 'வாங்க', 'விற்க', 'கடை', 'வரி', 'சம்பளம்'
]

EN_BANKING_WORDS = [
    'bank', 'account', 'card', 'loan', 'debt', 'payment', 'money', 'cash', 'rupee', 'price',
    'cost', 'expense', 'balance', 'transaction', 'transfer', 'insurance', 'bill', 'pay',
    'purchase', 'buy', 'sell', 'shop', 'tax', 'salary'
]

def main():
    print("STEP 1: Reading data/splits/oos_candidates_massive.csv...")
    if not os.path.exists(CANDIDATES_CSV):
        print(f"ERROR: {CANDIDATES_CSV} does not exist!")
        sys.exit(1)

    df_cand = pd.read_csv(CANDIDATES_CSV, encoding='utf-8')
    total_cand = len(df_cand)
    hi_cand = len(df_cand[df_cand['lang'] == 'hi'])
    ta_cand = len(df_cand[df_cand['lang'] == 'ta'])
    en_cand = len(df_cand[df_cand['lang'] == 'en'])
    print(f"Total candidates: {total_cand} (Expected: 90)")
    print(f"  hi: {hi_cand} (Expected: 30)")
    print(f"  ta: {ta_cand} (Expected: 30)")
    print(f"  en: {en_cand} (Expected: 30)")

    if total_cand != 90 or hi_cand != 30 or ta_cand != 30 or en_cand != 30:
        print("ERROR: Candidates count mismatch! Stopping.")
        sys.exit(1)

    # Index by (lang, draw_order)
    cand_map = {}
    for _, row in df_cand.iterrows():
        cand_map[(row['lang'], int(row['draw_order']))] = row

    print("\nSTEP 2 & 3: Building final out-of-scope rows and verifying massive_ids...")
    # Hindi draws: 1-6, 8-12, 14, 15, 16 (replaces 7), 18 (replaces 13)
    hi_draws = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 18]
    # Tamil draws: 1-15
    ta_draws = list(range(1, 16))
    # English draws: 1-15
    en_draws = list(range(1, 16))

    final_records = []

    # 1. Hindi
    print("Verifying Hindi final rows...")
    for d in hi_draws:
        if ('hi', d) not in cand_map:
            print(f"ERROR: Hindi draw {d} not found in candidates!")
            sys.exit(1)
        r = cand_map[('hi', d)]
        final_records.append({
            'lang': 'hi',
            'draw_order': d,
            'massive_id': str(r['massive_id']),
            'intent': 'out_of_scope',
            'massive_intent': r['intent'],
            'text': r['text'],
            'source_config': r['source_config'],
            'source_split': r['source_split']
        })

    # 2. Tamil
    print("Verifying Tamil final rows...")
    for d in ta_draws:
        if ('ta', d) not in cand_map:
            print(f"ERROR: Tamil draw {d} not found in candidates!")
            sys.exit(1)
        r = cand_map[('ta', d)]
        final_records.append({
            'lang': 'ta',
            'draw_order': d,
            'massive_id': str(r['massive_id']),
            'intent': 'out_of_scope',
            'massive_intent': r['intent'],
            'text': r['text'],
            'source_config': r['source_config'],
            'source_split': r['source_split']
        })

    # 3. English
    print("Verifying English final rows...")
    for d in en_draws:
        if ('en', d) not in cand_map:
            print(f"ERROR: English draw {d} not found in candidates!")
            sys.exit(1)
        r = cand_map[('en', d)]
        final_records.append({
            'lang': 'en',
            'draw_order': d,
            'massive_id': str(r['massive_id']),
            'intent': 'out_of_scope',
            'massive_intent': r['intent'],
            'text': r['text'],
            'source_config': r['source_config'],
            'source_split': r['source_split']
        })

    print(f"All 45 final candidate rows successfully verified against candidates CSV.")

    # STEP 4: Write data/splits/oos_final_massive.csv
    print(f"\nSTEP 4: Writing {FINAL_CSV}...")
    df_final = pd.DataFrame(final_records)
    cols_csv = ['lang', 'massive_id', 'intent', 'text', 'source_config', 'source_split', 'massive_intent']
    df_final_csv = df_final[cols_csv]
    df_final_csv.to_csv(FINAL_CSV, index=False, encoding='utf-8')
    print(f"Saved {len(df_final_csv)} rows to {FINAL_CSV} (UTF-8, no BOM).")

    # STEP 5: Write data/splits/oos_heldout.jsonl
    print(f"\nSTEP 5: Writing {HELDOUT_JSONL}...")
    with open(HELDOUT_JSONL, 'w', encoding='utf-8') as f_out:
        for r in final_records:
            tokens = r['text'].split()
            tags = ["O"] * len(tokens)
            item = {
                "tokens": tokens,
                "tags": tags,
                "intent": "out_of_scope",
                "lang": r['lang'],
                "template_id": "heldout",
                "massive_id": r['massive_id']
            }
            f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Saved {len(final_records)} JSON objects to {HELDOUT_JSONL} (UTF-8).")

    # STEP 6: Write/append removal and replacement log to data/splits/oos_review_log.csv
    print(f"\nSTEP 6: Updating {REVIEW_LOG_CSV}...")
    df_log_existing = pd.read_csv(REVIEW_LOG_CSV, encoding='utf-8')
    # Keep non-en rows if already present
    df_log_base = df_log_existing[df_log_existing['lang'] != 'en']

    en_log_rows = []
    for d in en_draws:
        r = cand_map[('en', d)]
        en_log_rows.append({
            'lang': 'en',
            'action': 'confirmed',
            'draw_order': d,
            'massive_id': r['massive_id'],
            'text': r['text'],
            'reason': 'author review, no removals',
            'replacement_draw_order': '',
            'replacement_massive_id': '',
            'reviewer': 'author review'
        })
    df_en_log = pd.DataFrame(en_log_rows)
    df_log_all = pd.concat([df_log_base, df_en_log], ignore_index=True)
    df_log_all.to_csv(REVIEW_LOG_CSV, index=False, encoding='utf-8')
    print(f"Updated {REVIEW_LOG_CSV}: {len(df_log_all)} total log entries ({len(df_log_base)} hi changes, {len(df_en_log)} en confirmations).")

    # STEP 8: Checks
    print("\n" + "=" * 80)
    print("STEP 8: Check Evaluations")
    print("=" * 80)

    # Check 1: 45 rows in oos_final_massive.csv, 15 per language
    df_chk = pd.read_csv(FINAL_CSV, encoding='utf-8')
    hi_final_count = len(df_chk[df_chk['lang'] == 'hi'])
    ta_final_count = len(df_chk[df_chk['lang'] == 'ta'])
    en_final_count = len(df_chk[df_chk['lang'] == 'en'])
    c1 = (len(df_chk) == 45 and hi_final_count == 15 and ta_final_count == 15 and en_final_count == 15)
    print(f"- 45 rows in oos_final_massive.csv, 15 per language: {'PASS' if c1 else 'FAIL'} (hi: {hi_final_count}, ta: {ta_final_count}, en: {en_final_count}, total: {len(df_chk)})")

    # Check 2: duplicate massive_id checks
    # Within each language:
    hi_dup = len(df_chk[df_chk['lang']=='hi']['massive_id']) == len(set(df_chk[df_chk['lang']=='hi']['massive_id']))
    ta_dup = len(df_chk[df_chk['lang']=='ta']['massive_id']) == len(set(df_chk[df_chk['lang']=='ta']['massive_id']))
    en_dup = len(df_chk[df_chk['lang']=='en']['massive_id']) == len(set(df_chk[df_chk['lang']=='en']['massive_id']))
    c2_within = hi_dup and ta_dup and en_dup

    # Across entire file:
    unique_ids_total = len(set(df_chk['massive_id']))
    c2_across = (unique_ids_total == 45)
    # Note on parallel corpus: MASSIVE has shared IDs across parallel locales (e.g. ID 250 in hi, ta, en)
    if c2_within and not c2_across:
        print(f"- no duplicate massive_id within each language: PASS (15 unique per language)")
        print(f"- distinct massive_ids across entire file: {unique_ids_total}/45 (Shared IDs exist due to MASSIVE parallel translations across locales: e.g. ID 250, 297)")
    else:
        print(f"- no duplicate massive_id across the file: {'PASS' if c2_across else 'FAIL'}")

    # Check 3: every row has intent out_of_scope and all tags O
    c3_intents = all(r['intent'] == 'out_of_scope' for r in final_records)
    jsonl_lines = []
    with open(HELDOUT_JSONL, 'r', encoding='utf-8') as f_in:
        for line in f_in:
            if line.strip():
                jsonl_lines.append(json.loads(line))
    c3_tags = all(all(tag == 'O' for tag in j['tags']) for j in jsonl_lines)
    c3_jsonl_intent = all(j['intent'] == 'out_of_scope' for j in jsonl_lines)
    c3 = c3_intents and c3_tags and c3_jsonl_intent
    print(f"- every row has intent out_of_scope and all tags O: {'PASS' if c3 else 'FAIL'}")

    # Check 4: no row contains a word from the banking/money lists
    bpat_hi = regex.compile(r'(?<![\p{L}\p{M}])(?:' + '|'.join(regex.escape(w) for w in sorted(HI_BANKING_WORDS, key=len, reverse=True)) + r')(?![\p{L}\p{M}])', regex.IGNORECASE)
    bpat_ta = regex.compile(r'(?<![\p{L}\p{M}])(?:' + '|'.join(regex.escape(w) for w in sorted(TA_BANKING_WORDS, key=len, reverse=True)) + r')(?![\p{L}\p{M}])', regex.IGNORECASE)
    bpat_en = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(w) for w in sorted(EN_BANKING_WORDS, key=len, reverse=True)) + r')(?!\w)', re.IGNORECASE)

    banking_hits = []
    for r in final_records:
        txt = r['text']
        lang = r['lang']
        if lang == 'hi' and bpat_hi.search(txt):
            banking_hits.append((lang, r['massive_id'], bpat_hi.search(txt).group(0), txt))
        elif lang == 'ta' and bpat_ta.search(txt):
            banking_hits.append((lang, r['massive_id'], bpat_ta.search(txt).group(0), txt))
        elif lang == 'en' and bpat_en.search(txt):
            banking_hits.append((lang, r['massive_id'], bpat_en.search(txt).group(0), txt))

    c4 = (len(banking_hits) == 0)
    print(f"- no row contains a word from the banking/money lists: {'PASS' if c4 else 'FAIL'}")
    if banking_hits:
        for hit in banking_hits:
            print(f"   [HIT in {hit[0]} | massive_id {hit[1]} | word '{hit[2]}' | text '{hit[3]}']")

    # Check 5: oos_heldout.jsonl has 45 lines, each valid JSON
    c5 = (len(jsonl_lines) == 45)
    print(f"- oos_heldout.jsonl has 45 lines, each valid JSON: {'PASS' if c5 else 'FAIL'} (Line count: {len(jsonl_lines)})")

    # STEP 9: Print the 45 final text rows grouped by language
    print("\n" + "=" * 80)
    print("45 FINAL OUT-OF-SCOPE TEXT ROWS (grouped by language):")
    print("=" * 80)

    for lang_code, lang_name in [('hi', 'HINDI (hi)'), ('ta', 'TAMIL (ta)'), ('en', 'ENGLISH (en)')]:
        print(f"\n--- {lang_name} (15 rows) ---")
        lang_rows = [r for r in final_records if r['lang'] == lang_code]
        for i, r in enumerate(lang_rows, start=1):
            print(f"{i} | massive_id: {r['massive_id']} | massive_intent: {r['massive_intent']} | text: {r['text']}")

if __name__ == '__main__':
    main()

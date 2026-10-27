import os
import sys
import re
import random
import pandas as pd
from datasets import load_dataset
from collections import Counter

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_CSV = "data/splits/oos_candidates_massive.csv"

HI_BANKING_WORDS = [
    'बैंक', 'खाता', 'खाते', 'कार्ड', 'लोन', 'ऋण', 'भुगतान', 'पैसे', 'पैसा', 'रुपये', 'रुपए', 'रुपया', 
    'कीमत', 'दाम', 'खर्च', 'बैलेंस', 'लेनदेन', 'ट्रांसफर', 'बीमा', 'बिल', 'पे', 'भुगतान करो', 
    'खरीद', 'खरीदो', 'बेच', 'दुकान', 'टैक्स', 'वेतन'
]

TA_BANKING_WORDS = [
    'வங்கி', 'கணக்கு', 'அட்டை', 'கடன்', 'பணம்', 'ரூபாய்', 'கட்டணம்', 'விலை', 'செலவு', 
    'பரிவர்த்தனை', 'பரிமாற்ற', 'காப்பீடு', 'பில்', 'வாங்க', 'விற்க', 'கடை', 'வரி', 'சம்பளம்'
]

TARGET_INTENTS = ['weather_query', 'play_music', 'alarm_set', 'general_greet']

def get_word_pattern(word_list):
    # Sort descending by length so longer multi-word phrases match first
    sorted_words = sorted(word_list, key=len, reverse=True)
    patterns = [r'(?<!\w)' + re.escape(w) + r'(?!\w)' for w in sorted_words]
    return re.compile('|'.join(patterns), re.IGNORECASE)

def process_config(config_name, lang_code, banking_words):
    print(f"\n=================================================================")
    print(f"STEP 1: Loading AmazonScience/massive for config={config_name}, split='test'")
    print(f"=================================================================")
    ds = load_dataset('AmazonScience/massive', config_name, split='test', trust_remote_code=True)
    row_count = len(ds)
    print(f"Total row count for {config_name}: {row_count}")
    
    intent_feature = ds.features['intent']
    intent_names = intent_feature.names
    print(f"\nFull list of intent names for {config_name} (Count: {len(intent_names)}):")
    print(", ".join(intent_names))
    
    # Check required intents
    for ti in TARGET_INTENTS:
        if ti not in intent_names:
            print(f"ERROR: Required intent '{ti}' is missing from {config_name}!")
            sys.exit(1)
    print(f"\nAll 4 required intents {TARGET_INTENTS} are present in {config_name}.")

    print(f"\n=================================================================")
    print(f"STEP 2: Filter for target intents in {config_name}")
    print(f"=================================================================")
    target_rows = []
    for r in ds:
        name = intent_feature.int2str(r['intent'])
        if name in TARGET_INTENTS:
            target_rows.append({
                'id': r['id'],
                'intent': name,
                'utt': r['utt'],
                'source_config': config_name,
                'source_split': 'test'
            })
            
    print(f"Total rows matching target intents in {config_name}: {len(target_rows)}")
    intent_counts = Counter(r['intent'] for r in target_rows)
    for ti in TARGET_INTENTS:
        print(f"  {ti}: {intent_counts[ti]}")

    print(f"\n=================================================================")
    print(f"STEP 3: Apply exclusion rules in {config_name}")
    print(f"=================================================================")
    banking_regex = get_word_pattern(banking_words)
    
    removed_3a = []
    removed_3b = []
    removed_3c = []
    
    for r in target_rows:
        text = r['utt']
        # 3a. containing a digit
        if re.search(r'\d', text):
            removed_3a.append(r)
        # 3b. fewer than 3 or more than 15 words
        words = text.split()
        if len(words) < 3 or len(words) > 15:
            removed_3b.append((r, len(words)))
        # 3c. containing banking words
        m = banking_regex.search(text)
        if m:
            removed_3c.append((r, m.group(0)))

    print(f"\nRule 3a - Exclude containing digit: {len(removed_3a)} rows removed")
    for r in removed_3a:
        print(f"  [3a ID {r['id']} | {r['intent']}]: {r['utt']}")

    print(f"\nRule 3b - Exclude <3 or >15 words: {len(removed_3b)} rows removed")
    for r, wcount in removed_3b:
        print(f"  [3b ID {r['id']} | words={wcount} | {r['intent']}]: {r['utt']}")

    print(f"\nRule 3c - Exclude banking/money words: {len(removed_3c)} rows removed")
    for r, match_word in removed_3c:
        print(f"  [3c ID {r['id']} | matched='{match_word}' | {r['intent']}]: {r['utt']}")

    # Apply combined exclusions
    remaining_rows = []
    for r in target_rows:
        text = r['utt']
        if re.search(r'\d', text):
            continue
        words = text.split()
        if len(words) < 3 or len(words) > 15:
            continue
        if banking_regex.search(text):
            continue
        remaining_rows.append(r)

    print(f"\nRemaining rows after all 3 exclusion rules for {config_name}: {len(remaining_rows)}")
    rem_counts = Counter(r['intent'] for r in remaining_rows)
    for ti in TARGET_INTENTS:
        print(f"  {ti}: {rem_counts[ti]}")

    print(f"\n=================================================================")
    print(f"STEP 4: Draw 30 rows using random.Random(42).sample for {config_name}")
    print(f"=================================================================")
    rng = random.Random(42)
    sampled_30 = rng.sample(remaining_rows, 30)

    sampled_records = []
    for idx, r in enumerate(sampled_30, start=1):
        role = "primary" if idx <= 15 else "reserve"
        sampled_records.append({
            'lang': lang_code,
            'role': role,
            'draw_order': idx,
            'massive_id': r['id'],
            'intent': r['intent'],
            'text': r['utt'],
            'source_config': config_name,
            'source_split': 'test'
        })
        
    return {
        'row_count': row_count,
        'intent_names': intent_names,
        'target_rows': target_rows,
        'intent_counts': intent_counts,
        'removed_3a': removed_3a,
        'removed_3b': removed_3b,
        'removed_3c': removed_3c,
        'remaining_rows': remaining_rows,
        'rem_counts': rem_counts,
        'sampled_records': sampled_records
    }

def check_inflected_banking_words(text, banking_words):
    flags = []
    # Check if any banking word root appears as a substring inside any token
    for bw in banking_words:
        if bw in text:
            # Check if it was NOT matched as a standalone word (or even if it was, flag the exact form)
            # Find the token containing bw
            for token in text.split():
                if bw in token and token != bw:
                    flags.append((bw, token))
    return flags

def main():
    hi_result = process_config('hi-IN', 'hi', HI_BANKING_WORDS)
    ta_result = process_config('ta-IN', 'ta', TA_BANKING_WORDS)

    # Combine into CSV
    all_records = hi_result['sampled_records'] + ta_result['sampled_records']
    df_out = pd.DataFrame(all_records)
    
    # Ensure columns match specification:
    # lang, role, draw_order, massive_id, intent, text, source_config, source_split
    columns = ['lang', 'role', 'draw_order', 'massive_id', 'intent', 'text', 'source_config', 'source_split']
    df_out = df_out[columns]
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"\nSuccessfully wrote {len(df_out)} candidate rows to {OUTPUT_CSV}")

    # Generate full report to data/splits/oos_report.txt
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("AMAZON MASSIVE OUT-OF-SCOPE CANDIDATE SELECTION REPORT")
    report_lines.append("=" * 80)
    
    for config_name, lang_code, res, bwords in [
        ("hi-IN", "hi", hi_result, HI_BANKING_WORDS),
        ("ta-IN", "ta", ta_result, TA_BANKING_WORDS)
    ]:
        report_lines.append(f"\nConfiguration: {config_name} (Language: {lang_code})")
        report_lines.append(f"Source split: 'test'")
        report_lines.append(f"Total rows in config test split: {res['row_count']}")
        report_lines.append(f"Target intents count: {len(res['target_rows'])}")
        for ti in TARGET_INTENTS:
            report_lines.append(f"  - {ti}: {res['intent_counts'][ti]}")
            
        report_lines.append(f"\nExclusion Rule 3a (containing digit): {len(res['removed_3a'])} rows removed")
        for r in res['removed_3a']:
            report_lines.append(f"  [3a ID {r['id']} | {r['intent']}]: {r['utt']}")
            
        report_lines.append(f"\nExclusion Rule 3b (<3 or >15 words): {len(res['removed_3b'])} rows removed")
        for r, wc in res['removed_3b']:
            report_lines.append(f"  [3b ID {r['id']} | words={wc} | {r['intent']}]: {r['utt']}")
            
        report_lines.append(f"\nExclusion Rule 3c (banking/money words): {len(res['removed_3c'])} rows removed")
        for r, mw in res['removed_3c']:
            report_lines.append(f"  [3c ID {r['id']} | matched='{mw}' | {r['intent']}]: {r['utt']}")
            
        report_lines.append(f"\nRemaining candidate rows: {len(res['remaining_rows'])}")
        for ti in TARGET_INTENTS:
            report_lines.append(f"  - {ti}: {res['rem_counts'][ti]}")
            
        report_lines.append(f"\nSampled 30 rows (15 primary, 15 reserve, seed=42):")
        report_lines.append("draw_order | massive_id | intent | role | text")
        for rec in res['sampled_records']:
            line = f"{rec['draw_order']} | {rec['massive_id']} | {rec['intent']} | {rec['role']} | {rec['text']}"
            report_lines.append(line)
            flags = check_inflected_banking_words(rec['text'], bwords)
            if flags:
                for root, token in flags:
                    report_lines.append(f"   --> FLAGGED: banking word root '{root}' appears in inflected/compound form in token '{token}'")

    report_path = "data/splits/oos_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"Detailed UTF-8 report written to {report_path}")

    # STEP 6: Print all 30 rows per language in plain text
    print("\n" + "=" * 80)
    print("STEP 6: Sampled 30 Rows per Language (draw_order | massive_id | intent | role | text)")
    print("=" * 80)

    for lang_title, res, bwords in [("HINDI (hi-IN)", hi_result, HI_BANKING_WORDS), ("TAMIL (ta-IN)", ta_result, TA_BANKING_WORDS)]:
        print(f"\n--- {lang_title} ---")
        for rec in res['sampled_records']:
            line = f"{rec['draw_order']} | {rec['massive_id']} | {rec['intent']} | {rec['role']} | {rec['text']}"
            print(line)
            # Check for inflected / compound banking words
            flags = check_inflected_banking_words(rec['text'], bwords)
            if flags:
                for root, token in flags:
                    print(f"   [FLAGGED: banking word root '{root}' appears in inflected/compound form in token '{token}']")

if __name__ == '__main__':
    main()

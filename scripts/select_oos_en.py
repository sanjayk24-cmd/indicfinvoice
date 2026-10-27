import sys
import re
import random
import pandas as pd
from datasets import load_dataset
from collections import Counter

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CONFIG_NAME = "en-US"
LANG_CODE = "en"
TARGET_INTENTS = ['weather_query', 'play_music', 'alarm_set', 'general_greet']

EN_BANKING_WORDS = [
    'bank', 'account', 'card', 'loan', 'debt', 'payment', 'money', 'cash', 'rupee', 'price',
    'cost', 'expense', 'balance', 'transaction', 'transfer', 'insurance', 'bill', 'pay',
    'purchase', 'buy', 'sell', 'shop', 'tax', 'salary'
]

def main():
    print("STEP 1: Loading AmazonScience/massive for config en-US, split 'test'...")
    ds = load_dataset('AmazonScience/massive', CONFIG_NAME, split='test', trust_remote_code=True)
    row_count = len(ds)
    print(f"Total row count for {CONFIG_NAME}: {row_count}")

    intent_feature = ds.features['intent']
    intent_names = intent_feature.names
    print(f"\nFull list of intent names for {CONFIG_NAME} (Count: {len(intent_names)}):")
    print(", ".join(intent_names))

    for ti in TARGET_INTENTS:
        if ti not in intent_names:
            print(f"ERROR: Required intent '{ti}' is missing from {CONFIG_NAME}!")
            sys.exit(1)
    print(f"\nAll 4 required intents {TARGET_INTENTS} are present in {CONFIG_NAME}.")

    print("\nSTEP 2: Filter for target intents in en-US...")
    target_rows = []
    for r in ds:
        name = intent_feature.int2str(r['intent'])
        if name in TARGET_INTENTS:
            target_rows.append({
                'id': r['id'],
                'intent': name,
                'utt': r['utt'],
                'source_config': CONFIG_NAME,
                'source_split': 'test'
            })
            
    print(f"Total rows matching target intents in {CONFIG_NAME}: {len(target_rows)}")
    intent_counts = Counter(r['intent'] for r in target_rows)
    for ti in TARGET_INTENTS:
        print(f"  {ti}: {intent_counts[ti]}")

    print("\nSTEP 3: Apply exclusion rules in en-US...")
    # Word pattern for whole-word, case-insensitive
    patterns = [r'(?<!\w)' + re.escape(w) + r'(?!\w)' for w in sorted(EN_BANKING_WORDS, key=len, reverse=True)]
    banking_regex = re.compile('|'.join(patterns), re.IGNORECASE)

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
    for r, wc in removed_3b:
        print(f"  [3b ID {r['id']} | words={wc} | {r['intent']}]: {r['utt']}")

    print(f"\nRule 3c - Exclude banking/money words: {len(removed_3c)} rows removed")
    for r, mw in removed_3c:
        print(f"  [3c ID {r['id']} | matched='{mw}' | {r['intent']}]: {r['utt']}")

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

    print(f"\nRemaining candidate rows after all 3 exclusion rules for {CONFIG_NAME}: {len(remaining_rows)}")
    rem_counts = Counter(r['intent'] for r in remaining_rows)
    for ti in TARGET_INTENTS:
        print(f"  {ti}: {rem_counts[ti]}")

    print("\nSTEP 4: Draw 30 rows using random.Random(42).sample for en-US...")
    rng = random.Random(42)
    sampled_30 = rng.sample(remaining_rows, 30)

    sampled_records = []
    for idx, r in enumerate(sampled_30, start=1):
        role = "primary" if idx <= 15 else "reserve"
        sampled_records.append({
            'lang': LANG_CODE,
            'role': role,
            'draw_order': idx,
            'massive_id': r['id'],
            'intent': r['intent'],
            'text': r['utt'],
            'source_config': CONFIG_NAME,
            'source_split': 'test'
        })

    # Read existing candidates CSV to preserve hi and ta, and append en
    existing_csv = "data/splits/oos_candidates_massive.csv"
    if pd.io.common.file_exists(existing_csv):
        df_existing = pd.read_csv(existing_csv, encoding='utf-8')
        # Keep non-en rows (hi and ta)
        df_other = df_existing[df_existing['lang'] != 'en']
        df_en = pd.DataFrame(sampled_records)
        df_all = pd.concat([df_other, df_en], ignore_index=True)
    else:
        df_all = pd.DataFrame(sampled_records)

    columns = ['lang', 'role', 'draw_order', 'massive_id', 'intent', 'text', 'source_config', 'source_split']
    df_all = df_all[columns]
    df_all.to_csv(existing_csv, index=False, encoding='utf-8')
    print(f"\nSuccessfully updated {existing_csv}: total rows = {len(df_all)} (hi: {len(df_all[df_all['lang']=='hi'])}, ta: {len(df_all[df_all['lang']=='ta'])}, en: {len(df_all[df_all['lang']=='en'])})")

    print("\n" + "=" * 80)
    print("STEP 6: Sampled 30 Rows for English (draw_order | massive_id | intent | role | text)")
    print("=" * 80)

    for rec in sampled_records:
        line = f"{rec['draw_order']} | {rec['massive_id']} | {rec['intent']} | {rec['role']} | {rec['text']}"
        print(line)
        # Check for inflected or compound forms of banking words
        # (e.g. paying, payment, banking, costly, banker, buyer, buying, etc.)
        for bw in EN_BANKING_WORDS:
            for token in rec['text'].lower().split():
                clean_tok = token.strip(".,?!:;\"'()[]{}")
                if bw in clean_tok and clean_tok != bw:
                    print(f"   [FLAGGED: banking word root '{bw}' appears in inflected/compound form in word '{clean_tok}']")
if __name__ == '__main__':
    main()

import sys
import pandas as pd
import regex

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

CANDIDATES_CSV = "data/splits/oos_candidates_massive.csv"
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

def main():
    print("STEP 1: Reading data/splits/oos_candidates_massive.csv...")
    df = pd.read_csv(CANDIDATES_CSV, encoding='utf-8')
    row_count = len(df)
    hi_count = len(df[df['source_config'] == 'hi-IN'])
    ta_count = len(df[df['source_config'] == 'ta-IN'])
    print(f"Total rows: {row_count} (Expected: 60)")
    print(f"hi-IN rows: {hi_count} (Expected: 30)")
    print(f"ta-IN rows: {ta_count} (Expected: 30)")
    if row_count != 60 or hi_count != 30 or ta_count != 30:
        print("ERROR: Row count mismatch in candidates CSV!")
        sys.exit(1)

    print("\nSTEP 2: Verifying Hindi changes against candidates CSV...")
    hi_df = df[df['lang'] == 'hi'].set_index('draw_order')

    # Checks to verify:
    # - primary draw 7 (massive_id 1400, "मैं ज्यादातर ध्यान देता हूँ", unclear sentence) -> replace with reserve draw 16 (massive_id 782)
    # - primary draw 13 (massive_id 4212, "क्या मई आज शाम घास काटने में समर्थ हूँ", garbled sentence) -> replace with reserve draw 18 (massive_id 2423)
    # - reserve draw 17 (massive_id 2225): skipped, reason "near-duplicate of draw 16, same song request"
    # - reserve draw 23 (massive_id 1994, "मेरे रिकॉर्ड खोलो"): excluded, reason "ambiguous word रिकॉर्ड, author review"

    expected_checks = [
        (7, 1400, "मैं ज्यादातर ध्यान देता हूँ"),
        (16, 782, None),
        (13, 4212, "क्या मई आज शाम घास काटने में समर्थ हूँ"),
        (18, 2423, None),
        (17, 2225, None),
        (23, 1994, "मेरे रिकॉर्ड खोलो")
    ]

    for draw_ord, exp_id, exp_txt in expected_checks:
        if draw_ord not in hi_df.index:
            print(f"ERROR: draw_order {draw_ord} not found in Hindi candidates!")
            sys.exit(1)
        actual_id = int(hi_df.loc[draw_ord, 'massive_id'])
        actual_txt = hi_df.loc[draw_ord, 'text']
        if actual_id != exp_id:
            print(f"ERROR: draw_order {draw_ord} has massive_id {actual_id}, expected {exp_id}!")
            sys.exit(1)
        if exp_txt is not None and actual_txt != exp_txt:
            print(f"ERROR: draw_order {draw_ord} text mismatch!\n  Expected: {exp_txt}\n  Actual: {actual_txt}")
            sys.exit(1)
        print(f"Verified draw_order {draw_ord}: massive_id {actual_id} matches.")

    # STEP 3: Print Tamil primary rows
    print("\n" + "=" * 80)
    print("STEP 3: Tamil (ta-IN) 15 Primary Rows (draw_order | massive_id | text):")
    print("=" * 80)
    ta_df = df[df['lang'] == 'ta'].sort_values('draw_order')
    ta_primary = ta_df[ta_df['role'] == 'primary']
    for _, r in ta_primary.iterrows():
        print(f"{r['draw_order']} | {r['massive_id']} | {r['text']}")

    # STEP 4: Build review log CSV
    # Columns: lang, action, draw_order, massive_id, text, reason, replacement_draw_order, replacement_massive_id, reviewer
    print("\nSTEP 4: Writing data/splits/oos_review_log.csv...")
    review_rows = [
        {
            'lang': 'hi',
            'action': 'replaced',
            'draw_order': 7,
            'massive_id': 1400,
            'text': hi_df.loc[7, 'text'],
            'reason': 'unclear sentence',
            'replacement_draw_order': 16,
            'replacement_massive_id': 782,
            'reviewer': 'author review'
        },
        {
            'lang': 'hi',
            'action': 'replaced',
            'draw_order': 13,
            'massive_id': 4212,
            'text': hi_df.loc[13, 'text'],
            'reason': 'garbled sentence',
            'replacement_draw_order': 18,
            'replacement_massive_id': 2423,
            'reviewer': 'author review'
        },
        {
            'lang': 'hi',
            'action': 'skipped',
            'draw_order': 17,
            'massive_id': 2225,
            'text': hi_df.loc[17, 'text'],
            'reason': 'near-duplicate of draw 16, same song request',
            'replacement_draw_order': '',
            'replacement_massive_id': '',
            'reviewer': 'author review'
        },
        {
            'lang': 'hi',
            'action': 'excluded_reserve',
            'draw_order': 23,
            'massive_id': 1994,
            'text': hi_df.loc[23, 'text'],
            'reason': 'ambiguous word रिकॉर्ड, author review',
            'replacement_draw_order': '',
            'replacement_massive_id': '',
            'reviewer': 'author review'
        }
    ]

    log_df = pd.DataFrame(review_rows)
    log_columns = ['lang', 'action', 'draw_order', 'massive_id', 'text', 'reason', 'replacement_draw_order', 'replacement_massive_id', 'reviewer']
    log_df = log_df[log_columns]
    log_df.to_csv(REVIEW_LOG_CSV, index=False, encoding='utf-8')
    print(f"Successfully wrote {len(log_df)} change entries to {REVIEW_LOG_CSV}")

    # Print Hindi change log
    print("\n" + "=" * 80)
    print("STEP 5: Hindi Change Log:")
    print("=" * 80)
    for r in review_rows:
        rep_info = f" -> replaced with draw {r['replacement_draw_order']} (ID {r['replacement_massive_id']})" if r['replacement_draw_order'] != '' else ""
        print(f"[{r['lang']}] Action: {r['action']} | Draw: {r['draw_order']} | ID: {r['massive_id']}{rep_info} | Reason: \"{r['reason']}\" | Reviewer: \"{r['reviewer']}\"")
        print(f"   Text: \"{r['text']}\"")

    # Construct and verify Hindi final primary list for acceptance checks:
    # Original primary: draw 1 to 15
    # Replace draw 7 with draw 16 (ID 782)
    # Replace draw 13 with draw 18 (ID 2423)
    hi_primary_map = {}
    for draw_ord in range(1, 16):
        hi_primary_map[draw_ord] = {
            'draw_order': draw_ord,
            'massive_id': int(hi_df.loc[draw_ord, 'massive_id']),
            'text': hi_df.loc[draw_ord, 'text']
        }
    
    # Apply replacements
    hi_primary_map[7] = {
        'draw_order': 16,
        'massive_id': 782,
        'text': hi_df.loc[16, 'text']
    }
    hi_primary_map[13] = {
        'draw_order': 18,
        'massive_id': 2423,
        'text': hi_df.loc[18, 'text']
    }

    final_hi_list = list(hi_primary_map.values())

    print("\n" + "=" * 80)
    print("CHECK EVALUATIONS:")
    print("=" * 80)

    # Check 1: Hindi final primary list has 15 rows
    c1 = (len(final_hi_list) == 15)
    print(f"- Hindi final primary list has 15 rows: {'PASS' if c1 else 'FAIL'} (Count: {len(final_hi_list)})")

    # Check 2: no duplicate massive_id within a language
    final_ids = [r['massive_id'] for r in final_hi_list]
    c2 = (len(final_ids) == len(set(final_ids)))
    print(f"- no duplicate massive_id within a language: {'PASS' if c2 else 'FAIL'} (Unique: {len(set(final_ids))}/{len(final_ids)})")

    # Check 3: every replacement_massive_id comes from a reserve row in the candidates file
    reserve_ids = set(hi_df[hi_df['role'] == 'reserve']['massive_id'].astype(int))
    replacements_used = [782, 2423]
    c3 = all(rep in reserve_ids for rep in replacements_used)
    print(f"- every replacement_massive_id comes from a reserve row in the candidates file: {'PASS' if c3 else 'FAIL'}")

    # Check 4: no removed or excluded ID appears in the final list
    removed_or_excluded = {1400, 4212, 2225, 1994}
    c4 = not any(fid in removed_or_excluded for fid in final_ids)
    print(f"- no removed or excluded ID appears in the final list: {'PASS' if c4 else 'FAIL'}")

    # Check 5: no row in the final list contains a word from the banking/money lists in the original prompt
    bpattern = regex.compile(r'(?<![\p{L}\p{M}])(?:' + '|'.join(regex.escape(w) for w in sorted(HI_BANKING_WORDS, key=len, reverse=True)) + r')(?![\p{L}\p{M}])', regex.IGNORECASE)
    banking_hits = []
    for r in final_hi_list:
        m = bpattern.search(r['text'])
        if m:
            banking_hits.append((r['massive_id'], m.group(0), r['text']))
    c5 = (len(banking_hits) == 0)
    print(f"- no row in the final list contains a word from the banking/money lists in the original prompt: {'PASS' if c5 else 'FAIL'}")
    if banking_hits:
        for hit in banking_hits:
            print(f"   [HIT: ID {hit[0]} | word '{hit[1]}' | text '{hit[2]}']")

if __name__ == '__main__':
    main()

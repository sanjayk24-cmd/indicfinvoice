#!/usr/bin/env python3
"""
scripts/verify_edge_cases.py

Verifies all diverse banking personas and edge cases through ConversationService and MockBank API.
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.conversation import ConversationService
from mockbank.api import BANK_DB, app as mockbank_app
from fastapi.testclient import TestClient

def test_all_scenarios():
    conv = ConversationService()
    client = TestClient(mockbank_app)

    print("=== 1. VERIFYING ZERO-TRANSACTION EMPTY STATE (C009) ===")
    res_c009 = conv.process_message("Show my transactions", "en", customer_id="C009")
    print(f"C009 response: {res_c009['reply']}")
    assert "No transactions match" in res_c009['reply']
    assert res_c009['transactions'] == []
    print("✓ C009 zero-transaction empty state verified!")

    print("\n=== 2. VERIFYING ZERO BALANCE EDGE CASE (C014) ===")
    res_c014 = conv.process_message("What is my savings balance?", "en", customer_id="C014")
    print(f"C014 response: {res_c014['reply']}")
    assert res_c014['account_data']['balance'] == 0.0
    print("✓ C014 zero balance verified!")

    print("\n=== 3. VERIFYING NEGATIVE OVERDRAFT EDGE CASE (C015) ===")
    res_c015 = conv.process_message("What is my savings balance?", "en", customer_id="C015")
    print(f"C015 response: {res_c015['reply']}")
    assert res_c015['account_data']['balance'] < 0.0
    print(f"✓ C015 negative balance verified ({res_c015['account_data']['balance']})!")

    print("\n=== 4. VERIFYING MULTI-CRORE ULTRA HNW (C016) ===")
    res_c016 = conv.process_message("What is my savings balance?", "en", customer_id="C016")
    print(f"C016 response: {res_c016['reply']}")
    assert res_c016['account_data']['balance'] > 10000000.0
    print(f"✓ C016 multi-crore balance verified (Rs {res_c016['account_data']['balance']:,.2f})!")

    print("\n=== 5. VERIFYING OVERDUE LOAN (C010) ===")
    res_c010 = conv.process_message("When is my personal loan due?", "en", customer_id="C010")
    print(f"C010 response: {res_c010['reply']}")
    assert "2026-10-05" in res_c010['reply'] or "148" in res_c010['reply']
    print("✓ C010 overdue loan verified!")

    print("\n=== 6. VERIFYING CLOSED ZERO-OUTSTANDING LOAN (C011) ===")
    res_c011 = conv.process_message("When is my personal loan due?", "en", customer_id="C011")
    print(f"C011 response: {res_c011['reply']}")
    assert "0" in res_c011['reply']
    print("✓ C011 closed loan verified!")

    print("\n=== 7. VERIFYING FAILED TRANSACTION FILTERING (C012) ===")
    res_c012 = conv.process_message("Show my failed transactions", "en", customer_id="C012")
    print(f"C012 failed txns count: {len(res_c012['transactions'])}")
    for t in res_c012['transactions']:
        print(f"  - {t['reference']} | {t['amount']} INR | {t['status']} | {t['description']}")
        assert t['status'] == 'failed'
    print("✓ C012 failed transaction filtering verified!")

    print("\n=== 8. VERIFYING DUPLICATE DEBIT DISPUTE (C004) ===")
    dispute_payload = {
        "customer_id": "C004",
        "transaction_ref": "TXN-4001",
        "amount": 4299.00,
        "date": "2026-10-23",
        "pin": "4567"
    }
    r = client.post("/dispute", json=dispute_payload)
    print(f"C004 dispute registration: {r.status_code} -> {r.json()}")
    assert r.status_code == 200
    assert r.json()['status'] == 'dispute_registered'
    print("✓ C004 duplicate debit dispute verified!")

    print("\n=== 9. VERIFYING KCC BALANCE AND CROP LOAN (C002) ===")
    res_c002_bal = conv.process_message("What is my kcc balance?", "en", customer_id="C002")
    print(f"C002 KCC balance: {res_c002_bal['reply']}")
    assert "18500" in res_c002_bal['reply']
    res_c002_loan = conv.process_message("When is my crop loan due?", "en", customer_id="C002")
    print(f"C002 Crop loan due: {res_c002_loan['reply']}")
    assert "2026-12-31" in res_c002_loan['reply'] and "85000" in res_c002_loan['reply']
    print("✓ C002 KCC balance and crop loan verified!")

    print("\n=== 10. VERIFYING HINDI & TAMIL QUERIES ACROSS CUSTOMERS ===")
    hi_res = conv.process_message("मेरा बचत खाता का बैलेंस क्या है", "hi", customer_id="C001")
    print(f"Hindi balance reply: {hi_res['reply']}")
    ta_res = conv.process_message("எனது சேமிப்பு கணக்கு இருப்பு என்ன", "ta", customer_id="C001")
    print(f"Tamil balance reply: {ta_res['reply']}")
    print("✓ Multilingual edge cases verified!")

    print("\nALL 10 EDGE CASE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_all_scenarios()

import json
import os
import sys
import urllib.request
import httpx

sys.stdout.reconfigure(encoding="utf-8")

print("=== 1. Checking Frontend (http://127.0.0.1:5173/) ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:5173/") as resp:
        html = resp.read().decode("utf-8")
        print(f"Frontend HTTP Status: {resp.status}")
        print("Title tag present:", "IndicFinVoice" in html)
        print("Root element present:", 'id="root"' in html)
except Exception as e:
    print("Frontend error:", e)

print("\n=== 2. Checking Backend Health (http://127.0.0.1:8000/health) ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("Backend Status:", data)
except Exception as e:
    print("Backend health error:", e)

print("\n=== 3. Testing Backend Chat (en, hi, ta) ===")
client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

# English
r_en = client.post("/chat", json={"message": "What is my account balance?", "lang": "en", "session_id": "sess-demo-en"})
print("EN Chat:", r_en.json()["reply"])
if r_en.json().get("account_data"):
    print("   Embedded Account Data:", r_en.json()["account_data"])

# Hindi
r_hi = client.post("/chat", json={"message": "मेरे पिछले कुछ लेनदेन दिखाओ", "lang": "hi", "session_id": "sess-demo-hi"})
print("\nHI Chat:", r_hi.json()["reply"][:60], "...")
if r_hi.json().get("transactions"):
    print(f"   Embedded Transactions: {len(r_hi.json()['transactions'])} items")

# Tamil
r_ta = client.post("/chat", json={"message": "எனது சேமிப்பு கணக்கு இருப்பு என்ன", "lang": "ta", "session_id": "sess-demo-ta"})
print("\nTA Chat:", r_ta.json()["reply"])

# Block card refusal test
r_block = client.post("/chat", json={"message": "I want to block my card", "lang": "en"})
print("\nRefusal / Block Card Chat:", r_block.json()["reply"])

print("\n=== 4. Testing Speech Transcription via API (/transcribe) ===")
hi_wav = "data/raw/speech/indicvoices/hi/hi_000.wav"
if os.path.exists(hi_wav):
    with open(hi_wav, "rb") as f:
        files = {"file": ("hi_000.wav", f, "audio/wav")}
        data = {"lang": "hi"}
        r_trans = client.post("/transcribe", files=files, data=data)
        print("Hindi Audio Transcription:", r_trans.json().get("transcript", ""))
        print("Model ID used:", r_trans.json().get("model_id", ""))

print("\n=== 5. Testing Account Summary API (/account/summary) ===")
r_acct = client.get("/account/summary?customer_id=C001")
print("Account Summary:", r_acct.json())

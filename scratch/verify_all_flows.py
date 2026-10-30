import urllib.request
import json

base = "http://127.0.0.1:8000/api"

def call_api(endpoint, method="GET", body=None):
    url = f"{base}{endpoint}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

print("Testing 1: Providers health...")
health = call_api("/health")
assert health["status"] == "healthy"
print("[OK] Health passed: healthy")

print("Testing 2: Intent detection...")
intent = call_api("/search/intent", method="POST", body={"query": "gaming laptop"})
assert intent["detected_category"] == "laptop"
print(f"[OK] Intent passed: category={intent['detected_category']}")

print("Testing 3: Dynamic questions...")
questions = call_api("/search/questions", method="POST", body={"query": "gaming laptop", "category": "laptop"})
assert len(questions) > 0
print(f"[OK] Dynamic questions passed: {len(questions)} dynamic questions")

print("Testing 4: Coupons & Offers API...")
coupons = call_api("/coupons/offers?query=laptop")
assert "offers" in coupons
print(f"[OK] Coupons passed: {len(coupons['offers'])} verified offers")

print("Testing 5: Customer Research History API...")
history = call_api("/history?category=all&limit=10")
assert "items" in history
print(f"[OK] History passed: {history['total']} items retrieved")

print("\n>>> ALL SYSTEM & REGRESSION CHECKS PASSED 100%! <<<")

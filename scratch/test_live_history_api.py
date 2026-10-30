import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000/api"

def make_req(endpoint, method="GET", body=None, token=None, guest_id=None):
    url = f"{base_url}{endpoint}"
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if guest_id:
        headers["X-Guest-ID"] = guest_id
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("1. Testing health...")
h = make_req("/health")
print("Health:", h["status"])

print("2. Testing Guest Profile Dashboard...")
guest_dash = make_req("/history/dashboard", guest_id="live_tester_1")
print("Guest Dashboard stats:", guest_dash["stats"])

print("3. Recording Research Activity (search, recommendation, comparison, review, coupon)...")
# Search
s = make_req("/history/record", method="POST", guest_id="live_tester_1", body={
    "category": "search",
    "title": "Searched for 'wireless headphones'",
    "query": "wireless headphones",
    "metadata": {"brand": "Sony"}
})
print("Recorded search:", s["id"])

# Recommendation
r = make_req("/history/record", method="POST", guest_id="live_tester_1", body={
    "category": "recommendation",
    "title": "Sony WH-1000XM5 Noise Cancelling Headphones",
    "query": "wireless headphones",
    "metadata": {
        "product": {
            "id": "sony_wh1000xm5",
            "title": "Sony WH-1000XM5 Wireless Active Noise Cancelling Headphones",
            "marketplace": "Amazon India",
            "price": 26990.0,
            "rating": 4.6,
            "trust_score": 95.2
        }
    }
})
print("Recorded recommendation:", r["id"])

# Comparison
c = make_req("/history/record", method="POST", guest_id="live_tester_1", body={
    "category": "comparison",
    "title": "Compared Top 3 ANC Headphones",
    "query": "wireless headphones",
    "metadata": {
        "compared_products": [
            {"title": "Sony WH-1000XM5", "price": 26990.0},
            {"title": "Bose QC45", "price": 24990.0},
            {"title": "Sennheiser Momentum 4", "price": 27990.0}
        ]
    }
})
print("Recorded comparison:", c["id"])

# Review Analysis
rev = make_req("/history/record", method="POST", guest_id="live_tester_1", body={
    "category": "review_analysis",
    "title": "Review Sentiment for Sony WH-1000XM5",
    "query": "wireless headphones",
    "metadata": {
        "sentiment_summary": {"positive": 88, "neutral": 8, "negative": 4},
        "total_reviews": 3400
    }
})
print("Recorded review analysis:", rev["id"])

# Coupon
coup = make_req("/history/record", method="POST", guest_id="live_tester_1", body={
    "category": "coupon",
    "title": "₹2,000 Instant Bank Discount on Sony XM5",
    "query": "wireless headphones",
    "metadata": {
        "coupon_code": "SONY2000",
        "discount_amount": 2000,
        "marketplace": "Amazon India"
    }
})
print("Recorded coupon:", coup["id"])

print("4. Saving Product to Bookmarks...")
saved = make_req("/history/save", method="POST", guest_id="live_tester_1", body={
    "product_id": "sony_wh1000xm5",
    "title": "Sony WH-1000XM5 Wireless Active Noise Cancelling Headphones",
    "marketplace": "Amazon India",
    "price": 26990.0,
    "original_price": 34990.0,
    "rating": 4.6,
    "trust_score": 95.2,
    "image_url": "https://m.media-amazon.com/images/I/61+ElP-fHjL._SL1500_.jpg",
    "product_url": "https://amazon.in/dp/B09XS7JWHH"
})
print("Saved product:", saved["title"])

print("5. Verifying Dashboard Summary...")
dash = make_req("/history/dashboard", guest_id="live_tester_1")
print("Updated Stats:", dash["stats"])
print("Recent History Count:", len(dash["recent_history"]))
print("Saved Products Count:", len(dash["saved_products"]))
assert dash["stats"]["total_searches"] >= 1
assert dash["stats"]["total_recommendations"] >= 1
assert dash["stats"]["total_comparisons"] >= 1
assert dash["stats"]["total_reviews_analyzed"] >= 1
assert dash["stats"]["total_coupons_viewed"] >= 1
assert dash["stats"]["total_saved_products"] >= 1

print("\n>>> ALL LIVE PROFILE & RESEARCH HISTORY API TESTS PASSED! <<<")

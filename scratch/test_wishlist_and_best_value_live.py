import urllib.request
import json

base_url = "http://127.0.0.1:8000/api"

def call(endpoint, method="GET", body=None, guest_id=None):
    url = f"{base_url}{endpoint}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if guest_id:
        headers["X-Guest-ID"] = guest_id
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

print("1. Checking health...")
h = call("/health")
assert h["status"] == "healthy"
print("[OK] Health status:", h["status"])

print("2. Generating recommendations for 'laptop' to test Best Value Finder...")
recs = call("/recommendations/generate", method="POST", body={
    "query": "laptop",
    "category": "laptop",
    "answers": {}
})
assert len(recs["recommendations"]) > 0
print(f"[OK] Recommendations generated: {len(recs['recommendations'])} products")

best_value_item = recs.get("best_value")
if best_value_item:
    print(f"[OK] Best Value Finder selected: '{best_value_item['product']['title']}'")
    print(f"     Price: Rs.{best_value_item['product']['current_price']} | Rating: {best_value_item['product']['rating']} | Badges: {best_value_item['category_badges']}")
    assert "Best Value" in best_value_item["category_badges"]
    assert best_value_item["product"]["current_price"] is not None and best_value_item["product"]["current_price"] > 0
    assert best_value_item["product"]["rating"] is not None and best_value_item["product"]["rating"] >= 3.5
else:
    print("[INFO] No product satisfied data sufficiency for Best Value label (authentic behavior).")

print("3. Testing Smart Wishlist saving and removal...")
# Save a product with real discount
sample_p = {
    "product_id": "test_wishlist_p1",
    "title": "Lenovo IdeaPad Slim 3 15-inch Laptop",
    "marketplace": "Amazon India",
    "price": 42990.0,
    "original_price": 58990.0,
    "rating": 4.4,
    "trust_score": 89.5,
    "image_url": "https://m.media-amazon.com/images/I/71s3B38J0AL._SL1500_.jpg",
    "product_url": "https://amazon.in/dp/example"
}
saved = call("/history/save", method="POST", guest_id="wishlist_tester_2", body=sample_p)
assert saved["product_id"] == "test_wishlist_p1"
print(f"[OK] Added to Smart Wishlist: '{saved['title']}' (Saved Rs.{int(saved['original_price'] - saved['price'])})")

# Fetch dashboard
dash = call("/history/dashboard", guest_id="wishlist_tester_2")
assert len(dash["saved_products"]) >= 1
print(f"[OK] Smart Wishlist item count: {len(dash['saved_products'])}")

# Clean up
removed = call("/history/save/test_wishlist_p1", method="DELETE", guest_id="wishlist_tester_2")
assert removed["status"] == "success"
print("[OK] Removed from Smart Wishlist successfully.")

print("\n>>> ALL TESTS FOR SMART WISHLIST AND BEST VALUE FINDER PASSED! <<<")

import pytest
import os
from app.services.history_service import HistoryService
from app.services.auth_service import AuthService

def test_history_service_full_flow():
    # Initialize DB
    HistoryService.initialize_db()

    user_id = "test_user_hist_123"

    # 1. Clear any prior test data
    HistoryService.clear_history(user_id=user_id)
    for p in HistoryService.get_saved_products(user_id=user_id):
        HistoryService.remove_saved_product(user_id=user_id, product_id=p.product_id)

    # 2. Record 5 categories of research activities
    # Search
    search_item = HistoryService.record_event(
        user_id=user_id,
        category="search",
        title="Searched for 'gaming laptop'",
        query="gaming laptop",
        metadata={"filters": {"budget": "under 80000"}}
    )
    assert search_item.category == "search"
    assert search_item.query == "gaming laptop"

    # Recommendation
    rec_item = HistoryService.record_event(
        user_id=user_id,
        category="recommendation",
        title="ASUS TUF Gaming A15",
        query="gaming laptop",
        metadata={
            "product": {
                "id": "asus_tuf_a15",
                "marketplace": "Amazon India",
                "price": 68990.0,
                "rating": 4.5,
                "trust_score": 92.4,
                "image_url": "https://example.com/asus.jpg"
            }
        }
    )
    assert rec_item.category == "recommendation"

    # Comparison
    comp_item = HistoryService.record_event(
        user_id=user_id,
        category="comparison",
        title="Compared 3 Laptops for Gaming",
        query="gaming laptop",
        metadata={
            "compared_products": [
                {"title": "ASUS TUF A15", "price": 68990.0},
                {"title": "Acer Nitro V", "price": 72990.0},
                {"title": "Lenovo LOQ", "price": 69990.0}
            ]
        }
    )
    assert comp_item.category == "comparison"

    # Review Analysis
    review_item = HistoryService.record_event(
        user_id=user_id,
        category="review_analysis",
        title="Review Sentiment Analysis for ASUS TUF A15",
        query="gaming laptop",
        metadata={
            "product_title": "ASUS TUF Gaming A15",
            "sentiment_summary": {"positive": 82, "neutral": 11, "negative": 7},
            "total_reviews": 1250
        }
    )
    assert review_item.category == "review_analysis"

    # Coupon & Offer
    coupon_item = HistoryService.record_event(
        user_id=user_id,
        category="coupon",
        title="₹3,000 Off with HDFC Card on ASUS TUF",
        query="gaming laptop",
        metadata={
            "coupon_code": "HDFC3000",
            "discount_amount": 3000,
            "marketplace": "Amazon India"
        }
    )
    assert coupon_item.category == "coupon"

    # 3. Retrieve history by category and all
    all_items = HistoryService.get_history(user_id=user_id, category="all")
    assert len(all_items) == 5

    search_items = HistoryService.get_history(user_id=user_id, category="search")
    assert len(search_items) == 1
    assert search_items[0].query == "gaming laptop"

    # 4. Save and remove product
    saved_p = HistoryService.save_product(
        user_id=user_id,
        product_data={
            "product_id": "asus_tuf_a15",
            "title": "ASUS TUF Gaming A15 (2024)",
            "marketplace": "Amazon India",
            "price": 68990.0,
            "original_price": 89990.0,
            "rating": 4.5,
            "trust_score": 92.4,
            "image_url": "https://example.com/asus.jpg",
            "product_url": "https://amazon.in/dp/example"
        }
    )
    assert saved_p.product_id == "asus_tuf_a15"
    assert saved_p.price == 68990.0

    saved_list = HistoryService.get_saved_products(user_id=user_id)
    assert len(saved_list) == 1
    assert saved_list[0].title == "ASUS TUF Gaming A15 (2024)"

    # 5. Dashboard summary stats
    summary = HistoryService.get_dashboard_summary(
        user_id=user_id,
        user_dict={"id": user_id, "email": "test@trustrank.ai", "name": "Tester"}
    )
    assert summary.stats.total_searches == 1
    assert summary.stats.total_recommendations == 1
    assert summary.stats.total_comparisons == 1
    assert summary.stats.total_reviews_analyzed == 1
    assert summary.stats.total_coupons_viewed == 1
    assert summary.stats.total_saved_products == 1
    assert summary.customer.email == "test@trustrank.ai"

    # 6. Remove saved product
    removed = HistoryService.remove_saved_product(user_id=user_id, product_id="asus_tuf_a15")
    assert removed is True
    assert len(HistoryService.get_saved_products(user_id=user_id)) == 0

    # 7. Clear history by category then all
    cleared_cat = HistoryService.clear_history(user_id=user_id, category="search")
    assert cleared_cat == 1
    assert len(HistoryService.get_history(user_id=user_id, category="search")) == 0

    cleared_all = HistoryService.clear_history(user_id=user_id)
    assert cleared_all == 4
    assert len(HistoryService.get_history(user_id=user_id)) == 0

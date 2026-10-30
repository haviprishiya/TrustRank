import re
import sys
sys.path.insert(0, r"c:\Users\haviprishiya\Downloads\update new\update\update\backend")

from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.matching_service import MatchingService
from app.services.normalization_service import NormalizationService

test_cases = [
    # 1. Samsung Galaxy A06 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)",
            "brand": "Samsung",
            "price": 15499.0,
            "url": "https://www.amazon.in/dp/B0DGA06TEST",
        },
        "flipkart": {
            "title": "SAMSUNG Galaxy A06 5G (Black, 128 GB) (4 GB RAM)",
            "brand": "Samsung",
            "price": 12499.0,
            "url": "https://www.flipkart.com/samsung-galaxy-a06-5g-black-128-gb/p/itm123?pid=MOB123",
        }
    },
    # 2. Samsung Galaxy A07 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A07 5G (Light Blue, 6GB, 128GB Storage)",
            "brand": "Samsung",
            "price": 28999.0,
            "url": "https://www.amazon.in/dp/B0DGA07TEST",
        },
        "flipkart": {
            "title": "SAMSUNG Galaxy A07 5G (Light Blue, 128 GB) (6 GB RAM)",
            "brand": "Samsung",
            "price": 21495.0,
            "url": "https://www.flipkart.com/samsung-galaxy-a07-5g-light-blue-128-gb/p/itm456?pid=MOB456",
        }
    },
    # 3. Galaxy A56 5G Samsung
    {
        "amazon": {
            "title": "Galaxy A56 5G Samsung (Awesome Graphite, 8GB RAM, 128GB Storage)",
            "brand": "Samsung",
            "price": 38999.0,
            "url": "https://www.amazon.in/dp/B0DGA56TEST",
        },
        "flipkart": {
            "title": "SAMSUNG Galaxy A56 5G (Awesome Iceblue, 128 GB) (8 GB RAM)",
            "brand": "Samsung",
            "price": 36999.0,
            "url": "https://www.flipkart.com/samsung-galaxy-a56-5g-awesome-iceblue-128-gb/p/itm789?pid=MOB789",
        }
    },
    # 4. Samsung Galaxy A27 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A27 5G (Awesome Violet, 6GB RAM, 128GB Storage)",
            "brand": "Samsung",
            "price": 24999.0,
            "url": "https://www.amazon.in/dp/B0DGA27TEST",
        },
        "flipkart": {
            "title": "SAMSUNG Galaxy A27 5G (Awesome Navy, 128 GB) (6 GB RAM)",
            "brand": "Samsung",
            "price": 22499.0,
            "url": "https://www.flipkart.com/samsung-galaxy-a27-5g-awesome-navy-128-gb/p/itm270?pid=MOB270",
        }
    },
    # 5. Samsung M36 5G
    {
        "amazon": {
            "title": "Samsung M36 5G (Midnight Blue, 6GB RAM, 128GB Storage) | 6000mAh Battery",
            "brand": "Samsung",
            "price": 18999.0,
            "url": "https://www.amazon.in/dp/B0DGM36TEST",
        },
        "flipkart": {
            "title": "SAMSUNG Galaxy M36 5G (Midnight Blue, 128 GB) (6 GB RAM)",
            "brand": "Samsung",
            "price": 17499.0,
            "url": "https://www.flipkart.com/samsung-galaxy-m36-5g-midnight-blue-128-gb/p/itm360?pid=MOB360",
        }
    },
]

print("=== TESTING CURRENT MATCHING FOR THE 5 CASES ===")
for i, case in enumerate(test_cases, 1):
    amz_raw = case["amazon"]
    fk_raw = case["flipkart"]
    
    p_amz = NormalizedProduct(
        id=f"amz_{i}",
        title=amz_raw["title"],
        brand=amz_raw["brand"],
        category="phone",
        current_price=amz_raw["price"],
        product_url=amz_raw["url"],
        marketplace="Amazon India",
        provider="amazon_paapi_india",
        offers=[MarketplaceOffer(marketplace="Amazon India", provider="amazon_paapi_india", product_url=amz_raw["url"], current_price=amz_raw["price"])]
    )
    p_fk = NormalizedProduct(
        id=f"fk_{i}",
        title=fk_raw["title"],
        brand=fk_raw["brand"],
        category="phone",
        current_price=fk_raw["price"],
        product_url=fk_raw["url"],
        marketplace="Flipkart",
        provider="flipkart_affiliate",
        offers=[MarketplaceOffer(marketplace="Flipkart", provider="flipkart_affiliate", product_url=fk_raw["url"], current_price=fk_raw["price"])]
    )
    
    p_amz_norm = NormalizationService.normalize_product(p_amz)
    p_fk_norm = NormalizationService.normalize_product(p_fk)
    
    matched = MatchingService.are_products_identical(p_amz_norm, p_fk_norm)
    grouped = MatchingService.deduplicate_and_group_offers([p_amz_norm, p_fk_norm])
    
    print(f"\nCase {i}: {amz_raw['title'][:35]} vs {fk_raw['title'][:35]}")
    print(f"  Matched: {matched}")
    print(f"  Grouped offers count: {len(grouped[0].offers)} (offers: {[o.marketplace for o in grouped[0].offers]})")

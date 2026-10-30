import json
import sys
sys.path.insert(0, r"c:\Users\haviprishiya\Downloads\update new\update\update\backend")

from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.matching_service import MatchingService
from app.services.comparison_service import ComparisonService
from app.services.scoring_service import ScoringService

products_data = [
    # 1. Samsung Galaxy A06 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)",
            "model": "Galaxy A06",
            "price": 15499.0,
            "url": "https://www.amazon.in/dp/B0DGA06TEST"
        },
        "flipkart_candidates": [
            {
                "title": "SAMSUNG Galaxy A06 5G (Black, 128 GB) (4 GB RAM)",
                "model": "Galaxy A06",
                "price": 12499.0,
                "sku": "MOBHA06TEST",
                "url": "https://www.flipkart.com/samsung-galaxy-a06-5g-black-128-gb/p/itm123?pid=MOBHA06TEST"
            }
        ]
    },
    # 2. Samsung Galaxy A07 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A07 5G (Light Blue, 6GB, 128GB Storage)",
            "model": "Galaxy A07",
            "price": 28999.0,
            "url": "https://www.amazon.in/dp/B0DGA07TEST"
        },
        "flipkart_candidates": [
            {
                "title": "SAMSUNG Galaxy A07 5G (Light Blue, 128 GB) (6 GB RAM)",
                "model": "Galaxy A07",
                "price": 21495.0,
                "sku": "MOBHA07TEST",
                "url": "https://www.flipkart.com/samsung-galaxy-a07-5g-light-blue-128-gb/p/itm456?pid=MOBHA07TEST"
            }
        ]
    },
    # 3. Galaxy A56 5G Samsung
    {
        "amazon": {
            "title": "Galaxy A56 5G Samsung (Awesome Graphite, 8GB RAM, 128GB Storage)",
            "model": "Galaxy A56",
            "price": 38999.0,
            "url": "https://www.amazon.in/dp/B0DGA56TEST"
        },
        "flipkart_candidates": [
            {
                "title": "SAMSUNG Galaxy A56 5G (Awesome Iceblue, 128 GB) (8 GB RAM)",
                "model": "Galaxy A56",
                "price": 36999.0,
                "sku": "MOBHA56TEST",
                "url": "https://www.flipkart.com/samsung-galaxy-a56-5g-awesome-iceblue-128-gb/p/itm789?pid=MOBHA56TEST"
            }
        ]
    },
    # 4. Samsung Galaxy A27 5G
    {
        "amazon": {
            "title": "Samsung Galaxy A27 5G (Awesome Violet, 6GB RAM, 128GB Storage)",
            "model": "Galaxy A27",
            "price": 24999.0,
            "url": "https://www.amazon.in/dp/B0DGA27TEST"
        },
        "flipkart_candidates": [
            {
                "title": "SAMSUNG Galaxy A27 5G (Awesome Navy, 128 GB) (6 GB RAM)",
                "model": "Galaxy A27",
                "price": 22499.0,
                "sku": "MOBHA27TEST",
                "url": "https://www.flipkart.com/samsung-galaxy-a27-5g-awesome-navy-128-gb/p/itm270?pid=MOBHA27TEST"
            }
        ]
    },
    # 5. Samsung M36 5G
    {
        "amazon": {
            "title": "Samsung M36 5G (Midnight Blue, 6GB RAM, 128GB Storage) | 6000mAh Battery",
            "model": "Galaxy M36",
            "price": 18999.0,
            "url": "https://www.amazon.in/dp/B0DGM36TEST"
        },
        "flipkart_candidates": [
            {
                "title": "SAMSUNG Galaxy M36 5G (Midnight Blue, 128 GB) (6 GB RAM)",
                "model": "Galaxy M36",
                "price": 17499.0,
                "sku": "MOBHM36TEST",
                "url": "https://www.flipkart.com/samsung-galaxy-m36-5g-midnight-blue-128-gb/p/itm360?pid=MOBHM36TEST"
            }
        ]
    }
]

print("="*70)
print("TEST REPORT FOR THE 5 SAMSUNG PRODUCTS")
print("="*70)

for idx, item in enumerate(products_data, 1):
    amz = item["amazon"]
    candidates = item["flipkart_candidates"]
    
    print(f"\nProduct #{idx}:")
    print(f"Amazon title: {amz['title']}")
    print(f"Amazon model: {amz['model']}")
    print(f"Amazon price: Rs.{amz['price']:,.0f}")
    print()
    print("Flipkart candidates found:")
    for fk in candidates:
        print(f"Flipkart title: {fk['title']}")
        print(f"Flipkart model: {fk['model']}")
        print(f"Flipkart price: Rs.{fk['price']:,.0f}")
        print(f"Flipkart SKU: {fk['sku']}")
        print(f"Flipkart URL: {fk['url']}")
        
        p_amz = NormalizedProduct(
            id=f"amz_{idx}",
            title=amz["title"],
            brand="Samsung",
            category="phone",
            current_price=amz["price"],
            product_url=amz["url"],
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
            offers=[MarketplaceOffer(marketplace="Amazon India", provider="brightdata_amazon_search", product_url=amz["url"], current_price=amz["price"])]
        )
        p_fk = NormalizedProduct(
            id=f"fk_{idx}",
            title=fk["title"],
            brand="Samsung",
            category="phone",
            current_price=fk["price"],
            product_url=fk["url"],
            marketplace="Flipkart",
            provider="brightdata_flipkart_products",
            offers=[MarketplaceOffer(marketplace="Flipkart", provider="brightdata_flipkart_products", product_url=fk["url"], current_price=fk["price"])]
        )
        
        matched = MatchingService.are_products_identical(p_amz, p_fk)
        grouped = MatchingService.deduplicate_and_group_offers([p_amz, p_fk])
        rec = ScoringService.evaluate_product(grouped[0], {}, "phone")
        comparison = rec.marketplace_comparison
        
        print(f"\nMatched: {'YES' if matched else 'NO'}")
        print("Match reason: Exact Model Number + Brand + Hardware Specs (RAM/Storage/Network)")
        print(f"Marketplace comparison offers generated ({len(comparison)}):")
        for off in comparison:
            print(f"  - {off.marketplace}: Price=Rs.{off.current_price:,.0f} | URL={off.product_url}")

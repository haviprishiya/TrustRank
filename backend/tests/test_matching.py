import unittest
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.matching_service import MatchingService

class TestMatchingService(unittest.TestCase):
    def test_multi_marketplace_deduplication_and_offers(self):
        prod_amazon = NormalizedProduct(
            id="amzn_101",
            title="Acer Nitro V Gaming Laptop 16GB RAM 512GB SSD RTX 4050",
            brand="Acer",
            category="laptop",
            image_url="https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500",
            current_price=71990.0,
            original_price=89990.0,
            discount_percent=20.0,
            currency="INR",
            rating=4.4,
            review_count=1850,
            availability="In Stock",
            product_url="https://www.amazon.in/dp/B0CX234",
            marketplace="Amazon India",
            provider="amazon_paapi_india",
            specifications={"RAM": "16 GB", "Storage": "512 GB SSD", "Graphics": "RTX 4050"},
            features=["144Hz FHD Display", "Intel Core i5 13th Gen"],
            offers=[
                MarketplaceOffer(
                    marketplace="Amazon India",
                    provider="amazon_paapi_india",
                    product_url="https://www.amazon.in/dp/B0CX234",
                    current_price=71990.0,
                    original_price=89990.0,
                    discount_percent=20.0,
                    currency="INR",
                    in_stock=True,
                    rating=4.4,
                    review_count=1850
                )
            ]
        )

        prod_flipkart = NormalizedProduct(
            id="fk_202",
            title="Acer Nitro V Intel Core i5 13th Gen 16 GB 512 GB SSD RTX 4050 Graphics Gaming Laptop",
            brand="Acer",
            category="laptop",
            image_url="https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500",
            current_price=70990.0,
            original_price=89990.0,
            discount_percent=21.0,
            currency="INR",
            rating=4.3,
            review_count=1200,
            availability="In Stock",
            product_url="https://www.flipkart.com/acer-nitro-v-gaming-laptop/p/itm123",
            marketplace="Flipkart",
            provider="flipkart_affiliate",
            specifications={"RAM": "16 GB", "Storage": "512 GB SSD", "Graphics": "RTX 4050"},
            features=["144Hz Display", "Backlit Keyboard"],
            offers=[
                MarketplaceOffer(
                    marketplace="Flipkart",
                    provider="flipkart_affiliate",
                    product_url="https://www.flipkart.com/acer-nitro-v-gaming-laptop/p/itm123",
                    current_price=70990.0,
                    original_price=89990.0,
                    discount_percent=21.0,
                    currency="INR",
                    in_stock=True,
                    rating=4.3,
                    review_count=1200
                )
            ]
        )

        grouped = MatchingService.deduplicate_and_group_offers([prod_amazon, prod_flipkart])
        self.assertEqual(len(grouped), 1)
        unified = grouped[0]
        self.assertEqual(len(unified.offers), 2)
        # Should pick the best current price (₹70,990 on Flipkart)
        self.assertEqual(unified.current_price, 70990.0)
        offer_marketplaces = {o.marketplace for o in unified.offers}
        self.assertIn("Amazon India", offer_marketplaces)
        self.assertIn("Flipkart", offer_marketplaces)

if __name__ == '__main__':
    unittest.main()

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
        self.assertEqual(unified.current_price, 71990.0)
        self.assertEqual(unified.product_url, "https://www.amazon.in/dp/B0CX234")
        self.assertEqual(unified.image_url, prod_amazon.image_url)
        self.assertEqual(unified.rating, 4.4)
        self.assertEqual(unified.review_count, 1850)
        flipkart_offer = next(offer for offer in unified.offers if offer.marketplace == "Flipkart")
        self.assertEqual(flipkart_offer.current_price, 70990.0)
        self.assertEqual(flipkart_offer.product_url, "https://www.flipkart.com/acer-nitro-v-gaming-laptop/p/itm123")
        offer_marketplaces = {o.marketplace for o in unified.offers}
        self.assertIn("Amazon India", offer_marketplaces)
        self.assertIn("Flipkart", offer_marketplaces)

    def test_croma_offer_merging_and_review_analysis(self):
        prod_amazon = NormalizedProduct(
            id="amzn_201",
            title="Apple MacBook Air M2 16GB 256GB Midnight",
            brand="Apple",
            category="laptop",
            current_price=89900.0,
            original_price=99900.0,
            currency="INR",
            rating=4.5,
            review_count=300,
            availability="In Stock",
            product_url="https://www.amazon.in/dp/B0CXM2",
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
            specifications={"RAM": "16 GB", "Storage": "256 GB SSD", "Processor": "Apple M2"},
            offers=[
                MarketplaceOffer(
                    marketplace="Amazon India",
                    provider="brightdata_amazon_search",
                    product_url="https://www.amazon.in/dp/B0CXM2",
                    current_price=89900.0,
                    currency="INR",
                    rating=4.5,
                    review_count=300
                )
            ]
        )

        prod_croma = NormalizedProduct(
            id="croma_311847",
            title="Apple MacBook Air M2 16GB 256GB Midnight macOS",
            brand="Apple",
            category="laptop",
            current_price=88990.0,
            original_price=99900.0,
            currency="INR",
            rating=4.8,
            review_count=120,
            availability="In Stock",
            product_url="https://www.croma.com/apple-macbook-air-m2/p/311847",
            marketplace="Croma",
            provider="croma_electronics",
            specifications={"RAM": "16 GB", "Storage": "256 GB SSD", "Processor": "Apple M2"},
            offers=[
                MarketplaceOffer(
                    marketplace="Croma",
                    provider="croma_electronics",
                    product_url="https://www.croma.com/apple-macbook-air-m2/p/311847",
                    current_price=88990.0,
                    currency="INR",
                    rating=4.8,
                    review_count=120
                )
            ]
        )

        grouped = MatchingService.deduplicate_and_group_offers([prod_amazon, prod_croma])
        self.assertEqual(len(grouped), 1)
        unified = grouped[0]
        self.assertEqual(len(unified.offers), 2)
        offer_marketplaces = {o.marketplace for o in unified.offers}
        self.assertIn("Amazon India", offer_marketplaces)
        self.assertIn("Croma", offer_marketplaces)

        # Review analysis should include both Amazon and Croma ratings
        self.assertIsNotNone(unified.review_analysis)
        self.assertEqual(unified.review_analysis.total_reviews_analyzed, 420)  # 300 + 120
        croma_review = next(r for r in unified.review_analysis.marketplace_breakdown if r.marketplace == "Croma")
        self.assertEqual(croma_review.rating, 4.8)
        self.assertEqual(croma_review.review_count, 120)

    def test_three_marketplace_fashion_and_skincare_matching(self):
        prod_amazon = NormalizedProduct(
            id="amzn_skincare_1",
            title="Minimalist 10% Niacinamide Face Serum with Zinc For Blemishes 30ml",
            brand="Minimalist",
            category="skincare",
            current_price=599.0,
            original_price=599.0,
            currency="INR",
            rating=4.4,
            review_count=12500,
            availability="In Stock",
            product_url="https://www.amazon.in/dp/B08FBN56B1",
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
            offers=[
                MarketplaceOffer(
                    marketplace="Amazon India",
                    provider="brightdata_amazon_search",
                    product_url="https://www.amazon.in/dp/B08FBN56B1",
                    current_price=599.0,
                    original_price=599.0,
                    currency="INR",
                    rating=4.4,
                    review_count=12500,
                )
            ]
        )

        prod_flipkart = NormalizedProduct(
            id="fk_skincare_1",
            title="Be Minimalist 10% Niacinamide Face Serum 30 ml",
            brand="Be Minimalist",
            category="skincare",
            current_price=569.0,
            original_price=599.0,
            currency="INR",
            rating=4.5,
            review_count=8200,
            availability="In Stock",
            product_url="https://www.flipkart.com/minimalist-10-niacinamide/p/itm12345",
            marketplace="Flipkart",
            provider="brightdata_flipkart_products",
            offers=[
                MarketplaceOffer(
                    marketplace="Flipkart",
                    provider="brightdata_flipkart_products",
                    product_url="https://www.flipkart.com/minimalist-10-niacinamide/p/itm12345",
                    current_price=569.0,
                    original_price=599.0,
                    currency="INR",
                    rating=4.5,
                    review_count=8200,
                )
            ]
        )

        prod_myntra = NormalizedProduct(
            id="myntra_skincare_1",
            title="Minimalist 10% Niacinamide Serum 30ml",
            brand="Minimalist",
            category="skincare",
            current_price=549.0,
            original_price=599.0,
            currency="INR",
            rating=4.6,
            review_count=4500,
            availability="In Stock",
            product_url="https://www.myntra.com/face-serum/minimalist/123456/buy",
            marketplace="Myntra",
            provider="myntra_fashion",
            offers=[
                MarketplaceOffer(
                    marketplace="Myntra",
                    provider="myntra_fashion",
                    product_url="https://www.myntra.com/face-serum/minimalist/123456/buy",
                    current_price=549.0,
                    original_price=599.0,
                    currency="INR",
                    rating=4.6,
                    review_count=4500,
                )
            ]
        )

        grouped = MatchingService.deduplicate_and_group_offers([prod_amazon, prod_flipkart, prod_myntra])
        self.assertEqual(len(grouped), 1)
        unified = grouped[0]
        self.assertEqual(len(unified.offers), 3)
        offer_marketplaces = {o.marketplace for o in unified.offers}
        self.assertIn("Amazon India", offer_marketplaces)
        self.assertIn("Flipkart", offer_marketplaces)
        self.assertIn("Myntra", offer_marketplaces)

        # Comparison service integration check
        from app.services.comparison_service import ComparisonService
        comp_offers = {o.marketplace: o for o in ComparisonService.marketplace_offers(unified)}
        self.assertIn("Amazon", comp_offers)
        self.assertIn("Flipkart", comp_offers)
        self.assertIn("Myntra", comp_offers)
        self.assertEqual(comp_offers["Amazon"].current_price, 599.0)
        self.assertEqual(comp_offers["Flipkart"].current_price, 569.0)
        self.assertEqual(comp_offers["Myntra"].current_price, 549.0)
        self.assertTrue(comp_offers["Myntra"].has_better_price)
        self.assertTrue(comp_offers["Myntra"].has_higher_rating)

if __name__ == '__main__':
    unittest.main()

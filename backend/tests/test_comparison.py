import unittest

from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.services.comparison_service import ComparisonService


class TestComparisonService(unittest.TestCase):
    def test_uses_real_offer_values_and_marks_better_price_and_rating(self):
        product = NormalizedProduct(
            id="phone-1", title="Example Phone", brand="Example", category="phone",
            current_price=30000, rating=4.2, review_count=200, availability="In Stock",
            product_url="https://www.amazon.in/dp/B0EXAMPLE", marketplace="Amazon India",
            provider="brightdata_amazon_search", offers=[
                MarketplaceOffer(
                    marketplace="Amazon India", provider="brightdata_amazon_search",
                    product_url="https://www.amazon.in/dp/B0EXAMPLE", current_price=30000,
                    rating=4.2, review_count=200, in_stock=True,
                ),
                MarketplaceOffer(
                    marketplace="Flipkart", provider="brightdata_flipkart_products",
                    product_url="https://www.flipkart.com/example/p/itm1", current_price=28000,
                    rating=4.5, review_count=500, in_stock=False,
                ),
            ],
        )

        offers = {offer.marketplace: offer for offer in ComparisonService.marketplace_offers(product)}

        self.assertEqual(offers["Amazon"].current_price, 30000)
        self.assertEqual(offers["Flipkart"].current_price, 28000)
        self.assertTrue(offers["Flipkart"].has_better_price)
        self.assertFalse(offers["Amazon"].has_better_price)
        self.assertTrue(offers["Flipkart"].has_higher_rating)
        self.assertEqual(offers["Amazon"].review_count, 200)
        self.assertEqual(offers["Flipkart"].availability, "Out of Stock")

    def test_missing_marketplace_offer_is_not_invented(self):
        product = NormalizedProduct(
            id="phone-2", title="Amazon Only Phone", brand="Example", category="phone",
            current_price=30000, rating=None, review_count=None, availability="Unknown",
            product_url="https://www.amazon.in/dp/B0ONLYAMZ", marketplace="Amazon India",
            provider="brightdata_amazon_search", offers=[],
        )

        offers = ComparisonService.marketplace_offers(product)

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].marketplace, "Amazon")
        self.assertIsNone(offers[0].rating)
        self.assertIsNone(offers[0].review_count)
        self.assertFalse(offers[0].has_better_price)

    def test_three_way_comparison_with_croma(self):
        product = NormalizedProduct(
            id="laptop-1", title="MacBook Air M2", brand="Apple", category="laptop",
            current_price=89900, rating=4.6, review_count=350, availability="In Stock",
            product_url="https://www.amazon.in/dp/B0MACBOOK", marketplace="Amazon India",
            provider="brightdata_amazon_search", offers=[
                MarketplaceOffer(
                    marketplace="Amazon India", provider="brightdata_amazon_search",
                    product_url="https://www.amazon.in/dp/B0MACBOOK", current_price=92000,
                    rating=4.5, review_count=300, in_stock=True,
                ),
                MarketplaceOffer(
                    marketplace="Flipkart", provider="brightdata_flipkart_products",
                    product_url="https://www.flipkart.com/macbook/p/itm1", current_price=91000,
                    rating=4.4, review_count=150, in_stock=True,
                ),
                MarketplaceOffer(
                    marketplace="Croma", provider="croma_electronics",
                    product_url="https://www.croma.com/macbook/p/311847", current_price=88990,
                    rating=4.8, review_count=85, in_stock=True,
                ),
            ],
        )

        offers = {offer.marketplace: offer for offer in ComparisonService.marketplace_offers(product)}

        self.assertEqual(len(offers), 3)
        self.assertIn("Croma", offers)
        self.assertEqual(offers["Croma"].current_price, 88990)
        # Croma has lowest price (88990 < 91000 < 92000)
        self.assertTrue(offers["Croma"].has_better_price)
        self.assertFalse(offers["Amazon"].has_better_price)
        self.assertFalse(offers["Flipkart"].has_better_price)
        # Croma has highest rating (4.8 > 4.5 > 4.4)
        self.assertTrue(offers["Croma"].has_higher_rating)
        self.assertFalse(offers["Amazon"].has_higher_rating)
        self.assertFalse(offers["Flipkart"].has_higher_rating)
        self.assertEqual(offers["Croma"].review_count, 85)


if __name__ == "__main__":
    unittest.main()

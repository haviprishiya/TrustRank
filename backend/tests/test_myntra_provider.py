import unittest
from unittest.mock import patch, AsyncMock

from app.providers.myntra_provider import MyntraProvider
from app.providers.registry import provider_registry
from app.models.schemas import NormalizedProduct
from app.services.brightdata_service import BrightDataServiceError
from app.services.review_service import ReviewService


class TestMyntraProvider(unittest.IsolatedAsyncioTestCase):
    def test_myntra_record_normalization(self):
        record = {
            "product_id": 25055006,
            "title": "Roadster",
            "product_description": "Men Maroon & Navy Blue Regular Fit Checked Casual Shirt",
            "url": "https://www.myntra.com/shirts/roadster/roadster-men-maroon--navy-blue-checked-casual-shirt/25055006/buy",
            "images": [
                "https://assets.myntassets.com/assets/images/25055006/test1.jpg",
                "https://assets.myntassets.com/assets/images/25055006/test2.jpg"
            ],
            "initial_price": 1499.0,
            "final_price": 599.0,
            "discount": 60.0,
            "rating": 4.2,
            "ratings_count": 3400,
            "reviews_count": 420,
            "product_specifications": [
                {"key": "Fabric", "value": "100% Cotton"},
                {"key": "Fit", "value": "Regular Fit"}
            ],
            "amount_of_stars": {
                "five_star": 2100,
                "four_star": 800,
                "three_star": 300,
                "two_star": 100,
                "one_star": 100
            },
            "what_customers_said": {
                "fit": "True to size",
                "quality": "Good fabric"
            }
        }

        product = MyntraProvider.normalize_record(record, "fashion")
        self.assertIsNotNone(product)
        self.assertIsInstance(product, NormalizedProduct)
        self.assertEqual(product.brand, "Roadster")
        self.assertEqual(product.title, "Roadster Men Maroon & Navy Blue Regular Fit Checked Casual Shirt")
        self.assertEqual(product.marketplace, "Myntra")
        self.assertEqual(product.provider, "myntra_fashion")
        self.assertEqual(product.source_product_id, "25055006")
        self.assertEqual(product.current_price, 599.0)
        self.assertEqual(product.original_price, 1499.0)
        self.assertEqual(product.discount_percent, 60.0)
        self.assertEqual(product.currency, "INR")
        self.assertEqual(product.rating, 4.2)
        self.assertEqual(product.review_count, 420)
        self.assertEqual(product.image_url, "https://assets.myntassets.com/assets/images/25055006/test1.jpg")
        self.assertEqual(product.specifications.get("Fabric"), "100% Cotton")
        self.assertEqual(product.specifications.get("Fit"), "Regular Fit")
        self.assertEqual(len(product.offers), 1)
        self.assertEqual(product.offers[0].marketplace, "Myntra")
        self.assertEqual(product.offers[0].current_price, 599.0)
        self.assertIsNone(product.offers[0].in_stock)
        self.assertIn("amount_of_stars", product.raw_data)
        self.assertIn("what_customers_said", product.raw_data)
        self.assertEqual(product.raw_data.get("ratings_count"), 3400)

    def test_missing_optional_fields_handling(self):
        minimal_record = {
            "product_id": 99999,
            "product_description": "Cotton Crew Neck T-Shirt",
            "url": "https://www.myntra.com/tshirts/brand/cotton-tshirt/99999/buy",
            "final_price": 499.0,
        }

        product = MyntraProvider.normalize_record(minimal_record, "clothing")
        self.assertIsNotNone(product)
        self.assertEqual(product.current_price, 499.0)
        self.assertIsNone(product.original_price)
        self.assertIsNone(product.discount_percent)
        self.assertIsNone(product.rating)
        self.assertIsNone(product.review_count)
        self.assertEqual(product.specifications, {})
        self.assertEqual(product.image_url, "")
        self.assertEqual(product.source_product_id, "99999")

    def test_invalid_or_non_myntra_url_rejected(self):
        invalid_record = {
            "title": "Not Myntra",
            "url": "https://www.flipkart.com/some-product/p/itm123",
            "final_price": 500.0
        }
        product = MyntraProvider.normalize_record(invalid_record, "fashion")
        self.assertIsNone(product)

    def test_review_analysis_reviews_unavailable_note(self):
        record = {
            "product_id": 12345,
            "title": "Puma",
            "product_description": "Running Shoes",
            "url": "https://www.myntra.com/shoes/puma/running-shoes/12345/buy",
            "final_price": 2999.0,
            "rating": 4.1,
            "reviews_count": 50,
        }
        product = MyntraProvider.normalize_record(record, "shoes")
        self.assertIsNotNone(product)

        analysis = ReviewService.analyze_product_reviews(product)
        self.assertIn("Reviews unavailable", analysis.source_note)

    def test_review_analysis_unrated_product_summary_reviews_unavailable(self):
        record = {
            "product_id": 54321,
            "title": "Roadster",
            "product_description": "Denim Jacket",
            "url": "https://www.myntra.com/jackets/roadster/denim/54321/buy",
            "final_price": 1999.0,
        }
        product = MyntraProvider.normalize_record(record, "clothing")
        self.assertIsNotNone(product)

        analysis = ReviewService.analyze_product_reviews(product)
        self.assertFalse(analysis.has_detailed_reviews)
        self.assertEqual(analysis.summary, "Reviews unavailable")

    def test_provider_registration(self):
        self.assertIn("myntra_fashion", provider_registry.providers)
        provider = provider_registry.get_provider("myntra_fashion")
        self.assertIsInstance(provider, MyntraProvider)
        self.assertEqual(provider.marketplace, "Myntra")

    async def test_non_fashion_category_skipped(self):
        provider = MyntraProvider()
        result = await provider.search("MacBook Air M2", "laptop")
        self.assertEqual(result, [])
        self.assertEqual(provider._last_status, "idle")
        self.assertIn("does not carry products for category 'laptop'", provider._last_message)

    async def test_search_uses_discovery_then_brightdata(self):
        provider = MyntraProvider()
        test_url = "https://www.myntra.com/shirts/roadster/shirt/25055006/buy"
        raw_record = {
            "product_id": 25055006,
            "title": "Roadster",
            "product_description": "Casual Shirt",
            "url": test_url,
            "final_price": 599.0,
            "rating": 4.2,
            "reviews_count": 100
        }

        with patch.object(provider, "is_configured", return_value=True), \
             patch.object(provider, "_search_direct_web", new_callable=AsyncMock, return_value=[test_url]), \
             patch("app.providers.myntra_provider.fetch_myntra_products", return_value=[raw_record]):
            products = await provider.search("roadster shirt", "fashion")

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].marketplace, "Myntra")
        self.assertEqual(products[0].current_price, 599.0)
        self.assertEqual(provider._last_status, "active")

    async def test_empty_brightdata_results_are_reported_without_fallback_products(self):
        provider = MyntraProvider()
        with patch.object(provider, "is_configured", return_value=True), \
             patch.object(provider, "_search_direct_web", new_callable=AsyncMock, return_value=[]):
            products = await provider.search("linen shirt", "shirt")

        self.assertEqual(products, [])
        self.assertEqual(provider._last_status, "empty")
        self.assertEqual(provider._last_message, "Live product data is currently unavailable for Myntra.")

    async def test_brightdata_failure_is_isolated_and_truthful(self):
        provider = MyntraProvider()
        test_url = "https://www.myntra.com/shirts/roadster/shirt/25055006/buy"
        with patch.object(provider, "is_configured", return_value=True), \
             patch.object(provider, "_search_direct_web", new_callable=AsyncMock, return_value=[test_url]), \
             patch("app.providers.myntra_provider.fetch_myntra_products", side_effect=BrightDataServiceError("Bright Data unavailable")):
            products = await provider.search("roadster shirt", "shirt")

        self.assertEqual(products, [])
        self.assertEqual(provider._last_status, "unavailable")
        self.assertIn("Bright Data unavailable", provider._last_message)

    async def test_duplicate_brightdata_products_are_removed(self):
        provider = MyntraProvider()
        test_url = "https://www.myntra.com/shirts/roadster/shirt/25055006/buy"
        raw_record = {
            "product_id": 25055006,
            "title": "Roadster",
            "product_description": "Casual Shirt",
            "url": test_url,
            "final_price": 599.0,
        }
        with patch.object(provider, "is_configured", return_value=True), \
             patch.object(provider, "_search_direct_web", new_callable=AsyncMock, return_value=[test_url]), \
             patch("app.providers.myntra_provider.fetch_myntra_products", return_value=[raw_record, raw_record]):
            products = await provider.search("roadster shirt", "shirt")

        self.assertEqual(len(products), 1)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, AsyncMock

from app.providers.croma_provider import CromaProvider
from app.models.schemas import NormalizedProduct


class TestCromaProvider(unittest.IsolatedAsyncioTestCase):
    def test_croma_record_normalization(self):
        title = "Apple MacBook Air (13.6 inch, M2, 16GB, 256GB, Midnight)"
        url = "https://www.croma.com/apple-macbook-air-13-6-inch-m2-16gb-256gb-macos-midnight-/p/311847"
        product = CromaProvider.normalize_croma_record(
            title=title,
            product_url=url,
            category="laptop",
            current_price=89900.0,
            original_price=99900.0,
            rating=4.7,
            review_count=142,
            image_url="https://media.croma.com/image/upload/v1234/test.jpg",
            brand="Apple"
        )
        self.assertIsNotNone(product)
        self.assertEqual(product.brand, "Apple")
        self.assertEqual(product.category, "laptop")
        self.assertEqual(product.current_price, 89900.0)
        self.assertEqual(product.original_price, 99900.0)
        self.assertEqual(product.discount_percent, 10.0)
        self.assertEqual(product.currency, "INR")
        self.assertEqual(product.rating, 4.7)
        self.assertEqual(product.review_count, 142)
        self.assertEqual(product.marketplace, "Croma")
        self.assertEqual(product.provider, "croma_electronics")
        self.assertEqual(product.source_product_id, "311847")
        self.assertEqual(len(product.offers), 1)
        self.assertEqual(product.offers[0].marketplace, "Croma")
        self.assertEqual(product.offers[0].current_price, 89900.0)

    def test_non_electronics_category_skipped(self):
        provider = CromaProvider()
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(provider.search("sunscreen", "skincare"))
        self.assertEqual(result, [])
        self.assertEqual(provider._last_status, "idle")
        self.assertIn("non-electronics", provider._last_message)

    def test_non_croma_or_search_url_rejected(self):
        # Search page URL should be rejected
        search_url = "https://www.croma.com/searchB?q=laptop"
        product = CromaProvider.normalize_croma_record(
            title="Laptops Search",
            product_url=search_url,
            category="laptop",
            current_price=50000.0
        )
        self.assertIsNone(product)

        # Non-Croma URL should be rejected
        external_url = "https://www.amazon.in/dp/B0TEST1234"
        product2 = CromaProvider.normalize_croma_record(
            title="Amazon Product",
            product_url=external_url,
            category="laptop",
            current_price=50000.0
        )
        self.assertIsNone(product2)

    def test_missing_reviews_gracefully_handled(self):
        url = "https://www.croma.com/samsung-galaxy-s24-5g/p/304123"
        product = CromaProvider.normalize_croma_record(
            title="Samsung Galaxy S24 5G",
            product_url=url,
            category="phone",
            current_price=74999.0,
            rating=None,
            review_count=None
        )
        self.assertIsNotNone(product)
        self.assertIsNone(product.rating)
        self.assertIsNone(product.review_count)
        self.assertEqual(product.offers[0].rating, None)
        self.assertEqual(product.offers[0].review_count, None)


if __name__ == "__main__":
    unittest.main()

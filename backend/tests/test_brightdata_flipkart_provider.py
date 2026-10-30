import unittest
from unittest.mock import patch

from app.providers.brightdata_provider import BrightDataFlipkartProvider
from app.services import brightdata_service
from app.services.brightdata_service import BrightDataServiceError


class TestBrightDataFlipkartProvider(unittest.IsolatedAsyncioTestCase):
    def test_normalizes_unified_schema_inr_fields(self):
        product = BrightDataFlipkartProvider.normalize_record({
            "item_id": "MOBHN7A8HYC9BPAU",
            "title": "realme P4x 5G (Matte Silver, 128 GB)",
            "url": "https://www.flipkart.com/realme-p4x-5g/p/itm575b1540859e4?pid=MOBHN7A8HYC9BPAU",
            "image_url": "https://images.example/phone.jpg",
            "price": "₹26,999",
            "sale_price": "₹24,999",
            "star_rating": "4.3",
            "review_count": "8,007",
            "availability": "in_stock",
            "brand": "realme",
            "store_name": "Flipkart",
        }, "phone")
        self.assertIsNotNone(product)
        self.assertEqual(product.current_price, 24999.0)
        self.assertEqual(product.original_price, 26999.0)
        self.assertEqual(product.currency, "INR")
        self.assertEqual(product.image_url, "https://images.example/phone.jpg")
        self.assertEqual(product.rating, 4.3)
        self.assertEqual(product.review_count, 8007)
        self.assertEqual(product.marketplace, "Flipkart")
        self.assertEqual(product.provider, "brightdata_flipkart_products")

    async def test_search_uses_discovery_then_unified_schema(self):
        provider = BrightDataFlipkartProvider()
        discovered_url = "https://www.flipkart.com/example-phone/p/itm123?pid=MOB123"
        unified_record = {
            "item_id": "MOB123", "title": "Example Phone", "url": discovered_url,
            "price": 59999, "image_url": "https://images.example/phone.jpg",
        }
        with patch.object(provider, "is_configured", return_value=True), patch(
            "app.providers.brightdata_provider.search_flipkart_product_urls", return_value=[discovered_url]
        ) as discovery, patch(
            "app.providers.brightdata_provider.fetch_flipkart_products", return_value=[unified_record]
        ) as unified:
            products = await provider.search("phone", "phone")
        discovery.assert_called_once_with("phone")
        unified.assert_called_once_with([discovered_url])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].current_price, 59999.0)
        self.assertEqual(provider._last_status, "active")

    async def test_provider_failure_returns_no_products_and_a_provider_error(self):
        provider = BrightDataFlipkartProvider()
        with patch.object(provider, "is_configured", return_value=True), patch(
            "app.providers.brightdata_provider.search_flipkart_product_urls",
            side_effect=BrightDataServiceError("Bright Data access was denied for this dataset.", 403),
        ):
            products = await provider.search("phone", "phone")
        self.assertEqual(products, [])
        self.assertEqual(provider._last_status, "unavailable")
        self.assertIn("access was denied", provider._last_message)

    def test_search_url_uses_query_and_discovery_dataset(self):
        with patch.object(brightdata_service, "_scrape_records", return_value=[
            {"url": "https://www.flipkart.com/example/p/itm123"},
        ]) as scrape:
            urls = brightdata_service.search_flipkart_product_urls("phone case")
        self.assertEqual(urls, ["https://www.flipkart.com/example/p/itm123"])
        self.assertEqual(scrape.call_args.args[0], brightdata_service.FLIPKART_SEARCH_DATASET_ID)
        self.assertIn("q=phone+case", scrape.call_args.args[1][0]["url"])

    def test_unified_schema_dataset_is_used_for_product_urls(self):
        with patch.object(brightdata_service, "_scrape_records", return_value=[]) as scrape:
            brightdata_service.fetch_flipkart_products(["https://www.flipkart.com/example/p/itm123"])
        self.assertEqual(scrape.call_args.args[0], brightdata_service.FLIPKART_PRODUCTS_DATASET_ID)
        self.assertEqual(scrape.call_args.args[1], [{"url": "https://www.flipkart.com/example/p/itm123", "all_variations": False}])

    def test_flipkart_image_priority_and_candidates(self):
        record = {
            "item_id": "TV123",
            "title": "LG 4K Smart TV",
            "url": "https://www.flipkart.com/lg-tv/p/itm123?pid=TV123",
            "primary_image": "https://images.example/primary.jpg",
            "image_url": "https://images.example/second.jpg",
            "image_urls": ["https://images.example/third.jpg", {"url": "https://images.example/fourth.jpg"}],
            "additional_image_urls": ["https://images.example/fifth.jpg"],
            "price": "45000",
        }
        product = BrightDataFlipkartProvider.normalize_record(record, "tv")
        self.assertIsNotNone(product)
        self.assertEqual(product.image_url, "https://images.example/primary.jpg")
        self.assertEqual(
            product.image_candidates,
            [
                "https://images.example/primary.jpg",
                "https://images.example/second.jpg",
                "https://images.example/third.jpg",
                "https://images.example/fourth.jpg",
                "https://images.example/fifth.jpg",
            ]
        )

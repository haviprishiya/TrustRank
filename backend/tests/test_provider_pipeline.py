import unittest
from unittest.mock import AsyncMock, patch

from app.models.schemas import MarketplaceOffer, NormalizedProduct
from app.providers.amazon_provider import AmazonCreatorsAPIProvider
from app.providers.brightdata_provider import BrightDataAmazonProvider
from app.providers.base import BaseProductProvider
from app.providers.registry import ProviderRegistry
from app.services.matching_service import MatchingService


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, *args, **kwargs):
        return self.response


class FakeProvider(BaseProductProvider):
    def __init__(self, provider_id, configured, result=None, error=None):
        super().__init__(provider_id, provider_id, provider_id)
        self.configured = configured
        self.result = result or []
        self.error = error

    def is_configured(self):
        return self.configured

    def get_required_env_keys(self):
        return ["FAKE_KEY"]

    async def search(self, query, category, limit=10):
        if self.error:
            raise self.error
        self._last_items_count = len(self.result)
        self._last_status = "active"
        return self.result


class TestProviderPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_brightdata_search_products_are_normalized_for_the_pipeline(self):
        provider = BrightDataAmazonProvider()
        brightdata_record = {
            "name": "Example Phone 128GB",
            "asin": "B012345678",
            "url": "https://www.amazon.in/dp/B012345678",
            "image": "https://images.example/phone.jpg",
            "final_price": "49,999.00",
            "initial_price": "54,999.00",
            "currency": "INR",
            "rating": 4.5,
            "num_ratings": "1,200",
            "brand": "Example",
            "availability": "In Stock",
        }
        with patch.object(provider, "is_configured", return_value=True), patch(
            "app.providers.brightdata_provider.search_amazon", return_value=[brightdata_record]
        ):
            products = await provider.search("phone", "phone")

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].title, "Example Phone 128GB")
        self.assertEqual(products[0].image_url, "https://images.example/phone.jpg")
        self.assertEqual(products[0].current_price, 49999.0)
        self.assertEqual(products[0].original_price, 54999.0)
        self.assertEqual(products[0].currency, "INR")
        self.assertEqual(products[0].rating, 4.5)
        self.assertEqual(products[0].review_count, 1200)
        self.assertEqual(products[0].product_url, "https://www.amazon.in/dp/B012345678")
        self.assertEqual(products[0].provider, "brightdata_amazon_search")

    async def test_creators_response_preserves_source_fields(self):
        provider = AmazonCreatorsAPIProvider()
        provider._get_access_token = AsyncMock(return_value="test-token")
        response = FakeResponse(200, {
            "itemsResult": {"items": [{
                "asin": "B012345678",
                "detailPageURL": "https://www.amazon.in/dp/B012345678?tag=example-21",
                "images": {"primary": {"large": {"url": "https://images.example/item.jpg"}}},
                "itemInfo": {
                    "title": {"displayValue": "Example Phone 128GB"},
                    "byLineInfo": {"brand": {"displayValue": "Example"}},
                    "features": {"displayValues": ["128GB storage"]},
                },
                "customerReviews": {"starRating": {"value": 4.2}, "count": 2100},
                "offersV2": {"listings": [{
                    "price": {"amount": 11999},
                    "availability": {"message": "In Stock"},
                }]},
            }]}
        })

        with patch.object(provider, "is_configured", return_value=True), patch("app.providers.amazon_provider.httpx.AsyncClient", return_value=FakeClient(response)):
            products = await provider.search("phone", "phone")

        self.assertEqual(len(products), 1)
        product = products[0]
        self.assertEqual(product.source_product_id, "B012345678")
        self.assertEqual(product.product_url, "https://www.amazon.in/dp/B012345678?tag=example-21")
        self.assertEqual(product.image_url, "https://images.example/item.jpg")
        self.assertEqual(product.current_price, 11999)
        self.assertEqual(product.rating, 4.2)
        self.assertEqual(product.review_count, 2100)
        self.assertIsNone(product.seller)

    async def test_creators_response_allows_missing_optional_fields(self):
        provider = AmazonCreatorsAPIProvider()
        provider._get_access_token = AsyncMock(return_value="test-token")
        response = FakeResponse(200, {
            "itemsResult": {"items": [{
                "asin": "B012345678",
                "detailPageURL": "https://www.amazon.in/dp/B012345678",
                "itemInfo": {"title": {"displayValue": "Example Phone"}},
            }]}
        })

        with patch.object(provider, "is_configured", return_value=True), patch("app.providers.amazon_provider.httpx.AsyncClient", return_value=FakeClient(response)):
            products = await provider.search("phone", "phone")

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].image_url, "")
        self.assertIsNone(products[0].current_price)
        self.assertIsNone(products[0].rating)
        self.assertIsNone(products[0].review_count)
        self.assertEqual(products[0].availability, "Unknown")

    async def test_registry_selects_configured_provider_and_isolates_failure(self):
        product = NormalizedProduct(
            id="real-1", source_product_id="source-1", title="Phone", brand="Example",
            category="phone", product_url="https://example.com/p/1", marketplace="Example",
            provider="configured",
        )
        registry = ProviderRegistry()
        registry.providers = {
            "missing": FakeProvider("missing", False, [product]),
            "working": FakeProvider("working", True, [product]),
            "broken": FakeProvider("broken", True, error=RuntimeError("provider failure")),
        }

        products = await registry.search_all("phone", "phone")

        self.assertEqual([p.id for p in products], ["real-1"])
        self.assertEqual(registry.providers["broken"].get_status().status, "unavailable")
        self.assertEqual(registry.providers["missing"].get_status().diagnostic_code, "configuration_missing")

    def test_deduplication_preserves_cross_marketplace_offers(self):
        amazon = NormalizedProduct(
            id="amazon-1", source_product_id="ASIN-1", title="Example Phone 128GB", brand="Example",
            category="phone", product_url="https://www.amazon.in/dp/ASIN-1", marketplace="Amazon India",
            provider="amazon_creators_india",
            offers=[MarketplaceOffer(marketplace="Amazon India", provider="amazon_creators_india", product_url="https://www.amazon.in/dp/ASIN-1")],
        )
        flipkart = NormalizedProduct(
            id="flipkart-1", source_product_id="FSN-1", title="Example Phone 128GB", brand="Example",
            category="phone", product_url="https://www.flipkart.com/example/p/FSN-1", marketplace="Flipkart",
            provider="flipkart_affiliate",
            offers=[MarketplaceOffer(marketplace="Flipkart", provider="flipkart_affiliate", product_url="https://www.flipkart.com/example/p/FSN-1")],
        )

        grouped = MatchingService.deduplicate_and_group_offers([amazon, flipkart])

        self.assertEqual(len(grouped), 1)
        self.assertEqual({offer.marketplace for offer in grouped[0].offers}, {"Amazon India", "Flipkart"})


if __name__ == "__main__":
    unittest.main()

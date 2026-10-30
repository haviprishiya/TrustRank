import unittest
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from app.main import app


class TestBrightDataProductsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.url = "https://www.amazon.in/dp/B0TEST1234"

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_success_returns_normalized_products(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            "title": "Example Headphones",
            "price": "1,999.00",
            "currency": "INR",
            "rating": "4.4",
            "reviews_count": "126",
            "image_url": "https://images.example/headphones.jpg",
            "url": self.url,
            "brand": "Example",
            "availability": "In Stock",
            "asin": "B0TEST1234",
        }]
        mock_post.return_value = response

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 200)
        payload = result.json()
        self.assertEqual(payload["count"], 1)
        product = payload["products"][0]
        self.assertEqual(product["title"], "Example Headphones")
        self.assertEqual(product["price"], 1999.0)
        self.assertEqual(product["reviews_count"], 126)
        self.assertEqual(product["image"], "https://images.example/headphones.jpg")
        self.assertEqual(product["url"], self.url)
        self.assertNotIn("test-key", str(payload))
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs["json"], [{"url": self.url}])
        self.assertEqual(mock_post.call_args.kwargs["params"]["dataset_id"], "gd_l7q7dkf244hwjntr0")

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_normalizes_documented_brightdata_fields(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            "name": "Bright Data Amazon Product",
            "final_price": "$19.95",
            "initial_price": "$29.95",
            "currency": "USD",
            "product_rating": "4.7 out of 5 stars",
            "number_of_reviews": "1,234 ratings",
            "images": ["https://images.example/product.jpg"],
            "product_url": self.url,
            "manufacturer": "Bright Brand",
            "asin": "B0TEST1234",
        }]
        mock_post.return_value = response

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 200)
        product = result.json()["products"][0]
        self.assertEqual(product["title"], "Bright Data Amazon Product")
        self.assertEqual(product["price"], 19.95)
        self.assertEqual(product["original_price"], 29.95)
        self.assertEqual(product["rating"], 4.7)
        self.assertEqual(product["reviews_count"], 1234)
        self.assertEqual(product["image"], "https://images.example/product.jpg")

    @patch("app.services.brightdata_service.os.getenv", return_value="")
    def test_scrape_missing_key_returns_safe_error(self, _mock_getenv):
        result = self.client.post("/products/scrape", json={"url": self.url})
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json()["detail"], "Bright Data is not configured on the server.")

    def test_scrape_rejects_non_amazon_url(self):
        result = self.client.post("/products/scrape", json={"url": "https://example.com/product"})
        self.assertEqual(result.status_code, 422)

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_asin_is_normalized_before_scraping(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{"asin": "B0CRMZHDG8", "title": "Example"}]
        mock_post.return_value = response
        result = self.client.post("/products/scrape", json={"url": "B0CRMZHDG8"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_post.call_args.kwargs["json"][0]["url"], "https://www.amazon.in/dp/B0CRMZHDG8")

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_query_searches_amazon_india_without_an_asin_or_url(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            "title": "Samsung Galaxy Example", "price": "₹19,999", "rating": "4.4",
            "reviews_count": "1,234", "main_image": "https://images.example/phone.jpg",
            "url": "https://www.amazon.in/dp/B0TEST1234", "asin": "B0TEST1234",
        }]
        mock_post.return_value = response

        result = self.client.post("/products/scrape", json={"query": "Samsung phone"})

        self.assertEqual(result.status_code, 200)
        product = result.json()["products"][0]
        self.assertEqual(product["currency"], "INR")
        self.assertEqual(product["price"], 19999.0)
        self.assertEqual(product["asin"], "B0TEST1234")
        self.assertEqual(mock_post.call_args.kwargs["params"]["dataset_id"], "gd_lwdb4vjm1ehb499uxs")
        self.assertEqual(mock_post.call_args.kwargs["json"], {"input": [{
            "keyword": "Samsung phone", "url": "https://www.amazon.in", "pages_to_search": 1,
        }]})

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.get")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_202_snapshot_response_is_downloaded(self, mock_post, mock_get, _mock_getenv):
        queued = Mock(status_code=202)
        queued.raise_for_status.return_value = None
        queued.json.return_value = {"snapshot_id": "snapshot-123"}
        progress = Mock()
        progress.raise_for_status.return_value = None
        progress.json.return_value = {"status": "ready"}
        snapshot = Mock()
        snapshot.raise_for_status.return_value = None
        snapshot.json.return_value = [{"title": "Snapshot Product", "asin": "B0TEST1234"}]
        mock_post.return_value = queued
        mock_get.side_effect = [progress, snapshot]

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["count"], 1)
        self.assertEqual(result.json()["products"][0]["title"], "Snapshot Product")

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_provider_failure_returns_safe_error(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("provider response omitted")
        mock_post.return_value = response

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json()["detail"], "Amazon scraping service is unavailable. Please try again.")

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_timeout_returns_gateway_timeout(self, mock_post, _mock_getenv):
        mock_post.side_effect = requests.Timeout()

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 504)
        self.assertEqual(result.json()["detail"], "Amazon scraping timed out. Please try again.")

    @patch("app.services.brightdata_service.os.getenv", return_value="test-key")
    @patch("app.services.brightdata_service.requests.post")
    def test_scrape_empty_response_returns_safe_error(self, mock_post, _mock_getenv):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = []
        mock_post.return_value = response

        result = self.client.post("/products/scrape", json={"url": self.url})

        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.json()["detail"], "Bright Data did not return products for this Amazon search.")

    def test_scrape_rejects_amazon_non_product_url(self):
        result = self.client.post("/products/scrape", json={"url": "https://www.amazon.com/s?k=headphones"})
        self.assertEqual(result.status_code, 422)


if __name__ == "__main__":
    unittest.main()

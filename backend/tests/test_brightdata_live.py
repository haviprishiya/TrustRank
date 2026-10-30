"""Opt-in integration test for the real Bright Data Amazon Products scraper.

Run with RUN_BRIGHTDATA_LIVE_TEST=1 from the backend directory.  It uses the
server-only BRIGHTDATA_API_KEY from backend/.env and never prints that key.
"""

import os
import unittest

from fastapi.testclient import TestClient

from app.main import app


@unittest.skipUnless(os.getenv("RUN_BRIGHTDATA_LIVE_TEST") == "1", "set RUN_BRIGHTDATA_LIVE_TEST=1 to run the paid live integration test")
class TestBrightDataLive(unittest.TestCase):
    def test_real_amazon_query_returns_normalized_products(self):
        response = TestClient(app).post(
            "/products/scrape",
            json={"query": "Samsung phone"},
        )
        self.assertEqual(response.status_code, 200, response.json().get("detail"))
        payload = response.json()
        self.assertGreaterEqual(payload["count"], 1)
        self.assertEqual(len(payload["products"]), payload["count"])
        self.assertTrue(payload["products"][0]["title"])
        self.assertIsNotNone(payload["products"][0]["price"])
        self.assertEqual(payload["products"][0]["currency"], "INR")

    def test_real_phone_search_reaches_recommendation_pipeline(self):
        response = TestClient(app).post(
            "/api/recommendations/generate",
            json={"query": "phone", "category": "phone", "answers": {}},
        )
        self.assertEqual(response.status_code, 200, response.json().get("detail"))
        payload = response.json()
        self.assertGreaterEqual(len(payload["recommendations"]), 1)
        product = payload["recommendations"][0]["product"]
        self.assertEqual(product["provider"], "brightdata_amazon_search")
        self.assertTrue(product["title"])
        self.assertTrue(product["image_url"])
        self.assertIsNotNone(product["current_price"])
        self.assertTrue(product["currency"])
        self.assertIsNotNone(product["rating"])
        self.assertIsNotNone(product["review_count"])
        self.assertTrue(product["brand"])
        self.assertTrue(product["availability"])
        self.assertTrue(product["product_url"])
        self.assertEqual(product["source"], "Bright Data Amazon Products Search")

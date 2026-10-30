import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["app"], "TrustRank")

    def test_providers_status(self):
        res = self.client.get("/api/providers/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("brightdata", data)
        self.assertIn("ai", data)
        self.assertIn("image", data)
        self.assertIn("search", data)
        self.assertIsInstance(data["providers"], list)
        self.assertGreater(len(data["providers"]), 0)

    def test_image_endpoint_reports_missing_configuration(self):
        res = self.client.post("/api/images/generate", json={"prompt": "A product hero image"})
        self.assertEqual(res.status_code, 503)

    def test_intent_detection_endpoint(self):
        res = self.client.post("/api/search/intent", json={"query": "gaming laptop under 70000"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["detected_category"], "laptop")
        self.assertEqual(data["extracted_budget"], 70000.0)

    def test_dynamic_questions_endpoint(self):
        res = self.client.post("/api/search/questions", json={"query": "skincare for oily skin"})
        self.assertEqual(res.status_code, 200)
        questions = res.json()
        self.assertIsInstance(questions, list)
        q_ids = [q["id"] for q in questions]
        self.assertIn("skin_concern", q_ids)

    def test_recommendations_generate_endpoint(self):
        payload = {
            "query": "laptop",
            "category": "laptop",
            "answers": {
                "budget": 60000.0,
                "primary_use": "programming",
                "ram": "16GB",
                "storage": "512GB",
                "priority": "portability"
            }
        }
        res = self.client.post("/api/recommendations/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("intent", data)
        self.assertIn("recommendations", data)
        self.assertIn("top_5_comparison", data)
        self.assertIn("analytics", data)
        self.assertIn("provider_statuses", data)
        self.assertEqual(data["intent"]["detected_category"], "laptop")

    def test_empty_query_validation(self):
        res = self.client.post("/api/search/intent", json={"query": ""})
        self.assertEqual(res.status_code, 400)

if __name__ == '__main__':
    unittest.main()

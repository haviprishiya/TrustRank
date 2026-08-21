import unittest
from app.models.schemas import UserRequirementAnswers
from app.services.pipeline import RecommendationPipeline
from app.providers.registry import provider_registry

class TestPipelineIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_full_pipeline_flow(self):
        req = UserRequirementAnswers(
            query="gaming laptop under 75000",
            category="laptop",
            answers={
                "budget": 75000.0,
                "primary_use": "gaming",
                "ram": "16GB",
                "storage": "512GB",
                "priority": "performance"
            }
        )
        
        res = await RecommendationPipeline.run_pipeline(req)
        self.assertEqual(res.intent.detected_category, "laptop")
        self.assertIsNotNone(res.analytics)
        self.assertIsInstance(res.provider_statuses, list)
        self.assertGreater(len(res.provider_statuses), 0)
        
        # Verify provider statuses are truthful
        creators_status = next((p for p in res.provider_statuses if p.provider_id == "amazon_creators_india"), None)
        self.assertIsNotNone(creators_status)
        self.assertIn("AMAZON_CREATORS_CREDENTIAL_ID", creators_status.env_keys_required)

if __name__ == '__main__':
    unittest.main()

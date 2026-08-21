import unittest
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.scoring_service import ScoringService

class TestScoringService(unittest.TestCase):
    def test_budget_penalties_and_recommendation_scoring(self):
        product = NormalizedProduct(
            id="test_laptop_1",
            title="ASUS TUF Gaming A15 16GB RAM 512GB SSD RTX 4060",
            brand="ASUS",
            category="laptop",
            image_url="https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500",
            current_price=74990.0,
            original_price=94990.0,
            discount_percent=21.0,
            currency="INR",
            rating=4.5,
            review_count=2400,
            availability="In Stock",
            product_url="https://www.amazon.in/dp/B0TUF4060",
            marketplace="Amazon India",
            provider="amazon_paapi_india",
            specifications={"RAM": "16 GB", "Storage": "512 GB SSD", "Graphics": "RTX 4060", "Processor": "AMD Ryzen 7"},
            features=["144Hz FHD", "RGB Backlit keyboard"]
        )

        # User wants a gaming laptop with budget 75000 and 16GB RAM
        answers = {
            "budget": 75000.0,
            "primary_use": "gaming",
            "ram": "16GB",
            "storage": "512GB",
            "priority": "performance",
            "brands": ["ASUS"]
        }

        rec = ScoringService.evaluate_product(product, answers, "laptop")
        self.assertGreaterEqual(rec.trustrank_score, 85.0)
        self.assertGreaterEqual(rec.requirement_match_percentage, 90.0)
        self.assertEqual(rec.budget_fit_score, 100.0)
        self.assertTrue(len(rec.positive_reasons) > 0)
        self.assertTrue(len(rec.best_for_you_explanation) > 0)

    def test_badges_assignment(self):
        p1 = NormalizedProduct(id="1", title="A", brand="ASUS", category="laptop", image_url="", current_price=70000, rating=4.5, review_count=1000, availability="In Stock", product_url="", marketplace="Amazon India", provider="")
        p2 = NormalizedProduct(id="2", title="B", brand="Dell", category="laptop", image_url="", current_price=50000, rating=4.2, review_count=3000, availability="In Stock", product_url="", marketplace="Flipkart", provider="")
        p3 = NormalizedProduct(id="3", title="C", brand="Lenovo", category="laptop", image_url="", current_price=80000, rating=4.7, review_count=5000, availability="In Stock", product_url="", marketplace="Amazon India", provider="")
        
        answers = {"budget": 75000.0, "primary_use": "programming", "ram": "16GB"}
        recs = [
            ScoringService.evaluate_product(p1, answers, "laptop"),
            ScoringService.evaluate_product(p2, answers, "laptop"),
            ScoringService.evaluate_product(p3, answers, "laptop")
        ]
        
        ranked = ScoringService.rank_and_assign_badges(recs)
        all_badges = [b for r in ranked for b in r.category_badges]
        self.assertIn("Best for You", all_badges)
        self.assertIn("Best Value", all_badges)
        self.assertIn("Best Reviewed", all_badges)

if __name__ == '__main__':
    unittest.main()

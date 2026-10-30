import unittest
from app.services.intent_service import IntentService
from app.services.question_service import QuestionService
from app.services.scoring_service import ScoringService
from app.models.schemas import NormalizedProduct

class TestDynamicCategories(unittest.TestCase):
    def test_all_category_detections_and_question_generation(self):
        cases = [
            ("apple iphone 15 pro max", "phone", ["budget", "ram", "storage", "camera", "battery", "display", "connectivity_5g"]),
            ("dell xps 15 gaming laptop", "laptop", ["budget", "processor", "ram", "storage", "gpu", "display", "battery"]),
            ("women floral summer dress", "dress", ["budget", "size", "color", "fabric", "fit", "pattern", "occasion"]),
            ("nike pegasus running shoes", "shoes", ["budget", "size", "type", "material", "color", "sole", "usage"]),
            ("sony bravia 55 inch 4k tv", "tv", ["budget", "screen_size", "resolution", "display_type", "refresh_rate", "smart_features"]),
            ("samsung double door refrigerator 260l", "refrigerator", ["budget", "capacity", "door_type", "energy_rating", "inverter", "frost_free"]),
            ("sony wh-1000xm5 wireless anc headphones", "headphones", ["budget", "type", "anc", "battery_life", "bluetooth", "microphone"]),
            ("canon eos r6 mirrorless camera", "camera", ["budget", "sensor", "megapixel", "lens", "video_resolution", "stabilization"]),
            ("samsung galaxy smartwatch amoled", "smartwatch", ["budget", "display", "battery", "gps", "calling", "health_features"]),
            ("ergonomic wooden office chair", "furniture", ["budget", "size", "material", "color", "style", "storage"]),
            ("philips digital air fryer 4l", "kitchen_appliances", ["budget", "type", "capacity", "power", "features"]),
            ("bosch front load 7kg washing machine", "washing_machine", ["budget", "machine_type", "capacity", "inverter"]),
        ]

        for query, expected_cat, required_q_ids in cases:
            intent = IntentService.detect_intent(query)
            self.assertEqual(intent.detected_category, expected_cat, f"Failed category detection for query '{query}'")
            
            questions = QuestionService.get_questions_for_intent(intent)
            q_ids = [q.id for q in questions]
            for req_id in required_q_ids:
                self.assertIn(req_id, q_ids, f"Question '{req_id}' missing for category '{expected_cat}'")

    def test_numeric_comparison_ram_ge_16gb(self):
        p_16gb = NormalizedProduct(
            id="l1",
            title="ASUS Vivobook 16GB RAM 512GB SSD",
            brand="ASUS",
            category="laptop",
            current_price=55000.0,
            availability="In Stock",
            marketplace="Amazon India",
            provider="amazon",
            specifications={"RAM": "16 GB", "Storage": "512 GB SSD"}
        )
        rec = ScoringService.evaluate_product(p_16gb, {"budget": 60000, "ram": "16GB"}, category="laptop")
        self.assertGreaterEqual(rec.requirement_match_percentage, 80.0)
        self.assertTrue(any("16GB" in r or "16 GB" in r for r in rec.positive_reasons))

        p_8gb = NormalizedProduct(
            id="l2",
            title="HP Laptop 8GB RAM 512GB SSD",
            brand="HP",
            category="laptop",
            current_price=45000.0,
            availability="In Stock",
            marketplace="Amazon India",
            provider="amazon",
            specifications={"RAM": "8 GB", "Storage": "512 GB SSD"}
        )
        rec_mismatch = ScoringService.evaluate_product(p_8gb, {"budget": 60000, "ram": "16GB"}, category="laptop")
        self.assertTrue(any("8 GB" in r or "8GB" in r for r in rec_mismatch.negative_reasons))

    def test_numeric_comparison_refrigerator_capacity_ge_250l(self):
        p_260l = NormalizedProduct(
            id="r1",
            title="LG 260 Litres Double Door Refrigerator",
            brand="LG",
            category="refrigerator",
            current_price=28000.0,
            availability="In Stock",
            marketplace="Flipkart",
            provider="flipkart",
            specifications={"Capacity": "260 Litres", "Door Type": "Double Door"}
        )
        rec = ScoringService.evaluate_product(p_260l, {"budget": 30000, "capacity": "250L"}, category="refrigerator")
        self.assertGreaterEqual(rec.requirement_match_percentage, 80.0)
        self.assertTrue(any("260 Litres" in r or "250L" in r for r in rec.positive_reasons))

    def test_numeric_comparison_tv_screen_size_ge_55_inch(self):
        p_43in = NormalizedProduct(
            id="t1",
            title="Sony Bravia 43 inch 4K Ultra HD TV",
            brand="Sony",
            category="tv",
            current_price=42000.0,
            availability="In Stock",
            marketplace="Amazon India",
            provider="amazon",
            specifications={"Screen Size": "43 inch", "Resolution": "4K"}
        )
        rec = ScoringService.evaluate_product(p_43in, {"budget": 50000, "screen_size": "55 inch"}, category="tv")
        self.assertTrue(any("43 inch" in r for r in rec.negative_reasons))

    def test_missing_attributes_show_not_available_without_guessing(self):
        p_sparse = NormalizedProduct(
            id="sparse1",
            title="Generic Fashion Women Dress",
            brand="Generic",
            category="dress",
            current_price=1500.0,
            availability="In Stock",
            marketplace="Amazon India",
            provider="amazon",
            specifications={}
        )
        rec = ScoringService.evaluate_product(p_sparse, {
            "budget": 2000,
            "fabric": "Silk",
            "fit": "Bodycon"
        }, category="dress")
        
        # Must report Not available rather than guessing
        self.assertTrue(any("Not available in listing specifications" in obs for obs in rec.neutral_observations))

if __name__ == '__main__':
    unittest.main()

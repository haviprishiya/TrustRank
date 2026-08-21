import unittest
from app.services.intent_service import IntentService

class TestIntentService(unittest.TestCase):
    def test_phone_does_not_match_headphones(self):
        intent_phone = IntentService.detect_intent("phone")
        self.assertEqual(intent_phone.detected_category, "phone")
        
        intent_smartphone = IntentService.detect_intent("best 5g smartphone")
        self.assertEqual(intent_smartphone.detected_category, "phone")
        
        intent_headphones = IntentService.detect_intent("wireless headphones")
        self.assertEqual(intent_headphones.detected_category, "headphones")
        
        intent_earbuds = IntentService.detect_intent("noise cancelling earbuds")
        self.assertEqual(intent_earbuds.detected_category, "headphones")

    def test_budget_extraction(self):
        intent1 = IntentService.detect_intent("gaming laptop under 70000")
        self.assertEqual(intent1.detected_category, "laptop")
        self.assertEqual(intent1.extracted_budget, 70000.0)
        
        intent2 = IntentService.detect_intent("phone under 25k")
        self.assertEqual(intent2.detected_category, "phone")
        self.assertEqual(intent2.extracted_budget, 25000.0)
        
        intent3 = IntentService.detect_intent("4k tv below ₹45000")
        self.assertEqual(intent3.detected_category, "tv")
        self.assertEqual(intent3.extracted_budget, 45000.0)

    def test_skincare_and_features(self):
        intent = IntentService.detect_intent("skincare for oily skin and acne")
        self.assertEqual(intent.detected_category, "skincare")
        self.assertIn("Oily Skin Formulation", intent.extracted_features)
        
        intent_wash = IntentService.detect_intent("salicylic acid face wash")
        self.assertEqual(intent_wash.detected_category, "skincare")

    def test_brand_extraction(self):
        intent = IntentService.detect_intent("Apple MacBook Air M2 16GB")
        self.assertEqual(intent.detected_category, "laptop")
        self.assertIn("Apple", intent.extracted_brands)

if __name__ == '__main__':
    unittest.main()

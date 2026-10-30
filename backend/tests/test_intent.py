import unittest
from app.services.intent_service import IntentService
from app.services.question_service import QuestionService

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

    def test_generic_requirement_extraction(self):
        intent = IntentService.detect_intent("best shampoo for dandruff and oily scalp")
        self.assertEqual(intent.detected_category, "hair_care")
        self.assertEqual(intent.extracted_requirements, ["dandruff", "oily scalp"])

        intent = IntentService.detect_intent("phone with good camera under 30000")
        self.assertEqual(intent.extracted_requirements, ["good camera"])
        self.assertEqual(intent.extracted_budget, 30000.0)

    def test_product_specific_wizard_questions(self):
        shampoo = IntentService.detect_intent("shampoo")
        shampoo_questions = QuestionService.get_questions_for_intent(shampoo)
        shampoo_text = " ".join(q.question + " " + " ".join(option.label for option in q.options) for q in shampoo_questions).lower()
        self.assertEqual(shampoo.detected_category, "hair_care")
        self.assertIn("hair concern", shampoo_text)
        self.assertNotIn("face wash", shampoo_text)
        self.assertNotIn("sunscreen", shampoo_text)

        face_wash = IntentService.detect_intent("face wash")
        self.assertEqual(face_wash.detected_category, "skincare")
        self.assertIn("skincare product", QuestionService.get_questions_for_intent(face_wash)[0].question.lower())

        lipstick = IntentService.detect_intent("lipstick")
        self.assertEqual(lipstick.detected_category, "makeup")
        self.assertIn("makeup", QuestionService.get_questions_for_intent(lipstick)[0].question.lower())

        chair = IntentService.detect_intent("office chair")
        self.assertEqual(chair.detected_category, "furniture")
        self.assertIn("chair", " ".join(q.question.lower() for q in QuestionService.get_questions_for_intent(chair)))

if __name__ == '__main__':
    unittest.main()

import unittest
from app.services.intent_service import IntentService
from app.services.question_service import QuestionService

class TestQuestionService(unittest.TestCase):
    def test_dynamic_questions_for_laptop(self):
        intent = IntentService.detect_intent("gaming laptop under 75000")
        questions = QuestionService.get_questions_for_intent(intent)
        
        q_ids = [q.id for q in questions]
        self.assertIn("budget", q_ids)
        self.assertIn("primary_use", q_ids)
        self.assertIn("ram", q_ids)
        self.assertIn("storage", q_ids)
        self.assertIn("priority", q_ids)
        self.assertIn("brands", q_ids)
        
        # Check budget was pre-populated
        budget_q = next(q for q in questions if q.id == "budget")
        self.assertEqual(budget_q.default_value, 75000.0)

    def test_dynamic_questions_for_skincare(self):
        intent = IntentService.detect_intent("skincare for oily acne prone skin")
        questions = QuestionService.get_questions_for_intent(intent)
        
        q_ids = [q.id for q in questions]
        self.assertIn("product_type", q_ids)
        self.assertIn("skin_concern", q_ids)
        self.assertIn("preferred_ingredients", q_ids)
        self.assertIn("avoid_ingredients", q_ids)
        
        concern_q = next(q for q in questions if q.id == "skin_concern")
        self.assertEqual(concern_q.default_value, "oily_acne")

if __name__ == '__main__':
    unittest.main()

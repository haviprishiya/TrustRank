import unittest
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.scoring_service import ScoringService

class TestScoringService(unittest.TestCase):
    @staticmethod
    def _marketplace_product(marketplace="Amazon India", price=28000.0, rating=4.2, review_count=1000, availability="In Stock"):
        return NormalizedProduct(
            id=f"{marketplace}-{price}-{rating}-{review_count}", title="Samsung Galaxy Example 5G 256GB",
            brand="Samsung", category="phone", image_url="https://images.example/phone.jpg",
            current_price=price, currency="INR", rating=rating, review_count=review_count,
            availability=availability, product_url=f"https://example.com/{marketplace}/{price}",
            marketplace=marketplace, provider="brightdata_amazon_search" if "Amazon" in marketplace else "brightdata_flipkart_products",
            specifications={"Storage": "256 GB", "Network": "5G Enabled"}, features=[],
        )

    @staticmethod
    def _phone_answers():
        return {"budget": 30000.0, "primary_use": "balanced", "storage": "256GB"}

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

    def test_actual_price_changes_the_price_component(self):
        lower_price = ScoringService.evaluate_product(self._marketplace_product(price=14000.0), self._phone_answers(), "phone")
        higher_price = ScoringService.evaluate_product(self._marketplace_product(price=56000.0), self._phone_answers(), "phone")

        self.assertGreater(lower_price.price_value_score, higher_price.price_value_score)
        self.assertIn("14,000", lower_price.scoring_breakdown_explanation["budget_fit"])
        self.assertIn("56,000", higher_price.scoring_breakdown_explanation["budget_fit"])

    def test_actual_rating_changes_the_rating_component(self):
        lower_rating = ScoringService.evaluate_product(self._marketplace_product(rating=3.5), self._phone_answers(), "phone")
        higher_rating = ScoringService.evaluate_product(self._marketplace_product(rating=4.8), self._phone_answers(), "phone")

        self.assertEqual(lower_rating.rating_score, 70.0)
        self.assertEqual(higher_rating.rating_score, 96.0)
        self.assertGreater(higher_rating.trustrank_score, lower_rating.trustrank_score)

    def test_actual_review_count_changes_the_review_component(self):
        few_reviews = ScoringService.evaluate_product(self._marketplace_product(review_count=10), self._phone_answers(), "phone")
        many_reviews = ScoringService.evaluate_product(self._marketplace_product(review_count=10000), self._phone_answers(), "phone")

        self.assertEqual(few_reviews.review_confidence_score, 25.0)
        self.assertEqual(many_reviews.review_confidence_score, 100.0)
        self.assertGreater(many_reviews.trustrank_score, few_reviews.trustrank_score)

    def test_actual_availability_changes_the_availability_component(self):
        in_stock = ScoringService.evaluate_product(self._marketplace_product(availability="In Stock"), self._phone_answers(), "phone")
        out_of_stock = ScoringService.evaluate_product(self._marketplace_product(availability="Out of Stock"), self._phone_answers(), "phone")

        self.assertEqual(in_stock.availability_score, 100.0)
        self.assertEqual(out_of_stock.availability_score, 0.0)
        self.assertGreater(in_stock.trustrank_score, out_of_stock.trustrank_score)

    def test_amazon_and_flipkart_products_are_scored_independently(self):
        amazon = ScoringService.evaluate_product(
            self._marketplace_product("Amazon India", price=30000.0, rating=4.1, review_count=500), self._phone_answers(), "phone"
        )
        flipkart = ScoringService.evaluate_product(
            self._marketplace_product("Flipkart", price=24000.0, rating=4.6, review_count=5000), self._phone_answers(), "phone"
        )

        self.assertEqual(amazon.product.marketplace, "Amazon India")
        self.assertEqual(flipkart.product.marketplace, "Flipkart")
        self.assertEqual(amazon.product.current_price, 30000.0)
        self.assertEqual(flipkart.product.current_price, 24000.0)
        self.assertNotEqual(amazon.trustrank_score, flipkart.trustrank_score)

    def test_missing_marketplace_data_has_no_substitute_component_score(self):
        recommendation = ScoringService.evaluate_product(
            self._marketplace_product(price=None, rating=None, review_count=None, availability="Unknown"), self._phone_answers(), "phone"
        )

        self.assertEqual(recommendation.price_value_score, 0.0)
        self.assertEqual(recommendation.rating_score, 0.0)
        self.assertEqual(recommendation.review_confidence_score, 0.0)
        self.assertEqual(recommendation.availability_score, 0.0)

    def test_recommendations_reflect_selected_preferences(self):
        budget_fitting_samsung = NormalizedProduct(
            id="samsung-m36", title="Samsung Galaxy M36 5G (8GB RAM, 128GB Storage)",
            brand="Samsung", category="phone", image_url="https://images.example/samsung.jpg",
            current_price=22000.0, currency="INR", rating=4.4, review_count=3500,
            availability="In Stock", product_url="https://amazon.in/samsung-m36",
            marketplace="Amazon India", provider="serpapi_shopping_india",
            specifications={"RAM": "8 GB", "Storage": "128 GB"}, features=["5G Network", "5000mAh Battery"]
        )

        expensive_samsung = NormalizedProduct(
            id="samsung-s24-ultra", title="Samsung Galaxy S24 Ultra 5G (12GB RAM, 256GB Storage)",
            brand="Samsung", category="phone", image_url="https://images.example/ultra.jpg",
            current_price=105000.0, currency="INR", rating=4.8, review_count=12000,
            availability="In Stock", product_url="https://amazon.in/samsung-s24",
            marketplace="Amazon India", provider="serpapi_shopping_india",
            specifications={"RAM": "12 GB", "Storage": "256 GB"}, features=["5G", "S-Pen"]
        )

        non_5g_other_brand = NormalizedProduct(
            id="nokia-flip", title="Nokia 2660 4G Keypad Phone",
            brand="Nokia", category="phone", image_url="https://images.example/nokia.jpg",
            current_price=5200.0, currency="INR", rating=4.1, review_count=800,
            availability="In Stock", product_url="https://flipkart.com/nokia",
            marketplace="Flipkart", provider="serpapi_shopping_india",
            specifications={}, features=[]
        )

        user_prefs = {
            "budget": 30000.0,
            "brands": ["Samsung"],
            "connectivity_5g": "5g_required",
            "ram": "8GB",
            "storage": "128GB"
        }

        rec_fit = ScoringService.evaluate_product(budget_fitting_samsung, user_prefs, "phone")
        rec_exp = ScoringService.evaluate_product(expensive_samsung, user_prefs, "phone")
        rec_other = ScoringService.evaluate_product(non_5g_other_brand, user_prefs, "phone")

        # The budget-fitting device matching the preferred brand must score significantly higher
        self.assertGreater(rec_fit.trustrank_score, rec_exp.trustrank_score)
        self.assertGreater(rec_fit.trustrank_score, rec_other.trustrank_score)

        ranked = ScoringService.rank_and_assign_badges([rec_exp, rec_fit, rec_other], target_budget=30000.0)
        # First rank and "Best for You" badge must go to the recommendation that satisfies preferences and budget
        self.assertEqual(ranked[0].product.id, "samsung-m36")
        self.assertIn("Best for You", ranked[0].category_badges)
        self.assertNotIn("Best for You", rec_exp.category_badges)

    def test_min_and_max_price_range_filtration(self):
        in_range_prod = NormalizedProduct(
            id="midrange", title="Midrange Phone 5G", brand="Samsung", category="phone",
            image_url="", current_price=22000.0, rating=4.5, review_count=2000,
            availability="In Stock", product_url="", marketplace="Amazon India", provider=""
        )
        too_cheap_prod = NormalizedProduct(
            id="cheap", title="Entry Phone", brand="Samsung", category="phone",
            image_url="", current_price=5000.0, rating=4.2, review_count=1000,
            availability="In Stock", product_url="", marketplace="Amazon India", provider=""
        )
        too_expensive_prod = NormalizedProduct(
            id="expensive", title="Ultra Flagship Phone", brand="Samsung", category="phone",
            image_url="", current_price=90000.0, rating=4.8, review_count=8000,
            availability="In Stock", product_url="", marketplace="Amazon India", provider=""
        )

        user_prefs = {
            "min_price": 15000.0,
            "max_price": 30000.0,
            "budget": {"min": 15000.0, "max": 30000.0}
        }

        rec_in = ScoringService.evaluate_product(in_range_prod, user_prefs, "phone")
        rec_cheap = ScoringService.evaluate_product(too_cheap_prod, user_prefs, "phone")
        rec_exp = ScoringService.evaluate_product(too_expensive_prod, user_prefs, "phone")

        self.assertEqual(rec_in.budget_fit_score, 100.0)
        self.assertLess(rec_cheap.budget_fit_score, 75.0)
        self.assertLess(rec_exp.budget_fit_score, 60.0)
        self.assertGreater(rec_in.trustrank_score, rec_cheap.trustrank_score)
        self.assertGreater(rec_in.trustrank_score, rec_exp.trustrank_score)

        ranked = ScoringService.rank_and_assign_badges(
            [rec_cheap, rec_exp, rec_in],
            min_price=15000.0,
            max_price=30000.0
        )
        self.assertEqual(ranked[0].product.id, "midrange")
        self.assertIn("Best for You", ranked[0].category_badges)

if __name__ == '__main__':
    unittest.main()

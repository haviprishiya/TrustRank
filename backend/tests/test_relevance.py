import unittest

from app.models.schemas import NormalizedProduct
from app.services.intent_service import IntentService
from app.services.relevance_service import RelevanceService


class TestRelevanceService(unittest.TestCase):
    @staticmethod
    def product(title, category="general"):
        return NormalizedProduct(
            id=title,
            title=title,
            brand="Test",
            category=category,
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
        )

    def assert_titles(self, query, products, expected):
        intent = IntentService.detect_intent(query)
        filtered = RelevanceService.filter_products(products, query, intent)
        self.assertEqual([product.title for product in filtered], expected)

    def test_fridge_matches_refrigerator_synonym_only(self):
        self.assert_titles(
            "fridge",
            [self.product("LG 260L Refrigerator"), self.product("LG Washing Machine")],
            ["LG 260L Refrigerator"],
        )

    def test_model_queries_keep_model_numbers(self):
        self.assert_titles(
            "iPhone 15",
            [self.product("Apple iPhone 15 128GB", "phone"), self.product("Apple iPhone 14 128GB", "phone")],
            ["Apple iPhone 15 128GB"],
        )
        self.assert_titles(
            "Samsung A36 5G",
            [self.product("Samsung Galaxy A36 5G", "phone"), self.product("Samsung Galaxy A35 5G", "phone")],
            ["Samsung Galaxy A36 5G"],
        )

    def test_plain_shampoo_does_not_require_a_purpose(self):
        self.assert_titles(
            "shampoo",
            [
                self.product("Anti-Dandruff Shampoo", "hair_care"),
                self.product("Daily Moisture Shampoo", "hair_care"),
                self.product("Daily Hair Conditioner", "hair_care"),
            ],
            ["Anti-Dandruff Shampoo", "Daily Moisture Shampoo"],
        )

    def test_requirement_filters_shampoo(self):
        self.assert_titles(
            "shampoo for dandruff",
            [self.product("Anti-Dandruff Shampoo", "hair_care"), self.product("Daily Moisture Shampoo", "hair_care")],
            ["Anti-Dandruff Shampoo"],
        )

    def test_product_and_requirement_queries(self):
        self.assert_titles(
            "laptop for gaming",
            [self.product("ASUS Gaming Laptop RTX 4060", "laptop"), self.product("Dell Office Laptop", "laptop")],
            ["ASUS Gaming Laptop RTX 4060"],
        )
        self.assert_titles(
            "running shoes",
            [self.product("Nike Running Shoes", "shoes"), self.product("Nike Casual Sneakers", "shoes")],
            ["Nike Running Shoes"],
        )

    def test_food_is_excluded_from_non_food_query(self):
        self.assert_titles(
            "shampoo",
            [self.product("Daily Moisture Shampoo", "hair_care"), self.product("Fruit Juice", "food")],
            ["Daily Moisture Shampoo"],
        )

    def test_generic_mobile_query_keeps_valid_smartphones(self):
        p1 = NormalizedProduct(
            id="p1", title="Samsung Galaxy S24 Ultra 5G", brand="Samsung", category="phone",
            marketplace="Amazon India", provider="serpapi_shopping_india"
        )
        p2 = NormalizedProduct(
            id="p2", title="Motorola G45 5G", brand="Motorola", category="phone",
            marketplace="Flipkart", provider="serpapi_shopping_india"
        )
        p3 = NormalizedProduct(
            id="p3", title="Universal Phone Case Cover", brand="Generic", category="phone",
            marketplace="Amazon India", provider="serpapi_shopping_india"
        )
        intent = IntentService.detect_intent("mobile")
        filtered = RelevanceService.filter_products([p1, p2, p3], "mobile", intent)
        titles = [p.title for p in filtered]
        self.assertIn("Samsung Galaxy S24 Ultra 5G", titles)
        self.assertIn("Motorola G45 5G", titles)
        self.assertNotIn("Universal Phone Case Cover", titles)


if __name__ == "__main__":
    unittest.main()

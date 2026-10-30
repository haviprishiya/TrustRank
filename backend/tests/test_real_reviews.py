import unittest
from app.models.schemas import CustomerReview, NormalizedProduct, MarketplaceOffer
from app.services.review_service import ReviewService
from app.services.scoring_service import ScoringService
from app.providers.registry import provider_registry


class TestRealReviewsPipeline(unittest.TestCase):
    def test_customer_review_model(self):
        review = CustomerReview(
            id="R12345",
            product_id="B0GV1L119H",
            marketplace="Amazon India",
            rating=5.0,
            title="Exceptional build and performance",
            review_text="This laptop has exceeded all expectations for daily office tasks and video editing.",
            reviewer_name="Rahul Verma",
            review_date="15 September 2026",
            verified_purchase=True,
            source_url="https://www.amazon.in/dp/B0GV1L119H"
        )
        self.assertEqual(review.rating, 5.0)
        self.assertEqual(review.reviewer_name, "Rahul Verma")
        self.assertTrue(review.verified_purchase)
        self.assertEqual(review.product_id, "B0GV1L119H")

    def test_review_analysis_with_real_written_reviews(self):
        product = NormalizedProduct(
            id="brightdata_B0GV1L119H",
            source_product_id="B0GV1L119H",
            title="Dell 15 Laptop Intel Core i3 16GB 512GB SSD",
            brand="Dell",
            category="laptop",
            current_price=38990.0,
            currency="INR",
            rating=4.2,
            review_count=1117,
            availability="In Stock",
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
            raw_data={
                "written_reviews": [
                    {
                        "review_id": "rev_1",
                        "asin": "B0GV1L119H",
                        "rating": 5.0,
                        "title": "Brand is brand! Always prefer brand!",
                        "review_text": "As a first-time laptop user, the Dell 15 has exceeded my expectations with its excellent performance.",
                        "author_name": "Priyaansh Deepak",
                        "review_posted_date": "10 September 2026",
                        "is_verified": True
                    },
                    {
                        "review_id": "rev_2",
                        "asin": "B0GV1L119H",
                        "rating": 5.0,
                        "title": "Smooth multitasking and fast boot",
                        "review_text": "16GB RAM handles dozens of tabs effortlessly. Screen is crisp.",
                        "author_name": "Amit Sharma",
                        "review_posted_date": "8 September 2026",
                        "is_verified": True
                    },
                    {
                        "review_id": "rev_3",
                        "asin": "B0GV1L119H",
                        "rating": 3.0,
                        "title": "Battery life could be slightly longer",
                        "review_text": "Lasts around 5 hours on heavy use, but charging is fast.",
                        "author_name": "Kiran S",
                        "review_posted_date": "5 September 2026",
                        "is_verified": True
                    }
                ],
                "product_rating_object": {
                    "five_star": 581,
                    "four_star": 279,
                    "three_star": 78,
                    "two_star": 45,
                    "one_star": 134
                }
            }
        )

        analysis = ReviewService.analyze_product_reviews(product)

        self.assertTrue(analysis.has_detailed_reviews)
        self.assertEqual(analysis.written_reviews_count, 3)
        self.assertEqual(len(analysis.written_reviews), 3)
        self.assertEqual(analysis.total_reviews_analyzed, 1117)
        self.assertIn("Priyaansh Deepak", [r.reviewer_name for r in analysis.written_reviews])
        self.assertGreater(analysis.positive_percentage, 50.0)
        self.assertTrue(any("Brand is brand" in p for p in analysis.most_praised_features))
        self.assertIn("Verified customer reviews & ratings returned by Amazon India", analysis.source_note)
        self.assertIn("3 authentic customer reviews", analysis.summary)
        self.assertIn("1,117 total ratings", analysis.summary)

    def test_review_analysis_when_reviews_unavailable(self):
        product = NormalizedProduct(
            id="brightdata_flipkart_12345",
            source_product_id="12345",
            title="Lenovo V15 AMD Ryzen 3 8GB 512GB SSD",
            brand="Lenovo",
            category="laptop",
            current_price=32990.0,
            currency="INR",
            rating=4.0,
            review_count=342,
            availability="In Stock",
            marketplace="Flipkart",
            provider="brightdata_flipkart_products",
            raw_data={"reviews": None}
        )

        analysis = ReviewService.analyze_product_reviews(product)

        self.assertFalse(analysis.has_detailed_reviews)
        self.assertEqual(analysis.written_reviews_count, 0)
        self.assertEqual(len(analysis.written_reviews), 0)
        self.assertEqual(analysis.total_reviews_analyzed, 342)
        self.assertEqual(analysis.combined_rating, 4.0)
        self.assertIn("Reviews unavailable", analysis.source_note)
        self.assertIn("Written review bodies not provided by marketplace feed", analysis.summary)
        self.assertEqual(analysis.positive_percentage, 0.0)
        self.assertEqual(analysis.neutral_percentage, 0.0)
        self.assertEqual(analysis.negative_percentage, 0.0)
        self.assertEqual(analysis.most_praised_features, [])
        self.assertEqual(analysis.common_complaints, [])
        self.assertEqual(analysis.recurring_themes, [])

    def test_duplicate_written_reviews_are_removed_and_false_strings_stay_false(self):
        product = NormalizedProduct(
            id="flipkart_1", source_product_id="FSN-1", title="Example Phone", brand="Example",
            category="phone", marketplace="Flipkart", provider="brightdata_flipkart_products",
            raw_data={"written_reviews": [
                {"review_id": "review-1", "review_text": "Good battery", "is_verified": "false"},
                {"review_id": "review-1", "review_text": "Good battery", "is_verified": "false"},
            ]}
        )

        analysis = ReviewService.analyze_product_reviews(product)

        self.assertEqual(analysis.written_reviews_count, 1)
        self.assertIs(analysis.written_reviews[0].verified_purchase, False)

    def test_optional_providers_do_not_block_active_providers(self):
        statuses = provider_registry.get_all_statuses()
        status_map = {s.provider_id: s for s in statuses}

        # Active providers
        amazon_provider = status_map.get("brightdata_amazon_search")
        self.assertIsNotNone(amazon_provider)
        self.assertTrue(amazon_provider.configured)
        self.assertFalse(amazon_provider.is_optional)

        flipkart_provider = status_map.get("brightdata_flipkart_products")
        self.assertIsNotNone(flipkart_provider)
        self.assertTrue(flipkart_provider.configured)
        self.assertFalse(flipkart_provider.is_optional)

        # Optional providers without credentials
        creators_provider = status_map.get("amazon_creators_india")
        self.assertIsNotNone(creators_provider)
        self.assertTrue(creators_provider.is_optional)
        self.assertEqual(creators_provider.status, "optional / unavailable")

        rapidapi_provider = status_map.get("rapidapi_amazon_india")
        self.assertIsNotNone(rapidapi_provider)
        self.assertTrue(rapidapi_provider.is_optional)
        self.assertEqual(rapidapi_provider.status, "optional / unavailable")

        # Croma requires SERPAPI_KEY
        croma_provider = status_map.get("croma_electronics")
        self.assertIsNotNone(croma_provider)
        if croma_provider.configured:
            self.assertIn(croma_provider.status, {"ready", "active", "empty", "unavailable"})
        else:
            self.assertEqual(croma_provider.status, "credentials_required")

    def test_trustrank_scoring_with_real_reviews(self):
        product = NormalizedProduct(
            id="brightdata_B0GV1L119H",
            title="Dell 15 Laptop Intel Core i3 16GB 512GB SSD",
            brand="Dell",
            category="laptop",
            current_price=38990.0,
            currency="INR",
            rating=4.2,
            review_count=1117,
            availability="In Stock",
            marketplace="Amazon India",
            provider="brightdata_amazon_search",
            raw_data={
                "written_reviews": [
                    {
                        "review_id": "rev_1",
                        "rating": 5.0,
                        "title": "Super fast and reliable",
                        "review_text": "Great machine for everyday use.",
                        "is_verified": True
                    }
                ]
            }
        )

        rec = ScoringService.evaluate_product(
            product=product,
            answers={"budget": 45000.0, "requirements": ["RAM", "Storage"]},
            category="laptop"
        )

        self.assertGreater(rec.trustrank_score, 0.0)
        self.assertGreater(rec.review_confidence_score, 50.0)
        self.assertEqual(rec.product.review_analysis.written_reviews_count, 1)
        self.assertEqual(rec.product.review_analysis.total_reviews_analyzed, 1117)


if __name__ == "__main__":
    unittest.main()

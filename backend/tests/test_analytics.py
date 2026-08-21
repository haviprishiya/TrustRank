import unittest
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.review_service import ReviewService
from app.services.analytics_service import AnalyticsService

class TestAnalyticsService(unittest.TestCase):
    def test_analytics_generation(self):
        products = [
            NormalizedProduct(
                id="p1",
                title="Apple iPhone 15 128GB Black",
                brand="Apple",
                category="phone",
                image_url="",
                current_price=69990.0,
                rating=4.6,
                review_count=12500,
                availability="In Stock",
                product_url="https://www.amazon.in/dp/B0IPHONE15",
                marketplace="Amazon India",
                provider="amazon_paapi_india",
                offers=[
                    MarketplaceOffer(marketplace="Amazon India", provider="amazon", product_url="", current_price=69990.0, rating=4.6, review_count=12500),
                    MarketplaceOffer(marketplace="Flipkart", provider="flipkart", product_url="", current_price=68999.0, rating=4.6, review_count=8200)
                ]
            ),
            NormalizedProduct(
                id="p2",
                title="OnePlus 12R 16GB 256GB Cool Blue",
                brand="OnePlus",
                category="phone",
                image_url="",
                current_price=42999.0,
                rating=4.4,
                review_count=4500,
                availability="In Stock",
                product_url="https://www.amazon.in/dp/B0OP12R",
                marketplace="Amazon India",
                provider="amazon_paapi_india",
                offers=[
                    MarketplaceOffer(marketplace="Amazon India", provider="amazon", product_url="", current_price=42999.0, rating=4.4, review_count=4500)
                ]
            )
        ]

        for p in products:
            p.review_analysis = ReviewService.analyze_product_reviews(p)

        analytics = AnalyticsService.generate_dashboard_data(products)
        self.assertEqual(analytics.total_products_analyzed, 2)
        self.assertEqual(analytics.total_reviews_represented, 17000)
        self.assertEqual(analytics.average_rating, 4.5)
        self.assertEqual(len(analytics.brand_analysis), 2)
        self.assertGreater(analytics.positive_review_percentage, 70.0)

if __name__ == '__main__':
    unittest.main()

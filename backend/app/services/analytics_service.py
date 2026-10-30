from collections import defaultdict
from typing import List
from app.models.schemas import (
    NormalizedProduct,
    AnalyticsDashboardData,
    BrandAnalytics,
    MarketplaceAnalytics,
    PriceBracketAnalytics,
    RatingBracketAnalytics
)
from app.services.review_service import ReviewService

class AnalyticsService:
    @staticmethod
    def _rating(product: NormalizedProduct):
        if product.review_analysis and product.review_analysis.combined_rating is not None:
            return product.review_analysis.combined_rating
        return product.rating

    @staticmethod
    def _review_count(product: NormalizedProduct) -> int:
        if product.review_analysis:
            return product.review_analysis.total_reviews_analyzed
        return product.review_count or 0

    @staticmethod
    def generate_dashboard_data(products: List[NormalizedProduct]) -> AnalyticsDashboardData:
        if not products:
            return AnalyticsDashboardData(
                total_products_analyzed=0,
                total_reviews_represented=0,
                average_rating=0.0,
                positive_review_percentage=0.0,
                neutral_review_percentage=0.0,
                negative_review_percentage=0.0,
                brand_analysis=[],
                marketplace_analysis=[],
                price_distribution=[],
                rating_distribution=[]
            )

        total_prods = len(products)
        total_reviews = sum(AnalyticsService._review_count(p) for p in products)
        rated_prods = [AnalyticsService._rating(p) for p in products if AnalyticsService._rating(p) is not None and AnalyticsService._rating(p) > 0]
        avg_rating = round(sum(rated_prods) / len(rated_prods), 2) if rated_prods else 0.0

        # Review Sentiment aggregation
        pos_list = [p.review_analysis.positive_percentage for p in products if p.review_analysis and p.review_analysis.total_reviews_analyzed > 0]
        neu_list = [p.review_analysis.neutral_percentage for p in products if p.review_analysis and p.review_analysis.total_reviews_analyzed > 0]
        neg_list = [p.review_analysis.negative_percentage for p in products if p.review_analysis and p.review_analysis.total_reviews_analyzed > 0]

        avg_pos = round(sum(pos_list) / len(pos_list), 1) if pos_list else 0.0
        avg_neu = round(sum(neu_list) / len(neu_list), 1) if neu_list else 0.0
        avg_neg = round(sum(neg_list) / len(neg_list), 1) if neg_list else 0.0

        # Brand Analysis
        brand_map = defaultdict(list)
        for p in products:
            brand_map[p.brand].append(p)

        brand_analytics: List[BrandAnalytics] = []
        for brand, b_prods in brand_map.items():
            b_count = len(b_prods)
            b_ratings = [AnalyticsService._rating(p) for p in b_prods if AnalyticsService._rating(p) is not None and AnalyticsService._rating(p) > 0]
            b_avg_rating = round(sum(b_ratings) / len(b_ratings), 1) if b_ratings else None
            b_tot_reviews = sum(AnalyticsService._review_count(p) for p in b_prods)
            b_prices = [p.current_price for p in b_prods if p.current_price is not None and p.current_price > 0]
            b_avg_price = round(sum(b_prices) / len(b_prices), 0) if b_prices else None
            
            b_pos = [p.review_analysis.positive_percentage for p in b_prods if p.review_analysis and p.review_analysis.total_reviews_analyzed > 0]
            b_neg = [p.review_analysis.negative_percentage for p in b_prods if p.review_analysis and p.review_analysis.total_reviews_analyzed > 0]
            
            brand_analytics.append(BrandAnalytics(
                brand=brand,
                product_count=b_count,
                average_rating=b_avg_rating,
                total_reviews=b_tot_reviews,
                average_price=b_avg_price,
                positive_percentage=round(sum(b_pos) / len(b_pos), 1) if b_pos else 0.0,
                negative_percentage=round(sum(b_neg) / len(b_neg), 1) if b_neg else 0.0
            ))

        brand_analytics.sort(key=lambda b: b.product_count, reverse=True)

        # Marketplace Analysis (Strictly Amazon India and Flipkart)
        mkt_map = defaultdict(list)
        for p in products:
            for offer in p.offers:
                mkt_norm = "Flipkart" if "flipkart" in (offer.marketplace or "").lower() else "Amazon India"
                mkt_map[mkt_norm].append(offer)
            if not p.offers:
                mkt_norm = "Flipkart" if "flipkart" in (p.marketplace or "").lower() else "Amazon India"
                mkt_map[mkt_norm].append(p)

        marketplace_analytics: List[MarketplaceAnalytics] = []
        for mkt, items in mkt_map.items():
            m_count = len(items)
            m_prices = [it.current_price for it in items if it.current_price is not None and it.current_price > 0]
            m_avg_price = round(sum(m_prices) / len(m_prices), 0) if m_prices else 0.0
            m_ratings = [it.rating for it in items if it.rating is not None and it.rating > 0]
            m_avg_rating = round(sum(m_ratings) / len(m_ratings), 1) if m_ratings else 0.0
            m_reviews = sum(it.review_count for it in items if it.review_count)
            
            marketplace_analytics.append(MarketplaceAnalytics(
                marketplace=mkt,
                product_count=m_count,
                average_price=m_avg_price,
                average_rating=m_avg_rating,
                total_reviews=m_reviews
            ))

        marketplace_analytics.sort(key=lambda m: m.product_count, reverse=True)

        # Price Distribution Brackets
        prices = [p.current_price for p in products if p.current_price is not None and p.current_price > 0]
        if prices:
            min_p, max_p = min(prices), max(prices)
            step = (max_p - min_p) / 4.0 if max_p > min_p else 1000.0
            
            price_brackets: List[PriceBracketAnalytics] = []
            for i in range(4):
                low = min_p + (i * step)
                high = min_p + ((i + 1) * step) if i < 3 else max_p + 1
                cnt = sum(1 for pr in prices if low <= pr < high or (i == 3 and pr <= max_p))
                price_brackets.append(PriceBracketAnalytics(
                    bracket_label=f"₹{int(low):,} - ₹{int(high):,}",
                    count=cnt,
                    min_price=round(low, 0),
                    max_price=round(high, 0)
                ))
        else:
            price_brackets = []

        # Rating Distribution Brackets
        rated_items = [p for p in products if p.rating is not None and p.rating > 0]
        rated_count = len(rated_items) if rated_items else 1
        
        rating_brackets: List[RatingBracketAnalytics] = [
            RatingBracketAnalytics(rating_range="4.5★ - 5.0★", count=sum(1 for p in products if p.rating and p.rating >= 4.5), percentage=round(sum(1 for p in products if p.rating and p.rating >= 4.5) / rated_count * 100, 1)),
            RatingBracketAnalytics(rating_range="4.0★ - 4.4★", count=sum(1 for p in products if p.rating and 4.0 <= p.rating < 4.5), percentage=round(sum(1 for p in products if p.rating and 4.0 <= p.rating < 4.5) / rated_count * 100, 1)),
            RatingBracketAnalytics(rating_range="3.5★ - 3.9★", count=sum(1 for p in products if p.rating and 3.5 <= p.rating < 4.0), percentage=round(sum(1 for p in products if p.rating and 3.5 <= p.rating < 4.0) / rated_count * 100, 1)),
            RatingBracketAnalytics(rating_range="Below 3.5★", count=sum(1 for p in products if p.rating and p.rating < 3.5), percentage=round(sum(1 for p in products if p.rating and p.rating < 3.5) / rated_count * 100, 1))
        ]

        return AnalyticsDashboardData(
            total_products_analyzed=total_prods,
            total_reviews_represented=total_reviews,
            average_rating=avg_rating,
            positive_review_percentage=avg_pos,
            neutral_review_percentage=avg_neu,
            negative_review_percentage=avg_neg,
            brand_analysis=brand_analytics,
            marketplace_analysis=marketplace_analytics,
            price_distribution=price_brackets,
            rating_distribution=rating_brackets
        )

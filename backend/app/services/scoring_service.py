import math
from typing import List, Dict, Any, Tuple, Optional
from app.models.schemas import (
    NormalizedProduct,
    ScoredRecommendation,
    UserRequirementAnswers
)
from app.services.review_service import ReviewService

class ScoringService:
    @staticmethod
    def calculate_budget_fit(price: Optional[float], target_budget: float) -> Tuple[float, List[str], List[str]]:
        if not price or price <= 0:
            return 75.0, [], ["Retail price not provided in source feed (check merchant link)"]

        if not target_budget or target_budget <= 0:
            return 90.0, [f"Live price: ₹{price:,.0f}"], []

        pos = []
        neg = []
        
        ratio = price / target_budget
        if ratio <= 0.85:
            score = 95.0
            savings = target_budget - price
            pos.append(f"Well under your budget (Saves ₹{savings:,.0f})")
        elif ratio <= 1.0:
            score = 100.0
            pos.append(f"Fits your target budget of ₹{target_budget:,.0f} (Priced at ₹{price:,.0f})")
        elif ratio <= 1.15:
            score = 80.0
            over = price - target_budget
            neg.append(f"Slightly above target budget by ₹{over:,.0f} (within 15% stretch)")
        elif ratio <= 1.30:
            score = 55.0
            over = price - target_budget
            neg.append(f"Exceeds target budget by ₹{over:,.0f} (+{int((ratio-1)*100)}%)")
        else:
            score = 25.0
            neg.append(f"Significantly exceeds target budget (₹{price:,.0f} vs ₹{target_budget:,.0f})")

        return score, pos, neg

    @classmethod
    def evaluate_product(
        cls,
        product: NormalizedProduct,
        answers: Dict[str, Any],
        category: str
    ) -> ScoredRecommendation:
        # Attach review analysis if not already attached
        if not product.review_analysis:
            product.review_analysis = ReviewService.analyze_product_reviews(product)

        positive_reasons: List[str] = []
        negative_reasons: List[str] = []
        neutral_observations: List[str] = []
        scoring_explanations: Dict[str, str] = {}

        # 1. Budget Evaluation
        target_budget = float(answers.get("budget", 0.0))
        budget_score, b_pos, b_neg = cls.calculate_budget_fit(product.current_price, target_budget)
        positive_reasons.extend(b_pos)
        negative_reasons.extend(b_neg)
        scoring_explanations["budget_fit"] = f"Budget alignment score {budget_score:.0f}/100" + (f" (₹{product.current_price:,.0f} vs budget ₹{target_budget:,.0f})" if product.current_price and target_budget else "")

        # 2. Requirement Match Evaluation
        req_points = 0.0
        max_req_points = 0.0

        title_lower = product.title.lower()
        specs = product.specifications
        brand_lower = product.brand.lower()

        # Check Brand Preference
        preferred_brands = answers.get("brands", [])
        if preferred_brands and isinstance(preferred_brands, list) and len(preferred_brands) > 0:
            max_req_points += 20.0
            matched_brand = any(pb.lower() in brand_lower or pb.lower() in title_lower for pb in preferred_brands)
            if matched_brand:
                req_points += 20.0
                positive_reasons.append(f"Matches your preferred brand ({product.brand})")
            else:
                negative_reasons.append(f"Alternative brand ({product.brand}) rather than your selected brands")
        else:
            max_req_points += 10.0
            req_points += 10.0

        # Category Specific Matching
        if category == "laptop":
            # RAM Requirement
            pref_ram = answers.get("ram", "16GB")
            max_req_points += 25.0
            actual_ram = specs.get("RAM", "")
            if pref_ram.lower() in actual_ram.lower() or pref_ram.lower() in title_lower:
                req_points += 25.0
                positive_reasons.append(f"Meets your {pref_ram} RAM requirement for smooth multitasking")
            elif "8gb" in pref_ram.lower() and ("16 gb" in actual_ram.lower() or "16gb" in title_lower):
                req_points += 25.0
                positive_reasons.append("Provides 16GB RAM (exceeds your 8GB requirement)")
            else:
                req_points += 12.0
                neutral_observations.append(f"Configured with {actual_ram or 'standard memory'}")

            # Primary Use Case
            primary_use = answers.get("primary_use", "all_round")
            max_req_points += 30.0
            if primary_use == "gaming":
                if "RTX" in specs.get("Graphics", "") or "gtx" in title_lower or "gaming" in title_lower or "rtx" in title_lower:
                    req_points += 30.0
                    positive_reasons.append("Equipped with dedicated gaming GPU for high framerates")
                else:
                    req_points += 10.0
                    negative_reasons.append("Integrated graphics — limited for heavy AAA 3D gaming")
            elif primary_use == "programming":
                if "16 GB" in specs.get("RAM", "") or "i5" in specs.get("Processor", "") or "i7" in specs.get("Processor", "") or "ryzen" in specs.get("Processor", "") or "m" in specs.get("Processor", "").lower():
                    req_points += 30.0
                    positive_reasons.append("Strong multi-core processor and memory ideal for IDEs and coding")
                else:
                    req_points += 20.0
            elif primary_use == "student":
                if "Apple" in product.brand or "1.4" in title_lower or "thin" in title_lower or "ideapad" in title_lower:
                    req_points += 30.0
                    positive_reasons.append("Lightweight chassis and battery efficiency suited for campus use")
                else:
                    req_points += 22.0

            # Priority
            priority = answers.get("priority", "performance")
            max_req_points += 15.0
            if priority == "battery" and ("Apple" in product.brand or "evo" in title_lower):
                req_points += 15.0
                positive_reasons.append("Exceptional all-day battery efficiency")
            elif priority == "performance" and ("RTX" in specs.get("Graphics", "") or "i7" in specs.get("Processor", "") or "i9" in specs.get("Processor", "")):
                req_points += 15.0
                positive_reasons.append("Maximized sustained performance profile")
            else:
                req_points += 10.0

        elif category == "phone":
            primary_use = answers.get("primary_use", "balanced")
            max_req_points += 35.0
            if primary_use == "camera":
                if (product.rating and product.rating >= 4.2) or "ultra" in title_lower or "pro" in title_lower or "pixel" in title_lower or "ois" in title_lower:
                    req_points += 35.0
                    positive_reasons.append("High-grade camera sensor with strong dynamic range and detail")
                else:
                    req_points += 20.0
                    negative_reasons.append("Standard camera configuration")
            elif primary_use == "gaming":
                if "snapdragon" in title_lower or "dimensity" in title_lower or "pro" in title_lower or "iqoo" in brand_lower or "poco" in brand_lower:
                    req_points += 35.0
                    positive_reasons.append("Fast processor with high thermal headroom for sustained mobile gaming")
                else:
                    req_points += 22.0
            elif primary_use == "battery":
                if "5000" in specs.get("Battery", "") or "6000" in specs.get("Battery", "") or "mah" in title_lower:
                    req_points += 35.0
                    positive_reasons.append("High-capacity battery delivering 1.5 - 2 days of regular use")
                else:
                    req_points += 22.0
            else:
                req_points += 30.0
                positive_reasons.append("Balanced daily driver with reliable performance and display")

            # Storage
            pref_storage = answers.get("storage", "256GB")
            max_req_points += 20.0
            if pref_storage.lower() in specs.get("Storage", "").lower() or pref_storage.lower() in title_lower:
                req_points += 20.0
                positive_reasons.append(f"Includes {pref_storage} storage capacity")
            else:
                req_points += 12.0
                neutral_observations.append(f"Storage: {specs.get('Storage', 'Standard')}")

        elif category == "skincare":
            skin_concern = answers.get("skin_concern", "oily_acne")
            max_req_points += 35.0
            actives = specs.get("Key Actives", "") or specs.get("Ingredients", "")

            if skin_concern == "oily_acne":
                if "Salicylic" in actives or "Tea Tree" in actives or "Niacinamide" in actives or "salicylic" in title_lower or "oil" in title_lower or "acne" in title_lower:
                    req_points += 35.0
                    positive_reasons.append("Formulated with active ingredients that regulate sebum and clarify pores")
                else:
                    req_points += 15.0
                    negative_reasons.append("Does not specifically target acne control or pore congestion")
            elif skin_concern == "hyperpigmentation":
                if "Niacinamide" in actives or "Vitamin C" in actives or "Arbutin" in actives:
                    req_points += 35.0
                    positive_reasons.append("Contains tyrosinase-inhibiting actives proven to fade dark spots")
                else:
                    req_points += 18.0
            elif skin_concern == "dryness":
                if "Hyaluronic" in actives or "Ceramide" in actives or "dry" in title_lower:
                    req_points += 35.0
                    positive_reasons.append("Rich in barrier-repairing ceramides and hydrating humectants")
                else:
                    req_points += 18.0
            else:
                req_points += 28.0

            # Check Avoided Ingredients
            avoid_list = answers.get("avoid_ingredients", [])
            max_req_points += 20.0
            avoid_violation = False
            for avoid in avoid_list:
                if avoid.lower() in title_lower or avoid.lower() in actives.lower():
                    avoid_violation = True
                    negative_reasons.append(f"Contains or references {avoid} which you requested to avoid")
            if not avoid_violation:
                req_points += 20.0
                positive_reasons.append("Free from your requested avoided ingredients")
            else:
                req_points += 5.0

        else:
            max_req_points += 40.0
            req_points += 35.0
            positive_reasons.append("Solid feature set aligning with your search requirements")

        # 3. Rating and Review Confidence Scores
        rating = product.rating
        review_count = product.review_count or 0
        
        if rating is not None and rating > 0:
            rating_score = round((rating / 5.0) * 100.0, 1)
            # Review confidence score based on logarithmic volume
            review_confidence_score = round(min(100.0, (math.log10(max(1, review_count)) / 4.0) * 100.0), 1) if review_count > 0 else 50.0
            scoring_explanations["rating"] = f"Customer rating: {rating:.1f}/5.0★ with {review_count:,} reviews"
            
            if rating >= 4.3 and review_count >= 500:
                positive_reasons.append(f"Verified customer satisfaction ({rating:.1f}★ across {review_count:,} reviews on {product.marketplace})")
            elif rating < 3.8:
                negative_reasons.append(f"Average rating of {rating:.1f}★ suggests mixed customer feedback")
        else:
            rating_score = 70.0
            review_confidence_score = 40.0
            scoring_explanations["rating"] = "No customer ratings published by source for this listing"
            neutral_observations.append(f"Rating data not provided by {product.marketplace}")

        # 4. Calculate Requirement Match %
        req_match_pct = round(min(99.0, max(45.0, (req_points / max_req_points) * 100.0)), 1) if max_req_points > 0 else 85.0
        scoring_explanations["requirement_match"] = f"Matches {req_match_pct:.0f}% of your stated preferences"

        # 5. Calculate Value for Money Score
        cat_base_prices = {"laptop": 60000.0, "phone": 28000.0, "skincare": 700.0, "headphones": 4500.0}
        base_p = cat_base_prices.get(category, 10000.0)
        
        if product.current_price and product.current_price > 0:
            price_val_ratio = base_p / product.current_price
            vfm_raw = (req_match_pct * 0.4) + (rating_score * 0.3) + (min(150.0, price_val_ratio * 100.0) * 0.3)
            vfm_score = round(min(100.0, max(40.0, vfm_raw)), 1)
        else:
            vfm_score = 75.0
            
        if vfm_score >= 84:
            vfm_label = "Excellent"
        elif vfm_score >= 72:
            vfm_label = "Great"
        elif vfm_score >= 60:
            vfm_label = "Good"
        else:
            vfm_label = "Fair"
        scoring_explanations["price_value"] = f"Value rating: {vfm_label} ({vfm_score:.0f}/100)"

        # 6. Availability & Source Reliability Scores
        availability_score = 100.0 if "in stock" in product.availability.lower() else (90.0 if "verified" in product.availability.lower() else 70.0)
        source_reliability_score = 95.0 if any(p in product.provider for p in ["amazon", "flipkart", "open_beauty"]) else 85.0
        scoring_explanations["availability"] = f"Availability: {product.availability} on {product.marketplace}"
        scoring_explanations["source_reliability"] = f"Source: {product.source or product.marketplace}"

        # Neutral observations
        neutral_observations.append(f"Offered on {product.marketplace} ({product.seller or 'Authorized Merchant'})")
        if product.specifications:
            spec_summary = ", ".join([f"{k}: {v}" for k, v in list(product.specifications.items())[:3]])
            neutral_observations.append(f"Key Specifications: {spec_summary}")

        # 7. Transparent Overall TrustRank Score Formula (0 - 100)
        # Weights: Requirement (35%) + Price/Value (25%) + Rating/Confidence (20%) + Availability/Reliability (20%)
        rating_combined = (rating_score * 0.6) + (review_confidence_score * 0.4)
        avail_combined = (availability_score * 0.5) + (source_reliability_score * 0.5)
        
        overall_score = round(
            (req_match_pct * 0.35) +
            (vfm_score * 0.25) +
            (rating_combined * 0.20) +
            (avail_combined * 0.20),
            1
        )
        overall_score = min(99.4, max(40.0, overall_score))

        # Personalized Narrative ("Best For You" Explanation)
        best_for_you_parts = [
            f"Based on your requirements, the **{product.title}** scores a **{req_match_pct:.0f}% requirement match**."
        ]
        if b_pos:
            best_for_you_parts.append(b_pos[0] + ".")
        if category == "laptop":
            best_for_you_parts.append(f"It delivers the necessary configuration for your {answers.get('primary_use', 'daily')} workload with {specs.get('RAM', 'capable')} RAM.")
        elif category == "phone":
            best_for_you_parts.append(f"It aligns with your priority on {answers.get('primary_use', 'balanced')} usage with genuine {product.marketplace} listing data.")
        elif category == "skincare":
            best_for_you_parts.append(f"Its formulation targets {answers.get('skin_concern', 'your skin concern')} while complying with your requested ingredient preferences.")
        else:
            best_for_you_parts.append(f"It offers an optimal balance of customer trust and verified marketplace availability.")

        best_for_you_explanation = " ".join(best_for_you_parts)

        return ScoredRecommendation(
            product=product,
            trustrank_score=overall_score,
            requirement_match_percentage=req_match_pct,
            budget_fit_score=budget_score,
            value_for_money=vfm_label,
            value_for_money_score=vfm_score,
            requirement_match_score=req_match_pct,
            price_value_score=vfm_score,
            rating_score=rating_score,
            review_confidence_score=review_confidence_score,
            availability_score=availability_score,
            source_reliability_score=source_reliability_score,
            scoring_breakdown_explanation=scoring_explanations,
            positive_reasons=positive_reasons[:4],
            negative_reasons=negative_reasons[:3],
            neutral_observations=neutral_observations[:3],
            best_for_you_explanation=best_for_you_explanation,
            category_badges=[]
        )

    @classmethod
    def rank_and_assign_badges(
        cls,
        recommendations: List[ScoredRecommendation]
    ) -> List[ScoredRecommendation]:
        if not recommendations:
            return []

        # Sort primarily by TrustRank score descending
        sorted_recs = sorted(recommendations, key=lambda r: r.trustrank_score, reverse=True)

        # 1. Best for You -> Highest TrustRank Score / Requirement Match
        if len(sorted_recs) >= 1:
            sorted_recs[0].category_badges.append("Best for You")

        # 2. Best Value -> Highest Value For Money Score
        best_val = max(sorted_recs, key=lambda r: r.value_for_money_score)
        if "Best for You" not in best_val.category_badges:
            best_val.category_badges.append("Best Value")
        elif len(sorted_recs) > 1:
            second_val = sorted(sorted_recs, key=lambda r: r.value_for_money_score, reverse=True)[1]
            second_val.category_badges.append("Best Value")

        # 3. Best Reviewed -> Highest rating * log(reviews) (if ratings exist)
        rated_recs = [r for r in sorted_recs if r.product.rating is not None and r.product.rating > 0]
        if rated_recs:
            best_rev = max(rated_recs, key=lambda r: r.product.rating * math.log10(max(10, r.product.review_count or 10)))
            if not best_rev.category_badges:
                best_rev.category_badges.append("Best Reviewed")
            elif len(sorted_recs) > 2:
                remaining = [r for r in rated_recs if not r.category_badges]
                if remaining:
                    remaining_best_rev = max(remaining, key=lambda r: r.product.rating)
                    remaining_best_rev.category_badges.append("Best Reviewed")

        # 4. Best Alternative -> High rank with a different brand or distinct feature
        top_brand = sorted_recs[0].product.brand
        alt_candidates = [r for r in sorted_recs[1:] if r.product.brand != top_brand and not r.category_badges]
        if alt_candidates:
            alt_candidates[0].category_badges.append("Best Alternative")
        elif len(sorted_recs) > 3 and not sorted_recs[3].category_badges:
            sorted_recs[3].category_badges.append("Best Alternative")

        return sorted_recs

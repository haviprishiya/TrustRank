import time
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    SearchIntent,
    UserRequirementAnswers,
    NormalizedProduct,
    ScoredRecommendation,
    RecommendationPipelineResponse,
    ProviderStatusInfo
)
from app.services.intent_service import IntentService
from app.services.matching_service import MatchingService
from app.services.scoring_service import ScoringService
from app.services.analytics_service import AnalyticsService
from app.services.relevance_service import RelevanceService
from app.providers.registry import provider_registry

class RecommendationPipeline:
    @classmethod
    async def run_pipeline(
        cls,
        user_request: UserRequirementAnswers
    ) -> RecommendationPipelineResponse:
        start_time = time.time()
        
        # 1. Intent Detection
        intent = IntentService.detect_intent(user_request.query)
        if user_request.category:
            intent.detected_category = user_request.category
            
        category = intent.detected_category
        
        # Enrich provider search query with user-selected preferences (brand, 5G, gaming, etc.)
        answers = user_request.answers or {}
        brands = answers.get("brands") if isinstance(answers.get("brands"), list) else []
        top_brand = brands[0].strip() if brands else ""
        
        base_query = (intent.normalized_query or user_request.query or "").strip()
        provider_query = base_query
        
        if category == "phone":
            tokens = []
            if top_brand and top_brand.lower() not in base_query.lower():
                tokens.append(top_brand)
            if answers.get("connectivity_5g") == "5g_required" and "5g" not in base_query.lower():
                tokens.append("5G")
            if base_query.lower() in ("mobile", "mobiles", "phone", "phones", ""):
                tokens.append("phone")
            else:
                tokens.append(base_query)
                if not any(w in base_query.lower() for w in ("phone", "mobile", "iphone", "galaxy", "pixel")):
                    tokens.append("phone")
            provider_query = " ".join(tokens)
            if provider_query.lower() in ("phone", "mobile"):
                provider_query = "mobile phone"
                
        elif category == "laptop":
            tokens = []
            if top_brand and top_brand.lower() not in base_query.lower():
                tokens.append(top_brand)
            if (answers.get("primary_use") == "gaming" or answers.get("priority") == "performance") and "gaming" not in base_query.lower():
                tokens.append("gaming")
            if base_query.lower() in ("laptop", "laptops", "notebook", "pc", ""):
                tokens.append("laptop")
            else:
                tokens.append(base_query)
                if not any(w in base_query.lower() for w in ("laptop", "notebook", "macbook", "thinkpad")):
                    tokens.append("laptop")
            provider_query = " ".join(tokens)
            
        else:
            if top_brand and top_brand.lower() not in base_query.lower():
                provider_query = f"{top_brand} {base_query}".strip()
        
        # 2. Live Providers Search
        raw_products: List[NormalizedProduct] = await provider_registry.search_all(
            query=provider_query,
            category=category,
            limit=25
        )
        
        total_found = len(raw_products)
        
        # 2.5 Strict Relevance Filtering
        # Filters out off-target categories, negative keywords, irrelevant accessories, and non-shopping content
        relevant_products = RelevanceService.filter_products(
            products=raw_products,
            query=user_request.query,
            intent=intent
        )
        if not relevant_products and raw_products:
            relevant_products = raw_products

        # 3. Deduplication & Multi-Marketplace Offer Matching
        deduplicated = MatchingService.deduplicate_and_group_offers(relevant_products)
        
        # Enforce Amazon India, Flipkart, and Myntra across all products and offers
        allowed_marketplaces = {"amazon india", "amazon", "flipkart", "myntra"}
        filtered_deduped: List[NormalizedProduct] = []
        for p in deduplicated:
            m_lower = (p.marketplace or "").lower()
            if any(am in m_lower for am in allowed_marketplaces):
                if "myntra" in m_lower:
                    p.marketplace = "Myntra"
                elif "flipkart" in m_lower:
                    p.marketplace = "Flipkart"
                else:
                    p.marketplace = "Amazon India"
                p.offers = [o for o in p.offers if any(am in (o.marketplace or "").lower() for am in allowed_marketplaces)]
                for off in p.offers:
                    off_m = (off.marketplace or "").lower()
                    if "myntra" in off_m:
                        off.marketplace = "Myntra"
                    elif "flipkart" in off_m:
                        off.marketplace = "Flipkart"
                    else:
                        off.marketplace = "Amazon India"
                filtered_deduped.append(p)
        if filtered_deduped:
            deduplicated = filtered_deduped

        dedup_count = len(deduplicated)
        
        # 4. Requirement Scoring & Evaluation
        scored_recommendations: List[ScoredRecommendation] = []
        for prod in deduplicated:
            rec = ScoringService.evaluate_product(
                product=prod,
                answers=user_request.answers,
                category=category
            )
            scored_recommendations.append(rec)
            
        # 5. Ranking and Badging
        answers_dict = user_request.answers or {}
        raw_budget = answers_dict.get("budget", 0.0)
        min_p = 0.0
        max_p = 0.0
        if isinstance(raw_budget, dict):
            min_p = float(raw_budget.get("min", 0.0) or 0.0)
            max_p = float(raw_budget.get("max", 0.0) or 0.0)
        else:
            try:
                max_p = float(raw_budget or 0.0)
            except (ValueError, TypeError):
                max_p = 0.0
                
        if "min_price" in answers_dict:
            try:
                min_p = float(answers_dict.get("min_price", 0.0) or 0.0)
            except (ValueError, TypeError):
                pass
        if "max_price" in answers_dict:
            try:
                max_p = float(answers_dict.get("max_price", 0.0) or 0.0)
            except (ValueError, TypeError):
                pass

        ranked = ScoringService.rank_and_assign_badges(
            scored_recommendations,
            target_budget=max_p,
            min_price=min_p,
            max_price=max_p
        )
        
        # 6. Top 5 Selection & Badged Entities
        top_5 = ranked[:5]
        best_for_you = next((r for r in ranked if "Best for You" in r.category_badges), top_5[0] if top_5 else None)
        best_value = next((r for r in ranked if "Best Value" in r.category_badges), top_5[1] if len(top_5) > 1 else None)
        best_reviewed = next((r for r in ranked if "Best Reviewed" in r.category_badges), top_5[2] if len(top_5) > 2 else None)
        best_alternative = next((r for r in ranked if "Best Alternative" in r.category_badges), top_5[3] if len(top_5) > 3 else None)
        
        # 7. Analytical Dashboard Data Generation
        analytics = AnalyticsService.generate_dashboard_data(deduplicated)
        
        # 8. Provider Statuses
        provider_statuses: List[ProviderStatusInfo] = provider_registry.get_all_statuses()
        
        elapsed = round(time.time() - start_time, 3)
        
        return RecommendationPipelineResponse(
            query=user_request.query,
            intent=intent,
            total_products_found=total_found,
            deduplicated_products_count=dedup_count,
            recommendations=ranked,
            top_5_comparison=top_5,
            best_for_you=best_for_you,
            best_value=best_value,
            best_reviewed=best_reviewed,
            best_alternative=best_alternative,
            analytics=analytics,
            provider_statuses=provider_statuses,
            execution_time_seconds=elapsed
        )

import time
import logging
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
from app.providers.registry import provider_registry

logger = logging.getLogger(__name__)

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
        
        # 2. Live Providers Search
        raw_products: List[NormalizedProduct] = await provider_registry.search_all(
            query=intent.normalized_query or user_request.query,
            category=category,
            limit=20
        )
        
        total_found = len(raw_products)
        logger.info("Pipeline raw products query=%r count=%d", user_request.query, total_found)
        
        # 3. Deduplication & Multi-Marketplace Offer Matching
        deduplicated = MatchingService.deduplicate_and_group_offers(raw_products)
        dedup_count = len(deduplicated)
        logger.info("Pipeline normalized/deduplicated query=%r count=%d", user_request.query, dedup_count)
        
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
        ranked = ScoringService.rank_and_assign_badges(scored_recommendations)
        logger.info("Pipeline scored query=%r count=%d", user_request.query, len(scored_recommendations))
        
        # 6. Top 5 Selection & Badged Entities
        top_5 = ranked[:5]
        logger.info("Pipeline final recommendations query=%r count=%d top5=%d", user_request.query, len(ranked), len(top_5))
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

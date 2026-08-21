import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from app.models.schemas import (
    SearchIntent,
    RequirementQuestion,
    UserRequirementAnswers,
    RecommendationPipelineResponse,
    ProviderStatusInfo,
    ScoredRecommendation
)
from app.services.intent_service import IntentService
from app.services.question_service import QuestionService
from app.services.pipeline import RecommendationPipeline
from app.providers.registry import provider_registry

router = APIRouter()
logger = logging.getLogger(__name__)

class IntentRequest(UserRequirementAnswers):
    pass

@router.post("/search/intent", response_model=SearchIntent)
async def analyze_search_intent(payload: Dict[str, str] = Body(...)):
    query = payload.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    return IntentService.detect_intent(query)

@router.post("/search/questions", response_model=List[RequirementQuestion])
async def get_requirement_questions(payload: Dict[str, str] = Body(...)):
    query = payload.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")
    
    intent = IntentService.detect_intent(query)
    # If category explicitly passed
    if "category" in payload and payload["category"]:
        intent.detected_category = payload["category"]
        
    questions = QuestionService.get_questions_for_intent(intent)
    return questions

@router.post("/recommendations/generate", response_model=RecommendationPipelineResponse)
async def generate_recommendations(request: UserRequirementAnswers):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        logger.info("Generating recommendations for query=%r category=%r", request.query, request.category)
        response = await RecommendationPipeline.run_pipeline(request)
        logger.info(
            "Recommendation generation completed: query=%r products=%d recommendations=%d",
            request.query,
            response.total_products_found,
            len(response.recommendations),
        )
        return response
    except Exception:
        # Keep the client response safe while retaining the full traceback in server logs.
        logger.exception("Recommendation generation failed for query=%r", request.query)
        raise HTTPException(status_code=500, detail="Recommendation generation failed. Check backend server logs for details.")

@router.get("/providers/status", response_model=List[ProviderStatusInfo])
async def get_providers_status():
    return provider_registry.get_all_statuses()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "TrustRank",
        "version": "1.0.0",
        "providers_registered": len(provider_registry.providers)
    }

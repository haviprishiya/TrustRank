import pytest
from app.models.schemas import NormalizedProduct, ScoredRecommendation
from app.services.scoring_service import ScoringService

def create_sample_product(
    id: str,
    title: str,
    price: float = None,
    original_price: float = None,
    rating: float = None,
    specs: dict = None,
    features: list = None
):
    return NormalizedProduct(
        id=id,
        title=title,
        brand="TestBrand",
        category="laptop",
        provider="amazon",
        marketplace="Amazon India",
        current_price=price,
        original_price=original_price,
        rating=rating,
        review_count=100 if rating else 0,
        specifications=specs or {},
        features=features or []
    )

def test_best_value_with_sufficient_data():
    # 3 products: all have price, rating, and specs
    # Prod A: Expensive, good rating
    # Prod B: Great price, high rating, original price markdown (Best Value!)
    # Prod C: Budget
    prod_a = create_sample_product("A", "Laptop Premium A", price=90000, rating=4.5, specs={"RAM": "16GB"})
    prod_b = create_sample_product("B", "Laptop Value B", price=55000, original_price=70000, rating=4.6, specs={"RAM": "16GB", "SSD": "512GB"})
    prod_c = create_sample_product("C", "Laptop Budget C", price=40000, rating=3.8, specs={"RAM": "8GB"})

    rec_a = ScoredRecommendation(product=prod_a, trustrank_score=90.0, value_for_money_score=75.0)
    rec_b = ScoredRecommendation(product=prod_b, trustrank_score=88.0, value_for_money_score=88.0)
    rec_c = ScoredRecommendation(product=prod_c, trustrank_score=75.0, value_for_money_score=70.0)

    ranked = ScoringService.rank_and_assign_badges([rec_a, rec_b, rec_c])
    
    # Check that Best Value was assigned to Prod B
    best_val_recs = [r for r in ranked if "Best Value" in r.category_badges]
    assert len(best_val_recs) == 1
    assert best_val_recs[0].product.id == "B"
    assert "Best Value" in best_val_recs[0].category_badges

def test_best_value_omitted_when_insufficient_data():
    # Products lack prices or ratings or specs
    # Prod D: Missing price (None)
    # Prod E: Missing rating (None)
    # Prod F: Missing specs & features
    prod_d = create_sample_product("D", "Product D No Price", price=None, rating=4.5, specs={"RAM": "16GB"})
    prod_e = create_sample_product("E", "Product E No Rating", price=50000, rating=None, specs={"RAM": "16GB"})
    prod_f = create_sample_product("F", "Product F No Specs", price=45000, rating=4.2, specs={}, features=[])

    rec_d = ScoredRecommendation(product=prod_d, trustrank_score=60.0, value_for_money_score=0.0)
    rec_e = ScoredRecommendation(product=prod_e, trustrank_score=65.0, value_for_money_score=50.0)
    rec_f = ScoredRecommendation(product=prod_f, trustrank_score=62.0, value_for_money_score=52.0)

    ranked = ScoringService.rank_and_assign_badges([rec_d, rec_e, rec_f])
    
    # Must NOT assign Best Value because of insufficient data!
    best_val_recs = [r for r in ranked if "Best Value" in r.category_badges]
    assert len(best_val_recs) == 0, "Best Value badge must be omitted when data is insufficient"

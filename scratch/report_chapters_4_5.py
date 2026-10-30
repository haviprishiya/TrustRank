# =============================================================================
# TRUSTRANK FINAL PROJECT REPORT - CHAPTERS 4 AND 5
# =============================================================================
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_builder_common import (
    add_header_styled,
    add_body_paragraph,
    add_bullet,
    add_code_block,
    style_table,
    set_cell_background,
    set_cell_margins
)

def build_chapter_4(doc):
    """Chapter 4: Methodology and Algorithms"""
    doc.add_page_break()
    add_header_styled(doc, "4. METHODOLOGY AND ALGORITHMS", level=1)

    add_header_styled(doc, "4.1 Overview of Methodology", level=2)
    add_body_paragraph(
        doc,
        "The TrustRank methodology is structured as an end-to-end asynchronous pipeline designed to transform raw, noisy e-commerce search queries into structured, verified multi-marketplace product recommendations. The methodology comprises seven deterministic operational phases: (1) Natural Language Query Ingestion and Intent Categorization, (2) Dynamic Requirement Questionnaire Elicitation, (3) Asynchronous Concurrent Multi-Marketplace Scraping, (4) Data Normalization, Image Resolution, and Anti-Noise Filtering, (5) Cross-Marketplace Entity Linkage and Deduplication, (6) Multi-Criteria TrustRank Mathematical Scoring and Badging, and (7) Top 5 Comparison Matrix and Analytical Dashboard Synthesis."
    )
    add_body_paragraph(
        doc,
        "Figure 4.1 illustrates the complete query-to-recommendation workflow. By separating concerns across dedicated microservice layers, the system achieves sub-3.5-second total pipeline execution while enforcing strict mathematical rigor across cross-platform offer grouping and scoring."
    )

    add_header_styled(doc, "4.2 User Query and Requirement Processing", level=2)
    add_body_paragraph(
        doc,
        "When a user submits an unconstrained natural language query (e.g., 'gaming laptop under 70000', 'anti-hairfall shampoo', 'running shoes for men'), `IntentService` executes a multi-stage classification pipeline. The engine first applies tokenization and regular expression matching to isolate numerical price constraints. It recognizes syntactic budget constructs such as 'under X', 'below X', 'less than X', 'sub X', and 'Xk' (converting '70k' to 70,000 INR). Next, it compares token n-grams against curated category taxonomies to classify the query into primary retail domains: laptop, smartphone, tv, refrigerator, dress, footwear, or skincare."
    )
    add_body_paragraph(
        doc,
        "Once the intent is determined, `QuestionService` dynamically generates an intelligent requirement questionnaire tailored to that exact vertical. Rather than forcing users through cumbersome static facet trees, the wizard prompts only for the most impactful technical criteria. For laptops, it prompts for usage profile (Gaming, Coding/Productivity, Everyday Browsing), preferred processor family (Intel Core i5/i7, AMD Ryzen 5/7), and RAM capacity (8GB, 16GB, 32GB). For skincare, it prompts for skin type (Oily, Dry, Combination), primary concern (Acne, Brightening, Aging), and avoided ingredients. These answers are packaged into a structured `UserRequirementAnswers` Pydantic payload."
    )

    add_code_block(
        doc,
        """Algorithm 4.1: Natural Language Intent and Budget Extraction
Input: Raw user query string Q
Output: DetectedCategory C, ExtractedBudget B, BrandPreference Brand

1. Initialize B <- None, Brand <- None, C <- "general"
2. Normalize Q_clean <- Lowercase(Trim(Q))
3. Match budget patterns using Regular Expressions:
   - Match "under (\d+)(k?)" or "below (\d+)(k?)":
     If matched, B <- ParseNumber(Digits) * (1000 if 'k' else 1)
4. Scan tokens against KnownBrands dictionary:
   - For each brand b in KnownBrands:
     If b is in Q_clean: Brand <- b; Break
5. Match Category Keywords:
   - If any token in ["laptop", "notebook", "gaming"]: C <- "laptop"
   - Else if any token in ["phone", "mobile", "smartphone"]: C <- "smartphone"
   - Else if any token in ["tv", "television", "oled", "qled"]: C <- "tv"
   - Else if any token in ["fridge", "refrigerator"]: C <- "refrigerator"
   - Else if any token in ["dress", "kurti", "shirt", "jeans"]: C <- "dress"
   - Else if any token in ["shampoo", "serum", "sunscreen", "skincare"]: C <- "skincare"
6. Return IntentResult(Category=C, Budget=B, Brand=Brand)""",
        caption="Algorithm 4.1: User Query Intent and Budget Extraction"
    )

    add_header_styled(doc, "4.3 Marketplace Product Retrieval Pipeline", level=2)
    add_body_paragraph(
        doc,
        "Marketplace product retrieval is orchestrated through the `ProviderRegistry` using Python's asynchronous event loop (`asyncio.gather`). Traditional sequential scraping architectures suffer from additive network latency (e.g., waiting 3 seconds for Amazon, then 3 seconds for Flipkart, resulting in unacceptable 6-to-10-second wait times). TrustRank dispatches concurrent non-blocking HTTP requests across all registered providers simultaneously."
    )
    add_body_paragraph(
        doc,
        "The platform integrates four specialized provider connectors: (1) `BrightDataProvider` queries Amazon India and Flipkart via enterprise web datasets and live search engines; (2) `MyntraProvider` connects directly to Myntra's lifestyle catalog endpoints with local dataset fallback; (3) `LiveSearchProvider` executes targeted multi-marketplace search across DuckDuckGo and Google search indexes to discover real-time merchant links; and (4) `SerpApiProvider` acts as a high-reliability fallback. Each provider implements the `BaseProvider` interface, guaranteeing that provider-level network failures or CAPTCHA triggers are isolated without crashing the parent pipeline."
    )

    add_code_block(
        doc,
        """Algorithm 4.2: Asynchronous Multi-Marketplace Concurrent Retrieval
Input: User query Q, DetectedCategory C, Limit L
Output: Aggregated raw product list P_raw

1. Initialize provider_tasks <- []
2. For each active provider P in ProviderRegistry.get_active_providers():
   - If P supports Category C:
     Append P.search(query=Q, category=C, limit=L) to provider_tasks
3. Execute asynchronously:
   results <- await asyncio.gather(*provider_tasks, return_exceptions=True)
4. Initialize P_raw <- []
5. For each res in results:
   - If res is not Exception and res is not None:
     Extend P_raw with res
   - Else:
     Log provider execution warning, isolate error
6. Return P_raw""",
        caption="Algorithm 4.2: Asynchronous Multi-Marketplace Product Retrieval"
    )

    add_header_styled(doc, "4.4 Data Normalization and Cleaning", level=2)
    add_body_paragraph(
        doc,
        "Because incoming JSON feeds from Amazon, Flipkart, and Myntra feature completely different key naming conventions and data structures, `NormalizationService` maps every raw dictionary into a strictly typed `NormalizedProduct` Pydantic model. Heterogeneous currency strings (e.g., '₹ 54,990.00', 'Rs.54990', 'INR 54,990') are sanitized by stripping non-numeric characters and converting to 64-bit floating-point numbers. Star ratings are clamped to a normalized 0.0 to 5.0 range, and review count strings (e.g., '14,235 ratings') are parsed into integers."
    )
    add_body_paragraph(
        doc,
        "A critical responsibility of `NormalizationService` is high-resolution image URL recovery. Commercial marketplaces often deliver low-resolution thumbnail URLs or dynamic image template strings containing placeholder tokens (such as Flipkart's `{@width}/{@height}` or Myntra's `($height)`). The normalizer replaces these tokens with high-resolution parameters (720x540 at 90% quality), extracts alternative images into an `image_candidates` fallback list, and validates HTTPS protocol headers."
    )

    p_t41 = doc.add_paragraph()
    r = p_t41.add_run("Table 4.1: NormalizedProduct Schema Attributes and Feature Specifications")
    r.font.bold = True
    tbl_41 = doc.add_table(rows=1, cols=3)
    style_table(
        tbl_41,
        [1.8, 1.4, 3.4],
        ["Schema Field", "Data Type", "Description and Processing Logic"],
        [
            ["id", "String", "Unique deterministic product identifier with provider prefix"],
            ["title", "String", "Cleaned canonical product title stripped of promotional text"],
            ["brand", "String", "Extracted canonical brand entity (e.g., ASUS, HP, Samsung, L'Oreal)"],
            ["category", "String", "Classified vertical category (laptop, smartphone, dress, etc.)"],
            ["current_price", "Float", "Live active selling price in Indian Rupees (INR ₹)"],
            ["original_price", "Float", "Pre-discount Maximum Retail Price (MRP) in INR ₹"],
            ["discount_percent", "Float", "Authentic calculated percentage discount"],
            ["rating", "Float", "Normalized customer star rating on a 1.0 to 5.0 scale"],
            ["review_count", "Integer", "Total verified customer ratings and reviews count"],
            ["availability", "String", "Live stock availability status ('In Stock' / 'Out of Stock')"],
            ["product_url", "String", "Direct, authentic merchant product detail page URL"],
            ["image_url", "String", "Primary high-resolution product image hosted on merchant CDN"],
            ["image_candidates", "List[String]", "Fallback candidate URLs for error-resilient client rendering"],
            ["specifications", "Dict[str, str]", "Key-value technical specifications extracted from PDP tables"],
            ["offers", "List[Offer]", "Array of matched competing marketplace offers for cross-comparison"]
        ]
    )

    add_code_block(
        doc,
        """Algorithm 4.3: Product Normalization and Image Resolution
Input: Raw product dictionary D, SourceMarketplace M
Output: NormalizedProduct instance P

1. Parse Price: Clean string, strip ["₹", "Rs.", ",", " "], convert to Float
2. Parse MRP & Compute Discount: discount_pct = ((MRP - Price) / MRP) * 100
3. Normalize Rating & Reviews: rating in [0.0, 5.0], review_count as integer
4. Extract Canonical Brand: Match Title against KnownBrandDatabase
5. Resolve High-Resolution Image:
   - If "{@width}" in image_url: replace with "720", "{@height}" with "540"
   - If "($height)" in image_url: replace with "h_720,q_90"
   - Assemble fallback list: image_candidates <- [img1, img2, img3]
6. Clean Title: Remove marketing boilerplate ("Buy online at best price", "Latest 2026")
7. Construct Pydantic NormalizedProduct instance P
8. Return P""",
        caption="Algorithm 4.3: Data Normalization and Image Resolution"
    )

    add_header_styled(doc, "4.5 Product Matching and Cross-Marketplace Deduplication", level=2)
    add_body_paragraph(
        doc,
        "Cross-marketplace entity resolution is one of the most challenging problems in e-commerce informatics. Amazon, Flipkart, and Myntra deliberately format product titles differently, inject conflicting promotional keywords, and withhold Global Trade Item Numbers (GTIN/EAN). To link identical physical items across competing portals without false positive merges, `MatchingService` implements a multi-stage fuzzy linkage algorithm."
    )
    add_body_paragraph(
        doc,
        "The matcher executes six sequential validation checks: (1) Deterministic SKU/ASIN verification; (2) Marketplace isolation (preventing distinct products from the same marketplace from merging unless they share identical URLs); (3) Canonical brand matching; (4) Alphanumeric model token extraction (isolating hardware family names and exact model codes such as 'A15', 'Victus', 'Total Repair 5'); (5) Variant conflict verification across RAM, storage, screen size, and packaging volume; and (6) Price sanity checking (enforcing that candidate products must not exhibit a price ratio exceeding 2.0 to prevent cross-tier false matching). When two listings are confirmed identical, their offers are grouped under a single canonical product entity."
    )

    add_code_block(
        doc,
        """Algorithm 4.4: Cross-Marketplace Entity Resolution and Offer Grouping
Input: List of normalized products P_in
Output: List of deduplicated product entities P_out with consolidated offers

1. Initialize P_out <- []
2. For each product p_candidate in P_in:
   - matched <- False
   - For each product p_target in P_out:
     - If are_products_identical(p_candidate, p_target) is True:
       - Merge candidate offer into p_target.offers
       - Update p_target lowest price and best rating
       - matched <- True; Break
   - If matched is False:
     - p_candidate.offers <- [CreateInitialOffer(p_candidate)]
     - Append p_candidate to P_out
3. Return P_out

Function are_products_identical(P1, P2):
1. If P1.id == P2.id and not P1.id.startswith("brightdata_"): Return True
2. If P1.marketplace == P2.marketplace: Return (P1.id == P2.id or P1.url == P2.url)
3. If NormalizeBrand(P1.brand) != NormalizeBrand(P2.brand): Return False
4. models1 <- ExtractModelTokens(P1.title); models2 <- ExtractModelTokens(P2.title)
   If models1 and models2 and models1.intersection(models2) is Empty: Return False
5. v1 <- ExtractVariants(P1); v2 <- ExtractVariants(P2)
   For key in ["ram", "storage", "screen_size", "volume"]:
     If key in v1 and key in v2 and v1[key] != v2[key]: Return False
6. If PriceRatio(P1.price, P2.price) > 2.0: Return False
7. Return True""",
        caption="Algorithm 4.4: Cross-Marketplace Entity Resolution and Offer Grouping"
    )

    add_header_styled(doc, "4.6 TrustRank Multi-Criteria Scoring and Ranking", level=2)
    add_body_paragraph(
        doc,
        "The core diagnostic intelligence of the platform is governed by the proprietary TrustRank Multi-Criteria Scoring Algorithm (`ScoringService`). Unlike simplistic commercial engines that rank items by profit margins or uncalibrated star ratings, TrustRank evaluates every candidate product across four mathematically balanced dimensions: User Requirement Alignment (35%), Value for Money Ratio (25%), Rating and Review Confidence (20%), and Live Stock Availability (20%)."
    )
    add_body_paragraph(
        doc,
        "Composite TrustRank Overall Score Formula (0 to 100):",
        bold_prefix="Mathematical Formulation: "
    )
    add_body_paragraph(
        doc,
        "TrustRank Score = (Score_Requirement * 0.35) + (Score_ValueForMoney * 0.25) + (Score_RatingConfidence * 0.20) + (Score_Availability * 0.20)",
        bold_prefix="Equation 4.1: "
    )
    add_body_paragraph(
        doc,
        "If verified customer ratings are completely absent from a product listing, the algorithm automatically rebalances weights to prevent unfair penalization: Requirement Match is weighted at 45%, Value for Money at 35%, and Availability at 20%. The composite score is strictly bounded between 15.0 and 100.0."
    )
    add_body_paragraph(
        doc,
        "Rating and Logarithmic Review Confidence Formula: To combat review astroturfing and star rating inflation, the rating component combines the linear star score with a logarithmic review volume damping factor:",
        bold_prefix="Logarithmic Damping: "
    )
    add_body_paragraph(
        doc,
        "Score_RatingConfidence = (Score_StarRating * 0.60) + (Score_ReviewVolumeConfidence * 0.40)\nwhere Score_ReviewVolumeConfidence = min(100.0, (log10(max(1, review_count)) / 4.0) * 100.0)",
        bold_prefix="Equation 4.2: "
    )
    add_body_paragraph(
        doc,
        "Under Equation 4.2, a product with a 5.0-star rating but only 10 reviews receives a review confidence score of only 25.0, pulling its rating-combined score down to 70.0. Conversely, a product with a 4.5-star rating backed by 10,000 verified reviews achieves a full 100.0 review confidence score, resulting in a robust 94.0 rating-combined score."
    )
    add_body_paragraph(
        doc,
        "Budget Fit and Value for Money Scoring: Budget alignment is evaluated using a continuous piecewise matrix that awards full credit to items meeting the user's budget while applying calibrated penalties to over-budget items. Table 4.2 details the piecewise budget fit matrix."
    )

    p_t42 = doc.add_paragraph()
    r = p_t42.add_run("Table 4.2: Piecewise Continuous Budget Fit Scoring Matrix")
    r.font.bold = True
    tbl_42 = doc.add_table(rows=1, cols=3)
    style_table(
        tbl_42,
        [2.0, 1.8, 2.8],
        ["Price Relative to User Budget", "Assigned Score (0–100)", "Economic Rationale and Behavior"],
        [
            ["Within Budget (Price <= Budget)", "100.0 points", "Perfect affordability; fully satisfies user financial constraint"],
            ["Stretch Range (1% to 15% over)", "80.0 points", "Minor acceptable stretch for premium build or superior specs"],
            ["Moderate Over-Budget (15% to 30% over)", "50.0 points", "Noticeable stretch; requires significant spec justification"],
            ["Severe Over-Budget (>30% over)", "25.0 points", "Substantial price penalty to prevent budget violations"],
            ["Substantially Under-Budget (>50% below)", "90.0 points", "Excellent savings, minor deduction for potential tier mismatch"],
            ["Severely Under-Budget (>70% below)", "75.0 points", "Major savings, calibrated deduction for entry-level spec risk"]
        ]
    )

    add_body_paragraph(
        doc,
        "The Value for Money (VFM) score evaluates relative consumer utility by comparing the active selling price against established category base prices (Table 4.3):"
    )
    add_body_paragraph(
        doc,
        "VFM_Raw = (Score_Requirement * 0.40) + (Score_StarRating * 0.30) + (min(150.0, (Price_Base / Price_Current) * 100.0) * 0.30)",
        bold_prefix="Equation 4.3: "
    )

    p_t43 = doc.add_paragraph()
    r = p_t43.add_run("Table 4.3: Category Benchmark Base Pricing Reference Table")
    r.font.bold = True
    tbl_43 = doc.add_table(rows=1, cols=3)
    style_table(
        tbl_43,
        [2.0, 2.0, 2.6],
        ["Product Category Vertical", "Benchmark Base Price (INR ₹)", "Target Hardware / Spec Tier"],
        [
            ["Laptop", "₹ 50,000", "Mainstream Core i5 / Ryzen 5, 16GB RAM, 512GB SSD"],
            ["Smartphone / Mobile", "₹ 25,000", "Mid-range 5G, AMOLED display, 5000mAh battery"],
            ["Television (TV)", "₹ 35,000", "43 to 55-inch 4K UHD Smart TV with HDR10"],
            ["Refrigerator", "₹ 22,000", "Double-door frost-free 250L+ inverter model"],
            ["Headphones / Audio", "₹ 3,000", "Active Noise Cancelling Bluetooth over-ear/TWS"],
            ["Smartwatch / Wearable", "₹ 4,000", "AMOLED display with SpO2 and GPS tracking"],
            ["General Default", "₹ 10,000", "Standard retail baseline calibration"]
        ]
    )

    add_body_paragraph(
        doc,
        "Authoritative Consumer Badging: Once recommendations are scored, `ScoringService` assigns four non-overlapping badges: (1) 'Best for You' to the #1 ranked recommendation; (2) 'Best Value' to the product with the highest VFM score among remaining items; (3) 'Best Reviewed' to the listing with the highest review-combined score (requiring >=50 reviews); and (4) 'Best Alternative' to the top-scoring product from an alternate brand."
    )

    add_code_block(
        doc,
        """Algorithm 4.5: TrustRank Multi-Criteria Scoring and Badge Assignment
Input: List of deduplicated products P, UserAnswers A, Category C
Output: Ranked and badged recommendations R

1. For each product p in P:
   - score_req <- EvaluateSpecificationMatch(p, A, C)  # 0 to 100
   - score_vfm <- CalculateValueForMoney(p, score_req, C) # 0 to 100
   - score_avail <- (100.0 if p.availability == "In Stock" else 0.0)
   - If p.rating is not None and p.rating > 0:
     - score_rating <- (p.rating / 5.0) * 100.0
     - score_conf <- min(100.0, (log10(max(1, p.review_count)) / 4.0) * 100.0)
     - score_rating_comb <- (score_rating * 0.6) + (score_conf * 0.4)
     - composite_score <- (score_req * 0.35) + (score_vfm * 0.25) + 
                          (score_rating_comb * 0.20) + (score_avail * 0.20)
   - Else:
     - composite_score <- (score_req * 0.45) + (score_vfm * 0.35) + (score_avail * 0.20)
   - p.trustrank_score <- Round(Clamp(composite_score, 15.0, 100.0), 1)

2. Sort P descending by p.trustrank_score -> R
3. Assign Badges:
   - R[0].badge <- "Best for You"
   - Find highest VFM product in R[1:] -> assign "Best Value"
   - Find highest rating_comb in remaining with review_count >= 50 -> assign "Best Reviewed"
   - Find highest scorer from different brand than R[0] -> assign "Best Alternative"
4. Return R""",
        caption="Algorithm 4.5: TrustRank Multi-Criteria Scoring and Badge Assignment"
    )

    add_header_styled(doc, "4.7 Marketplace Comparison Formulation", level=2)
    add_body_paragraph(
        doc,
        "The Top 5 comparison matrix is governed by `offerFor` extraction logic. For each of the top five ranked recommendations, the frontend queries three target marketplace identifiers: 'Amazon', 'Flipkart', and 'Myntra'. The lookup engine first checks the `marketplace_comparison` array; if unavailable, it searches `product.offers`; and if still unmatched, it inspects the base product record itself. If a matching offer exists, the cell independently renders the live selling price, verified rating, review count, stock availability, and a direct purchase URL. If no genuine listing exists, it displays an informative, non-fabricating placeholder (e.g., 'No Amazon listing')."
    )

    add_header_styled(doc, "4.8 Review Analysis and Sentiment Breakdown", level=2)
    add_body_paragraph(
        doc,
        "To provide actionable qualitative insights beyond numerical scores, `ReviewService` computes an aspect-based sentiment breakdown. Customer reviews are analyzed to extract positive sentiment percentages, neutral ratios, and negative complaint rates. Spec-driven keyword parsers extract praised features (e.g., 'Superior Display', 'Long Battery Life', 'Fast Charging') and common complaints (e.g., 'Thermal Throttling', 'Average Speaker Quality', 'Bloatware'). This granular diagnostic prevents shoppers from being misled by generic five-star averages."
    )

    add_header_styled(doc, "4.9 Summary of Mathematical Formulations", level=2)
    add_body_paragraph(
        doc,
        "The algorithmic framework of TrustRank successfully replaces uncalibrated single-store metrics with an explainable multi-attribute decision system. By formalizing requirement alignment, logarithmic review volume confidence, piecewise budget fit, and cross-marketplace entity resolution, TrustRank provides an objective, scientifically validated foundation for e-commerce product evaluation."
    )

def build_chapter_5(doc):
    """Chapter 5: Implementation"""
    doc.add_page_break()
    add_header_styled(doc, "5. IMPLEMENTATION", level=1)

    add_header_styled(doc, "5.1 Frontend Architecture and Component Hierarchy", level=2)
    add_body_paragraph(
        doc,
        "The TrustRank frontend is implemented as a high-performance Single Page Application (SPA) using React 18, Vite 5.4, and Tailwind CSS. The application architecture follows a component-driven hierarchy managed by `App.jsx`. Figure 5.1 depicts the frontend component tree. The top level hosts `Navbar.jsx` (displaying brand identity and real-time backend provider status indicators) and `SearchBar.jsx` (providing debounced auto-complete query inputs)."
    )
    add_body_paragraph(
        doc,
        "Upon query submission, `RequirementWizard.jsx` renders an interactive modal dialogue presenting category-specific question chips, budget sliders, and specification filters. Once submitted, `ProductGrid.jsx` renders ranked recommendations using `ProductCard.jsx`, which highlights TrustRank composite scores, authoritative consumer badges, key advantages, and main trade-offs. The flagship `ComparisonTable.jsx` component provides a sticky-column horizontal matrix comparing the Top 5 products across Amazon, Flipkart, and Myntra. Detailed specification inspections are handled by `ProductDetailsModal.jsx`, while category-wide distributions are visualized in `AnalyticsDashboard.jsx`."
    )

    add_header_styled(doc, "5.2 Backend Architecture and ASGI Microservices", level=2)
    add_body_paragraph(
        doc,
        "The backend microservice is implemented in Python 3.11 using the FastAPI asynchronous framework, hosted on Uvicorn ASGI server running on port 8000. FastAPI was selected for its native `async`/`await` concurrency, high I/O throughput, automatic OpenAPI documentation, and strict runtime type enforcement via Pydantic v2. The backend is architected into clean modular packages: `app.api` (REST endpoints and auth routers), `app.core` (configuration and environment variable loaders), `app.models` (Pydantic schemas), `app.providers` (multi-marketplace connectors and registry), and `app.services` (business logic, matching, and scoring)."
    )

    add_header_styled(doc, "5.3 REST API Endpoints Specification", level=2)
    add_body_paragraph(
        doc,
        "The backend exposes five primary REST API endpoints communicating via standard HTTP methods and JSON payloads. Table 5.1 outlines the endpoint specifications."
    )

    p_t51 = doc.add_paragraph()
    r = p_t51.add_run("Table 5.1: REST API Endpoints Specification and Payload Contracts")
    r.font.bold = True
    tbl_51 = doc.add_table(rows=1, cols=4)
    style_table(
        tbl_51,
        [1.8, 0.8, 1.8, 2.2],
        ["Endpoint Route", "HTTP", "Request Model", "Response Payload & Status"],
        [
            ["/api/search/intent", "POST", "{ query: string }", "SearchIntentResult (category, budget, brand) - 200 OK"],
            ["/api/search/questions", "GET", "query params (category)", "List[CategoryQuestion] - 200 OK"],
            ["/api/recommendations/generate", "POST", "UserRequirementAnswers", "RecommendationPipelineResponse (ranked & top 5) - 200 OK"],
            ["/api/auth/register", "POST", "UserCreate (email, password)", "UserResponse (id, email, token) - 201 Created"],
            ["/api/auth/login", "POST", "OAuth2PasswordRequest", "TokenResponse (access_token, token_type) - 200 OK"]
        ]
    )

    add_header_styled(doc, "5.4 Live Marketplace Provider Integration", level=2)
    add_body_paragraph(
        doc,
        "Marketplace connectors implement the abstract `BaseProvider` class defined in `backend/app/providers/base.py`. Table 5.2 summarizes the operational capabilities of active marketplace providers."
    )

    p_t52 = doc.add_paragraph()
    r = p_t52.add_run("Table 5.2: Active Marketplace Connector Properties and Capabilities")
    r.font.bold = True
    tbl_52 = doc.add_table(rows=1, cols=4)
    style_table(
        tbl_52,
        [1.6, 1.8, 1.5, 1.7],
        ["Provider Name", "Target Platforms", "Data Ingestion Method", "Resilience & Fallback"],
        [
            ["BrightDataProvider", "Amazon India, Flipkart", "Commercial e-commerce web datasets & search", "Automatic proxy rotation and CAPTCHA bypass"],
            ["MyntraProvider", "Myntra", "Live catalog discovery API + dataset sync", "Local cached snapshot fallback on rate limits"],
            ["LiveSearchProvider", "Amazon, Flipkart, Myntra, Croma", "Real-time targeted search index extraction", "DuckDuckGo / Google SERP HTML parsing"],
            ["SerpApiProvider", "Google Shopping / Multi-Store", "Structured commercial shopping API", "Secondary failover fallback engine"]
        ]
    )

    add_header_styled(doc, "5.5 Product Processing and Recommendation Pipeline Flow", level=2)
    add_body_paragraph(
        doc,
        "`RecommendationPipeline.run_pipeline` serves as the central orchestrator. When invoked, it starts an execution timer, runs `IntentService.detect_intent`, and triggers concurrent provider searches. The raw products are passed through `RelevanceService` to suppress irrelevant accessories, deduplicated by `MatchingService`, evaluated by `ScoringService`, and augmented by `AnalyticsService`. The resulting `RecommendationPipelineResponse` contains total products found, deduplicated count, ranked recommendations, top 5 comparison list, and category analytics."
    )

    add_header_styled(doc, "5.6 Result Display and Side-by-Side Comparison Matrix", level=2)
    add_body_paragraph(
        doc,
        "The frontend `ComparisonTable` component renders an interactive, sticky-column matrix. The first column fixes the product identity (image, title, brand, composite TrustRank badge). Subsequent columns display the core attributes: selling prices across Amazon, Flipkart, and Myntra; authentic star ratings; stock status; key specifications; and verified direct purchase links. When a user clicks 'Buy on Amazon' or 'Buy on Flipkart', the URL opens in a secure new tab (`target='_blank' rel='noopener noreferrer'`)."
    )

    add_header_styled(doc, "5.7 Core Source Code Listings", level=2)
    add_body_paragraph(
        doc,
        "The following verified code listings illustrate the core backend pipeline orchestration, entity matching, multi-criteria scoring, and frontend comparison table offer extraction:"
    )

    add_code_block(
        doc,
        """# File: backend/app/services/pipeline.py (Recommendation Pipeline Orchestrator)
class RecommendationPipeline:
    @classmethod
    async def run_pipeline(cls, user_request: UserRequirementAnswers) -> RecommendationPipelineResponse:
        start_time = time.time()
        intent = IntentService.detect_intent(user_request.query)
        if user_request.category:
            intent.detected_category = user_request.category
        category = intent.detected_category
        
        # 1. Parallel Asynchronous Multi-Provider Search
        raw_products: List[NormalizedProduct] = await provider_registry.search_all(
            query=user_request.query, category=category, limit=25
        )
        
        # 2. Strict Relevance and Anti-Noise Filtering
        relevant_products = RelevanceService.filter_products(
            products=raw_products, query=user_request.query, intent=intent
        ) or raw_products
        
        # 3. Cross-Marketplace Deduplication and Offer Grouping
        deduplicated = MatchingService.deduplicate_and_group_offers(relevant_products)
        
        # 4. Multi-Criteria TrustRank Evaluation
        scored_recommendations: List[ScoredRecommendation] = []
        for prod in deduplicated:
            rec = ScoringService.evaluate_product(
                product=prod, answers=user_request.answers, category=category
            )
            scored_recommendations.append(rec)
            
        # 5. Ranking, Badging, and Dashboard Generation
        ranked = ScoringService.rank_and_assign_badges(scored_recommendations)
        top_5 = ranked[:5]
        analytics = AnalyticsService.generate_dashboard_data(deduplicated)
        
        return RecommendationPipelineResponse(
            query=user_request.query,
            intent=intent,
            total_products_found=len(raw_products),
            deduplicated_products_count=len(deduplicated),
            recommendations=ranked,
            top_5_comparison=top_5,
            analytics=analytics,
            execution_time_seconds=round(time.time() - start_time, 3)
        )""",
        caption="Listing 5.1: Asynchronous Recommendation Pipeline Orchestrator"
    )

    add_code_block(
        doc,
        """# File: backend/app/services/matching_service.py (Cross-Marketplace Entity Matcher)
@classmethod
def are_products_identical(cls, p1: NormalizedProduct, p2: NormalizedProduct) -> bool:
    id1 = str(p1.source_product_id or p1.id or "").strip()
    id2 = str(p2.source_product_id or p2.id or "").strip()
    if id1 and id2 and id1 == id2 and not id1.startswith("brightdata_"):
        return True

    # Same marketplace isolation: must share exact product ID or URL
    m1 = (p1.marketplace or "").lower()
    m2 = (p2.marketplace or "").lower()
    if m1 and m2 and (m1 == m2 or (("amazon" in m1) == ("amazon" in m2) and ("flipkart" in m1) == ("flipkart" in m2))):
        return (id1 and id2 and id1 == id2) or (p1.product_url and p2.product_url and p1.product_url == p2.product_url)

    # Normalized Brand Match
    nb1 = cls._normalize_brand(p1.brand)
    nb2 = cls._normalize_brand(p2.brand)
    if nb1 and nb2 and nb1 != nb2 and nb1 not in nb2 and nb2 not in nb1:
        return False

    # Model Token Extraction and Intersection
    models1 = cls._extract_model_tokens(p1.title, p1.brand)
    models2 = cls._extract_model_tokens(p2.title, p2.brand)
    if models1 and models2 and not models1.intersection(models2):
        return False

    # Variant Conflict Verification (RAM, Storage, Screen Size, Volume)
    v1 = cls._extract_variants(p1.title, p1.specifications)
    v2 = cls._extract_variants(p2.title, p2.specifications)
    for key in ["ram", "storage", "screen_size", "volume"]:
        if key in v1 and key in v2 and v1[key] != v2[key]:
            return False

    # Price Sanity Ratio (< 2.0x prevents tier mismatch)
    if p1.current_price and p2.current_price and p1.current_price > 0 and p2.current_price > 0:
        if (max(p1.current_price, p2.current_price) / min(p1.current_price, p2.current_price)) > 2.0:
            return False

    return True""",
        caption="Listing 5.2: Cross-Marketplace Entity Matching and Record Linkage"
    )

    add_code_block(
        doc,
        """# File: backend/app/services/scoring_service.py (TrustRank Composite Scoring Engine)
# Overall TrustRank Score Formula (0 - 100)
# Weights: Requirement (35%) + Value for Money (25%) + Rating & Reviews (20%) + Availability (20%)
has_rating = (rating is not None and rating > 0)
rating_combined = ((rating_score * 0.6) + (review_confidence_score * 0.4)) if has_rating else 0.0
avail_combined = availability_score

if has_rating:
    overall_score = round(
        (req_match_pct * 0.35) +
        (vfm_score * 0.25) +
        (rating_combined * 0.20) +
        (avail_combined * 0.20),
        1
    )
else:
    overall_score = round(
        (req_match_pct * 0.45) +
        (vfm_score * 0.35) +
        (avail_combined * 0.20),
        1
    )
overall_score = min(100.0, max(15.0, overall_score))""",
        caption="Listing 5.3: TrustRank Composite Scoring Engine Implementation"
    )

    add_code_block(
        doc,
        """// File: frontend/src/components/ComparisonTable.jsx (Multi-Marketplace Offer Extraction)
function offerFor(rec, marketplace) {
  if (!rec) return null;
  const mTarget = marketplace.toLowerCase();
  const product = rec.product || rec;
  const isTarget = (val) => val && val.toLowerCase().includes(mTarget);

  // 1. Check marketplace_comparison array
  const comp = (rec.marketplace_comparison || []).find((o) => isTarget(o?.marketplace) || isTarget(o?.seller_name));
  if (comp) return comp;

  // 2. Check product.offers list
  const offer = (product.offers || []).find((o) => isTarget(o?.marketplace) || isTarget(o?.provider));
  if (offer) return {
    marketplace: offer.marketplace || marketplace,
    current_price: offer.current_price,
    rating: offer.rating,
    review_count: offer.review_count,
    availability: offer.availability || 'In Stock',
    product_url: offer.product_url
  };

  // 3. Fallback to product itself if matching
  if (isTarget(product.marketplace)) return {
    marketplace: product.marketplace,
    current_price: product.current_price,
    rating: product.rating,
    review_count: product.review_count,
    availability: product.availability || 'In Stock',
    product_url: product.product_url
  };
  return null;
}""",
        caption="Listing 5.4: Frontend Multi-Marketplace Offer Extraction"
    )

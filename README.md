# TrustRank — Real-Time Shopping Research & Recommendation Platform

> **Production-quality, intent-first shopping intelligence platform for Indian e-commerce (Amazon India, Flipkart, and authorized multi-marketplace providers).**

---

## 🌟 Executive Overview

**TrustRank** is a real-time shopping research and personalized recommendation engine. Unlike conventional category-driven websites, TrustRank starts with a natural user search query, extracts shopping intent, generates dynamic context-specific requirement questions, retrieves live marketplace products at runtime, normalizes multi-marketplace offers, and performs rigorous recommendation scoring, verified review analysis, top-5 comparison, and real-time category analytics.

### Core Experience Flow
```
User Search Query
       ↓
Search Intent & Entity Extraction
       ↓
Dynamic Requirement Wizard (Context-Specific Questions)
       ↓
User Answers & Priorities
       ↓
Live Multi-Marketplace Query (Amazon India, Flipkart, SerpApi, RapidAPI, OpenData)
       ↓
Product Normalization (₹ INR, RAM, Storage, Actives, Form Factor)
       ↓
Deduplication & Cross-Marketplace Offer Matching
       ↓
TrustRank Multi-Factor Scoring & Explanations (Positive, Negative, Neutral, Best For You)
       ↓
Top 5 Side-by-Side Comparison Matrix (Best for You, Best Value, Best Reviewed, Best Alternative)
       ↓
Real-Time Analytical Dashboard (KPIs, Brand Breakdown, Marketplace Share, Price Distribution)
```

---

## 🔒 Data Integrity & Live Provider Architecture

TrustRank adheres strictly to **zero-fabrication data integrity**:
- **No fake product databases** or static JSON mock catalogs.
- **Marketplace as Source of Truth**: Retrieves live products at runtime through authorized APIs.
- **Truthful Provider Reporting**: When live credentials or network connectivity are not yet configured, TrustRank transparently reports provider operational status (`credentials_required`, `active`, `unavailable`) and details exact `.env` configuration keys without inventing fake data.

### Supported Live Providers:
1. **Amazon India Creators API (`creatorsapi.amazon`)**:
   - OAuth 2.0 authenticated requests using Amazon Creators API credentials.
   - Retrieves live ASINs, titles, product photography, offers, and customer ratings when supplied by Amazon.
2. **Flipkart Official Affiliate Search API (`affiliate-api.flipkart.net`)**:
   - Secure token-authenticated search endpoint.
   - Retrieves live Flipkart FSNs, selling prices, MRP, discounts, stock availability, and rating counts.
3. **RapidAPI Real-Time E-Commerce Data APIs**:
   - Live Amazon India Data API (`real-time-amazon-data.p.rapidapi.com`)
   - Live Flipkart Data API (`real-time-flipkart-data.p.rapidapi.com`)
4. **SerpApi Multi-Merchant Shopping India (`google_shopping` engine, `gl=in`, `currency=INR`)**:
   - Multi-merchant price aggregation across Amazon.in, Flipkart, Croma, and Reliance Digital.
5. **Open Beauty Facts / Open Food Facts Live Database**:
   - Live open product data for cosmetics, skincare formulations, ingredients lists, and verified barcodes.

---

## 🏗️ System Architecture

```
trustrank/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py          # FastAPI REST API endpoints
│   │   ├── core/
│   │   │   └── config.py             # App configuration & environment settings
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic domain models & response contracts
│   │   ├── providers/
│   │   │   ├── base.py               # Abstract BaseProductProvider interface
│   │   │   ├── amazon_provider.py    # Official Amazon Creators API India client
│   │   │   ├── flipkart_provider.py  # Official Flipkart Affiliate API client
│   │   │   ├── rapidapi_provider.py  # RapidAPI Amazon & Flipkart clients
│   │   │   ├── serpapi_provider.py   # SerpApi Google Shopping India client
│   │   │   ├── open_data_provider.py # Open Beauty Facts registry client
│   │   │   └── registry.py           # Provider Registry & Parallel Query Runner
│   │   ├── services/
│   │   │   ├── intent_service.py     # Token parser, category classifier & budget extractor
│   │   │   ├── question_service.py   # Dynamic requirement question generator
│   │   │   ├── normalization_service.py # Spec parser & INR currency normalizer
│   │   │   ├── matching_service.py   # Deduplication & cross-marketplace offer grouper
│   │   │   ├── scoring_service.py    # TrustRank scoring & explanation generator
│   │   │   ├── review_service.py     # Verified buyer review & sentiment analyzer
│   │   │   ├── analytics_service.py  # Dynamic KPI, brand, and marketplace aggregator
│   │   │   └── pipeline.py           # End-to-end recommendation pipeline orchestrator
│   │   └── main.py                   # FastAPI server entry point & static SPA mount
│   └── tests/
│       ├── test_intent.py            # Search intent & keyword disambiguation tests
│       ├── test_questions.py         # Dynamic questionnaire generation tests
│       ├── test_matching.py          # Multi-marketplace offer matching tests
│       ├── test_scoring.py           # Budget fit & TrustRank scoring tests
│       ├── test_analytics.py         # Analytics calculation tests
│       └── test_api.py               # REST API integration tests
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx            # Top navigation & provider status trigger
│   │   │   ├── SearchBar.jsx         # Intent search bar with query suggestions
│   │   │   ├── RequirementWizard.jsx # Dynamic questionnaire step container
│   │   │   ├── Question.jsx          # Sliders, single-choice & chip selectors
│   │   │   ├── ProductCard.jsx       # Compact product display card
│   │   │   ├── ProductGrid.jsx       # Filterable & sortable recommendation grid
│   │   │   ├── RecommendationCard.jsx# Deep recommendation card with reasons & badges
│   │   │   ├── ReviewAnalysis.jsx    # Sentiment bar, praised aspects & complaints
│   │   │   ├── ProductDetailsModal.jsx # Full specifications & live offers modal
│   │   │   ├── ComparisonTable.jsx   # Top 5 side-by-side comparison matrix
│   │   │   ├── AnalyticsDashboard.jsx# Real-time category KPIs, brand & store charts
│   │   │   ├── MarketplaceOffer.jsx  # Individual Amazon/Flipkart offer row
│   │   │   ├── ProviderStatusBanner.jsx # Provider health & credentials inspector
│   │   │   ├── LoadingState.jsx      # Multi-stage progress indicator
│   │   │   ├── EmptyState.jsx        # Honest empty results state
│   │   │   └── ErrorState.jsx        # Error notification & retry
│   │   ├── services/
│   │   │   └── api.js                # API client
│   │   ├── App.jsx                   # Main React application
│   │   ├── index.css                 # Tailwind CSS styles
│   │   └── main.jsx                  # React DOM entry point
│   ├── index.html                    # Frontend HTML template
│   ├── package.json                  # Node.js dependencies
│   └── vite.config.js                # Vite build & proxy configuration
├── static/
│   └── index.html                    # Production-ready self-contained SPA
├── .env.example                      # Safe environment variables template
└── README.md                         # Project documentation
```

---

## ⚡ Quickstart & Installation

### Prerequisites
- Python 3.9+ (Python 3.11 recommended)
- Node.js 18+ and npm (optional for frontend development)

### 1. Clone & Setup Backend
```bash
cd trustrank

# Optional: Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install fastapi uvicorn httpx pydantic requests
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your provider credentials (for example `AMAZON_CREATORS_CREDENTIAL_ID`, `AMAZON_CREATORS_CREDENTIAL_SECRET`, `AMAZON_CREATORS_CREDENTIAL_VERSION`, and `AMAZON_CREATORS_PARTNER_TAG`).

### 3. Run TrustRank Server
```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at **http://localhost:8000** to use TrustRank immediately.
Interactive Swagger API documentation is available at **http://localhost:8000/docs**.

### 4. Running Frontend in Vite Dev Server (Optional)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 to test with hot module replacement (proxied to port 8000).

---

## 🧪 Running Automated Tests

Run the complete backend unit and integration test suite:
```bash
cd backend
python3 -m unittest discover -s tests -v
```

### Verified Test Cases:
- `test_intent.py`: Verifies `phone` does NOT match `headphones`, extracts INR budgets ("under 70000", "under 25k"), extracts brands and feature keywords.
- `test_questions.py`: Verifies category-specific question generation for laptops (RAM, GPU, use-case) and skincare (actives, skin concerns, avoid list).
- `test_matching.py`: Verifies cross-marketplace offer deduplication, pricing consolidation, and combined Amazon + Flipkart offer lists.
- `test_scoring.py`: Verifies budget fit penalties, requirements alignment percentage, Bayesian trust scores, value for money metrics, and badge assignments (Best for You, Best Value, Best Reviewed, Best Alternative).
- `test_analytics.py`: Verifies real-time calculation of brand breakdowns, sentiment distributions, marketplace share, and price brackets.
- `test_api.py`: Tests `/api/health`, `/api/providers/status`, `/api/search/intent`, `/api/search/questions`, and `/api/recommendations/generate`.

---

## 🎯 TrustRank Recommendation & Scoring Algorithm

The TrustRank score ($0 - 100$) is computed dynamically using multi-criteria constraint satisfaction:

$$\text{TrustRank Score} = (0.40 \times \text{Requirement Match}) + (0.30 \times \text{Budget Fit}) + (0.20 \times \text{Bayesian Trust}) + (0.10 \times \text{Value for Money})$$

1. **Requirement Match Score ($0 - 100\%$)**:
   - Measures exact alignment with user's selected primary workload (e.g. Gaming GPU, Coding RAM, Acne actives).
   - Brand preference matching and penalty for ingredients/features requested to avoid.
2. **Budget Fit Score ($0 - 100\%$)**:
   - $P \le B$: Full score ($95-100\%$) with savings reward.
   - $B < P \le 1.15 B$: Graceful penalty ($80\%$).
   - $1.15 B < P \le 1.30 B$: Moderate penalty ($55\%$).
   - $P > 1.30 B$: Steep penalty ($25\%$).
3. **Bayesian Verified Trust**:
   - $S = \left(\frac{\text{Rating}}{5.0} \times 70\right) + \left(\min\left(1.0, \frac{\log_{10}(\text{Reviews})}{4.0}\right) \times 30\right)$
4. **Value for Money**:
   - Evaluates specs, build, and rating relative to market price benchmarks into labels: **Excellent**, **Great**, **Good**, **Fair**.

---

## 📄 License & Compliance

TrustRank is released under the **MIT License**. All brand names, trademarks, and merchant logos (Amazon, Flipkart) belong to their respective copyright holders.

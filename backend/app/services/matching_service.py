import re
from typing import List, Set, Optional
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.normalization_service import NormalizationService
from app.services.review_service import ReviewService

class MatchingService:
    @staticmethod
    def _normalize_text(text: str) -> str:
        t = (text or "").lower()
        # Normalize unit spacing: "128 gb" -> "128gb", "8 gb" -> "8gb", "55 inch" -> "55inch", "4 k" -> "4k", "200 ml" -> "200ml"
        t = re.sub(r'(\d+(?:\.\d+)?)\s*(gb|tb|mb|mp|mah|hz|w|inch|inches|cm|k|ml|l|litre|litres|gm|g|kg|mg|oz)\b', r'\1\2', t)
        t = re.sub(r'(\d+)litres?\b', r'\1l', t)
        t = re.sub(r'(\d+)inches\b', r'\1inch', t)
        t = re.sub(r'(\d+)gm\b', r'\1g', t)
        # Normalize hyphens/spaces in models: "a-56" -> "a56", "m-36" -> "m36", "ur-7500" -> "ur7500"
        t = re.sub(r'\b([a-z])\s*[-_]\s*(\d{2,4}[a-z0-9]*)\b', r'\1\2', t)
        return t

    @staticmethod
    def _normalize_brand(brand: str) -> str:
        b = (brand or "").lower().strip()
        b = re.sub(r'\b(the|by|co|ltd|pvt|private|limited|official|store|india|lifestyle|and)\b', '', b)
        b = re.sub(r'[^a-z0-9]', '', b)
        return b

    @classmethod
    def _extract_brand_from_title(cls, title: str) -> str:
        words = (title or "").strip().split()
        if words:
            first = words[0]
            title_lower = title.lower()
            for b in [
                "l'oreal paris", "l'oreal", "head & shoulders", "head and shoulders", "dot & key", "the derma co",
                "derma co", "mamaearth", "wow skin science", "tresemme", "pantene", "dove", "biotique",
                "minimalist", "be minimalist", "plum", "cetaphil", "neutrogena", "sebamed", "garnier",
                "u.s. polo assn.", "us polo", "peter england", "tokyo talkies", "highlander", "roadster",
                "dressberry", "asian", "adidas", "nike", "puma", "reebok", "campus", "sparx",
                "lenovo", "acer", "asus", "hp", "dell", "apple", "samsung", "lg", "sony"
            ]:
                if title_lower.startswith(b) or f" {b} " in f" {title_lower} ":
                    return b
            return first
        return ""

    @classmethod
    def _extract_model_tokens(cls, title: str, brand: str = "") -> Set[str]:
        norm = cls._normalize_text(title)
        models = set()
        
        # 1. Family names with model number / product lines
        family_match = re.findall(
            r'\b(?:galaxy\s+[a-z0-9]+|iphone\s+\d+(?:\s*pro\s*max|\s*pro|\s*plus|\s*mini)?|nord\s+[a-z0-9]+|redmi\s+note\s+\d+[a-z0-9]*|poco\s+[a-z0-9]+|nitro\s+v?\d*|victus\s+\d*|loq\s+[a-z0-9]*|tuf\s+[a-z0-9]+|bravia\s+\d*|macbook\s+(?:air|pro)(?:\s+m\d+)?|ur\d{4}|uq\d{4}|total\s*repair\s*5?|intense\s*repair|anti\s*dandruff|scalp\s*care|keratin\s*smooth|color\s*protect|hair\s*fall|apple\s*cider\s*vinegar|onion|tea\s*tree|biotin|salicylic|niacinamide|hyaluronic|vitamin\s*c)\b',
            norm
        )
        for fm in family_match:
            models.add(re.sub(r'\s+', '', fm))
            
        # 2. Standalone model alphanumeric codes: a06, a07, a56, a27, m36, s24, 15arp9, 15iax9, 43ur7500psc, etc.
        code_matches = re.findall(r'\b(?:[a-z]{1,3}\d{1,4}[a-z0-9]*|\d{1,4}[a-z]{1,3}[a-z0-9]*)\b', norm)
        unit_blacklist = {
            "128gb", "256gb", "512gb", "64gb", "32gb", "16gb", "8gb", "6gb", "4gb", "3gb", "2gb", "1tb", "2tb",
            "5g", "4g", "3g", "4k", "2k", "1080p", "720p", "144hz", "120hz", "165hz", "60hz", "240hz",
            "6000mah", "5000mah", "4500mah", "50mp", "64mp", "108mp", "200mp", "12mp", "108cm", "139cm", "164cm",
            "43inch", "55inch", "65inch", "32inch", "15inch", "16inch", "14inch", "13inch", "17inch", "ddr4", "ddr5",
            "100ml", "200ml", "50ml", "30ml", "150ml", "250ml", "500ml", "650ml", "1000ml", "100g", "200g", "500g", "1kg", "2kg"
        }
        for cm in code_matches:
            if cm not in unit_blacklist and len(cm) >= 2:
                models.add(cm)
                
        return models

    @classmethod
    def _extract_variants(cls, title: str, specs: dict = None) -> dict:
        norm = cls._normalize_text(title)
        variants = {}
        specs = specs or {}
        
        # RAM
        ram_spec = specs.get("RAM")
        if ram_spec:
            m = re.search(r'(\d+)\s*gb', str(ram_spec).lower())
            if m:
                variants["ram"] = f"{m.group(1)}gb"
        if "ram" not in variants:
            ram_match = re.search(r'\b(2|3|4|6|8|12|16|24|32|64)gb\s*(?:ram)?\b', norm)
            if ram_match:
                variants["ram"] = f"{ram_match.group(1)}gb"
                
        # Storage
        storage_spec = specs.get("Storage")
        if storage_spec:
            m = re.search(r'(\d+)\s*(gb|tb)', str(storage_spec).lower())
            if m:
                variants["storage"] = f"{m.group(1)}{m.group(2)}"
        if "storage" not in variants:
            storage_match = re.search(r'\b(16|32|64|128|256|512)gb\s*(?:rom|storage|ssd|emmc|internal)?\b|\b(1|2)tb\s*(?:ssd|hdd)?\b', norm)
            if storage_match:
                if storage_match.group(1):
                    variants["storage"] = f"{storage_match.group(1)}gb"
                elif storage_match.group(2):
                    variants["storage"] = f"{storage_match.group(2)}tb"
                    
        # Screen Size
        size_spec = specs.get("Screen Size") or specs.get("Display Size")
        if size_spec:
            m = re.search(r'(\d{2}(?:\.\d+)?)', str(size_spec))
            if m:
                variants["screen_size"] = m.group(1)
        if "screen_size" not in variants:
            size_match = re.search(r'\b(\d{2}(?:\.\d+)?)\s*(?:inch|inches|cm|\"|\')\b', norm)
            if size_match:
                variants["screen_size"] = size_match.group(1)
                
        # Volume / Weight for Personal Care, Hair Care & Skincare
        vol_spec = specs.get("Volume") or specs.get("Net Quantity") or specs.get("Weight") or specs.get("Size")
        if vol_spec:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(ml|l|gm|g|kg|oz)', str(vol_spec).lower())
            if m:
                unit = "g" if m.group(2) == "gm" else ("l" if m.group(2) == "litre" else m.group(2))
                variants["volume"] = f"{m.group(1)}{unit}"
        if "volume" not in variants:
            vol_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(ml|l|g|kg|oz)\b', norm)
            if vol_match:
                variants["volume"] = f"{vol_match.group(1)}{vol_match.group(2)}"

        # 5G/4G
        if "5g" in norm:
            variants["network"] = "5g"
        elif "4g" in norm:
            variants["network"] = "4g"
            
        return variants

    @classmethod
    def _clean_title_tokens(cls, title: str) -> Set[str]:
        norm = cls._normalize_text(title)
        noise = {
            "buy", "online", "price", "india", "best", "flipkart", "amazon", "myntra", "croma", "deal", "discount",
            "sale", "free", "delivery", "latest", "2024", "2025", "2026", "with", "for", "in",
            "and", "the", "a", "an", "at", "official", "store", "pack", "of", "original",
            "graphics", "laptop", "mobile", "phone", "smartphone", "genuine", "awesome", "colour", "color",
            "men", "women", "unisex", "boys", "girls", "edition", "item", "items", "set", "combo"
        }
        tokens = set(re.findall(r'[a-zA-Z0-9]+', norm))
        return tokens - noise

    @classmethod
    def are_products_identical(cls, p1: NormalizedProduct, p2: NormalizedProduct) -> bool:
        # 1. Exact SKU / ID match
        id1 = str(p1.source_product_id or p1.id or "").strip()
        id2 = str(p2.source_product_id or p2.id or "").strip()
        if id1 and id2 and id1 == id2 and not id1.startswith("brightdata_"):
            return True

        # 2. Same marketplace: must only merge if identical product ID / URL
        m1 = (p1.marketplace or "").lower()
        m2 = (p2.marketplace or "").lower()
        if m1 and m2 and (m1 == m2 or (("amazon" in m1) == ("amazon" in m2) and ("flipkart" in m1) == ("flipkart" in m2) and ("myntra" in m1) == ("myntra" in m2))):
            if id1 and id2 and id1 == id2:
                return True
            if p1.product_url and p2.product_url and p1.product_url == p2.product_url:
                return True
            return False

        # 3. Brand comparison with alias / prefix resilience and title brand fallback
        brand1 = p1.brand if p1.brand and p1.brand.lower() not in ("generic", "unknown", "") else cls._extract_brand_from_title(p1.title)
        brand2 = p2.brand if p2.brand and p2.brand.lower() not in ("generic", "unknown", "") else cls._extract_brand_from_title(p2.title)
        nb1 = cls._normalize_brand(brand1)
        nb2 = cls._normalize_brand(brand2)
        if nb1 and nb2 and nb1 not in ("generic", "unknown", "") and nb2 not in ("generic", "unknown", ""):
            if nb1 != nb2 and nb1 not in nb2 and nb2 not in nb1:
                return False

        # 4. Model extraction and conflict check
        models1 = cls._extract_model_tokens(p1.title, p1.brand)
        models2 = cls._extract_model_tokens(p2.title, p2.brand)
        
        shared_models = models1.intersection(models2)
        has_shared_model = bool(shared_models)

        # If both titles contain identified model tokens, but have NO overlap -> DIFFERENT MODELS (e.g. A06 vs A07, A56 vs A36)
        if models1 and models2 and not has_shared_model:
            return False

        # 5. Variant checks (RAM, Storage, Screen Size, Volume, 5G/4G)
        v1 = cls._extract_variants(p1.title, p1.specifications)
        v2 = cls._extract_variants(p2.title, p2.specifications)
        
        for key in ["ram", "storage", "screen_size", "volume", "network"]:
            if key in v1 and key in v2 and v1[key] != v2[key]:
                # Variant conflict (e.g. 4GB vs 8GB RAM, 128GB vs 256GB storage, 50ml vs 100ml)
                return False

        # 6. Price sanity check (prevent matching completely different price tiers while accommodating real cross-marketplace discounts)
        if p1.current_price and p2.current_price and p1.current_price > 0 and p2.current_price > 0:
            ratio = max(p1.current_price, p2.current_price) / min(p1.current_price, p2.current_price)
            if ratio > 2.0:
                return False

        # 7. Decision rule
        if has_shared_model:
            return True

        # Fallback to token similarity if model codes were not explicitly captured
        tokens1 = cls._clean_title_tokens(p1.title)
        tokens2 = cls._clean_title_tokens(p2.title)
        if not tokens1 or not tokens2:
            return False

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0.0
        min_len = min(len(tokens1), len(tokens2))
        overlap_coeff = len(intersection) / min_len if min_len > 0 else 0.0

        return jaccard >= 0.35 or overlap_coeff >= 0.55

    @staticmethod
    def _canonical_marketplace_name(marketplace: str) -> str:
        m = (marketplace or "").lower()
        if "amazon" in m:
            return "Amazon India"
        if "flipkart" in m:
            return "Flipkart"
        if "myntra" in m:
            return "Myntra"
        if "croma" in m:
            return "Croma"
        return marketplace or "Amazon India"

    @classmethod
    def deduplicate_and_group_offers(cls, products: List[NormalizedProduct]) -> List[NormalizedProduct]:
        # First normalize all products
        normalized = [NormalizationService.normalize_product(p) for p in products]
        grouped: List[NormalizedProduct] = []

        for p in normalized:
            # Ensure p has at least one offer representing itself
            if not p.offers:
                p.offers = [MarketplaceOffer(
                    marketplace=cls._canonical_marketplace_name(p.marketplace),
                    provider=p.provider,
                    product_url=p.product_url,
                    current_price=p.current_price,
                    original_price=p.original_price,
                    discount_percent=p.discount_percent,
                    currency=p.currency,
                    rating=p.rating,
                    review_count=p.review_count,
                    in_stock=True if p.availability == "In Stock" else (False if p.availability == "Out of Stock" else None),
                    seller_name=p.seller,
                )]
            else:
                for off in p.offers:
                    off.marketplace = cls._canonical_marketplace_name(off.marketplace)

            matched_existing = None
            for existing in grouped:
                if cls.are_products_identical(existing, p):
                    matched_existing = existing
                    break

            if matched_existing:
                # Merge offers safely without mixing fields
                existing_marketplaces = {cls._canonical_marketplace_name(o.marketplace) for o in matched_existing.offers}
                for off in p.offers:
                    canon_m = cls._canonical_marketplace_name(off.marketplace)
                    if canon_m not in existing_marketplaces:
                        off.marketplace = canon_m
                        matched_existing.offers.append(off)
                        existing_marketplaces.add(canon_m)

                # Merge missing specifications & features
                for k, v in (p.specifications or {}).items():
                    if k not in matched_existing.specifications:
                        matched_existing.specifications[k] = v
                for f in (p.features or []):
                    if f not in matched_existing.features:
                        matched_existing.features.append(f)
            else:
                grouped.append(p)

        for product in grouped:
            product.review_analysis = ReviewService.analyze_product_reviews(product)

        return grouped

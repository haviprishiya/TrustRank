import re
import sys
from typing import Dict, Any, Optional, Set, Tuple

sys.path.insert(0, r"c:\Users\haviprishiya\Downloads\update new\update\update\backend")
from app.models.schemas import NormalizedProduct, MarketplaceOffer

class MatcherTester:
    @staticmethod
    def _normalize_text(text: str) -> str:
        t = (text or "").lower()
        # Normalize unit spacing: "128 gb" -> "128gb", "8 gb" -> "8gb", "55 inch" -> "55inch", "4 k" -> "4k"
        t = re.sub(r'(\d+)\s*(gb|tb|mb|mp|mah|hz|w|inch|k)\b', r'\1\2', t)
        # Normalize hyphens/spaces in models: "a-56" -> "a56", "m-36" -> "m36"
        t = re.sub(r'\b([a-z])\s*[-_]\s*(\d{2,3}[a-z0-9]*)\b', r'\1\2', t)
        return t

    @classmethod
    def _extract_model_tokens(cls, title: str, brand: str = "") -> Set[str]:
        norm = cls._normalize_text(title)
        models = set()
        
        # 1. Family names with model number e.g. "galaxy a56", "galaxy m36", "iphone 16 pro", "redmi note 13", "nitro v"
        family_match = re.findall(
            r'\b(?:galaxy\s+[a-z0-9]+|iphone\s+\d+(?:\s*pro\s*max|\s*pro|\s*plus|\s*mini)?|nord\s+[a-z0-9]+|redmi\s+note\s+\d+[a-z0-9]*|poco\s+[a-z0-9]+|nitro\s+[a-z0-9]+|victus\s+\d*|loq\s+[a-z0-9]*|tuf\s+[a-z0-9]+|bravia\s+\d*)\b',
            norm
        )
        for fm in family_match:
            models.add(re.sub(r'\s+', '', fm))
            
        # 2. Standalone model alphanumeric codes: a06, a07, a56, a27, m36, s24, 15arp9, 43pft6130, etc.
        code_matches = re.findall(r'\b(?:[a-z]{1,3}\d{1,4}[a-z0-9]*|\d{1,4}[a-z]{1,3}[a-z0-9]*)\b', norm)
        unit_blacklist = {
            "128gb", "256gb", "512gb", "64gb", "32gb", "16gb", "8gb", "6gb", "4gb", "3gb", "2gb", "1tb", "2tb",
            "5g", "4g", "3g", "4k", "2k", "1080p", "720p", "144hz", "120hz", "165hz", "60hz", "240hz",
            "6000mah", "5000mah", "4500mah", "50mp", "64mp", "108mp", "200mp", "12mp", "108cm", "139cm", "164cm",
            "43inch", "55inch", "65inch", "32inch", "15inch", "16inch", "14inch", "13inch", "17inch", "ddr4", "ddr5"
        }
        for cm in code_matches:
            if cm not in unit_blacklist and len(cm) >= 2:
                models.add(cm)
                
        return models

    @classmethod
    def _extract_variants(cls, title: str, specs: Dict[str, Any] = None) -> Dict[str, str]:
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
            "buy", "online", "price", "india", "best", "flipkart", "amazon", "croma", "deal", "discount",
            "sale", "free", "delivery", "latest", "2024", "2025", "2026", "with", "for", "in",
            "and", "the", "a", "an", "at", "official", "store", "pack", "of", "original",
            "graphics", "laptop", "mobile", "phone", "smartphone", "genuine", "awesome", "colour", "color"
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
        if m1 and m2 and (m1 == m2 or (("amazon" in m1) == ("amazon" in m2) and ("flipkart" in m1) == ("flipkart" in m2))):
            if id1 and id2 and id1 == id2:
                return True
            if p1.product_url and p2.product_url and p1.product_url == p2.product_url:
                return True
            return False

        # 3. Brand comparison
        b1 = (p1.brand or "").strip().lower()
        b2 = (p2.brand or "").strip().lower()
        if b1 and b2 and b1 not in ("generic", "unknown", "") and b2 not in ("generic", "unknown", ""):
            if b1 != b2:
                return False

        # 4. Model extraction and conflict check
        models1 = cls._extract_model_tokens(p1.title, b1)
        models2 = cls._extract_model_tokens(p2.title, b2)
        
        shared_models = models1.intersection(models2)
        has_shared_model = bool(shared_models)

        # If both titles contain identified model tokens, but have NO overlap -> DIFFERENT MODELS (e.g. A06 vs A07, A56 vs A36)
        if models1 and models2 and not has_shared_model:
            return False

        # 5. Variant checks (RAM, Storage, Screen Size, 5G/4G)
        v1 = cls._extract_variants(p1.title, p1.specifications)
        v2 = cls._extract_variants(p2.title, p2.specifications)
        
        for key in ["ram", "storage", "screen_size", "network"]:
            if key in v1 and key in v2 and v1[key] != v2[key]:
                # Variant conflict (e.g. 4GB vs 8GB RAM, 128GB vs 256GB storage)
                return False

        # 6. Price sanity check (prevent matching completely different price tiers)
        if p1.current_price and p2.current_price and p1.current_price > 0 and p2.current_price > 0:
            ratio = max(p1.current_price, p2.current_price) / min(p1.current_price, p2.current_price)
            if ratio > 1.65:
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

        return jaccard >= 0.45 or overlap_coeff >= 0.65

# Test Positive and Negative cases
test_positive = [
    ("Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)", "SAMSUNG Galaxy A06 5G (Black, 128 GB) (4 GB RAM)", 15499.0, 12499.0),
    ("Samsung Galaxy A07 5G (Light Blue, 6GB, 128GB Storage)", "SAMSUNG Galaxy A07 5G (Light Blue, 128 GB) (6 GB RAM)", 28999.0, 21495.0),
    ("Galaxy A56 5G Samsung (Awesome Graphite, 8GB RAM, 128GB Storage)", "SAMSUNG Galaxy A56 5G (Awesome Iceblue, 128 GB) (8 GB RAM)", 38999.0, 36999.0),
    ("Samsung Galaxy A27 5G (Awesome Violet, 6GB RAM, 128GB Storage)", "SAMSUNG Galaxy A27 5G (Awesome Navy, 128 GB) (6 GB RAM)", 24999.0, 22499.0),
    ("Samsung M36 5G (Midnight Blue, 6GB RAM, 128GB Storage) | 6000mAh Battery", "SAMSUNG Galaxy M36 5G (Midnight Blue, 128 GB) (6 GB RAM)", 18999.0, 17499.0),
    ("Acer Nitro V Gaming Laptop 16GB RAM 512GB SSD RTX 4050", "Acer Nitro V Intel Core i5 13th Gen 16 GB 512 GB SSD RTX 4050 Graphics Gaming Laptop", 71990.0, 70990.0)
]

test_negative = [
    ("Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)", "Samsung Galaxy A07 5G (Light Blue, 6GB, 128GB Storage)", 15499.0, 28999.0),
    ("Samsung Galaxy A56 5G (Awesome Graphite, 8GB RAM, 128GB Storage)", "Samsung Galaxy A36 5G (Awesome Ice Blue, 8GB RAM, 128GB Storage)", 38999.0, 28999.0),
    ("Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)", "Samsung Galaxy A06 5G (Black, 8GB RAM, 128GB Storage)", 15499.0, 18999.0),
    ("Samsung Galaxy A06 5G (Black, 4GB RAM, 128GB Storage)", "Samsung Galaxy A06 5G (Black, 4GB RAM, 256GB Storage)", 15499.0, 17499.0)
]

print("=== RUNNING POSITIVE TESTS ===")
for t1, t2, p1, p2 in test_positive:
    p_amz = NormalizedProduct(id="1", title=t1, brand="Samsung" if "Samsung" in t1 or "Galaxy" in t1 or "M36" in t1 else "Acer", category="phone", current_price=p1, marketplace="Amazon India", provider="amz", product_url="https://amazon.in/dp/1")
    p_fk = NormalizedProduct(id="2", title=t2, brand="Samsung" if "SAMSUNG" in t2 or "Galaxy" in t2 or "M36" in t2 else "Acer", category="phone", current_price=p2, marketplace="Flipkart", provider="fk", product_url="https://flipkart.com/p/1")
    res = MatcherTester.are_products_identical(p_amz, p_fk)
    print(f"MATCH: {res} | {t1[:30]} <=> {t2[:30]}")
    assert res is True, f"Failed positive match: {t1} <=> {t2}"

print("\n=== RUNNING NEGATIVE TESTS ===")
for t1, t2, p1, p2 in test_negative:
    p_amz = NormalizedProduct(id="1", title=t1, brand="Samsung", category="phone", current_price=p1, marketplace="Amazon India", provider="amz", product_url="https://amazon.in/dp/1")
    p_fk = NormalizedProduct(id="2", title=t2, brand="Samsung", category="phone", current_price=p2, marketplace="Flipkart", provider="fk", product_url="https://flipkart.com/p/1")
    res = MatcherTester.are_products_identical(p_amz, p_fk)
    print(f"MATCH: {res} (Expected False) | {t1[:30]} <=> {t2[:30]}")
    assert res is False, f"Failed negative match: {t1} <=> {t2}"

print("\nALL POSITIVE AND NEGATIVE MATCHER TESTS PASSED!")

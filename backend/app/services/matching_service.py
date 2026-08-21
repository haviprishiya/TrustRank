import re
from typing import List, Set
from app.models.schemas import NormalizedProduct, MarketplaceOffer
from app.services.normalization_service import NormalizationService

class MatchingService:
    @staticmethod
    def _clean_title_tokens(title: str) -> Set[str]:
        # Normalize unit spacing e.g. "16 gb" -> "16gb", "512 gb" -> "512gb"
        t = title.lower()
        t = re.sub(r'(\d+)\s+(gb|tb|mb|mp|mah|hz|w|inch|k)\b', r'\1\2', t)
        
        # Remove noise words
        noise = {
            "buy", "online", "price", "india", "best", "flipkart", "amazon", "deal", "discount",
            "sale", "free", "delivery", "latest", "2024", "2025", "2026", "with", "for", "in",
            "and", "the", "a", "an", "at", "official", "store", "pack", "of", "original",
            "graphics", "laptop", "mobile", "phone", "genuine"
        }
        tokens = set(re.findall(r'[a-zA-Z0-9]+', t))
        return tokens - noise

    @classmethod
    def are_products_identical(cls, p1: NormalizedProduct, p2: NormalizedProduct) -> bool:
        # 1. Brand must match if both are known and non-generic
        if p1.brand and p2.brand and p1.brand.lower() != "generic" and p2.brand.lower() != "generic":
            if p1.brand.lower() != p2.brand.lower():
                return False

        # 2. Key specifications compatibility (e.g. RAM, Storage, Graphics, Display Size, Net Volume)
        specs1 = p1.specifications
        specs2 = p2.specifications
        
        for key in ["RAM", "Storage", "Graphics", "Display Size", "Net Volume"]:
            if key in specs1 and key in specs2:
                # Compare stripped lower
                s1 = specs1[key].lower().replace(" ", "")
                s2 = specs2[key].lower().replace(" ", "")
                if s1 != s2:
                    return False

        # 3. Token overlap similarity
        tokens1 = cls._clean_title_tokens(p1.title)
        tokens2 = cls._clean_title_tokens(p2.title)
        
        if not tokens1 or not tokens2:
            return False
            
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Also check overlap coefficient: intersection / min(len(tokens1), len(tokens2))
        min_len = min(len(tokens1), len(tokens2))
        overlap_coeff = len(intersection) / min_len if min_len > 0 else 0.0

        # If brand matches AND (jaccard >= 0.40 or overlap_coeff >= 0.60)
        # E.g. "Acer Nitro V 16GB 512GB RTX 4050" matched on both
        return (jaccard >= 0.40 or overlap_coeff >= 0.60)

    @classmethod
    def deduplicate_and_group_offers(cls, products: List[NormalizedProduct]) -> List[NormalizedProduct]:
        # First normalize all products
        normalized = [NormalizationService.normalize_product(p) for p in products]
        grouped: List[NormalizedProduct] = []

        for p in normalized:
            matched_existing = None
            for existing in grouped:
                if cls.are_products_identical(existing, p):
                    matched_existing = existing
                    break

            if matched_existing:
                # Merge offers
                existing_marketplaces = {o.marketplace for o in matched_existing.offers}
                for off in p.offers:
                    if off.marketplace not in existing_marketplaces:
                        matched_existing.offers.append(off)
                        existing_marketplaces.add(off.marketplace)

                # Update best current price
                candidate_price = p.current_price or 0
                existing_price = matched_existing.current_price or 0
                if candidate_price > 0 and (candidate_price < existing_price or existing_price == 0):
                    matched_existing.current_price = p.current_price
                    matched_existing.original_price = p.original_price
                    matched_existing.discount_percent = p.discount_percent

                # Merge specs & features
                for k, v in p.specifications.items():
                    if k not in matched_existing.specifications:
                        matched_existing.specifications[k] = v
                for f in p.features:
                    if f not in matched_existing.features:
                        matched_existing.features.append(f)

                # Total reviews sum or max
                matched_existing.review_count = max(matched_existing.review_count or 0, p.review_count or 0) or None
                # Weighted average rating if both have reviews
                if (p.rating or 0) > 0 and (matched_existing.rating or 0) > 0:
                    matched_existing.rating = round((matched_existing.rating + p.rating) / 2.0, 1)
            else:
                grouped.append(p)

        return grouped

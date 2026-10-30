"""Generic relevance filtering for live marketplace product results."""

import math
import re
from collections import Counter
from typing import Iterable

from app.models.schemas import NormalizedProduct, SearchIntent


class RelevanceService:
    # Query glue words do not describe what a marketplace listing is.
    STOP_WORDS = {
        "a", "an", "and", "best", "buy", "for", "in", "of", "on", "or", "the",
        "to", "under", "with", "within", "below", "budget", "price", "online",
    }
    REQUIREMENT_STOP_WORDS = {
        "best", "good", "quality", "high", "daily", "general", "use", "used", "related",
    }
    FOOD_TERMS = {
        "food", "grocery", "groceries", "edible", "beverage", "beverages", "snack", "snacks",
        "fruit", "fruits", "vegetable", "vegetables", "rice", "flour", "sugar", "milk", "juice",
    }
    SYNONYMS = {
        "fridge": {"fridge", "refrigerator"},
        "refrigerator": {"fridge", "refrigerator"},
        "mobile": {"mobile", "phone", "smartphone"},
        "mobiles": {"mobile", "mobiles", "phone", "phones", "smartphone", "smartphones"},
        "phone": {"phone", "smartphone"},
        "smartphone": {"phone", "smartphone"},
        "laptop": {"laptop", "laptops", "notebook", "notebooks", "macbook", "macbooks", "chromebook", "chromebooks", "ultrabook", "ultrabooks"},
        "laptops": {"laptop", "laptops", "notebook", "notebooks", "macbook", "macbooks", "chromebook", "chromebooks", "ultrabook", "ultrabooks"},
        "tv": {"tv", "television"},
        "television": {"tv", "television"},
        "ac": {"ac", "air", "conditioner"},
        "air": {"air", "ac"},
        "conditioner": {"conditioner", "ac"},
        "headphone": {"headphone", "headphones", "earphone", "earphones", "earbuds", "earbud", "tws", "airpods"},
        "headphones": {"headphone", "headphones", "earphone", "earphones", "earbuds", "earbud", "tws", "airpods"},
        "shoe": {"shoe", "shoes", "sneaker", "sneakers", "footwear"},
        "shoes": {"shoe", "shoes", "sneaker", "sneakers", "footwear"},
        "dress": {"dress", "dresses", "gown", "kurti", "kurtis", "kurta", "kurtas", "frock"},
        "dresses": {"dress", "dresses", "gown", "kurti", "kurtis", "kurta", "kurtas", "frock"},
        "kurti": {"kurti", "kurtis", "kurta", "kurtas", "dress", "tunic", "top"},
        "kurtis": {"kurti", "kurtis", "kurta", "kurtas", "dress", "tunic", "top"},
        "kurta": {"kurti", "kurtis", "kurta", "kurtas", "dress", "tunic", "top"},
        "kurtas": {"kurti", "kurtis", "kurta", "kurtas", "dress", "tunic", "top"},
        "jeans": {"jeans", "jean", "denim", "trousers", "pants"},
        "jean": {"jeans", "jean", "denim", "trousers", "pants"},
        "skincare": {"skincare", "skin", "care", "serum", "lotion", "cream", "cleanser", "facewash", "moisturizer", "sunscreen", "gel", "mask"},
        "camera": {"camera", "cameras", "dslr", "camcorder"},
        "cameras": {"camera", "cameras", "dslr", "camcorder"},
    }

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        tokens = {
            token for token in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(token) > 1 and token not in cls.STOP_WORDS
        }
        return {alias for token in tokens for alias in cls.SYNONYMS.get(token, {token})}

    @classmethod
    def _requirement_tokens(cls, requirement: str) -> set[str]:
        return {
            token for token in cls._tokens(requirement)
            if token not in cls.REQUIREMENT_STOP_WORDS and not token.isdigit()
        }

    @classmethod
    def _product_text(cls, product: NormalizedProduct) -> str:
        specs = " ".join(f"{key} {value}" for key, value in product.specifications.items())
        return " ".join(filter(None, [
            product.title, product.brand, product.description or "", specs,
            " ".join(product.features),
        ])).lower()

    @classmethod
    def _is_food(cls, product: NormalizedProduct) -> bool:
        product_tokens = cls._tokens(cls._product_text(product))
        category_tokens = cls._tokens(product.category)
        return bool(product_tokens & cls.FOOD_TERMS or category_tokens & cls.FOOD_TERMS)

    @staticmethod
    def _matches(token: str, product_tokens: set[str]) -> bool:
        # Supports plural forms and product-model prefixes without inventing a
        # synonym catalog or hardcoding brands/categories.
        stem = token.rstrip("s")
        return any(
            candidate == token or candidate.rstrip("s") == stem or
            (len(stem) >= 4 and (candidate.startswith(stem) or stem.startswith(candidate)))
            for candidate in product_tokens
        )

    @classmethod
    def filter_products(
        cls,
        products: Iterable[NormalizedProduct],
        query: str,
        intent: SearchIntent,
    ) -> list[NormalizedProduct]:
        candidates = list(products)
        if not candidates:
            return []

        query_tokens = cls._tokens(query)
        product_tokens = [cls._tokens(cls._product_text(product)) for product in candidates]
        document_frequency = Counter(
            token for tokens in product_tokens for token in query_tokens if cls._matches(token, tokens)
        )
        # A token that occurs in only a subset of live candidates is specific
        # evidence (brand/model/active/form factor) and prevents unrelated
        # category results from leaking through.
        specificity_limit = max(1, math.ceil(len(candidates) * 0.8))
        distinctive_tokens = {
            token for token, count in document_frequency.items()
            if 0 < count < specificity_limit
        }
        phrase = " ".join(query.lower().split())

        ranked: list[tuple[float, NormalizedProduct]] = []
        requirement_sets = [cls._requirement_tokens(requirement) for requirement in intent.extracted_requirements]
        for product, tokens in zip(candidates, product_tokens):
            if cls._is_food(product) and not (set(cls._tokens(query)) & cls.FOOD_TERMS):
                continue

            from app.services.intent_service import CATEGORY_DEFINITIONS
            known_brands = set()
            if intent.detected_category in CATEGORY_DEFINITIONS:
                cat_def = CATEGORY_DEFINITIONS[intent.detected_category]
                neg_keywords = cat_def.get("negative_keywords", [])
                title_lower = product.title.lower()
                if any(re.search(r'\b' + re.escape(neg) + r'\b', title_lower) for neg in neg_keywords):
                    continue
                known_brands = {b.lower() for b in cat_def.get("brands", [])}

            text = cls._product_text(product)
            matches = {token for token in query_tokens if cls._matches(token, tokens)}
            distinctive_matches = matches & distinctive_tokens
            category_match = intent.detected_category != "general" and product.category == intent.detected_category
            brand_in_cat = bool(product.brand and product.brand.lower() in known_brands)
            phrase_match = bool(phrase and phrase in text)

            # Purpose clauses are hard relevance constraints. Modifiers such
            # as "daily" are intentionally ignored, but meaningful terms
            # must appear in the actual listing fields.
            if requirement_sets and any(
                not requirement_set or not all(cls._matches(token, tokens) for token in requirement_set)
                for requirement_set in requirement_sets
            ):
                continue

            # Special case for generic phone/laptop searches:
            # Modern smartphones (Samsung Galaxy, OnePlus Nord, Motorola G, Realme, etc.)
            # and laptops do not necessarily include the generic word "phone" or "mobile" in their commercial titles.
            is_generic_category_query = (
                intent.detected_category in {"phone", "laptop"}
                and any(tok in {"mobile", "mobiles", "phone", "phones", "smartphone", "smartphones", "laptop", "laptops", "notebook"} for tok in query_tokens)
                and not any(cls._matches(b, query_tokens) for b in known_brands)
            )

            if is_generic_category_query:
                # Accept if product belongs to category, or brand is recognized in category, or matches tokens
                if not (category_match or brand_in_cat or matches):
                    continue
            elif distinctive_tokens:
                required_matches = 1 if len(distinctive_tokens) == 1 else min(2, len(distinctive_tokens))
                if len(distinctive_matches) < required_matches and not phrase_match:
                    continue
            elif not matches:
                continue

            score = len(matches) * 3.0
            score += len(distinctive_matches) * 4.0
            score += 5.0 if phrase_match else 0.0
            score += 3.0 if category_match else 0.0
            score += 2.0 if brand_in_cat else 0.0
            if product.brand and cls._matches(product.brand.lower(), query_tokens):
                score += 4.0
            ranked.append((score, product))

        return [product for _, product in sorted(ranked, key=lambda item: item[0], reverse=True)]

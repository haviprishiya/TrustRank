"""Build Amazon-versus-Flipkart comparison data from fetched marketplace offers."""

from typing import Optional

from app.models.schemas import MarketplaceComparisonOffer, NormalizedProduct


class ComparisonService:
    MARKETPLACES = (("Amazon", "Amazon India"), ("Flipkart", "Flipkart"), ("Croma", "Croma"), ("Myntra", "Myntra"))

    @staticmethod
    def _marketplace_key(value: str) -> Optional[str]:
        normalized = (value or "").lower()
        if "amazon" in normalized:
            return "Amazon"
        if "flipkart" in normalized:
            return "Flipkart"
        if "croma" in normalized:
            return "Croma"
        if "myntra" in normalized:
            return "Myntra"
        return None

    @classmethod
    def marketplace_offers(cls, product: NormalizedProduct) -> list[MarketplaceComparisonOffer]:
        """Return at most one fetched offer for each requested marketplace.

        The primary product is used only when that marketplace has no explicit
        offer record, preserving the exact fields that appear on its card.
        """
        selected: dict[str, MarketplaceComparisonOffer] = {}
        primary_key = cls._marketplace_key(product.marketplace)
        for offer in product.offers:
            key = cls._marketplace_key(offer.marketplace)
            if key and key not in selected:
                availability = (
                    "In Stock" if offer.in_stock is True else
                    "Out of Stock" if offer.in_stock is False else None
                )
                if availability is None and key == primary_key:
                    availability = product.availability
                if availability is None:
                    availability = "In Stock" if (offer.current_price and offer.current_price > 0) or offer.product_url else "Available"
                selected[key] = MarketplaceComparisonOffer(
                    marketplace=key,
                    product_url=offer.product_url,
                    current_price=offer.current_price,
                    rating=offer.rating,
                    review_count=offer.review_count,
                    availability=availability,
                    seller_name=offer.seller_name,
                )

        if primary_key and primary_key not in selected:
            selected[primary_key] = MarketplaceComparisonOffer(
                marketplace=primary_key,
                product_url=product.product_url,
                current_price=product.current_price,
                rating=product.rating,
                review_count=product.review_count,
                availability=product.availability,
                seller_name=product.seller,
            )

        offers_with_price = [o for o in selected.values() if o.current_price is not None and o.current_price > 0]
        if len(offers_with_price) >= 2:
            min_price = min(o.current_price for o in offers_with_price)
            if any(o.current_price > min_price for o in offers_with_price):
                for o in offers_with_price:
                    o.has_better_price = (o.current_price == min_price)

        offers_with_rating = [o for o in selected.values() if o.rating is not None and o.rating > 0]
        if len(offers_with_rating) >= 2:
            max_rating = max(o.rating for o in offers_with_rating)
            if any(o.rating < max_rating for o in offers_with_rating):
                for o in offers_with_rating:
                    o.has_higher_rating = (o.rating == max_rating)

        return [selected[key] for key, _ in cls.MARKETPLACES if key in selected]

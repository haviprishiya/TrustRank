import asyncio
import logging
from typing import List, Dict
from app.models.schemas import NormalizedProduct, ProviderStatusInfo
from app.providers.base import BaseProductProvider
from app.providers.amazon_provider import AmazonCreatorsAPIProvider
from app.providers.flipkart_provider import FlipkartAffiliateProvider
from app.providers.rapidapi_provider import RapidApiAmazonProvider, RapidApiFlipkartProvider
from app.providers.serpapi_provider import SerpApiShoppingProvider
from app.providers.open_data_provider import OpenBeautyFactsProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, BaseProductProvider] = {
            "amazon_creators_india": AmazonCreatorsAPIProvider(),
            "flipkart_affiliate": FlipkartAffiliateProvider(),
            "rapidapi_amazon_india": RapidApiAmazonProvider(),
            "rapidapi_flipkart": RapidApiFlipkartProvider(),
            "serpapi_shopping_india": SerpApiShoppingProvider(),
            "open_beauty_facts": OpenBeautyFactsProvider()
        }

    def get_provider(self, provider_id: str) -> BaseProductProvider:
        return self.providers.get(provider_id)

    def get_all_statuses(self) -> List[ProviderStatusInfo]:
        return [provider.get_status() for provider in self.providers.values()]

    async def search_all(self, query: str, category: str, limit: int = 15) -> List[NormalizedProduct]:
        """
        Executes parallel searches across all available configured providers.
        Aggregates live products and updates provider statuses.
        """
        selected = [
            provider for provider in self.providers.values()
            if provider.is_enabled() and provider.is_configured()
        ]
        logger.info("Provider selection query=%r category=%r selected=%s", query, category, [p.provider_id for p in selected])

        async def run_provider(provider: BaseProductProvider):
            logger.info("Provider request started provider=%s query=%r", provider.provider_id, query)
            try:
                result = await provider.search(query, category, limit=limit)
                logger.info("Provider request succeeded provider=%s products=%d", provider.provider_id, len(result))
                return result
            except Exception as error:
                logger.exception("Provider request failed provider=%s error_type=%s", provider.provider_id, type(error).__name__)
                provider.record_unexpected_error(error)
                return error

        tasks = [run_provider(provider) for provider in selected]
            
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_products: List[NormalizedProduct] = []
        for provider, result in zip(selected, results_nested):
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                # Providers normally translate errors into status-bearing empty results.
                # Preserve diagnostics if an unexpected exception escapes one adapter.
                provider.record_unexpected_error(result)
                
        return all_products

provider_registry = ProviderRegistry()

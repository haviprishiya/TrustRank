import asyncio
from typing import List, Dict
from app.models.schemas import NormalizedProduct, ProviderStatusInfo
from app.providers.base import BaseProductProvider
from app.providers.amazon_provider import AmazonPAAPIProvider
from app.providers.flipkart_provider import FlipkartAffiliateProvider
from app.providers.rapidapi_provider import RapidApiAmazonProvider, RapidApiFlipkartProvider
from app.providers.serpapi_provider import SerpApiShoppingProvider
from app.providers.open_data_provider import OpenBeautyFactsProvider
from app.providers.live_search_provider import LiveSearchMarketplaceProvider

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, BaseProductProvider] = {
            "amazon_paapi_india": AmazonPAAPIProvider(),
            "flipkart_affiliate": FlipkartAffiliateProvider(),
            "rapidapi_amazon_india": RapidApiAmazonProvider(),
            "rapidapi_flipkart": RapidApiFlipkartProvider(),
            "serpapi_shopping_india": SerpApiShoppingProvider(),
            "open_beauty_facts": OpenBeautyFactsProvider(),
            "live_search_india": LiveSearchMarketplaceProvider()
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
        tasks = []
        for p_id, provider in self.providers.items():
            tasks.append(provider.search(query, category, limit=limit))
            
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_products: List[NormalizedProduct] = []
        for result in results_nested:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                # Exception handled within provider, but safe guard here
                pass
                
        return all_products

provider_registry = ProviderRegistry()

import asyncio
from typing import List, Dict
from app.models.schemas import NormalizedProduct, ProviderStatusInfo
from app.providers.base import BaseProductProvider
from app.providers.amazon_provider import AmazonPAAPIProvider, AmazonCreatorsAPIProvider
from app.providers.flipkart_provider import FlipkartAffiliateProvider
from app.providers.brightdata_provider import BrightDataAmazonProvider, BrightDataFlipkartProvider
from app.providers.myntra_provider import MyntraProvider
from app.providers.croma_provider import CromaProvider
from app.providers.rapidapi_provider import RapidApiAmazonProvider, RapidApiFlipkartProvider
from app.providers.serpapi_provider import SerpApiShoppingProvider
from app.providers.open_data_provider import OpenBeautyFactsProvider
from app.providers.live_search_provider import LiveSearchMarketplaceProvider

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, BaseProductProvider] = {
            "amazon_creators_india": AmazonCreatorsAPIProvider(),
            "amazon_paapi_india": AmazonPAAPIProvider(),
            "flipkart_affiliate": FlipkartAffiliateProvider(),
            "brightdata_amazon_search": BrightDataAmazonProvider(),
            "brightdata_flipkart_products": BrightDataFlipkartProvider(),
            "myntra_fashion": MyntraProvider(),
            "croma_electronics": CromaProvider(),
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
        Executes parallel searches across authorized Amazon and Flipkart live providers.
        Aggregates live products and updates provider statuses.
        """
        async def _run_provider(p: BaseProductProvider):
            try:
                return await asyncio.wait_for(p.search(query, category, limit=limit), timeout=18.0)
            except asyncio.TimeoutError:
                p._last_status = "unavailable"
                p._last_message = f"{p.name} search timed out after 18 seconds."
                return []
            except Exception as e:
                p._last_status = "unavailable"
                p._last_message = str(e)
                return []

        tasks = []
        for p_id, provider in self.providers.items():
            # Search configured Amazon, Flipkart, and Myntra providers
            if provider.is_configured() and p_id not in ("croma_electronics", "open_beauty_facts"):
                tasks.append(_run_provider(provider))
            
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_products: List[NormalizedProduct] = []
        for result in results_nested:
            if isinstance(result, list):
                all_products.extend(result)
                
        return all_products

provider_registry = ProviderRegistry()

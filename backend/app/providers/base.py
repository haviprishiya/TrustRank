from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import NormalizedProduct, ProviderStatusInfo

class BaseProductProvider(ABC):
    def __init__(self, provider_id: str, name: str, marketplace: str):
        self.provider_id = provider_id
        self.name = name
        self.marketplace = marketplace
        self._last_latency_ms: Optional[float] = None
        self._last_items_count: int = 0
        self._last_status: str = "initialized"
        self._last_message: str = "Initialized"

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the required API keys / credentials are set."""
        pass

    @abstractmethod
    def get_required_env_keys(self) -> List[str]:
        """Returns the list of environment variable names needed for this provider."""
        pass

    def record_unexpected_error(self, error: Exception) -> None:
        self._last_status = "unavailable"
        self._last_items_count = 0
        self._last_message = f"Provider request failed unexpectedly: {type(error).__name__}"

    @abstractmethod
    async def search(self, query: str, category: str, limit: int = 10) -> List[NormalizedProduct]:
        """Performs a live runtime search for products."""
        pass

    def get_status(self) -> ProviderStatusInfo:
        configured = self.is_configured()
        enabled = self.is_enabled()
        status = self._last_status if configured else "credentials_required"
        if not enabled:
            status = "disabled"
            message = "Provider disabled by configuration."
        else:
            message = self._last_message if configured else f"Authorized provider credentials required: {', '.join(self.get_required_env_keys())}"

        if not enabled:
            diagnostic_code = "provider_disabled"
        elif not configured:
            diagnostic_code = "configuration_missing"
        elif status in {"error", "unavailable"}:
            diagnostic_code = "provider_unavailable"
        elif status == "active" and self._last_items_count == 0:
            diagnostic_code = "no_products_found"
        elif status == "empty":
            diagnostic_code = "no_products_found"
        elif status == "idle":
            diagnostic_code = "skipped_for_category"
        elif status == "initialized":
            diagnostic_code = "not_run"
        else:
            diagnostic_code = "success"
        
        return ProviderStatusInfo(
            provider_id=self.provider_id,
            name=self.name,
            marketplace=self.marketplace,
            status=status,
            message=message,
            configured=configured,
            env_keys_required=self.get_required_env_keys(),
            latency_ms=self._last_latency_ms,
            items_fetched=self._last_items_count,
            enabled=enabled,
            diagnostic_code=diagnostic_code
        )

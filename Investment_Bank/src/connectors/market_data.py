import httpx
from src.config import settings


class MarketDataConnector:
    def __init__(self, base_url=None, timeout=3.0):
        self.base_url = base_url or settings.mock_base_url
        self.timeout = timeout

    def market_data(self):
        response = httpx.get(f"{self.base_url}/market-data", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fx_rate(self, currency_code):
        response = httpx.get(f"{self.base_url}/fx/{currency_code}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def index_rate(self, index_code):
        response = httpx.get(f"{self.base_url}/indices/{index_code}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

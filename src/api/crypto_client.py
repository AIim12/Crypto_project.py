from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class BaseCryptoClient(ABC):
    """
    Abstract base class for any crypto price provider.
    """

    @abstractmethod
    def get_price(self, coin_id: str, vs_currency: str = "usd") -> float:
        """
        Return the current price of `coin_id` in `vs_currency`.
        `coin_id` should match the provider's internal ID (e.g. 'bitcoin').
        """
        raise NotImplementedError

    @abstractmethod
    def get_supported_coins(self) -> Dict[str, str]:
        """
        Return a mapping from lowercased symbol to coin_id.
        Example: {'btc': 'bitcoin', 'eth': 'ethereum'}
        """
        raise NotImplementedError

    @abstractmethod
    def get_supported_coins_with_details(self) -> list[dict]:
        """
        Return a list of dictionaries, each containing 'id', 'symbol', and 'name'.
        """
        raise NotImplementedError


class CoinGeckoClient(BaseCryptoClient):
    """
    Concrete implementation for CoinGecko with a resilient session.
    - Uses a requests.Session for connection pooling.
    - Implements retry logic with exponential backoff for robustness.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, timeout: int = 10):
        self.session = self._create_resilient_session()
        self.timeout = timeout

    @staticmethod
    def _create_resilient_session() -> requests.Session:
        """Creates a session with retry logic."""
        session = requests.Session()
        # Retry on 5XX errors and 429 (rate limit)
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1  # e.g., sleep for 1s, 2s, 4s
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> float:
        """
        Fetch current price for a single coin from CoinGecko.
        Raises RuntimeError if the request fails after all retries.
        """
        endpoint = f"{self.BASE_URL}/simple/price"
        params = {"ids": coin_id, "vs_currencies": vs_currency}

        try:
            response = self.session.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()  # Will raise HTTPError for non-2xx responses
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to call CoinGecko API after retries: {exc}") from exc

        data: Dict[str, Any] = response.json()

        if not data or coin_id not in data or vs_currency not in data[coin_id]:
            raise RuntimeError(
                f"Price not found in CoinGecko response for coin_id='{coin_id}', "
                f"vs_currency='{vs_currency}'. Raw response: {data}"
            )

        price_value = data[coin_id][vs_currency]

        try:
            return float(price_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Unexpected price format from CoinGecko: {price_value!r}") from exc

    def get_supported_coins_with_details(self) -> list[dict]:
        """
        Fetches the full list of coins from CoinGecko.
        Returns a list of dicts, each with id, symbol, and name.
        """
        endpoint = f"{self.BASE_URL}/coins/list"
        try:
            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to fetch supported coins after retries: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("Failed to parse JSON from CoinGecko coin list.") from exc

    def get_supported_coins(self) -> Dict[str, str]:
        """
        Fetches and caches a list of supported coins (symbol -> id mapping).
        This method reuses get_supported_coins_with_details to avoid a second API call.
        """
        coins = self.get_supported_coins_with_details()
        symbol_to_id: Dict[str, str] = {}

        for coin in coins:
            coin_id = coin.get("id")
            symbol = coin.get("symbol")
            if not coin_id or not symbol:
                continue
            
            symbol_to_id[symbol.lower()] = coin_id

        return symbol_to_id

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any

import requests


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
        Optionally return a mapping from symbol to coin_id.
        Example: {'btc': 'bitcoin', 'eth': 'ethereum'}
        """
        raise NotImplementedError


class CoinGeckoClient(BaseCryptoClient):
    """
    Concrete implementation of BaseCryptoClient using CoinGecko's public API.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> float:
        """
        Fetch current price for a single coin from CoinGecko.
        Raises RuntimeError if the response is invalid or the coin is not found.
        """
        endpoint = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Error while calling CoinGecko API: {exc}") from exc

        data: Dict[str, Any] = response.json()

        if coin_id not in data or vs_currency not in data[coin_id]:
            raise RuntimeError(
                f"Price not found in CoinGecko response for coin_id='{coin_id}', "
                f"vs_currency='{vs_currency}'. Raw response: {data}"
            )

        price_value = data[coin_id][vs_currency]

        # CoinGecko returns numeric value; we enforce float.
        try:
            return float(price_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Unexpected price format from CoinGecko: {price_value!r}"
            ) from exc

    def get_supported_coins(self) -> Dict[str, str]:
        """
        Fetch a list of supported coins and return symbol -> id mapping.
        This is helpful for letting the user select which coins to track.
        """
        endpoint = f"{self.BASE_URL}/coins/list"

        try:
            response = requests.get(endpoint, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Error while fetching supported coins: {exc}") from exc

        coins = response.json()
        symbol_to_id: Dict[str, str] = {}

        for coin in coins:
            # coin example: {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}
            coin_id = coin.get("id")
            symbol = coin.get("symbol")
            if not coin_id or not symbol:
                continue
            # Use lowercase to normalize
            symbol_to_id[symbol.lower()] = coin_id

        return symbol_to_id


from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

from mongoengine import DoesNotExist, QuerySet, ValidationError

from src.api.crypto_client import BaseCryptoClient
from src.database.mongo import MongoDBConnection, get_default_connection
from src.models.coin import (
    CoinPrice,
    CoinPriceDocument,
    TrackedCoin,
    TrackedCoinDocument,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =========================
# Analytics Data Structures
# =========================

@dataclass
class MarketAnalytics:
    """Holds aggregated analytics for a coin over a window of time."""
    coin_id: str
    record_count: int
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    average_price: float
    net_change_percent: float

@dataclass
class TrendAnalysis:
    """Holds trend and volatility analysis for a coin."""
    coin_id: str
    record_count: int
    trend: str
    volatility: str
    momentum_score: float
    net_change_percent: float


MAJOR_COINS = {
    "bitcoin": {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    "btc": {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    "ethereum": {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    "eth": {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    "solana": {"id": "solana", "symbol": "sol", "name": "Solana"},
    "sol": {"id": "solana", "symbol": "sol", "name": "Solana"},
    "ripple": {"id": "ripple", "symbol": "xrp", "name": "Ripple"},
    "xrp": {"id": "ripple", "symbol": "xrp", "name": "Ripple"},
    "cardano": {"id": "cardano", "symbol": "ada", "name": "Cardano"},
    "ada": {"id": "cardano", "symbol": "ada", "name": "Cardano"},
    "dogecoin": {"id": "dogecoin", "symbol": "doge", "name": "Dogecoin"},
    "doge": {"id": "dogecoin", "symbol": "doge", "name": "Dogecoin"},
    "binancecoin": {"id": "binancecoin", "symbol": "bnb", "name": "Binance Coin"},
    "bnb": {"id": "binancecoin", "symbol": "bnb", "name": "Binance Coin"},
}


class CryptoTracker:
    """High-level service for tracking and analyzing crypto prices."""

    def __init__(
        self,
        client: BaseCryptoClient,
        connection: Optional[MongoDBConnection] = None,
    ) -> None:
        self.client = client
        self.connection = connection or get_default_connection()
        self.connection.connect()

    # =========================
    # Tracked Coins CRUD
    # =========================

    def add_tracked_coin(self, *, coin_id: str, symbol: str, name: str) -> TrackedCoin:
        """Creates a new tracked coin entry."""
        if TrackedCoinDocument.objects(coin_id=coin_id).first():
            raise ValueError(f"Coin with id='{coin_id}' is already tracked.")
        try:
            doc = TrackedCoinDocument(coin_id=coin_id, symbol=symbol.lower(), name=name)
            doc.save()
            logging.info(f"Added new tracked coin: {name} ({symbol})")
            return doc.to_dataclass()
        except ValidationError as exc:
            raise ValueError(f"Invalid data for new coin: {exc}") from exc

    def list_tracked_coins(self) -> List[TrackedCoin]:
        """Returns all tracked coins."""
        return [doc.to_dataclass() for doc in TrackedCoinDocument.objects.order_by("name")]

    def delete_tracked_coin(self, coin_id: str, delete_prices: bool = False) -> None:
        """Deletes a tracked coin and optionally its price history."""
        deleted_count = TrackedCoinDocument.objects(coin_id=coin_id).delete()
        if deleted_count == 0:
            raise ValueError(f"Tracked coin with id='{coin_id}' not found.")
        logging.info(f"Deleted tracked coin '{coin_id}'.")

        if delete_prices:
            deleted_prices = CoinPriceDocument.objects(coin_id=coin_id).delete()
            logging.info(f"Deleted {deleted_prices} price records for '{coin_id}'.")

    # =========================
    # Price Snapshot Logic
    # =========================

    def record_price_for_coin(self, coin_id: str) -> CoinPrice:
        """Fetches and stores a single price snapshot."""
        price = self.client.get_price(coin_id)
        timestamp = datetime.now(timezone.utc)
        doc = CoinPriceDocument(coin_id=coin_id, price=price, timestamp=timestamp).save()
        logging.info(f"Recorded price for '{coin_id}': ${price:,.4f}")
        return doc.to_dataclass()

    def record_prices_for_all_tracked(self) -> list[CoinPrice]:
        """Fetches and stores prices for all tracked coins."""
        prices: list[CoinPrice] = []
        tracked_coins = self.list_tracked_coins()
        
        if not tracked_coins:
            logging.warning("No tracked coins to record prices for.")
            return prices

        logging.info(f"Starting price recording for {len(tracked_coins)} coins.")
        for tracked in tracked_coins:
            try:
                price = self.record_price_for_coin(tracked.coin_id)
                prices.append(price)
            except Exception as exc:
                logging.error(f"Failed to record price for {tracked.name} ({tracked.coin_id}): {exc}")

        logging.info(f"Successfully recorded prices for {len(prices)} of {len(tracked_coins)} coins.")
        return prices

    def get_price_history(self, coin_id: str, limit: int) -> List[CoinPrice]:
        """Gets the last N price records for a coin."""
        return [
            doc.to_dataclass()
            for doc in CoinPriceDocument.objects(coin_id=coin_id).order_by("-timestamp").limit(limit)
        ]

    # =========================
    # New Analytics Methods
    # =========================

    def get_market_analytics(self, coin_id: str, limit: int) -> MarketAnalytics:
        """Calculates market analytics over the last N records."""
        history = self.get_price_history(coin_id, limit)
        actual_count = len(history)

        if actual_count < 2:
            raise ValueError(f"Not enough data for market analysis. Need at least 2 records, but found {actual_count}.")

        prices = [item.price for item in history]
        # History is newest first, so reverse for open/close
        open_price = prices[-1]
        close_price = prices[0]
        
        net_change = ((close_price - open_price) / open_price) * 100.0 if open_price != 0 else 0.0

        return MarketAnalytics(
            coin_id=coin_id,
            record_count=actual_count,
            open_price=open_price,
            close_price=close_price,
            high_price=max(prices),
            low_price=min(prices),
            average_price=statistics.mean(prices),
            net_change_percent=net_change,
        )

    def get_trend_analysis(self, coin_id: str, limit: int) -> TrendAnalysis:
        """Performs trend, volatility, and momentum analysis."""
        history = self.get_price_history(coin_id, limit)
        actual_count = len(history)

        if actual_count < 4:
            raise ValueError(f"Not enough data for trend analysis. Need at least 4 records, but found {actual_count}.")

        prices = [item.price for item in history]
        # 1. Volatility
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices) if actual_count > 1 else 0
        coeff_var = (std_dev / mean_price) if mean_price != 0 else 0
        
        if coeff_var < 0.01:
            volatility = "Low"
        elif coeff_var < 0.05:
            volatility = "Medium"
        else:
            volatility = "High"

        # 2. Trend (simple slope calculation on time series)
        n = actual_count
        sum_x = sum(range(n))
        sum_y = sum(prices)
        sum_xy = sum(i * prices[i] for i in range(n))
        sum_x2 = sum(i**2 for i in range(n))
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        except ZeroDivisionError:
            slope = 0

        # Normalize slope to get trend strength
        norm_slope = (slope / mean_price) * 100 if mean_price != 0 else 0
        if norm_slope > 0.5:
            trend = "Strong Uptrend"
        elif norm_slope > 0.1:
            trend = "Uptrend"
        elif norm_slope < -0.5:
            trend = "Strong Downtrend"
        elif norm_slope < -0.1:
            trend = "Downtrend"
        else:
            trend = "Sideways"

        # 3. Momentum Score & Net Change
        open_price = prices[-1]
        close_price = prices[0]
        net_change = ((close_price - open_price) / open_price) * 100.0 if open_price != 0 else 0.0
        
        momentum = (abs(net_change) * 0.5) + (abs(norm_slope) * 20)
        momentum_score = min(max(momentum, 0), 10)

        return TrendAnalysis(
            coin_id=coin_id,
            record_count=n,
            trend=trend,
            volatility=volatility,
            momentum_score=momentum_score,
            net_change_percent=net_change
        )
    # =========================
    # Interactive Search
    # =========================

    def search_coins(self, query: str, limit: int = 10) -> list[dict]:
        """
        Searches for coins, prioritizing a local list of major coins before
        querying the CoinGecko API.
        """
        query = query.lower()
        
        # 1. Prioritize search in the hardcoded major coins list
        if query in MAJOR_COINS:
            logging.info(f"Found '{query}' in the priority list.")
            return [MAJOR_COINS[query]]

        # 2. Fallback to API search if not in the priority list
        logging.info(f"'{query}' not in priority list, searching via API...")
        all_coins = self.client.get_supported_coins_with_details()
        results: list[dict] = []

        for coin in all_coins:
            symbol = coin.get("symbol", "").lower()
            coin_id = coin.get("id", "").lower()
            name = coin.get("name", "").lower()

            # --- Quality and relevance filters ---
            if not all([symbol, coin_id, name]): continue
            if "." in symbol or len(symbol) > 10: continue
            if any(kw in name for kw in ["-peg", "wrapped", "token", "staked"]): continue

            # Match query against id, symbol, or name
            if query == symbol or query == coin_id or query == name:
                results.append(coin)
                if len(results) >= limit: break
        
        return results

    def add_tracked_coin_interactive(self, query: str) -> TrackedCoin:
        """Guides the user through searching for and adding a coin."""
        matches = self.search_coins(query)
        if not matches:
            raise ValueError(f"No quality coins found for query '{query}'. Try a different symbol or name.")

        print("\n--- Found Coins ---")
        for i, coin in enumerate(matches, start=1):
            print(f"{i}) {coin['name']} ({coin['symbol'].upper()})")

        # If only one match is found from the priority list, add it directly
        if len(matches) == 1 and matches[0] in MAJOR_COINS.values():
            selected_coin = matches[0]
            print(f"\nAuto-selecting best match: {selected_coin['name']}.")
        else:
            # Otherwise, prompt the user to choose
            while True:
                try:
                    choice_str = input(f"Select number to track (1-{len(matches)}, or 0 to cancel): ").strip()
                    choice = int(choice_str)
                    if 0 <= choice <= len(matches): break
                    logging.error("❌ Invalid number. Please choose from the list.")
                except ValueError:
                    logging.error("❌ Invalid input. Please enter a number.")
            
            if choice == 0:
                raise ValueError("Operation cancelled by user.")
            
            selected_coin = matches[choice - 1]

        return self.add_tracked_coin(
            coin_id=selected_coin["id"],
            symbol=selected_coin["symbol"],
            name=selected_coin["name"],
        )
    
    def close(self) -> None:
        """Cleanly close the MongoDB connection."""
        self.connection.disconnect()

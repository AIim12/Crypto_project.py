from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import List, Optional

from mongoengine import DoesNotExist, QuerySet

from src.api.crypto_client import BaseCryptoClient
from src.database.mongo import MongoDBConnection, get_default_connection
from src.models.coin import (
    CoinPrice,
    CoinPriceDocument,
    TrackedCoin,
    TrackedCoinDocument,
)


class CryptoTracker:
    """
    High-level service that coordinates:
    - Which coins are tracked (CRUD on TrackedCoin)
    - Storing price snapshots (CRUD on CoinPrice)
    - Business logic: price change, reports, etc.
    """

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

    def add_tracked_coin(
        self,
        *,
        coin_id: str,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> TrackedCoin:
        """
        Create a tracked coin entry using a SAFE coin_id (recommended).
        Example: coin_id="bitcoin"
        """

        # Check if already exists
        existing = TrackedCoinDocument.objects(coin_id=coin_id).first()
        if existing:
            return existing.to_dataclass()

        coin_name = name or coin_id
        coin_symbol = symbol or coin_id

        doc = TrackedCoinDocument(
            coin_id=coin_id,
            symbol=coin_symbol.lower(),
            name=coin_name,
            is_active=True,
        )
        doc.save()

        return doc.to_dataclass()

    def list_tracked_coins(self, active_only: bool = False) -> List[TrackedCoin]:
        """
        Return all tracked coins.
        """
        query: QuerySet[TrackedCoinDocument] = TrackedCoinDocument.objects()
        if active_only:
            query = query.filter(is_active=True)

        return [doc.to_dataclass() for doc in query]

    def update_tracked_coin_status(self, coin_id: str, is_active: bool) -> TrackedCoin:
        """
        Activate or deactivate a tracked coin.
        """
        try:
            doc = TrackedCoinDocument.objects.get(coin_id=coin_id)
        except DoesNotExist as exc:
            raise ValueError(f"Tracked coin with id='{coin_id}' not found.") from exc

        doc.is_active = is_active
        doc.save()
        return doc.to_dataclass()

    def delete_tracked_coin(self, coin_id: str, delete_prices: bool = False) -> None:
        """
        Delete a tracked coin.
        Optionally also delete its historical prices.
        """
        TrackedCoinDocument.objects(coin_id=coin_id).delete()

        if delete_prices:
            CoinPriceDocument.objects(coin_id=coin_id).delete()

    # =========================
    # Price Snapshot Logic
    # =========================

    def record_price_for_coin(self, coin_id: str) -> CoinPrice:
        """
        Fetch live price from API and store it in MongoDB.
        """
        price = self.client.get_price(coin_id)
        timestamp = datetime.now(timezone.utc)

        doc = CoinPriceDocument(
            coin_id=coin_id,
            price=price,
            timestamp=timestamp,
        )
        doc.save()

        return doc.to_dataclass()

    def record_prices_for_all_active(self) -> List[CoinPrice]:
        """
        Fetch and store prices for all active tracked coins.
        """
        prices: List[CoinPrice] = []

        for tracked in self.list_tracked_coins(active_only=True):
            price = self.record_price_for_coin(tracked.coin_id)
            prices.append(price)

        return prices

    def get_price_history(
        self,
        coin_id: str,
        limit: int = 20,
    ) -> List[CoinPrice]:
        """
        Get last N price records for a coin.
        """
        query: QuerySet[CoinPriceDocument] = (
            CoinPriceDocument.objects(coin_id=coin_id)
            .order_by("-timestamp")
            .limit(limit)
        )

        return [doc.to_dataclass() for doc in query]

    def get_latest_price(self, coin_id: str) -> Optional[CoinPrice]:
        """
        Get most recent price record for a coin.
        """
        doc = (
            CoinPriceDocument.objects(coin_id=coin_id)
            .order_by("-timestamp")
            .first()
        )

        return doc.to_dataclass() if doc else None

    def get_percentage_change(
        self,
        coin_id: str,
        lookback: int = 2,
    ) -> Optional[float]:
        """
        Compute percentage change over the last `lookback` records.
        """
        history = self.get_price_history(coin_id=coin_id, limit=lookback)

        if len(history) < 2:
            return None

        latest = history[0]
        oldest = history[-1]

        if oldest.price == 0:
            return None

        change = ((latest.price - oldest.price) / oldest.price) * 100.0
        return change

    # =========================
    # Utility / Debug
    # =========================

    def to_debug_dict(self, coin_price: CoinPrice) -> dict:
        """
        Convert CoinPrice dataclass to a JSON-friendly dict.
        """
        return asdict(coin_price)

    def close(self) -> None:
        """
        Cleanly close the MongoDB connection.
        """
        self.connection.disconnect()

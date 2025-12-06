from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    FloatField,
    StringField,
)


# ------------------------
# Pure Python dataclasses
# ------------------------


@dataclass(frozen=True)
class TrackedCoin:
    """
    Represents a coin that the user wants to track.
    """
    coin_id: str           # e.g. "bitcoin"
    symbol: str            # e.g. "btc"
    name: str              # e.g. "Bitcoin"
    is_active: bool = True


@dataclass(frozen=True)
class CoinPrice:
    """
    Pure Python dataclass used by business logic to represent
    a single price snapshot for a coin.
    """
    coin_id: str
    price: float
    timestamp: datetime


# ------------------------
# MongoEngine ORM documents
# ------------------------


class TrackedCoinDocument(Document):
    """
    Tracks which coins are being monitored by the system.
    """
    meta = {
        "collection": "tracked_coins",
        "indexes": ["coin_id", "symbol"],
    }

    coin_id = StringField(required=True, unique=True)
    symbol = StringField(required=True)
    name = StringField(required=True)
    is_active = BooleanField(default=True)

    def to_dataclass(self) -> TrackedCoin:
        return TrackedCoin(
            coin_id=self.coin_id,
            symbol=self.symbol,
            name=self.name,
            is_active=self.is_active,
        )


class CoinPriceDocument(Document):
    """
    Stores historical price snapshots for coins.
    """
    meta = {
        "collection": "coin_prices",
        "indexes": ["coin_id", "timestamp"],
    }

    coin_id = StringField(required=True)
    price = FloatField(required=True)
    timestamp = DateTimeField(required=True)

    def to_dataclass(self) -> CoinPrice:
        return CoinPrice(
            coin_id=self.coin_id,
            price=self.price,
            timestamp=self.timestamp,
        )

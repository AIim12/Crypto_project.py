from __future__ import annotations

import os
from typing import Optional

from mongoengine import connect, disconnect


class MongoDBConnection:
    """
    Handles MongoDB connection lifecycle.
    Uses environment variables when available.
    """

    def __init__(
        self,
        db_name: str,
        host: str = "localhost",
        port: int = 27017,
    ) -> None:
        self.db_name = db_name
        self.host = host
        self.port = port
        self._connected: bool = False

    def connect(self) -> None:
        if self._connected:
            return

        connect(
            db=self.db_name,
            host=self.host,
            port=self.port,
        )
        self._connected = True

    def disconnect(self) -> None:
        if self._connected:
            disconnect()
            self._connected = False


def get_default_connection() -> MongoDBConnection:
    """
    Returns a default MongoDB connection using environment variables if provided.
    """

    db_name = os.getenv("MONGO_DB_NAME", "crypto_monitor")
    host = os.getenv("MONGO_HOST", "localhost")
    port_str: Optional[str] = os.getenv("MONGO_PORT")

    port = int(port_str) if port_str else 27017

    return MongoDBConnection(db_name=db_name, host=host, port=port)

from __future__ import annotations

import os
from typing import Optional

from mongoengine import connect, disconnect


class MongoDBConnection:
    """
    Handles the MongoDB connection lifecycle using a URI for flexibility.
    """

    def __init__(self, uri: str, db_name: str) -> None:
        self.uri = uri
        self.db_name = db_name
        self._connected: bool = False

    def connect(self) -> None:
        """Establishes the database connection if not already connected."""
        if self._connected:
            return
        # mongoengine's connect function can take a host URI
        connect(db=self.db_name, host=self.uri)
        self._connected = True
        print("🔌 Database connection established.")

    def disconnect(self) -> None:
        """Closes the database connection if it is open."""
        if self._connected:
            disconnect()
            self._connected = False
            print("🔌 Database connection closed.")


def get_default_connection() -> MongoDBConnection:
    """
    Initializes a MongoDB connection using environment variables.
    
    Prioritizes MONGO_URI for full connection string, but falls back to
    individual MONGO_HOST, MONGO_PORT, and MONGO_DB_NAME for local dev.
    """
    db_name = os.getenv("MONGO_DB_NAME", "crypto_monitor")
    
    # Prioritize full URI for production-like environments (e.g., MongoDB Atlas)
    if mongo_uri := os.getenv("MONGO_URI"):
        return MongoDBConnection(uri=mongo_uri, db_name=db_name)

    # Fallback for local development
    host = os.getenv("MONGO_HOST", "localhost")
    port_str: Optional[str] = os.getenv("MONGO_PORT")
    port = int(port_str) if port_str and port_str.isdigit() else 27017
    
    local_uri = f"mongodb://{host}:{port}/"
    
    return MongoDBConnection(uri=local_uri, db_name=db_name)

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from src.services.tracker import CryptoTracker
from src.models.coin import TrackedCoin


# Mock data from CoinGecko API
MOCK_COINS_LIST = [
    {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'},
    {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'},
    {'id': 'ripple', 'symbol': 'xrp', 'name': 'XRP'},
    {'id': 'spam-coin-peg', 'symbol': 'spam.x', 'name': 'SpamCoin'},
]

@pytest.fixture
def mock_crypto_client():
    """Fixture for a mocked BaseCryptoClient."""
    client = MagicMock()
    client.get_supported_coins_with_details.return_value = MOCK_COINS_LIST
    return client

@pytest.fixture
def mock_db_connection():
    """Fixture to mock the database connection."""
    conn = MagicMock()
    return conn

@pytest.fixture
def tracker_service(mock_crypto_client, mock_db_connection):
    """Fixture for a CryptoTracker service instance with a mocked client and DB."""
    # We disable the real DB connection for unit tests
    with patch('src.services.tracker.get_default_connection', return_value=mock_db_connection):
        service = CryptoTracker(client=mock_crypto_client)
        # Prevent the real connect() from being called in tests
        service.connection.connect = MagicMock()
        return service


def test_search_filters_spam_tokens(tracker_service: CryptoTracker):
    """
    Verify that the search function filters out tokens with weird symbols.
    """
    # Act
    results = tracker_service.search_coins(query="spam")

    # Assert
    assert len(results) == 0

def test_search_finds_valid_tokens(tracker_service: CryptoTracker):
    """
    Verify that search correctly finds coins by name, symbol, or id.
    """
    # Act & Assert
    assert len(tracker_service.search_coins(query="btc")) == 1
    assert tracker_service.search_coins(query="btc")[0]['id'] == 'bitcoin'
    
    assert len(tracker_service.search_coins(query="ethereum")) == 1
    assert tracker_service.search_coins(query="ethereum")[0]['id'] == 'ethereum'

    assert len(tracker_service.search_coins(query="xrp")) >= 1
    assert tracker_service.search_coins(query="xrp")[0]['id'] == 'ripple'


@patch('builtins.input', side_effect=['1', '']) # User chooses '1'
@patch('src.services.tracker.TrackedCoinDocument')
def test_add_coin_interactive_success(mock_doc, mock_input, tracker_service: CryptoTracker):
    """
    Test the interactive add coin workflow succeeds with valid input.
    """
    # Arrange
    # Make the save method return a mock object that can be converted to a dataclass
    mock_instance = MagicMock()
    mock_instance.to_dataclass.return_value = TrackedCoin(
        coin_id='bitcoin', symbol='btc', name='Bitcoin', is_active=True
    )
    mock_doc.objects.return_value.first.return_value = None # No existing coin
    mock_doc.return_value.save.return_value = mock_instance

    # Act
    result = tracker_service.add_tracked_coin_interactive(query="bitcoin")

    # Assert
    assert result is not None
    assert result.coin_id == 'bitcoin'
    mock_input.assert_called_with("Select number to track (or 0 to cancel): ")


@patch('builtins.input', side_effect=['99', '0']) # User enters out-of-range, then cancels
def test_add_coin_interactive_out_of_range_and_cancel(mock_input, tracker_service: CryptoTracker):
    """
    Test that the interactive add function handles out-of-range and cancel inputs.
    """
    # Act & Assert
    with pytest.raises(ValueError, match="Operation cancelled by user"):
        tracker_service.add_tracked_coin_interactive(query="btc")
    
    # Ensures the loop for input validation ran before cancellation
    assert mock_input.call_count > 1


def test_record_prices_fail_safe(tracker_service: CryptoTracker):
    """
    Test that the price recording loop continues even if one coin fails.
    """
    # Arrange
    # Simulate two active coins
    active_coins = [
        TrackedCoin(coin_id='bitcoin', symbol='btc', name='Bitcoin'),
        TrackedCoin(coin_id='ethereum', symbol='eth', name='Ethereum'),
    ]
    tracker_service.list_tracked_coins = MagicMock(return_value=active_coins)
    
    # Make the API call succeed for bitcoin but fail for ethereum
    tracker_service.client.get_price.side_effect = [
        65000.0, # Success for bitcoin
        RuntimeError("API failed for ethereum") # Failure for ethereum
    ]
    
    # Mock the DB save call
    with patch('src.services.tracker.CoinPriceDocument') as mock_price_doc:
        # Act
        results = tracker_service.record_prices_for_all_active()

        # Assert
        # 1. Check that only one price was successfully recorded
        assert len(results) == 1
        assert results[0].coin_id == 'bitcoin'
        assert results[0].price == 65000.0
        
        # 2. Check that the DB save method was called only once
        mock_price_doc.assert_called_once()
        
        # 3. Check that get_price was called for both coins
        assert tracker_service.client.get_price.call_count == 2

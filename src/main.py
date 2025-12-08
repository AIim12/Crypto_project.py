from __future__ import annotations

import logging

from mongoengine.errors import DoesNotExist

from src.api.crypto_client import CoinGeckoClient
from src.services.tracker import CryptoTracker, MarketAnalytics, TrendAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

# ===================================
# CLI Menu Action Handlers
# ===================================

def handle_add_coin(tracker: CryptoTracker):
    """Guides the user to add a new tracked coin."""
    query = input("Search by symbol or name (e.g., btc, ethereum): ").strip()
    if not query:
        raise ValueError("Search query cannot be empty.")
    
    coin = tracker.add_tracked_coin_interactive(query=query)
    logging.info(f"✅ Successfully added and now tracking: {coin.name} ({coin.symbol})")

def handle_list_coins(tracker: CryptoTracker):
    """Displays all currently tracked coins."""
    coins = tracker.list_tracked_coins()
    if not coins:
        logging.info("No coins are currently being tracked.")
        return
    
    print("\n--- Tracked Coins ---")
    for coin in coins:
        print(f"• {coin.name} ({coin.symbol.upper()})")

def handle_record_prices(tracker: CryptoTracker):
    """Initiates price recording for all tracked coins."""
    tracker.record_prices_for_all_tracked()

def handle_market_analytics(tracker: CryptoTracker):
    """Handles the market analytics feature."""
    coin_id = input("Enter coin_id for analysis (e.g., bitcoin): ").strip().lower()
    if not coin_id:
        raise ValueError("Coin ID cannot be empty.")

    while True:
        limit_str = input("Analyze last how many records? (default 10): ").strip() or "10"
        if limit_str.isdigit() and int(limit_str) > 1:
            limit = int(limit_str)
            break
        logging.error("❌ Invalid number. Please enter an integer greater than 1.")

    analytics = tracker.get_market_analytics(coin_id, limit)
    
    if analytics.record_count < limit:
        logging.warning(f"⚠️ Only {analytics.record_count} records were available. Analytics computed on this subset.")

    print(f"\n--- Market Analytics for {analytics.coin_id.capitalize()} (Last {analytics.record_count} Records) ---")
    print(f"  Open Price:          ${analytics.open_price:,.4f}")
    print(f"  Close Price:         ${analytics.close_price:,.4f}")
    print(f"  High Price:          ${analytics.high_price:,.4f}")
    print(f"  Low Price:           ${analytics.low_price:,.4f}")
    print(f"  Average Price:       ${analytics.average_price:,.4f}")
    print(f"  Net Change:          {analytics.net_change_percent:+.2f}%")

def handle_trend_analysis(tracker: CryptoTracker):
    """Handles the trend and volatility analysis feature."""
    coin_id = input("Enter coin_id for analysis (e.g., bitcoin): ").strip().lower()
    if not coin_id:
        raise ValueError("Coin ID cannot be empty.")

    while True:
        limit_str = input("Analyze last how many records? (default 10): ").strip() or "10"
        if limit_str.isdigit() and int(limit_str) > 3:
            limit = int(limit_str)
            break
        logging.error("❌ Invalid number. Please enter an integer greater than 3.")
    
    analysis = tracker.get_trend_analysis(coin_id, limit)

    if analysis.record_count < limit:
        logging.warning(f"⚠️ Only {analysis.record_count} records were available. Analytics computed on this subset.")

    print(f"\n--- Trend & Volatility for {analysis.coin_id.capitalize()} (Last {analysis.record_count} Records) ---")
    print(f"  Trend:               {analysis.trend}")
    print(f"  Volatility:          {analysis.volatility}")
    print(f"  Momentum Score:      {analysis.momentum_score:.1f} / 10")
    print(f"  Net Change:          {analysis.net_change_percent:+.2f}%")


def handle_delete_coin(tracker: CryptoTracker):
    """Deletes a tracked coin."""
    coin_id = input("Enter coin_id to delete: ").strip().lower()
    if not coin_id:
        raise ValueError("Coin ID cannot be empty.")
    
    while True:
        confirm_str = input(f"🚨 Are you sure you want to permanently delete '{coin_id}'? (yes/no): ").strip().lower()
        if confirm_str in {"yes", "y", "no", "n"}:
            break
        logging.error("❌ Invalid input. Please enter 'yes' or 'no'.")
    
    if confirm_str in {"no", "n"}:
        logging.info("Delete operation cancelled.")
        return

    delete_prices = input("Delete all associated price history too? (yes/no): ").strip().lower() in {"yes", "y"}
    tracker.delete_tracked_coin(coin_id, delete_prices)
    logging.info(f"✅ Successfully deleted '{coin_id}'.")

# ===================================
# Main Application Loop
# ===================================

def print_menu() -> None:
    """Prints the main application menu."""
    print("\n╔═══════════════════════════════════════╗")
    print("║      Crypto Demo Analytics System     ║")
    print("╠═══════════════════════════════════════╣")
    print("║ 1) Add Tracked Coin                   ║")
    print("║ 2) List Tracked Coins                 ║")
    print("║ 3) Record Live Prices (Snapshot)      ║")
    print("║                                       ║")
    print("║ 4) Market Analytics (Last X Records)  ║")
    print("║ 5) Trend & Volatility Analysis        ║")
    print("║                                       ║")
    print("║ 6) Delete a Tracked Coin              ║")
    print("║ 0) Exit                               ║")
    print("╚═══════════════════════════════════════╝")

def main() -> None:
    """Main application entry point and loop."""
    client = CoinGeckoClient()
    tracker = CryptoTracker(client=client)

    actions = {
        "1": handle_add_coin,
        "2": handle_list_coins,
        "3": handle_record_prices,
        "4": handle_market_analytics,
        "5": handle_trend_analysis,
        "6": handle_delete_coin,
    }

    try:
        while True:
            print_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "0":
                logging.info("Exiting application.")
                break
            
            action = actions.get(choice)
            if action:
                try:
                    action(tracker)
                except (ValueError, KeyError, DoesNotExist) as e:
                    logging.error(f"❌ Error: {e}")
                except Exception as e:
                    logging.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
            else:
                logging.error("❌ Invalid option. Please select from the menu.")
            
            input("\nPress Enter to continue...")

    finally:
        tracker.close()


if __name__ == "__main__":
    main()

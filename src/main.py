from __future__ import annotations

from typing import Optional

from src.api.crypto_client import CoinGeckoClient
from src.services.tracker import CryptoTracker


def print_menu() -> None:
    print("\n=== Crypto Monitoring System ===")
    print("1) Add tracked coin")
    print("2) List tracked coins")
    print("3) Record prices for all active coins")
    print("4) Show price history for a coin")
    print("5) Show percentage change for a coin")
    print("6) Update coin active status")
    print("7) Delete tracked coin")
    print("0) Exit")


def ask(prompt: str) -> str:
    return input(f"{prompt}: ").strip()


def main() -> None:
    client = CoinGeckoClient()
    tracker = CryptoTracker(client=client)

    try:
        while True:
            print_menu()
            choice = ask("Select option")

            if choice == "1":
                coin_id = ask("Enter CoinGecko coin_id (e.g., bitcoin, ethereum)")
                name = ask("Enter display name (optional)") or None

                try:
                    coin = tracker.add_tracked_coin(
                        coin_id=coin_id,
                        name=name,
                    )
                    print("✅ Tracked coin added:", coin)
                except Exception as exc:  # noqa: BLE001
                    print("❌ Error:", exc)

            elif choice == "2":
                coins = tracker.list_tracked_coins()
                if not coins:
                    print("No tracked coins.")
                for coin in coins:
                    print("•", coin)

            elif choice == "3":
                prices = tracker.record_prices_for_all_active()
                if not prices:
                    print("No active coins to record.")
                else:
                    for p in prices:
                        print("📌 Recorded:", p)

            elif choice == "4":
                coin_id = ask("Enter coin_id")
                limit_str = ask("How many records? (default 10)") or "10"
                limit = int(limit_str)

                history = tracker.get_price_history(coin_id, limit)
                if not history:
                    print("No history found.")
                else:
                    for item in history:
                        print("•", item)

            elif choice == "5":
                coin_id = ask("Enter coin_id")
                lookback_str = ask("Lookback count (default 2)") or "2"
                lookback = int(lookback_str)

                change = tracker.get_percentage_change(coin_id, lookback)
                if change is None:
                    print("Not enough data to calculate change.")
                else:
                    print(f"Δ Change over last {lookback} records: {change:.4f} %")

            elif choice == "6":
                coin_id = ask("Enter coin_id")
                status_str = ask("Set active? (yes/no)").lower()

                is_active = status_str in {"yes", "y", "true", "1"}

                try:
                    updated = tracker.update_tracked_coin_status(
                        coin_id=coin_id,
                        is_active=is_active,
                    )
                    print("✅ Updated:", updated)
                except Exception as exc:  # noqa: BLE001
                    print("❌ Error:", exc)

            elif choice == "7":
                coin_id = ask("Enter coin_id")
                delete_prices_str = ask("Delete price history too? (yes/no)").lower()
                delete_prices = delete_prices_str in {"yes", "y", "true", "1"}

                tracker.delete_tracked_coin(
                    coin_id=coin_id,
                    delete_prices=delete_prices,
                )
                print("✅ Coin deleted.")

            elif choice == "0":
                print("Exiting...")
                break

            else:
                print("❌ Invalid option.")

    finally:
        tracker.close()


if __name__ == "__main__":
    main()

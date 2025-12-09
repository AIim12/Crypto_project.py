## Crypto Analytics System CLI

## 1. Project Overview
The **Crypto Analytics System** is a robust Command-Line Interface (CLI) application developed in Python. It allows users to track cryptocurrency prices in real-time using the **CoinGecko API**, store historical data in a local **MongoDB** database, and perform statistical market analysis.

This project demonstrates advanced Python concepts including Object-Oriented Programming (OOP), Type Hinting, API integration with retry logic, database persistence via an ODM (Object-Document Mapper), and mathematical trend analysis.

---

## 2. Key Features
* **Live Price Tracking**: Fetches real-time price data from the CoinGecko API.
* **Interactive Search**: Smart search functionality to find coins by name or symbol (e.g., "btc", "ethereum").
* **Persistence**: Stores tracked coins and price history in a MongoDB database using MongoEngine.
* **Market Analytics**: Calculates key metrics over a customizable window (Open, Close, High, Low, Average, Net Change %).
* **Trend & Volatility Analysis**: 
    * Computes linear regression slope to determine trends (Uptrend, Downtrend, Sideways).
    * Calculates standard deviation/coefficient of variation to classify volatility (Low, Medium, High).
    * Generates a momentum score (0-10) based on slope and net change.
* **Robustness**: Implements exponential backoff and retry logic for API stability.
* **Data Management**: Capabilities to add, list, and delete coins (including cascading deletion of price history).

---

## 3. Tech Stack
* **Language**: Python 3.10+
* **Database**: MongoDB (requires local installation or Docker)
* **ODM**: `mongoengine` (for object-document mapping)
* **API Client**: `requests` with `urllib3` (for HTTP retries)
* **Testing**: `pytest` and `pytest-mock`
* **Linting**: `pylint`

---

## 4. Project Structure
```text
Python_project_2-3/
├── conftest.py                # Pytest configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── src/
│   ├── main.py                # Application entry point (CLI loop)
│   ├── api/
│   │   └── crypto_client.py   # CoinGecko API client with retry logic
│   ├── database/
│   │   └── mongo.py           # MongoDB connection handler
│   ├── models/
│   │   └── coin.py            # Data models (dataclasses & MongoEngine docs)
│   └── services/
│       └── tracker.py         # Business logic, analytics algorithms
└── tests/
    └── test_tracker_service.py # Unit tests
````

-----

## 5\. Prerequisites & Installation

### ⚠️ Critical Requirement: MongoDB

This application **will not run** without a database connection. You must install MongoDB using **one** of the two options below.

#### Option 1: Docker (Easiest / Universal)

If you have Docker installed, this is the fastest method for any OS.

```bash
docker run -d -p 27017:27017 --name crypto-mongo mongo:latest
```

#### Option 2: Native Installation (OS Specific)

**macOS** (Recommended via Homebrew)

1.  Tap the MongoDB registry:
    ```bash
    brew tap mongodb/brew
    ```
2.  Install MongoDB Community Edition:
    ```bash
    brew install mongodb-community
    ```
3.  Start the service:
    ```bash
    brew services start mongodb-community
    ```

**Windows**

1.  **Download the MSI Installer:** Visit the [MongoDB Download Center](https://www.mongodb.com/try/download/community) and download "MongoDB Community Server".
2.  **Run the Installer:** Select the **"Complete"** setup type.  
    *Important:* Check the box "Install MongoDB as a Service".
3.  **Verify:** Open Task Manager -\> Services tab -\> Ensure `MongoDB` is running.

**Linux (Ubuntu/Debian)**

1.  Install via Apt:
    ```bash
    sudo apt-get update
    sudo apt-get install -y mongodb
    ```
2.  Start the Service:
    ```bash
    sudo systemctl start mongodb
    sudo systemctl enable mongodb
    ```

-----

### Python Environment Setup

**1. Clone the Repository**

```bash
git clone <repository_url>
cd Python_project_2-3
```

**2. Create a Virtual Environment**

  * **macOS / Linux:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

  * **Windows:**

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

-----

## 6\. How to Run

To start the application, execute the `src.main` module from the project root:

```bash
python -m src.main
```

*Note: Ensure your virtual environment is active and MongoDB is running (localhost:27017) before executing this command.*

-----

## 7\. Usage Guide

Upon running the application, you will see the main menu:

```text
╔═══════════════════════════════════════╗
║      Crypto Demo Analytics System     ║
╠═══════════════════════════════════════╣
║ 1) Add Tracked Coin                   ║
║ 2) List Tracked Coins                 ║
║ 3) Record Live Prices (Snapshot)      ║
║                                       ║
║ 4) Market Analytics (Last X Records)  ║
║ 5) Trend & Volatility Analysis        ║
║                                       ║
║ 6) Delete a Tracked Coin              ║
║ 0) Exit                               ║
╚═══════════════════════════════════════╝
```

### Typical Workflow

1.  **Add a Coin**: Select Option `1`. Type `bitcoin` or `btc`. Select the correct match from the list.
2.  **Record Prices**: Select Option `3`. This fetches the current price for all tracked coins and saves it to the database. *Repeat this a few times to generate history.*
3.  **Analyze**: Select Option `4` or `5`. Enter the coin ID (e.g., `bitcoin`) and the number of records to analyze.

### Example Output (Trend Analysis)

```text
--- Trend & Volatility for Bitcoin (Last 10 Records) ---
  Trend:               Uptrend
  Volatility:          Low
  Momentum Score:      7.5 / 10
  Net Change:          +2.15%
```

-----

## 8\. Development & Testing

### Running Unit Tests

The project includes automated tests using `pytest` to verify the search logic, price recording, and failure handling.

```bash
pytest
```

*Expected Output: `Passed` for all tests in `tests/test_tracker_service.py`.*

### Code Quality (Linting)

The code follows PEP 8 standards. To check code quality using `pylint`:

```bash
pylint src
```

-----

## 9\. Academic Requirements Coverage

This project fulfills all required baseline features:
- API integration (CoinGecko)
- Database storage (MongoDB)
- OOP structure (models, service layer, CLI)

Additionally, it implements optional complexity:
- Robust retry logic
- Market analytics (open, close, high, low, avg, change)
- Trend & volatility detection
- Clean architecture with separation of concerns

-----

## 10\. Known Issues / Constraints

  * **API Rate Limits**: The CoinGecko Public API has a rate limit of \~10-30 calls/minute. The built-in retry logic helps, but aggressive usage may result in temporary 429 errors.
  * **Data Sufficiency**: Analytics features (Options 4 & 5) require at least 2-4 historical price records to function. Please run Option 3 multiple times after adding a coin.

-----

## 11\. Resources

  * [CoinGecko Main Site](https://coingecko.com/)
  * [CoinGecko API Docs](https://api.coingecko.com/api/v3/coins/list)

<!-- end list -->

```
```

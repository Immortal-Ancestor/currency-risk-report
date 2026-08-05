# Portfolio Currency Exposure Risk Report

A command-line tool built for **DGTR 3720 (Data Transformation)** at the University of Lethbridge. It helps individual investors understand their foreign-currency (FX) risk by converting international positions to USD, simulating a 10% adverse FX move, and flagging any position where that shock would cause a loss exceeding 5% of total portfolio value.

## Business problem

Retail investors holding international assets are exposed to currency risk they often don't quantify. This tool turns raw multi-currency holdings into a clear, ranked risk report with actionable recommendations.

## How it works

1. Prompts the user to enter each currency position (code + local-currency amount)
2. Pulls the latest official daily FX rate for each currency from **FRED** (Federal Reserve Bank of St. Louis)
3. Converts every position to USD and calculates each one's weight in the total portfolio
4. Simulates a 10% adverse FX move on each position
5. Flags any position whose simulated loss would exceed 5% of total portfolio value
6. Prints a formatted risk report with recommendations (hedging instruments, position sizing review, etc.)

Supports EUR, JPY, GBP, CAD, AUD, CHF, CNY, and MXN.

## Setup

```bash
pip install requests
```

Get a free API key at [fredaccount.stlouisfed.org/apikeys](https://fredaccount.stlouisfed.org/apikeys), then set it as an environment variable so it's never stored in the code:

```bash
# macOS/Linux
export FRED_API_KEY="your_key_here"

# Windows
set FRED_API_KEY=your_key_here
```

## Run it

```bash
python currency_risk_report.py
```

Enter currency codes and amounts when prompted; type `done` when finished.

## Tech

Python · `requests` · FRED REST API · currency conversion & risk-threshold logic

---
Built by Niyat Thapa. AI tools were used to help debug and review parts of this script; the design, business logic, and final work are the author's own.

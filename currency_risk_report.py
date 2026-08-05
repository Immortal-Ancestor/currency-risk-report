# Program:  Portfolio Currency Exposure Risk Report
# Course:   DGTR-3720 | Assignment 1
# Author:   NIYAT THAPA

# Purpose:
#   Helps individual investors understand their foreign currency
#   risk by converting international positions to USD and flagging
#   any position where a 10% adverse FX move would cause a loss
#   exceeding 5% of the total portfolio value.

# Business Problem:
#   Retail investors holding international assets are exposed to currency (FX) risk. This tool quantifies that risk and generates actionable recommendations.

# API Used:
#   FRED - Federal Reserve Bank of St. Louis
#   https://fred.stlouisfed.org/docs/api/fred/
#   Provides official daily FX rates for all major currency pairs.

# Assumptions:
#   - User enters position sizes in local (foreign) currency units
#   - FX shock is set to 10% (realistic adverse move)
#   - A position is flagged if its simulated loss exceeds 5% of
#     the total portfolio value
#   - Rates reflect the most recent available FRED daily data

# How to Run:
#   1. pip install requests
#   2. Get a free API key at https://fredaccount.stlouisfed.org/apikeys
#   3. Set it as an environment variable:
#        macOS/Linux:  export FRED_API_KEY="your_key_here"
#        Windows:      set FRED_API_KEY=your_key_here
#   4. python currency_risk_report.py
#   5. Enter currency codes and local amounts when prompted

import requests

# --- Settings ---
# The FRED API key is read from an environment variable so it never lives in
# the source code (safe to publish this file publicly on GitHub).
# Get a free key at https://fredaccount.stlouisfed.org/apikeys, then set it:
#   macOS/Linux:  export FRED_API_KEY="your_key_here"
#   Windows:      set FRED_API_KEY=your_key_here
import os
FRED_API_KEY = os.environ.get("FRED_API_KEY")
FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
FX_SHOCK = 0.10            # simulate a 10% adverse FX move
RISK_THRESHOLD_PCT = 0.05  # flag if simulated loss exceeds 5% of total portfolio

# Each currency maps to its FRED series ID and full name
# invert=True means FRED quotes as foreign/USD, so we flip it to get USD/foreign
CURRENCY_CONFIG = {
    "EUR": {"series": "DEXUSEU", "invert": False, "name": "Euro"},
    "JPY": {"series": "DEXJPUS", "invert": True,  "name": "Japanese Yen"},
    "GBP": {"series": "DEXUSUK", "invert": False, "name": "British Pound"},
    "CAD": {"series": "DEXCAUS", "invert": True,  "name": "Canadian Dollar"},
    "AUD": {"series": "DEXUSAL", "invert": False, "name": "Australian Dollar"},
    "CHF": {"series": "DEXSZUS", "invert": True,  "name": "Swiss Franc"},
    "CNY": {"series": "DEXCHUS", "invert": True,  "name": "Chinese Yuan"},
    "MXN": {"series": "DEXMXUS", "invert": True,  "name": "Mexican Peso"},
}

# Calls FRED API and returns (rate, date) — rate is USD per 1 unit of foreign currency
# Grabs last 5 observations in case the most recent one is missing
def get_fx_rate(series_id, invert):
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "sort_order": "desc", "limit": 5, "file_type": "json"}
    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        for obs in data["observations"]:
            if obs["value"] != ".":
                rate = float(obs["value"])
                if invert:
                    rate = 1 / rate  # flip to USD per foreign unit
                return rate, obs["date"]
        return None, None
    except requests.exceptions.ConnectionError:
        print("  ERROR: No internet connection.")
        return None, None
    except requests.exceptions.Timeout:
        print("  ERROR: FRED API timed out.")
        return None, None
    except requests.exceptions.HTTPError as e:
        print(f"  ERROR: HTTP error: {e}")
        return None, None
    except (KeyError, ValueError) as e:
        print(f"  ERROR: Unexpected data format: {e}")
        return None, None

# Prompts user to enter each currency and local amount — keeps looping until 'done'
def get_portfolio():
    print("\n" + "=" * 60)
    print("  PORTFOLIO CURRENCY EXPOSURE RISK REPORT")
    print("=" * 60)
    print("\nSupported currencies:", ", ".join(CURRENCY_CONFIG.keys()))
    print("\nEnter your portfolio positions. Type 'done' when finished.\n")
    portfolio = []
    while True:
        currency = input("  Currency code (or 'done'): ").strip().upper()
        if currency == "DONE":
            if len(portfolio) == 0:
                print("  Please enter at least one position.")
                continue
            break
        if currency not in CURRENCY_CONFIG:
            print(f"  '{currency}' not supported. Choose from: {', '.join(CURRENCY_CONFIG.keys())}")
            continue
        try:
            amount_str = input(f"  Amount invested in {currency}: ").strip()
            amount = float(amount_str.replace(",", ""))  # allow comma-formatted input
            if amount <= 0:
                print("  Amount must be greater than zero.")
                continue
        except ValueError:
            print("  Invalid amount. Please enter a number.")
            continue
        portfolio.append({"currency": currency, "amount": amount})
        print(f"  Added: {currency} {amount:,.2f}\n")
    return portfolio

# Fetches the latest FX rate and date from FRED for each unique currency in the portfolio
def fetch_rates(portfolio):
    unique_currencies = list({p["currency"] for p in portfolio})
    print("\nFetching latest available FX rates from Federal Reserve Economic Data (FRED)...")
    rates = {}
    for currency in unique_currencies:
        config = CURRENCY_CONFIG[currency]
        rate, date = get_fx_rate(config["series"], config["invert"])
        if rate is not None:
            rates[currency] = {"rate": rate, "date": date}
            print(f"  {currency} ({config['name']}): 1 {currency} = ${rate:.4f} USD  (as of {date})")
        else:
            print(f"  WARNING: Could not retrieve rate for {currency}. Skipping.")
    return rates

# Converts each local currency position to USD using the fetched FX rate,
# then calculates portfolio weight, simulated loss, and risk flag
def analyze_portfolio(portfolio, rates):
    valid_positions = [p for p in portfolio if p["currency"] in rates]
    if not valid_positions:
        return [], 0
    converted = []
    for p in valid_positions:
        usd_value = p["amount"] * rates[p["currency"]]["rate"]  # local amount x FX rate = USD value
        converted.append({"currency": p["currency"], "local_amount": p["amount"], "usd_value": usd_value})
    total_value = sum(p["usd_value"] for p in converted)
    results = []
    for p in converted:
        currency = p["currency"]
        weight_pct = (p["usd_value"] / total_value) * 100
        simulated_loss = p["usd_value"] * FX_SHOCK
        # A position is flagged if the estimated FX loss is greater than 5% of the whole portfolio
        flagged = simulated_loss > (total_value * RISK_THRESHOLD_PCT)
        results.append({
            "currency": currency,
            "name": CURRENCY_CONFIG[currency]["name"],
            "local_amount": p["local_amount"],
            "usd_value": p["usd_value"],
            "rate": rates[currency]["rate"],
            "date": rates[currency]["date"],
            "weight_pct": weight_pct,
            "simulated_loss": simulated_loss,
            "flagged": flagged,
        })
    results.sort(key=lambda x: x["weight_pct"], reverse=True)
    return results, total_value

# Prints the formatted risk report to the terminal
def print_report(results, total_value):
    print("\n" + "=" * 60)
    print("  CURRENCY EXPOSURE RISK REPORT")
    print(f"  FX Shock Assumption : {FX_SHOCK * 100:.0f}% adverse move")
    print(f"  Risk Flag Threshold : {RISK_THRESHOLD_PCT * 100:.0f}% of total portfolio value")
    print("=" * 60)
    print(f"\n  {'CURRENCY':<8} {'NAME':<20} {'LOCAL AMT':>12} {'USD VALUE':>12} {'WEIGHT':>8} {'10% LOSS':>12}  STATUS")
    print(f"  {'-'*8} {'-'*20} {'-'*12} {'-'*12} {'-'*8} {'-'*12}  {'-'*10}")
    warning_count = 0
    for r in results:
        status = "WARNING" if r["flagged"] else "OK"
        if r["flagged"]:
            warning_count += 1
        print(f"  {r['currency']:<8} {r['name']:<20} {r['local_amount']:>12,.0f} ${r['usd_value']:>11,.0f} {r['weight_pct']:>7.1f}% ${r['simulated_loss']:>11,.0f}  {status}")
    print(f"  {'-'*80}")
    print(f"  {'TOTAL PORTFOLIO (USD)':<42} ${total_value:>11,.0f}")
    print("\n" + "=" * 60)
    print("  RISK SUMMARY")
    print("=" * 60)
    if warning_count == 0:
        print(f"\n  No positions exceed the {RISK_THRESHOLD_PCT * 100:.0f}% risk threshold.")
        print("  Portfolio FX risk is within acceptable limits.")
    else:
        print(f"\n  {warning_count} position(s) flagged for elevated FX risk.")
        print(f"  A {FX_SHOCK * 100:.0f}% adverse FX move on flagged positions would")
        print(f"  result in losses exceeding ${total_value * RISK_THRESHOLD_PCT:,.0f} (5% of portfolio).")
        print("\n  Recommended actions:")
        print("  - Consider FX hedging instruments (forwards, options)")
        print("  - Review position sizing for flagged currencies")
        print("  - Monitor central bank policy divergence for flagged pairs")
    if results:
        largest = results[0]
        print(f"\n  Largest single exposure: {largest['currency']} ({largest['name']}) at {largest['weight_pct']:.1f}% of portfolio")
    print("\n  Data source: Federal Reserve Bank of St. Louis (FRED)")
    print("=" * 60 + "\n")

# Runs all steps in order
def main():
    if not FRED_API_KEY:
        print("\nERROR: FRED_API_KEY environment variable is not set.")
        print("Get a free key at https://fredaccount.stlouisfed.org/apikeys")
        print('Then run: export FRED_API_KEY="your_key_here"  (macOS/Linux)')
        print("      or: set FRED_API_KEY=your_key_here        (Windows)")
        return
    portfolio = get_portfolio()
    rates = fetch_rates(portfolio)
    if not rates:
        print("\nERROR: Could not retrieve any FX rates. Check your internet connection.")
        return
    results, total_value = analyze_portfolio(portfolio, rates)
    if not results:
        print("\nERROR: No valid positions to analyze.")
        return
    print_report(results, total_value)

if __name__ == "__main__":
    main()
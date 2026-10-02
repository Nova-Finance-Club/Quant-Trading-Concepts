"""
Build the shared course dataset from Yahoo Finance.

Run once from the repo root:   python data/build_dataset.py
Notebooks only ever read the CSVs this script writes -- they never call yfinance
themselves, so they keep working even when Yahoo is down or rate-limiting.

Outputs (all in data/):
    prices.csv  -- daily close, adjusted for splits and dividends; one column per ticker
    volume.csv  -- daily share volume; one column per ticker (NaN for indices)
    meta.csv    -- ticker, name, asset_type, sector
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# Fixed dates so every member of the club works with exactly the same numbers.
# To refresh the data, move END forward and re-run the script.
START = "2010-01-01"
END = "2026-10-01"  # yfinance treats END as exclusive

OUT_DIR = Path(__file__).resolve().parent

# Large, liquid US stocks with full history since 2010, a few per GICS sector.
# Names with large spin-offs that Yahoo does not adjust for (e.g. GE, MMM) are
# left out on purpose: they show fake one-day crashes in adjusted prices.
STOCKS = {
    # ticker: (name, sector)
    "AAPL": ("Apple", "Information Technology"),
    "MSFT": ("Microsoft", "Information Technology"),
    "NVDA": ("NVIDIA", "Information Technology"),
    "ADBE": ("Adobe", "Information Technology"),
    "CSCO": ("Cisco Systems", "Information Technology"),
    "GOOGL": ("Alphabet (Class A)", "Communication Services"),
    "NFLX": ("Netflix", "Communication Services"),
    "DIS": ("Walt Disney", "Communication Services"),
    "VZ": ("Verizon", "Communication Services"),
    "AMZN": ("Amazon", "Consumer Discretionary"),
    "HD": ("Home Depot", "Consumer Discretionary"),
    "MCD": ("McDonald's", "Consumer Discretionary"),
    "NKE": ("Nike", "Consumer Discretionary"),
    "SBUX": ("Starbucks", "Consumer Discretionary"),
    "PG": ("Procter & Gamble", "Consumer Staples"),
    "KO": ("Coca-Cola", "Consumer Staples"),
    "PEP": ("PepsiCo", "Consumer Staples"),
    "WMT": ("Walmart", "Consumer Staples"),
    "COST": ("Costco", "Consumer Staples"),
    "JNJ": ("Johnson & Johnson", "Health Care"),
    "UNH": ("UnitedHealth", "Health Care"),
    "PFE": ("Pfizer", "Health Care"),
    "MRK": ("Merck", "Health Care"),
    "ABT": ("Abbott Laboratories", "Health Care"),
    "JPM": ("JPMorgan Chase", "Financials"),
    "BAC": ("Bank of America", "Financials"),
    "GS": ("Goldman Sachs", "Financials"),
    "V": ("Visa", "Financials"),
    "BRK-B": ("Berkshire Hathaway (Class B)", "Financials"),
    "XOM": ("Exxon Mobil", "Energy"),
    "CVX": ("Chevron", "Energy"),
    "COP": ("ConocoPhillips", "Energy"),
    "SLB": ("Schlumberger", "Energy"),
    "CAT": ("Caterpillar", "Industrials"),
    "UNP": ("Union Pacific", "Industrials"),
    "LMT": ("Lockheed Martin", "Industrials"),
    "UPS": ("United Parcel Service", "Industrials"),
    "NEE": ("NextEra Energy", "Utilities"),
    "DUK": ("Duke Energy", "Utilities"),
    "APD": ("Air Products", "Materials"),
    "SHW": ("Sherwin-Williams", "Materials"),
    "AMT": ("American Tower", "Real Estate"),
    "PLD": ("Prologis", "Real Estate"),
}

# ETFs: the market, its sectors, and the other asset classes a portfolio needs.
ETFS = {
    "SPY": ("S&P 500", "Equity - US Large Cap"),
    "QQQ": ("Nasdaq-100", "Equity - US Large Cap"),
    "IWM": ("Russell 2000", "Equity - US Small Cap"),
    "XLK": ("Technology Select Sector", "Equity - Sector"),
    "XLF": ("Financial Select Sector", "Equity - Sector"),
    "XLE": ("Energy Select Sector", "Equity - Sector"),
    "XLV": ("Health Care Select Sector", "Equity - Sector"),
    "XLY": ("Consumer Discretionary Select Sector", "Equity - Sector"),
    "XLP": ("Consumer Staples Select Sector", "Equity - Sector"),
    "XLI": ("Industrial Select Sector", "Equity - Sector"),
    "XLU": ("Utilities Select Sector", "Equity - Sector"),
    "XLB": ("Materials Select Sector", "Equity - Sector"),
    "TLT": ("20+ Year Treasury Bond", "Bonds - Government"),
    "IEF": ("7-10 Year Treasury Bond", "Bonds - Government"),
    "LQD": ("Investment Grade Corporate Bond", "Bonds - Corporate"),
    "HYG": ("High Yield Corporate Bond", "Bonds - Corporate"),
    "GLD": ("Gold", "Commodities"),
    "VNQ": ("US Real Estate (REITs)", "Real Estate"),
}

# Indices: not tradable, but needed as inputs.
INDICES = {
    "^VIX": ("CBOE Volatility Index", "Volatility"),
    "^IRX": ("13-Week T-Bill Yield (annual %, not a price)", "Rates"),
}

# Any one-day move bigger than this gets flagged for a manual look.
JUMP_THRESHOLD = 0.40


def build_meta() -> pd.DataFrame:
    """One row per ticker, so notebooks can group by sector or asset type."""
    rows = []
    for asset_type, universe in [("stock", STOCKS), ("etf", ETFS), ("index", INDICES)]:
        for ticker, (name, sector) in universe.items():
            rows.append({"ticker": ticker, "name": name, "asset_type": asset_type, "sector": sector})
    return pd.DataFrame(rows)


def download(tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download adjusted closes and volumes. Returns (prices, volume), dates x tickers."""
    raw = yf.download(
        tickers,
        start=START,
        end=END,
        auto_adjust=True,  # adjust Close for splits AND dividends -> returns are total returns
        progress=False,
        threads=True,
    )
    prices = raw["Close"][tickers]
    volume = raw["Volume"][tickers]
    # Yahoo returns timezone-free dates for daily data; make sure the index is a clean date index
    prices.index = pd.to_datetime(prices.index).normalize()
    volume.index = prices.index
    prices.index.name = volume.index.name = "date"
    return prices, volume


def validate(prices: pd.DataFrame, volume: pd.DataFrame, meta: pd.DataFrame) -> list[str]:
    """Hard checks raise; soft checks return warnings to print."""
    # Hard check 1: every ticker actually came back
    missing = [t for t in meta.ticker if t not in prices.columns or prices[t].isna().all()]
    if missing:
        raise RuntimeError(f"No data returned for: {missing}. Re-run (Yahoo sometimes rate-limits).")

    # Hard check 2: no duplicated dates
    if prices.index.duplicated().any():
        raise RuntimeError("Duplicated dates in the price index.")

    # Hard check 3: prices must be positive (^IRX is a yield and can be 0, so it is skipped)
    tradables = meta.loc[meta.asset_type != "index", "ticker"]
    if (prices[tradables] <= 0).any().any():
        raise RuntimeError("Non-positive prices found.")

    warnings = []

    # Soft check 1: each ticker should start at the beginning of the sample
    first_valid = prices.apply(lambda s: s.first_valid_index())
    late = first_valid[first_valid > prices.index[0] + pd.Timedelta(days=10)]
    for t, d in late.items():
        warnings.append(f"{t}: history starts late, on {d.date()}")

    # Soft check 2: gaps inside a ticker's history (missing days on the shared calendar)
    for t in prices.columns:
        s = prices[t].loc[first_valid[t]:]
        n_gaps = int(s.isna().sum())
        if n_gaps > 0:
            warnings.append(f"{t}: {n_gaps} missing days inside its history")

    # Soft check 3: suspicious one-day jumps (unadjusted splits or spin-offs look like this)
    returns = prices[tradables].pct_change(fill_method=None)
    jumps = returns.stack()
    jumps = jumps[jumps.abs() > JUMP_THRESHOLD]
    for (d, t), r in jumps.items():
        warnings.append(f"{t}: {r:+.0%} move on {d.date()} -- check for a split or spin-off")

    return warnings


def main() -> None:
    meta = build_meta()
    tickers = meta.ticker.tolist()
    print(f"Downloading {len(tickers)} tickers from {START} to {END} ...")
    prices, volume = download(tickers)

    # Use the stock market's own trading calendar (SPY's trading days) for every column.
    # ^VIX/^IRX occasionally print on days the stock market is closed, and vice versa.
    calendar = prices["SPY"].dropna().index
    prices = prices.reindex(calendar)
    volume = volume.reindex(calendar)

    # Index volume is meaningless (Yahoo reports 0) -- mark it as missing instead
    index_tickers = meta.loc[meta.asset_type == "index", "ticker"]
    volume[index_tickers] = np.nan

    warnings = validate(prices, volume, meta)

    prices.round(6).to_csv(OUT_DIR / "prices.csv")
    volume.to_csv(OUT_DIR / "volume.csv", float_format="%.0f")
    meta.to_csv(OUT_DIR / "meta.csv", index=False)

    print(f"Saved {prices.shape[1]} tickers x {prices.shape[0]} trading days "
          f"({prices.index[0].date()} to {prices.index[-1].date()}) to {OUT_DIR}")
    if warnings:
        print(f"\n{len(warnings)} warning(s) -- review before using:")
        for w in warnings:
            print("  -", w)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()

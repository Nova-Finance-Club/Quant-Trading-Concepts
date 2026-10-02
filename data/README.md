# Course dataset

Daily data for 43 US stocks, 18 ETFs and 2 indices, from 2010-01-04 to 2026-09-30, downloaded from Yahoo Finance.

| File | Contents |
|---|---|
| `prices.csv` | Daily close, adjusted for splits and dividends (so `pct_change()` gives total returns). One column per ticker. |
| `volume.csv` | Daily share volume. Empty for the indices. |
| `meta.csv` | `ticker`, `name`, `asset_type` (stock / etf / index), `sector` |
| `sample_headlines.csv` | 120 headlines about **fictional** companies, written for the course and labelled positive / negative / neutral (used in A2 and A5). Not real news. |

```python
import pandas as pd
prices = pd.read_csv("../data/prices.csv", index_col="date", parse_dates=True)
meta = pd.read_csv("../data/meta.csv")
```

**Things to know**

- `^VIX` is a volatility index level and `^IRX` is the 13-week T-bill yield in annual percent. Neither is a price, so don't compute returns on them. Daily risk-free rate ≈ `prices["^IRX"] / 100 / 252`.
- The stocks were chosen because they are large *today*. That builds in survivorship bias: backtests on this universe look better than they would have in real time.
- All columns share SPY's trading calendar. `^IRX` has 2 missing days.

**Refreshing the data:** move `END` forward in `build_dataset.py` and run `python data/build_dataset.py` from the repo root. The script stops if any ticker fails to download and prints warnings for gaps or suspicious one-day jumps.

# Quant-Trading-Concepts

#### Official repository of the Nova Finance Club's Quant Trading department.

A hands-on course in quantitative finance, written for students with a solid maths background and basic Python, but no prior quant experience. Every notebook follows the same five steps: **Motivation → Intuition → The math → Code it → Takeaways and where it breaks**. All code runs on real market data from the shared `data/` folder.

## How to use it

Everyone takes the **Common Core**, then the track for their team, then the **Capstone**.

### 00 · Common Core (everyone)
| # | Notebook |
|---|---|
| 1 | Prices and returns |
| 2 | Risk and performance: volatility, Sharpe ratio, drawdown |
| 3 | Correlation and diversification |
| 4 | Your first backtest |
| 5 | How trading works: order book, spread and price impact |
| 6 | Backtest biases: look-ahead, survivorship, overfitting |
| 7 | Transaction costs and turnover |

### 01 · Portfolio & Risk track
| # | Notebook |
|---|---|
| PR1 | Markowitz: optimal portfolios and why they break |
| PR2 | Covariance shrinkage (Ledoit–Wolf) |
| PR3 | Risk parity and Hierarchical Risk Parity (HRP) |
| PR4 | Factor models |
| PR5 | Position sizing: Kelly and volatility targeting |
| PR6 | Value at Risk and stress testing |
| PR7 | Drawdown control |

### 02 · Signal Research track
| # | Notebook |
|---|---|
| SR1 | Momentum (cross-sectional and time-series) |
| SR2 | Pairs trading and cointegration |
| SR3 | The Kalman filter |
| SR4 | Regime detection (hidden Markov models) |
| SR5 | Feature engineering and the information coefficient |
| SR6 | Walk-forward and purged cross-validation |
| SR7 | Tree ensembles (random forests, gradient boosting) |

### 03 · Sentiment & Alternative Data track
| # | Notebook |
|---|---|
| SAR1 | The alternative data landscape |
| SAR2 | Text to numbers: tokens, lexicons, sentiment scores |
| SAR3 | Attention signals and event studies |
| SAR4 | Point-in-time data: timestamps, time zones, the market close |
| SAR5 | Text classification: TF-IDF and logistic regression |

### 04 · Capstone (everyone)
| # | Notebook |
|---|---|
| K1 | From backtest to paper trading |
| K2 | A complete system, from data to report |

## Data

`data/` holds daily prices and volumes for 43 US stocks, 18 ETFs, the VIX and the 13-week T-bill rate (2010–2026), plus 120 fictional labelled headlines for the sentiment notebooks. See [`data/README.md`](data/README.md). To refresh the market data, run `python data/build_dataset.py`.

## Setup

Python 3.10+ with `numpy`, `pandas`, `matplotlib`, `scipy`, `statsmodels` and `scikit-learn` (all included in Anaconda). `yfinance` is only needed to rebuild the dataset.

## Archive

`archive/` contains the previous, more advanced version of the course (33 notebooks), kept for reference.

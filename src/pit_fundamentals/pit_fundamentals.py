"""Point-in-time fundamentals — the discipline that keeps a value screen honest.

The single most important rule in fundamental backtesting: a value is knowable only on the date it
was FILED, never the period it describes. Q4 results dated "2023-12-31" might not be public until
February. Index by filing date and look-ahead bias becomes structurally impossible; index by period
date and every backtest silently cheats.

This module shows the mechanics — parsing SEC XBRL companyfacts by filing date, building trailing-
twelve-month (TTM) sums point-in-time, and the standard distress/quality FORMULAS a value screen
uses. The formulas are textbook (Sloan accruals, Altman Z'', Merton distance-to-default); what a
real strategy keeps private are the THRESHOLDS applied to them, which live in config, not here.

SEC companyfacts is a free, keyless API — it only requires a descriptive User-Agent per SEC policy.
Set your own contact string below.
"""
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

SEC_USER_AGENT = "your-name your-email@example.com"    # SEC requires a contact string; no API key


# ---------------------------------------------------------------- point-in-time XBRL --------------

def companyfacts_series(facts: dict, concept: str, unit: str = "USD") -> pd.DataFrame:
    """Extract one XBRL concept as a filing-date-indexed series.

    facts: the JSON from SEC companyfacts (data['facts']['us-gaap']). Returns a frame with the
    period end, the value, and — critically — `filed` (the date it became public). We index by
    `filed`, deduplicate to the latest restatement available as of each filing, and NEVER use the
    period date for as-of lookups.
    """
    node = facts.get(concept, {}).get("units", {}).get(unit, [])
    if not node:
        return pd.DataFrame(columns=["end", "val", "filed"])
    df = pd.DataFrame(node)
    df["filed"] = pd.to_datetime(df["filed"])
    df["end"] = pd.to_datetime(df["end"])
    # keep quarterly/annual points; sort by when the market could actually see them
    return df[["end", "val", "filed"]].sort_values("filed").reset_index(drop=True)


def asof(series: pd.DataFrame, as_of: date, lag_days: int = 0) -> Optional[float]:
    """Latest value KNOWABLE as of a date. `filed + lag_days <= as_of` — no hindsight, ever."""
    if series.empty:
        return None
    cut = pd.Timestamp(as_of) - pd.Timedelta(days=lag_days)
    v = series[series["filed"] <= cut]
    return float(v["val"].iloc[-1]) if len(v) else None


def ttm_asof(flow_series: pd.DataFrame, as_of: date, lag_days: int = 0) -> Optional[float]:
    """Trailing-twelve-month sum of a FLOW concept (revenue, net income), point-in-time.

    Sums the four most recent quarterly observations filed on or before `as_of`. Flows must be
    summed (unlike balance-sheet levels, which are taken as the latest point) — mixing them up is
    a common and silent error.
    """
    if flow_series.empty:
        return None
    cut = pd.Timestamp(as_of) - pd.Timedelta(days=lag_days)
    v = flow_series[flow_series["filed"] <= cut].tail(4)
    return float(v["val"].sum()) if len(v) == 4 else None


# ---------------------------------------------------------------- distress / quality formulas -----

def sloan_accruals(net_income_ttm, cfo_ttm, total_assets) -> Optional[float]:
    """Sloan (1996) accruals / assets = (net income - operating cash flow) / assets.
    HIGH = earnings not backed by cash (aggressive accounting); the accrual anomaly predicts lower
    future returns. A LEVEL screen (a ceiling), not a trend."""
    if not total_assets:
        return None
    return (net_income_ttm - cfo_ttm) / total_assets


def altman_z_double_prime(working_capital, retained_earnings, ebit, book_equity,
                          total_liabilities, total_assets) -> Optional[float]:
    """Altman Z'' — the non-manufacturing / emerging-market variant (no sales/assets term, uses
    book rather than market equity). Distress zone roughly < 1.1. Ill-defined for financials."""
    if not total_assets or not total_liabilities:
        return None
    return (6.56 * working_capital / total_assets
            + 3.26 * retained_earnings / total_assets
            + 6.72 * ebit / total_assets
            + 1.05 * book_equity / total_liabilities)


def merton_distance_to_default(equity_value, equity_vol, debt_face, rf, horizon=1.0) -> Optional[float]:
    """Merton structural-credit distance-to-default (naive one-shot approximation).

    Treats equity as a call on assets struck at the debt face. Higher DD = further from default.
    Economically ill-defined for banks/insurers (leverage is the business) — screen those out.
    """
    if not debt_face or equity_value <= 0 or equity_vol <= 0:
        return None
    V = equity_value + debt_face                       # crude asset-value proxy
    sigma_v = equity_vol * equity_value / V            # de-lever the vol
    if sigma_v <= 0:
        return None
    d2 = (np.log(V / debt_face) + (rf - 0.5 * sigma_v ** 2) * horizon) / (sigma_v * np.sqrt(horizon))
    return float(d2)


if __name__ == "__main__":
    # Formula sanity checks (no network needed).
    print("Sloan accruals (NI 90, CFO 120, TA 1000):",
          round(sloan_accruals(90, 120, 1000), 4), "(negative = cash-backed, good)")
    print("Altman Z'' (healthy):",
          round(altman_z_double_prime(200, 400, 150, 600, 400, 1000), 2))
    print("Merton DD (low leverage):",
          round(merton_distance_to_default(800, 0.35, 200, 0.04), 2))
    print("\nPoint-in-time rule: every value indexed by FILING date, looked up with `filed <= as_of`.")

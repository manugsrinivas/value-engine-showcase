"""Lot-true after-tax backtest post-processor.

Applies US federal capital-gains treatment to a backtest's LOT LEDGER (one row per realization)
plus its equity curve, producing an after-tax equity curve and an annual tax report.

Why lot-true matters (the incident that produced this design):
    An earlier version classified each position's ENTIRE P&L by its final-exit date. Partial
    profits realized short-term inside a >1yr position were silently taxed at the long-term
    rate — overstating after-tax CAGR by ~3 percentage points. The schema guard below REFUSES
    position-level input so the retracted method can't be re-run by accident.

Model (standard and parameterizable; state tax ignored):
  - Each realized LOT is classified by its own calendar holding period: >365 days = long-term.
  - Per calendar year: net ST and net LT P&L; IRS netting (a net loss in one bucket offsets the
    other's gain; ANY residual net loss carries forward IN ITS OWN CHARACTER — the naive branch
    chain drops the {one bucket zero, other negative} case; this one doesn't).
  - Tax is paid out of equity at each year-end, so the drag COMPOUNDS (the honest part naive
    "multiply by (1-rate) at the end" analyses miss).
  - Cash/interest income is taxed as ordinary income.
  - Reports both hold-to-end and liquidate-at-end variants.

Usage:
    python tax_engine.py <label> lots.csv equity_curve.csv [interest_income]

    lots.csv columns:   ticker, entry_date, sale_date, proceeds, basis, pnl, reason
    equity curve:       date-indexed CSV, first column = equity

Rates default to ST 32% / LT 15%; override with env TAX_ST / TAX_LT.
"""
import os
import sys

import numpy as np
import pandas as pd

ST_RATE = float(os.environ.get("TAX_ST", "0.32"))
LT_RATE = float(os.environ.get("TAX_LT", "0.15"))


def tax_process(lots_csv, curve_csv, interest_income=0.0, label=""):
    b = pd.read_csv(lots_csv)
    # SCHEMA GUARD: lot-true taxation needs per-REALIZATION rows. A position-level blotter
    # (realized_pnl keyed by final exit) mis-taxes short-term partials at the LT rate — the
    # retracted method. Refuse it loudly rather than produce a flattering wrong number.
    if "sale_date" not in b.columns or "pnl" not in b.columns:
        raise SystemExit(
            f"tax_engine: '{lots_csv}' is not a lot ledger "
            f"(need ticker,entry_date,sale_date,proceeds,basis,pnl,reason). A position-level "
            f"blotter taxes each position's whole P&L by final-exit date = the retracted, "
            f"LT-flattering method.")
    b["entry_date"] = pd.to_datetime(b["entry_date"])
    b["sale_date"] = pd.to_datetime(b["sale_date"])
    b["lt"] = (b["sale_date"] - b["entry_date"]).dt.days > 365
    b["year"] = b["sale_date"].dt.year

    eq = pd.read_csv(curve_csv, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    n_years = max(1, len(set(eq.index.year)))
    interest_per_year = interest_income / n_years

    st_carry = lt_carry = 0.0
    tax_rows = []
    for y in sorted(b["year"].unique()):
        yb = b[b["year"] == y]
        st = yb.loc[~yb["lt"], "pnl"].sum() + st_carry
        lt = yb.loc[yb["lt"], "pnl"].sum() + lt_carry
        st_carry = lt_carry = 0.0
        # IRS netting: cross-offset, then carry ANY residual loss in ITS OWN character.
        # (Covers every sign combination — including {st == 0, lt < 0}, which a naive
        # three-branch chain silently drops, vaporizing the carryforward.)
        if st < 0 and lt > 0:
            off = min(-st, lt); st += off; lt -= off
        elif lt < 0 and st > 0:
            off = min(-lt, st); lt += off; st -= off
        if st < 0:
            st_carry, st = st, 0.0
        if lt < 0:
            lt_carry, lt = lt, 0.0
        tax = st * ST_RATE + lt * LT_RATE + interest_per_year * ST_RATE
        tax_rows.append({"year": int(y), "st_net": st, "lt_net": lt, "tax": tax})

    # Deduct each year's tax from equity at year-end; scale everything after (compounding drag).
    at = eq.astype(float).copy()
    for r in tax_rows:
        ye = at[at.index.year == r["year"]]
        if not len(ye) or r["tax"] <= 0:
            continue
        pay_date = ye.index[-1]
        if at.loc[pay_date] <= 0:
            continue
        factor = max(0.0, 1.0 - r["tax"] / at.loc[pay_date])
        at.loc[at.index > pay_date] *= factor
        at.loc[pay_date] *= factor

    def m(s):
        yrs = (s.index[-1] - s.index[0]).days / 365.25
        return {"tot": (s.iloc[-1] / s.iloc[0] - 1) * 100,
                "cagr": ((s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1) * 100,
                "final": float(s.iloc[-1])}

    start_cap = float(eq.iloc[0])
    unrealized = max(0.0, float(eq.iloc[-1]) - start_cap - b["pnl"].sum())
    liq_tax = unrealized * LT_RATE   # approximation: end-of-window open lots are long-dated
    res = {"label": label, "pre": m(eq), "post": m(at), "tax_rows": tax_rows,
           "total_tax": sum(r["tax"] for r in tax_rows), "at_curve": at,
           "st_pnl": b.loc[~b["lt"], "pnl"].sum(), "lt_pnl": b.loc[b["lt"], "pnl"].sum(),
           "liq_tax": liq_tax, "final_after_liq": m(at)["final"] - liq_tax}
    return res


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    r = tax_process(sys.argv[2], sys.argv[3],
                    float(sys.argv[4]) if len(sys.argv) > 4 else 0.0, sys.argv[1])
    print(f"=== {r['label']}  (ST {ST_RATE:.0%} / LT {LT_RATE:.0%}) ===")
    print(f"  PRE-tax : {r['pre']['tot']:+.0f}%  CAGR {r['pre']['cagr']:.1f}%  "
          f"final ${r['pre']['final']:,.0f}")
    print(f"  POST-tax: {r['post']['tot']:+.0f}%  CAGR {r['post']['cagr']:.1f}%  "
          f"final ${r['post']['final']:,.0f}  (tax paid ${r['total_tax']:,.0f})")
    print(f"  liquidate-at-end final: ${r['final_after_liq']:,.0f} (liq tax ${r['liq_tax']:,.0f})")
    print(f"  realized P&L character: ST ${r['st_pnl']:,.0f} / LT ${r['lt_pnl']:,.0f}")

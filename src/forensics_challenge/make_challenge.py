"""Generate a backtest with FOUR planted bugs — an audit challenge.

This produces a small, self-contained "toy-strat" project whose README quotes headline numbers.
Four of those numbers are wrong, each in a way I actually hit in real research. Your job (or a
candidate's): find all four using accounting identities and a measurement-basis audit, not by
eyeballing returns. Solutions in SOLUTIONS.md — don't peek first.

The four bug classes (this is the generator, so no spoilers beyond the class names you already
see in the audit methodology):
  1. Risk-free basis        3. Data integrity
  2. Accounting identity    4. Window validity

Run:  python make_challenge.py   ->   writes ./toy-strat/
Then audit ./toy-strat/ (its README makes the claims; the CSVs are the evidence).
"""
import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "toy-strat"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

dates = pd.bdate_range("2018-01-02", "2024-12-31")
n = len(dates)

# --- cash ETF (T-bill-like) with ONE impossible bar planted ---
cash_r = np.where(dates < pd.Timestamp("2022-06-01"), 0.015 / 252, 0.045 / 252)
cash_r = cash_r + rng.normal(0, 0.00004, n)
cash_r_clean = cash_r.copy()
bad_i = int(np.where(dates == pd.Timestamp("2021-05-03"))[0][0])
cash_r[bad_i] = 0.06                                   # +6%/day on a T-bill ETF — impossible
cash_px = 100 * np.cumprod(1 + cash_r)

spy_px = 300 * np.cumprod(1 + rng.normal(0.00048, 0.0112, n))

# --- strategy: invested through 2024-02-15, then a dead cash-drift tail (window bug) ---
cut = int(np.where(dates <= pd.Timestamp("2024-02-15"))[0][-1])
strat_r = rng.normal(0.00093, 0.0105, n)
strat_r[cut + 1:] = cash_r_clean[cut + 1:]
eq = 100_000 * np.cumprod(1 + strat_r)

pd.DataFrame({"date": dates, "spy_close": spy_px.round(4),
              "cash_etf_close": cash_px.round(4)}).to_csv(OUT / "prices.csv", index=False)
pd.DataFrame({"date": dates, "equity": eq.round(2)}).to_csv(OUT / "equity_curve.csv", index=False)

cohorts = pd.date_range("2018-01-05", "2024-02-09", freq="MS") + pd.Timedelta(days=4)
pd.DataFrame({"fill_date": cohorts.date,
              "n_candidates": rng.integers(25, 60, len(cohorts))}).to_csv(
    OUT / "candidates.csv", index=False)

# --- blotter + per-lot ledger, with a basis-omission bug planted in the lots ---
blot_total = round((eq[-1] - 100_000) * 0.92, 2)
n_pos = 60
w = rng.dirichlet(np.ones(n_pos) * 0.6)
pnls = np.round(w * blot_total, 2)
pnls[rng.choice(n_pos, 18, replace=False)] *= -1
pnls = np.round(pnls + (blot_total - pnls.sum()) / n_pos, 2)
tickers = [f"TK{i:02d}" for i in range(n_pos)]
entries = pd.to_datetime(rng.choice(dates[:cut - 260], n_pos))
exits = entries + pd.to_timedelta(rng.integers(90, 500, n_pos), unit="D")
blot = pd.DataFrame({"ticker": tickers, "entry_date": entries.date, "exit_date": exits.date,
                     "realized_pnl": pnls})
blot.to_csv(OUT / "blotter.csv", index=False)

lots_rows, bug = [], set(rng.choice(n_pos, 20, replace=False))
for i, row in blot.iterrows():
    k = int(rng.integers(1, 4))
    parts = rng.dirichlet(np.ones(k)) * row["realized_pnl"]
    for j, p in enumerate(parts):
        bump = 1000.0 if (i in bug and j == k - 1) else 0.0   # phantom gain in some final lots
        sale = row["exit_date"] if j == k - 1 else \
            (pd.Timestamp(row["entry_date"]) + pd.Timedelta(days=int(60 + 40 * j))).date()
        lots_rows.append({"ticker": row["ticker"], "entry_date": row["entry_date"],
                          "sale_date": sale, "pnl": round(p + bump, 2),
                          "reason": "final" if j == k - 1 else "partial"})
pd.DataFrame(lots_rows).to_csv(OUT / "lots.csv", index=False)

# --- the README that makes the (partly wrong) claims ---
def stats(px):
    r = px.pct_change().dropna()
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    return ((px.iloc[-1] / px.iloc[0] - 1) * 100,
            ((px.iloc[-1] / px.iloc[0]) ** (1 / yrs) - 1) * 100,
            r.mean() / r.std() * np.sqrt(252))       # raw Sharpe (planted basis bug)

eqs, spys = pd.Series(eq, index=dates), pd.Series(spy_px, index=dates)
qs, qc, qsh = stats(eqs); ss, sc, ssh = stats(spys)
(OUT / "README.md").write_text(f"""# Toy-Strat — momentum-value hybrid (2018-2024 backtest)

Headline results (from metrics.py):

| Metric | Strategy | SPY B&H |
|---|---|---|
| Total return | {qs:.0f}% | {ss:.0f}% |
| CAGR | {qc:.1f}% | {sc:.1f}% |
| Sharpe | {qsh:.2f} | {ssh:.2f} |

Realized P&L (blotter.csv): ${blot_total:,.0f} across {n_pos} closed positions;
per-realization detail in lots.csv; entry cohorts in candidates.csv.
Idle cash earns the cash ETF rate (prices.csv, cash_etf_close).
""", encoding="utf-8")

print(f"Wrote {OUT}/ — audit it. Four headline numbers are wrong.")

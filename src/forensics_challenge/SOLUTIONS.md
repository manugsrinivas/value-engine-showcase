# Solutions — the four planted bugs

Don't read this until you've tried the audit. Each bug is one I hit in real research.

### 1. Risk-free basis (Sharpe)
The README's Sharpe is `mean/std * sqrt(252)` — **raw, zero risk-free**. Recompute on returns in
excess of the cash ETF (the same series the strategy earns on idle balances) and the Sharpe drops
materially — **and so does SPY's**, so the *gap* mostly survives. A raw Sharpe isn't wrong-by-
definition, but it's the wrong basis to quote next to a benchmark. Tell: nothing subtracts a cash
return anywhere.

### 2. Accounting identity (the lot ledger)
`lots.csv` totals ~$20k **more** than `blotter.csv`, and more than the entire portfolio gain implied
by `equity_curve.csv`. A per-lot ledger claiming more realized profit than the account ever made is
arithmetically impossible → the lots file is the broken one (20 positions each carry a phantom
+$1,000 final lot). Tell: per-position `sum(lot pnl) == blotter realized_pnl` fails, always by a
round number; the equity-conservation identity only closes under the blotter.

### 3. Data integrity (the cash series)
`prices.csv` has a **+6%/day** bar on the cash ETF (2021-05-03). A T-bill ETF cannot move ±1%/day —
categorically impossible for the asset class. It matters because idle cash is credited at this
series' rate, so the bad bar compounds into fake return. Tell: scan every input series for
`|daily return| > class_ceiling` and *look at the survivors*.

### 4. Window validity (the dead tail)
Entry cohorts (`candidates.csv`) end **2024-02-09**, but the README quotes a window through
**2024-12-31**. The last ~10 months are a forced wind-down: no entries possible, the book decaying
to cash, the equity curve drifting at the cash rate. That dead tail dilutes CAGR and isn't the
strategy. Tell: the equity curve's rolling short-window volatility collapses to ~cash level after
the last cohort. Fix by ending the window where the data supports it.

**Meta-lesson:** none of these announced themselves in the headline numbers. Each was found by an
identity or a basis check — treating a number as guilty until it survives independent scrutiny.

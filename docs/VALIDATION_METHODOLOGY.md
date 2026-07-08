# Validation Methodology — How Signals Earn Their Way In (or Don't)

The core discipline of this project: **no signal touches the live model without surviving a
pre-registered gauntlet designed to kill it.** This document describes that gauntlet.

## The problem this solves

Backtest overfitting is the default failure mode of systematic investing. Test enough ideas against
one historical sample and something will look great by chance. Three project-specific incidents made
this concrete (all caught before deployment):

1. **The look-ahead market-cap floor.** A market-cap filter using *current* market caps "added
   +200%+ to the backtest." Reconstructing caps *as-of each trade date* (raw shares × price, with
   split-factor reconciliation) showed the entire effect was hindsight: winners are mechanically
   large *today*. The clean version of the same filter was rejected.
2. **The silent no-op gates.** Several gates referenced data fields that were unpopulated for most
   names — the backtest "passed" them because they never actually fired. Rule since then: **verify a
   gate bites** (changes the candidate set) before believing any A/B result.
3. **The concentration mirage.** A size floor that looked strongly additive (PBO 0.13, DSR 0.99 on
   the full sample!) turned out to be a position-count/compounding artifact: the *dropped* names were
   more profitable per trade; the equity-curve gain came purely from concentrating the same capital
   into fewer names. Walk-forward analysis and a trade-level mechanism decomposition exposed it.

## The gauntlet (applied to every candidate signal)

1. **Point-in-time construction.** Every input is dated by *when it became knowable* (SEC filing
   date, not period end; knowledge-lag on external data). If a value can't be reconstructed as-of
   the decision date, it doesn't get tested.
2. **Coverage & bite check.** What fraction of candidates does the signal cover, and how many does
   it actually affect at the proposed threshold? (Kills silent no-ops up front.)
3. **Redundancy pre-check.** Rank-correlation against already-deployed signals. Orthogonality is
   necessary but not sufficient — correlated signals get tested as *replacements*, not additions.
4. **A/B on the full multi-regime window** (2014–2025: two bears, one crash, two bull runs, one
   sideways grind) — *and* on a second window, with same-run baselines only (a re-fetched price
   panel shifts the basis; pre/post numbers never mix).
5. **Walk-forward selection test.** Expanding *and* rolling in-sample windows pick the "best"
   variant; it's applied out-of-sample. A real effect keeps winning OOS with a *stable* chosen
   parameter; an overfit one wobbles between variants (this distinction killed the size floor).
6. **Overfit statistics.**
   - **CSCV Probability of Backtest Overfitting** (Bailey, Borwein, López de Prado, Zhu): across
     all C(S, S/2) in/out partitions, how often does the in-sample winner land in the bottom half
     out-of-sample?
   - **Deflated Sharpe Ratio**: the observed Sharpe haircut for the *number of trials run*, return
     skew/kurtosis, and sample length. Nothing is "credible" below DSR 0.95.
   - **Combinatorially Purged CV** regime distributions: performance across all combinations of
     held-out time-blocks (with embargo gaps for overlapping holds) — reported as the *distribution*
     (median, 5th-percentile worst regime mix, fraction positive), not an average.
7. **Proxy controls.** Any surviving effect is decomposed against size, sector, and liquidity —
   a "signal" whose dropped names are systematically small/illiquid/one-sector is a factor bet in
   disguise and is either neutralized or rejected.
8. **Interaction testing.** Survivors are re-tested *on top of the live configuration* (so
   redundancy with deployed signals shows up as harm, not double-counted credit), then in pairwise
   combinations. This surfaced both a redundancy trap (a "new" valuation signal that was ~0.6
   rank-correlated with deployed models — stacking it deepened drawdowns) and a genuine positive
   interaction (a distress gate that makes a stronger valuation tilt safe by pruning the names it
   would otherwise over-concentrate into).
9. **Ledger entry either way.** Every result — especially the nulls — is written up with effect
   sizes and the reproduction commands. Negative results are treated as capital: they prevent
   re-litigating dead ideas.

## The scoreboard (honesty in numbers)

- **~15 candidate overlays tested** across fundamental trend, quality, distress, insider,
  analyst, concentration, and risk-tilt families.
- **~12 rejected** — most with the same signature: they cut the beaten-down "re-rater" tail that
  carries a value strategy's P&L.
- **3 deployed** — all sharing one shape: *orthogonal level-based vetoes* (solvency level,
  earnings-quality level, data-completeness) or *breadth-preserving defensive tilts*, adopted for
  drawdown/robustness benefits rather than return claims.
- **1 ML model demoted**: an XGBoost ranking model with out-of-sample AUC ≈ 0.51 was kept
  monitoring-only. The deployed selection logic is fully deterministic and reproducible.

## The meta-lesson

> **The screen is the edge. Overlays mostly aren't.**

A simple, structural value screen with disciplined breadth beat nearly every enhancement bolted on
top of it. The validation harness's job was mostly to *protect* the strategy from its
enhancements — which is, in practice, what most quant validation is for.

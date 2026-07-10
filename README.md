# Systematic Value Investment Engine — Project Showcase

> Resume/portfolio-ready description of this project. Safe to publish as a standalone README
> (contains methodology + engineering narrative, no proprietary signal parameters or account data).

## One-paragraph summary (for a resume or repo tagline)

A fully-automated, end-to-end **systematic value investing platform**: it screens ~2,100 US equities
nightly using point-in-time SEC XBRL fundamentals, values each name with multiple independent models
(DCF, Graham Number, rate-anchored Graham Revised, Earnings Power Value), applies validated
quality/distress gates (Sloan accruals, Merton distance-to-default, Altman Z″), sizes a ~40-name
breadth portfolio with defensive tilts, and executes autonomously on a brokerage API with
protective-stop management, corporate-action handling, and cash-settlement-aware order logic — all
validated through an institutional-grade anti-overfitting harness (walk-forward, combinatorially
purged cross-validation, Probability of Backtest Overfitting, Deflated Sharpe Ratio).

## What it demonstrates (skills matrix)

| Domain | Concrete evidence in this project |
|---|---|
| **Quant research methodology** | CSCV-PBO, Deflated Sharpe, CPCV regime distributions, walk-forward CV, cluster-robust inference; every signal pre-registered with kill criteria |
| **Financial modeling** | IV/DCF engine, Graham Number/Revised, EPV, Merton structural credit (distance-to-default), Altman Z″, Sloan accruals, Beneish M-score, reverse-DCF implied expectations |
| **Point-in-time data engineering** | SEC XBRL companyfacts parsed by *filing date* (never period date) — leak-free by construction; split-safe market caps from raw shares × split-factor reconciliation; 271-feature engineered panels with schema-versioned parquet caching |
| **Live trading systems** | Scheduled morning/evening execution loops on a brokerage API; buying-power-aware order sizing; wash-trade-safe stop re-arming; corporate-action (split) state re-anchoring; naked-position auto-arm sweeps; T+1 cash-settlement handling |
| **ML with honest evaluation** | XGBoost vol-regime + triple-barrier classifiers built, then **demoted to monitoring-only** after out-of-sample AUC ≈ 0.51 — the discipline to not deploy ML that doesn't validate |
| **Negative-result rigor** | ~15 overlays tested, ~12 rejected with documented, reproducible nulls (momentum, dividend/revenue growth, insider Form 4, analyst revisions, sector caps, size floors…) |
| **Software engineering** | Monorepo with research/live separation, env-knob A/B harness, resumable block scrapers, self-healing schedulers, git audit trail, weekly auto-generated monitoring reports |

## The intellectual core (what makes it interesting to talk about)

1. **"The screen is the edge; overlays mostly aren't."** Fifteen fundamental overlays were tested
   through the same gauntlet. Nearly all failed — including several that *looked* additive until a
   clean point-in-time re-test exposed look-ahead bias (e.g., a market-cap floor that "added 200%"
   until market caps were reconstructed as-of trade date). The survivors share one shape:
   **orthogonal LEVEL vetoes** (solvency, earnings quality, data completeness) rather than
   trend/health gates, which systematically amputate the beaten-down re-raters that carry the P&L.

2. **Exploit edges as breadth-preserving *tilts*, not gates.** A margin-of-safety decomposition showed
   deeper-discount entries genuinely earn more (+3.3% vs −0.9% per trade), but *tightening the value
   gate* to capture it was a concentration mirage (non-monotonic, breadth collapsing 41→30 names). The
   validated way to harvest the edge was a continuous **iv-discount sizing tilt** — overweight the
   cheapest names while *every* name stays held — which beat the prior multi-model-confluence tilt on
   every axis and in all four walk-forward folds with breadth intact. The same principle rejected the
   value-gate tightening, momentum, and a daily-loss circuit breaker: **a dip-buying book must never
   sell (or filter away) weakness — that fights its own edge.**

3. **Interaction-aware combination testing.** The model was built by testing signals 1-by-1 *on top of*
   the live configuration (so redundancy shows up as harm, not double-counted credit) — surfacing both
   a redundancy trap (mid-cycle earnings yield ≈ the already-live earnings-power model; stacking deepened
   drawdowns) and a genuine positive interaction (a distress red-flag gate makes a stronger sizing tilt
   safe by pruning the traps it would otherwise over-weight).

4. **Layered, whipsaw-free crash defense.** The optimization target was **drawdown resilience**, not raw
   return. A synthetic fast-crash on the live book quantified it: an *orderly* crash caps the loss at the
   average stop distance (~−9%), while the irreducible tail is an *overnight gap-down* (stops slip). The
   response was a **layered** defense that never whipsaws — position stops, a gap-through-stop exit, a low
   0.54 beta, a macro dial for slow/credit crashes, and a market-gap *entry pause* (don't buy the falling
   knife) — plus the **redeploy engine**: in the COVID crash the screen bought at 55%-below-IV discounts
   and those trades returned +43%, turning the drawdown into the book's best inventory. Every *selling*
   crash-rule tested (daily-loss circuit breaker, gap-sell) was rejected for whipsawing the recovery.

## Validation results (final deployed config vs. the market, 2014–2025 backtest)

Final config: IV/DCF value screen + quality/distress gates + **iv-discount sizing tilt** + **LTCG-aware
one-year hold** + a **macro safety dial** (scales to T-bills in credit/macro stress). Shown both with the
dial off (pure equity book) and on (as deployed), against SPY buy-and-hold on the identical window.

| Metric | SPY B&H | Model (dial off) | **Model (dial on — deployed)** |
|---|---|---|---|
| Total return | 312% | 799% | **693%** |
| CAGR | 13.1% | 21.1% | **19.7%** |
| Sharpe | 0.79 | 1.02 | **1.15** |
| Sortino | 0.96 | 1.57 | **1.77** |
| Max drawdown | −33.7% | −21.3% | **−19.2%** |
| Beta to SPY | 1.00 | 0.94 | **0.54** |
| Alpha / yr | — | +8.7% | **+12.0%** |

The safety dial gives up ~1.4pp of CAGR to **halve beta (0.94→0.54)** and lift Sharpe/Sortino — turning
the book into a genuine low-correlation defensive leg (its role in a multi-strategy portfolio).

*(Backtest on a survivorship-bounded 13F universe with cost modeling; live paper-traded since June 2026
under an execution-integrity shakedown. **Absolute levels are survivorship-flattered** — the claims defended
are the *relative/structural* ones: lower beta, shallower drawdown, higher Sortino, and the process. Honest
limits documented: the safety dial is a macro/credit-stress detector that **caught the 2022 bear but missed
the fast COVID shock**; the book's COVID resilience came from position stops + crash-discount redeploy, not
the dial; a true 2008 replay is infeasible on free data (machine-readable fundamentals begin 2009). The
crash tail — an overnight gap-down that slips through stops — is real and unhedged beyond the low starting beta.)*

## Architecture sketch

```
SEC XBRL (point-in-time) ─┐
Alpaca market data        ├─> nightly screen: IV/DCF value filter + quality gates
FRED macro (AAA yield…)   ┘        │  (ROE, FCF/assets, accruals, Merton DD, Altman-Z″ redflag,
13F institutional filings          │   data-completeness fail-closed gate)
                                   ▼
                    valuation confluence (4 models) ──> sizing tilts (yield-weight × confluence)
                                   ▼
                    candidate CSV -> morning executor (bracket entries, protective stops,
                    BP-aware sizing, corp-action guard, naked-position sweep)
                                   ▼
                    evening manager (partial TP / runners / max-hold renewal / SGOV safety dial)
                                   ▼
                    weekly holdings thesis report + monitoring pack (auto-generated)
```

## How to present this publicly (see note)

**Suggested repo structure for a public showcase** (methodology without the edge):
- This README (or an expanded version with charts)
- The validation-harness write-up (PBO/DSR/CPCV methodology + the negative-results ledger)
- Architecture diagrams + a sanitized excerpt of the monitoring report
- **Not** the signal parameters, threshold values, config files, or account details

**Resume bullets (pick 2-3):**
- Built an end-to-end systematic value-investing platform (SEC XBRL point-in-time pipeline →
  multi-model valuation engine → automated brokerage execution) paper-trading a ~40-name portfolio
- Designed an anti-overfitting validation harness (walk-forward, CPCV, PBO, Deflated Sharpe) that
  rejected 12 of 15 candidate signals and caught two look-ahead biases before deployment
- Backtested to Sharpe 1.15 / Sortino 1.77 / −19% max-drawdown at beta 0.54 vs SPY 0.79 / −34% over
  2014–2025, via a macro safety dial + an iv-discount sizing tilt, with a layered whipsaw-free crash
  defense (stops, gap-through exit, market-gap entry-pause) validated to beat every sell-on-weakness rule

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
   ~0.5 beta (0.47 in the dial's out-of-sample window), a macro dial for slow/credit crashes, and a market-gap *entry pause* (don't buy the falling
   knife) — plus the **redeploy engine**: in the COVID crash the screen bought at 55%-below-IV discounts
   and those trades returned +43%, turning the drawdown into the book's best inventory. Every *selling*
   crash-rule tested (daily-loss circuit breaker, gap-sell) was rejected for whipsawing the recovery.

## Validation results (final deployed config vs. the market; all figures total-return)

Final config: IV/DCF value screen + quality/distress gates + **iv-discount sizing tilt** + **LTCG-aware
one-year hold** + a **macro safety dial** (scales to T-bills in credit/macro stress).

**Full multi-regime window, 2014–2025 — dial OFF** (the dial is a model *trained on 2008–2019*, so
dial-on results are only reported on its out-of-sample window below — no in-sample credit taken):

| Metric | SPY B&H | QQQ B&H | **Model (dial off)** |
|---|---|---|---|
| Total return | 312% | 595% | **817%** |
| CAGR | 13.1% | 18.4% | **21.3%** |
| Sharpe / Sortino | 0.79 / 0.96 | 0.89 / 1.13 | **1.09 / 1.68** |
| Max drawdown | −33.7% | −35.1% | **−20.4%** |

**Safety-dial evaluation, 2020–2026 only (strictly out-of-sample for the dial):**

| Metric | SPY B&H | QQQ B&H | **Model dial ON (deployed)** |
|---|---|---|---|
| Total return | 152% | 254% | **339%** |
| CAGR | 15.3% | 21.5% | **25.6%** |
| Sharpe / Sortino | 0.81 / 0.99 | 0.91 / 1.20 | **1.22 / 1.82** |
| Max drawdown | −33.7% | −35.1% | **−19.6%** |

In its out-of-sample window the dial improved *every* axis (it de-risked into the 2022 bear) — the basis
for keeping it deployed as the low-correlation defensive leg of a multi-strategy portfolio.

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
                    iv-discount + confluence signals ──> sizing tilt (yield-weight × deep-discount overweight)
                                   ▼
                    candidate CSV -> morning executor (bracket entries, protective stops,
                    BP-aware sizing, corp-action guard, naked-position sweep)
                                   ▼
                    evening manager (partial TP / runners / 260-bar LTCG hold renewal / SGOV macro dial)
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

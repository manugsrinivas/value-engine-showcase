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

2. **Multi-model valuation confluence.** Names where four independent valuation models agree
   (>20% margin of safety on each) win materially more often (39% vs 27%) — implemented not as a
   filter but as a *breadth-preserving sizing tilt*, validated to cut drawdowns ~3pp at zero Sharpe
   cost, with the benefit concentrated exactly in choppy/trap-heavy and bear regimes.

3. **Interaction-aware combination testing.** The final model came from testing signals 1-by-1
   *on top of* the live configuration (so redundancy shows up as harm, not double-counted credit) —
   which revealed both a redundancy trap (mid-cycle earnings yield ≈ the already-live EPV/Graham
   models; stacking deepened drawdowns 8pp) and a genuine positive interaction (a distress red-flag
   gate makes a stronger confluence tilt safe by pruning the traps it would otherwise over-boost).

4. **Defense-first objective.** The optimization target was never raw return: it was
   **market-wide-drawdown resilience** — Sortino, worst-24-month window, and crash-window behavior
   (COVID 2020, 2022 rate bear) — reflecting a real allocator's mandate rather than a backtest
   beauty contest.

## Validation results (final deployed configuration, 2014–2025 backtest)

| Metric | Baseline screen | Final model |
|---|---|---|
| Total return | 515% | **560%** |
| Sharpe | 0.85 | **0.88** |
| Sortino | 1.26 | **1.32** |
| Max drawdown | −27.8% | −27.9% (flat) |
| Worst 24-month drawdown | −23.2% | **−21.9%** |
| COVID crash window | +9.3% | **+12.0%** (with a −20% intra-window trough vs SPY −33% — resilience, not immunity) |
| Out-of-sample folds w/ better drawdown | — | **3 of 4** |

*(Backtest on a survivorship-bounded 13F universe with cost modeling; live paper-traded since
June 2026 with a documented execution-integrity shakedown. Absolute levels are backtest levels;
the claim defended is the relative improvement and the process, not a live-return promise. Crash-window forensics: COVID resilience is structural (broad stop-and-redeploy, consistent across all configurations); 2022-bear outperformance traced substantially to a concentrated energy winner and is not claimed as a repeatable property.)*

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
- Improved worst-24-month drawdown and Sortino vs baseline via interaction-tested distress gates
  and a multi-model valuation-confluence sizing tilt, validated across COVID and 2022-bear regimes

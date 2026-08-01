# Systematic Value Investment Engine

This is the research and engineering record of a fully-automated systematic value investing
platform I built and paper-trade live: it screens ~2,100 US equities nightly using point-in-time
SEC XBRL fundamentals, values each name with multiple independent models (DCF, Graham Number,
rate-anchored Graham Revised, Earnings Power Value), applies validated quality/distress gates
(Sloan accruals, Merton distance-to-default, Altman Z″), sizes a ~40-name breadth portfolio with
defensive tilts, and executes autonomously on a trading API — protective-stop management,
corporate-action handling, cash-settlement-aware order logic and all.

What I've published here is the **methodology and the engineering story** — the parts I think are
worth reading. The live signal parameters, thresholds, and account details stay private; the
process is the point.

## Why I thought this was worth building

I wanted to know whether a disciplined individual — with free data, honest statistics, and enough
engineering — could build a value strategy whose claims survive the same scrutiny I'd apply to
anyone else's backtest. That meant treating my own results as adversarially as possible: every
signal had to survive a pre-registered validation gauntlet (walk-forward, combinatorially purged
CV, Probability of Backtest Overfitting, Deflated Sharpe), every headline number had to survive
forensic re-measurement, and every rejected idea had to be documented well enough that I'd never
accidentally re-test it. Roughly four of every five ideas I tried died under that process — and
the record of *how* they died turned out to be the most valuable thing in the repo.

## What I'd highlight

1. **The screen is the edge; overlays mostly aren't.** Fifteen fundamental overlays went through
   the same gauntlet. Nearly all failed — including several that *looked* additive until a clean
   point-in-time re-test exposed look-ahead bias (a market-cap floor "added 200%" until market
   caps were reconstructed as-of trade date). The survivors share one shape: **orthogonal LEVEL
   vetoes** (solvency, earnings quality, data completeness) rather than trend/health gates, which
   systematically amputate the beaten-down re-raters that carry a value book's P&L.

2. **Harvest edges as breadth-preserving *tilts*, not gates.** Deeper-discount entries genuinely
   earn more (+3.3% vs −0.9% per trade), but *tightening the value gate* to capture that was a
   concentration mirage. The validated way to harvest it was a continuous sizing tilt — overweight
   the cheapest names while every name stays held. The same principle rejected momentum filters
   and every daily-loss circuit breaker I tried: **a dip-buying book must never sell or filter
   away weakness — that fights its own edge.**

3. **Test additions on top of the deployed model, not a naive baseline** — redundancy then shows
   up as harm instead of stolen credit. This surfaced both a redundancy trap (an earnings-yield
   lens that duplicated the deployed earnings-power model; stacking them deepened drawdowns) and a
   genuine positive interaction (a distress red-flag gate that makes a stronger sizing tilt safe).

4. **Defense in layers, never whipsaw.** The optimization target was drawdown resilience, not raw
   return. Fast crashes are handled by position stops plus a redeploy engine (in the COVID crash
   the screen bought at 55%-below-value discounts and those trades returned +43%); slow credit
   bears are handled by a macro dial that scales into T-bills. When I later ran four pre-registered
   studies trying to *replace* that dial (15 variants: transparent rules, regime gating, tax-aware
   actions, smoothed signals), every challenger died — several in instructive ways (a variant that
   dominated at zero signal lag lost its entire edge to a single day of realistic latency). The
   original design survived because its warmth is *informed*, not mechanical.

5. **The forensics habit.** Numbers only count here if they survive four independent checks:
   accounting identities to the penny, an independent from-scratch recomputation, a bottom-up
   decomposition, and regeneration with a measured noise floor. That habit caught real bugs in my
   own results — phantom taxable gains from a broken lot ledger, one corrupt T-bill bar that
   compounded into ~23 points of fake return, Sharpe quoted on a zero-risk-free basis, and an
   evaluation window that ran 14 months past the data's coverage. Each fix shipped with a guard so
   the same class of error can't silently recur.

## Validation results (fully audited, 2026-07-29; all figures total-return, Sharpe excess of T-bills)

These numbers are the FIFTH measurement of this strategy — each prior set was retired when an
adversarial audit found a data or methodology defect (EPS reconstruction, unscaled share counts,
look-ahead beta, stale panel vintage, window tails past the last enterable cohort, an untaxed
benchmark, and a macro-timing leak in the risk dial's training features). The audit trail is the
point: every defect was found by attacking my own results, and the corrections were published even
though they made the numbers worse.

**Full multi-regime window, 2014-01 → 2025-09 — dial OFF:**

| Metric | SPY B&H | QQQ B&H | **Model (dial off)** |
|---|---|---|---|
| Total return | 346% | 658% | **+321%** |
| CAGR | 13.6% | 18.8% | **13.0%** |
| Sharpe | 0.72 | — | **0.62** |
| Max drawdown | −33.7% | −35.1% | **−29.5%** |
| After-tax CAGR (liq, $72k NJ) | 11.8% | 16.8% | **9.7%** |

**Read that honestly: the raw screen does NOT beat buy-and-hold over the full cycle** — it loses
on return, Sharpe and after-tax, winning only on drawdown. Publishing that is deliberate.

**Deployed configuration — dial ON, out-of-sample 2020-01 → 2025-09** (the dial is trained
strictly on 2008–2019 with a 63-day embargo at the boundary; its training features carry explicit
FRED publication lags so it cannot see unpublished macro):

| Metric | SPY B&H | **Model dial ON (deployed)** |
|---|---|---|
| Total return | 123% | **+223%** |
| CAGR | 15.0% | **~22%** *(21.6–22.6% across start-date jitter)* |
| Sharpe | 0.64 | **~0.9** *(0.89–0.92)* |
| Max drawdown | −33.7% | **≈−21%** *(−20.2 to −21.3)* |
| After-tax CAGR (liq) | 12.6% | **~17.4%** *(17.39% measured; conservative — see note)* |

*Point estimates above are deliberately reported as ranges: a regeneration test (jittering the
simulation start date) moves the CAGR by ~±0.5pp, so citing 22.6% to the decimal would be false
precision. The independent verification pass also confirmed the accounting identity to $0.00 and
reproduced every statistic from the raw equity curve; the after-tax figure is conservative because
the lot ledger taxes P&L gross of transaction costs (commissions adjust basis in reality).*

The deployed claim survives audit: index-beating return at two-thirds the drawdown, pre- and
post-tax, on a strictly out-of-sample window. Neither configuration beats QQQ buy-and-hold
(18.8%/yr full-window) — this book is the defensive leg of a larger stack whose growth leg holds
the QQQ exposure; it is not a QQQ substitute. The risk dial's one genuine skill is the slow bear
(2022: risk score 0.84 for months); it does NOT see fast crashes (COVID: 0.01) — those are
handled by stop-losses + a cash-redeploy engine, and the two mechanisms are complementary by
design, not by luck. Overfitting re-verification (CSCV, 12,870 splits over the 4 calibration variants actually
tested): **Deflated Sharpe 0.989** — the strategy's Sharpe survives the multiple-testing
haircut at 95%. PBO across the variants is 0.91, which says the CALIBRATION choice among
four near-identical configurations (return corr 0.80–0.89) is not statistically separable —
so the chosen calibration rests on a-priori valuation convention, and no variant-vs-variant
delta is claimed as skill. Both numbers published as measured.

### What defends what — and the quadrant that nothing defends

Two independent risk mechanisms run underneath the screen. Both were finally tested this week with
*mechanism-matched controls* — the test that asks "would a dumb version of this do just as well?"
The result replaced a comfortable assumption with a map, and the map has a hole in it:

| Regime | Defended by | Evidence |
|---|---|---|
| **Fast crash** (COVID-style) | stop-losses + cash redeploy | Stopped book finished 2020 at **+57.2%** (DD −20.2%) vs **+27.5%** (DD −46.5%) unstopped. **75% of that year's P&L came from positions opened *after* the March-23 bottom**, financed by stop exits that realised only −$9.3k — roughly a 6× return on the cost of stopping out. The macro dial is blind here (it scored 0.00 through the crash). |
| **Rate-driven bear** (2022, 2018Q4) | the macro dial | **+9.33pp CAGR / +0.267 Sharpe** versus an exposure-matched constant-weight control holding the same *average* equity. Every constant weight scores Sharpe 0.66 — static de-levering cannot raise Sharpe — while the dial reaches 0.92. That gap is timing value by construction. |
| **Slow, non-rate bear** (2011 sovereign, 2015-16 commodity) | **nothing** | Walk-forward CV across four out-of-sample folds: AUC **0.500 / 0.502 / 0.688 / 0.708**. The dial has genuine skill only in the rate-driven folds; in 2015-16 it sat *below its own median* during the selloff. And stops are actively **harmful** in slow bears (2022: −19.5% stopped vs −12.9% unstopped — whipsaw). |

**So the dial is a rate-regime detector, not crash insurance.** Its evidence base is two
out-of-sample episodes of the *same* stress type, not four of varied types. I publish that
distinction because it changes what the strategy may honestly be sold as: the fast-crash defense is
mechanism-backed and strong, the rate-bear defense is real but narrow, and a 2011-style grind has no
signal behind it at all — only position caps, breadth, and the cash the screen holds when little is
cheap.

A caveat I keep attached to the dial result: out-of-sample AUC rises monotonically with training
size (690 rows → 0.500, 2,954 → 0.708), so "it needs ~8 years of data" is an equally consistent
reading of the failures. Both readings counsel the same restraint — don't assume it generalises to
a stress type it has never seen.

## Where the model loses — and why I publish that

Absolute levels above are survivorship-flattered (documented and bounded; a clean-data replay is
gated before any real capital). Beyond that, the model has honest structural losses I'd rather
state than have discovered: it goes flat in **value-factor winters** (2015-16-type — cheap keeps
getting cheaper, and the edge *is* the exposure); it cannot track **mega-cap concentration
rallies** (2023-type — a value screen will never own the index's seven largest growth names); it
wins raw returns but loses *smoothness* in low-vol grind-up bulls; and after tax, a buy-and-hold
QQQ is the one benchmark it doesn't beat — deferral is uncatchable compounding, which is exactly
why this book is the defensive leg of a multi-strategy portfolio rather than the growth leg.

## Architecture

```
SEC XBRL (point-in-time) ─┐
Alpaca market data        ├─> nightly screen: IV/DCF value filter + quality gates
FRED macro (AAA yield…)   ┘        │  (ROE, FCF/assets, accruals, Merton DD, Altman-Z″ redflag,
13F institutional filings          │   data-completeness fail-closed gate)
                                   ▼
                    valuation-confluence signals ──> sizing tilt (yield-weight × deep-discount overweight)
                                   ▼
                    candidate CSV -> morning executor (entries, protective stops,
                    BP-aware sizing, corp-action guard, naked-position sweep)
                                   ▼
                    evening manager (partial TP / runners / LTCG-aware holds / macro dial)
                                   ▼
                    weekly holdings thesis report + monitoring pack (auto-generated)
```

## Show me the code

Prose is cheap; [**`src/`**](src/) has the runnable pieces — all generic infrastructure or textbook
financial math (the strategy's actual edge stays private). Highlights: a [lot-true tax
engine](src/tax_engine/), a [backtest-audit challenge](src/forensics_challenge/) with four planted
bugs, the [anti-overfitting statistics](src/validation_stats/) (PBO / Deflated Sharpe /
cluster-robust inference), [cash-account execution patterns](src/execution_patterns/), [point-in-time
XBRL + distress formulas](src/pit_fundamentals/), and an [honest cash-sim skeleton](src/cash_sim/).
Most have a zero-setup `python <file>.py` self-demo.

## The deep dives

- **[The Negative-Results Ledger](docs/NEGATIVE_RESULTS.md)** — every idea that failed the
  gauntlet, with the mechanism of failure. I think this is the most valuable document in the repo.
- **[Validation Methodology](docs/VALIDATION_METHODOLOGY.md)** — the pre-registered gauntlet
  (PBO, Deflated Sharpe, CPCV, walk-forward, cluster-robust inference) and the look-ahead
  incidents it caught before deployment.
- **[Execution Engineering](docs/EXECUTION_ENGINEERING.md)** — the unglamorous half: the
  execution-layer failure classes a live system actually hits (wash-trade collisions, naked-stop
  windows, settlement races, corporate actions) and the engineering that closed each one.

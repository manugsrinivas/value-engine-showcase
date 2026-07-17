# Systematic Value Investment Engine

This is the research and engineering record of a fully-automated systematic value investing
platform I built and paper-trade live: it screens ~2,100 US equities nightly using point-in-time
SEC XBRL fundamentals, values each name with multiple independent models (DCF, Graham Number,
rate-anchored Graham Revised, Earnings Power Value), applies validated quality/distress gates
(Sloan accruals, Merton distance-to-default, Altman Z″), sizes a ~40-name breadth portfolio with
defensive tilts, and executes autonomously on a brokerage API — protective-stop management,
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

## Validation results (final deployed config; all figures total-return, Sharpe/Sortino excess of T-bills)

**Full multi-regime window, 2014–2025 — dial OFF** (the dial is trained on 2008–2019, so dial-on
results are only reported on its out-of-sample window below — no in-sample credit taken):

| Metric | SPY B&H | QQQ B&H | **Model (dial off)** |
|---|---|---|---|
| Total return | 312% | 595% | **762%** |
| CAGR | 13.1% | 18.4% | **20.6%** |
| Sharpe / Sortino | 0.70 / 0.85 | 0.81 / 1.04 | **0.97 / 1.51** |
| Max drawdown | −33.7% | −35.1% | **−20.9%** |

**Safety-dial evaluation, 2020-01 → 2025-06 (strictly out-of-sample for the dial):**

| Metric | SPY B&H | **Model dial ON (deployed)** |
|---|---|---|
| Total return | 106% | **272%** |
| CAGR | 14.1% | **27.0%** |
| Sharpe / Sortino | 0.60 / 0.75 | **1.11 / 1.67** |
| Max drawdown | −33.7% | **−19.6%** |

The dial is held as **explicitly-priced insurance, not alpha**: regime decomposition shows its one
genuine win is the slow/grinding bear (2022: drawdown halved, −7.7% vs −18.2% without it), while in
fast V-crashes it reacts late, and its de-risking trims cost ~1.7pp/yr after tax. I keep it because
a slow bear is the one storm nothing else in the stack can see coming.

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

## The deep dives

- **[The Negative-Results Ledger](docs/NEGATIVE_RESULTS.md)** — every idea that failed the
  gauntlet, with the mechanism of failure. I think this is the most valuable document in the repo.
- **[Validation Methodology](docs/VALIDATION_METHODOLOGY.md)** — the pre-registered gauntlet
  (PBO, Deflated Sharpe, CPCV, walk-forward, cluster-robust inference) and the look-ahead
  incidents it caught before deployment.
- **[Execution Engineering](docs/EXECUTION_ENGINEERING.md)** — the unglamorous half: the
  execution-layer failure classes a live system actually hits (wash-trade collisions, naked-stop
  windows, settlement races, corporate actions) and the engineering that closed each one.

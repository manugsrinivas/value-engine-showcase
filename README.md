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

Reported on **both bases**, because mixing them flatters any actively-traded strategy: a
buy-and-hold benchmark defers all capital-gains tax to a single terminal bill, while this book
pays tax every year. Quoting a pre-tax Sharpe beside an after-tax CAGR would hide that.

All figures below are from a **pinned, reproducible artifact** — candidate set, risk dial, price
panels and code commit are all hashed, and the run regenerates the equity curve byte-identically.
Window `2020-01-02 → 2025-08-29`, which is where the pinned candidate set can last open a position.

**PRE-TAX** (all figures total-return; Sharpe excess of T-bills):

| Metric | SPY B&H | QQQ B&H | **Model dial ON (deployed)** |
|---|---|---|---|
| Total return | +115.4% | +172.8% | **+204.5%** |
| CAGR | 14.53% | 19.41% | **21.75%** |
| Sharpe | 0.623 | 0.716 | **0.901** |
| Max drawdown | −33.7% | −35.1% | **−20.1%** |

**AFTER-TAX** (same window; true FIFO tax lots; single filer ~$72k NJ: 27.5% short / 20.5% long; identical rules
both sides — annual tax on realised gains and on dividends, paid out of the account at year-end, plus one
terminal bill on unrealised gain for the *liquidate* rows. Corrected 2026-09-16: the SPY "hold" cell used to
show its liquidate figure, and QQQ has now been measured on this window):

| Metric | SPY B&H | QQQ B&H | **Model dial ON (deployed)** |
|---|---|---|---|
| CAGR — hold | 14.22% | 19.28% | **16.87%** |
| CAGR — liquidate | 12.10% | 16.46% | **16.25%** |
| Sharpe (hold curve) | 0.61 | 0.71 | **0.698** |
| Max drawdown (hold curve, Dec-31 lump tax) | −33.8% | −35.2% | **−26.3%** |

*Tax per $100k over the window: strategy $50,718 on $162,760 of realized P&L plus a $7,106 terminal bill; SPY
$2,300 of dividend tax plus $21,366 at liquidation; QQQ $1,146 plus $34,278.*

> **Corrected 2026-09-11 — the previous version of this table was too flattering.** It read 17.37%
> hold / 16.70% liquidate / Sharpe 0.720 / −25.6% on $45,580 of tax. The simulator's lot ledger used
> average cost, and every scale-in purchase inherited the position's original entry date — so shares
> bought 200 days in and sold 200 days later were taxed as a 400-day long-term sale. 166 of 404
> closed trades scaled in. With true first-in-first-out lots, each purchase keeps its own holding
> clock: the long-term share of realized gains falls from 91% to 51%, tax rises by $5,138, and
> after-tax CAGR drops about half a point. The pre-tax equity curve does not move (verified
> byte-identical against the same code without the fix), and the old figures reproduce exactly from
> the old ledger — so this is a method correction, not noise.

> #### ⚠ Three caveats that must travel with the number above
>
> **1. The margin over SPY is not statistically significant.** The +7.22pp/yr spread has
> **t = 0.70, p = 0.48**. Over 5.66 years the sampling error on the CAGR is ~9pp, so the honest
> 95% confidence interval is roughly **4%–39%**. No benchmark this account could actually buy
> reaches significance — the best is a cash-matched IWM at t = 1.93, still short of 1.96. At the
> observed information ratio, separating this from luck would take **30–44 years** of track record.
>
> **2. Excluding 2020 (2021-01-04 → 2025-08-29, pre-tax), the book only ties SPY** — 15.04% vs 14.32% (IR t 0.08)
> — and its Sharpe is roughly equal (0.72 vs 0.68; 0.70 vs 0.66 from the 2020-12-31 close); the slice also starts
> ~85% invested in 2020 cohorts. The headline margin is carried by the crash year.
>
> **3. 45.6% of lifetime P&L comes from a single entry cohort** (2020-04-02), whose entry date was
> set by a library default in the simulator's quarterly calendar rather than by any model decision.
>
> A previous version of this file quoted **~22% CAGR / Sharpe 0.92 / −21.3% DD** with a
> "21.6–22.6% jitter band". Those came from an earlier run whose artifacts were **not preserved**
> and can no longer be audited. The jitter band is also **retired as an error bar**: it measured
> *path noise* (same inputs, different start date), not the uncertainty of the return, and quoting
> a ±0.5pp band for a quantity with a ±9pp standard error understates the uncertainty by more than
> an order of magnitude.
>
> **The honest one-line summary is "promising and unproven", not "validated".**

**The honest reading of the tax column.** The model's edge shrinks materially after tax: its
CAGR falls 21.75% → 16.25% (liquidate basis), its Sharpe 0.901 → 0.698, and its drawdown deepens
−20.1% → −26.3% on the hold basis, because annual tax payments come out of the equity curve at each
year-end. The benchmarks barely move, because deferral is itself a structural advantage — a buy-and-hold
fund pays its capital-gains bill once, at the end. The margin over SPY narrows from +7.22pp to +4.15pp a
year liquidate-vs-liquidate (+2.65pp hold-vs-hold), with ~7pp less hold-basis drawdown. QQQ, which pays
almost no tax along the way, is ahead by 2.41pp on the hold basis and level on the liquidate basis
(−0.21pp). These are point estimates on one path, and the pre-tax margin they rest on was already not
statistically significant (caveat 1 above). Anyone comparing this to an index fund should use the
after-tax table, not the pre-tax one.

### Overfitting statistics — published as measured, including the one that got worse

**Deflated Sharpe** (Bailey & López de Prado) haircuts the observed Sharpe for the number of
configurations actually tried, plus skew and kurtosis. The figure depends on how honestly you count
trials, so it is reported across a range rather than at the flattering end:

| trials counted (N) | Deflated Sharpe |
|---|---|
| 4 — the calibration variants formally A/B-tested | 0.957 |
| 20 | 0.908 |
| **30 — an honest count of the configurations actually run** | **0.894** |
| 100 | 0.850 |

**At an honest trial count the Sharpe does NOT clear the conventional 0.95 bar.** An earlier
version of this file reported "Deflated Sharpe 0.989 — survives the multiple-testing haircut at
95%" on N = 4 and a since-superseded vintage. That claim is withdrawn: it was true only at the
narrowest defensible trial count.

**PBO** (Probability of Backtest Overfitting, CSCV over the four calibration variants) is **0.91**.
That says the *choice among those four near-identical configurations* (return correlation 0.80–0.89)
is not statistically separable — so the selected calibration rests on an a-priori valuation
convention, and **no variant-versus-variant delta is claimed as skill**.

Both numbers are published because they are unflattering. A repository that reports its overfitting
diagnostics only when they pass is not reporting them.

### What defends what — and the quadrant that nothing defends

Two independent risk mechanisms run underneath the screen. Both were finally tested this week with
*mechanism-matched controls* — the test that asks "would a dumb version of this do just as well?"
The result replaced a comfortable assumption with a map, and the map has a hole in it:

| Regime | Defended by | Evidence |
|---|---|---|
| **Fast crash** (COVID-style) | stop-losses + cash redeploy | Stopped book finished 2020 at **+57.2%** (DD −20.2%) vs **+27.5%** (DD −46.5%) unstopped. **75% of that year's P&L came from positions opened *after* the March-23 bottom**, financed by stop exits that realised only −$9.3k — roughly a 6× return on the cost of stopping out. The macro dial is blind here (it scored 0.00 through the crash). |
| **Rate-driven bear** (2022, 2018Q4) | the macro dial | **+9.33pp CAGR / +0.267 Sharpe** versus an exposure-matched constant-weight control holding the same *average* equity. Every constant weight scores Sharpe 0.66 — static de-levering cannot raise Sharpe — while the dial reaches 0.92. That gap is timing value by construction. |
| **Slow, non-rate bear** (2011 sovereign, 2015-16 commodity) | **nothing** | Walk-forward CV across four out-of-sample folds: AUC **0.500 / 0.502 / 0.688 / 0.708**. The dial has genuine skill only in the rate-driven folds; in 2015-16 it sat *below its own median* during the selloff. And stops are actively **harmful** in slow bears (2022: −19.5% stopped vs −12.9% unstopped — whipsaw). |

> **Added 2026-08-26 — the dial's net contribution over the DEPLOYED window is not positive.** The
> `+9.33pp` above is measured *inside the rate-bear windows where the dial fires*. Measured across
> the whole deployed 2020+ window instead, it contributes **0.00pp of drawdown protection and comes
> out ~1.7pp behind an exposure-matched constant weight** — because `risk_score` averaged **0.001
> (max 0.002) through the entire COVID crash** and only fires in 2022. Three independent lines now
> agree the book's downside protection is **stop-losses plus the crash-discount redeploy engine**,
> not the dial: this project's own handoff had already recorded COVID as "risk 0.00", a forensic
> audit found the book **68% invested going into the crash** with all seven open names stopping out
> at **−7.05% while SPY fell −26.67%**, and an independent study reproduced the null. *Caveat that
> travels with it: that third measurement was on a SPY sleeve rather than this book, so its absolute
> levels are not ours, and the stop evidence rests on seven names in one crash.*
>
> Recording this because the earlier framing was the more dangerous kind of error: the observation
> ("risk 0.00 through the crash") was correct and written down, but labelled as the dial working
> rather than the dial not firing. A stale number leaves a trail; a right observation under a wrong
> label does not.

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

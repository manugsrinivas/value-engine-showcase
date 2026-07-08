# The Negative-Results Ledger

> Most quant write-ups show what worked. This project's most valuable asset is the documented record
> of what *didn't* — each entry below was a plausible, literature-backed idea that failed a
> pre-registered validation gauntlet on point-in-time data. Signal families are named; live
> thresholds and tuned parameters are intentionally omitted.

## Rejected signal families (and why)

| Family | Hypothesis | Verdict & mechanism |
|---|---|---|
| **Price momentum (12-1)** | Avoid falling knives | Cuts the beaten-down re-raters that carry the P&L — the *reason* a value name is cheap is that its recent numbers are bad |
| **Dividend growth** | Quality signal | Same mechanism: dividend-cutters are disproportionately future re-raters |
| **Revenue growth floor** | Avoid melting businesses | Monotonically worse as the floor tightens |
| **Beneish M-score** | Avoid earnings manipulators | 7 of 8 components are health-*trend* indices → same re-rater-cutting failure |
| **Interest coverage** | Solvency screen | Redundant with a market-based structural credit measure (Merton distance-to-default) already deployed |
| **Insider Form 4 (3 formulations)** | Follow informed buying | No robust effect after cluster-robust inference |
| **Analyst revision/price-target signals** | Follow the sell side | Pooled t-stat +4.5 collapsed to +0.4 under cluster-robust inference (the flagship kill for that statistical upgrade) |
| **Sector concentration cap** | Reduce correlated-cluster risk | Made drawdowns *worse* at every level — the correlated cheap cluster IS where deep value lives; capping it removes the recovery engine |
| **Market-cap floor** | Avoid fragile micro-caps | Full-sample stats looked excellent (low PBO, high DSR) but failed strict walk-forward; trade-level decomposition showed a pure concentration/compounding artifact — the dropped small-caps were *more* profitable |
| **Net share issuance** | Dilution veto (Pontiff-Woodgate) | Behaved exactly like the trend family: worse returns and deeper drawdowns |
| **NOA bloat (Hirshleifer)** | Balance-sheet accrual stock | Orthogonal to deployed gates but null through the gauntlet |
| **Low-volatility tilt** | Defensive sizing | **Inverted** in this universe: the low-vol names win far less often — value re-raters are, by nature, high-volatility beaten-down names. A low-vol tilt fights the strategy's own edge |
| **Quality-factor gates (ROE / gross-profitability / FCF-yield floors)** | Classic quality screen | At full data coverage: a regime-dependent factor tilt (helps in quality bulls, hurts across the full cycle) that adds drawdown; earlier "validation" traced to a window effect + partially-inert gates |
| **Cross-sectional ML ranking** | Learn what wins | Out-of-sample AUC ≈ 0.51 at every horizon/feature-set tried → demoted to monitoring-only |
| **Conviction concentration (top-N by margin of safety)** | Back the best ideas | Breadth beat concentration — with no reliable ex-ante winner signal, many small shots dominate few big ones |
| **Periodic rebalancing (all cadences tested)** | Portfolio hygiene | Every rebalance-to-target variant destroyed returns vs letting winners run |

## What survived (the pattern)

Three deployments, one shape — **orthogonal LEVEL vetoes and breadth-preserving defensive tilts**:

1. **Structural distress vetoes** (market-based distance-to-default; accounting-based Altman-Z″ +
   negative-equity red-flag) — kept primarily as *tail insurance*; the accounting version validated
   with a positive interaction: it makes a stronger valuation tilt safe by pruning distress names.
2. **Earnings-quality level ceiling** (Sloan accruals) + a **fail-closed data-completeness gate**
   ("don't hold what you can't evaluate") — the completeness gate was the single strongest
   overlay tested, robust across all regimes.
3. **Multi-model valuation confluence tilt** — overweight (never filter) names where independent
   valuation models (DCF, Graham-family, earnings-power) agree; validated as a drawdown reducer
   with benefits concentrated in choppy/trap-heavy and bear regimes.

## The transferable lessons

1. **Trend/health gates on a value screen are self-defeating** — they remove the names whose
   recovery pays for the strategy.
2. **Orthogonality ≠ additivity.** Uncorrelated signals still failed; correlation screens are a
   pre-filter, not a validation.
3. **Full-sample statistics can unanimously endorse an artifact.** Only walk-forward stability and
   mechanism-level decomposition (what *specifically* drives the delta?) catch concentration and
   window effects.
4. **Test additions on top of the deployed model,** not a naive baseline — redundancy then shows up
   as harm instead of stolen credit.
5. **Negative results compound.** A written null with reproduction steps is the only durable defense
   against re-testing the same idea in eighteen months.

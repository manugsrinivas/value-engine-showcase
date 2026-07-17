# Code

The docs tell the story; this is the code behind it. Everything here is either fully generic
infrastructure or textbook financial math — the strategy's actual edge (screen thresholds, sizing
parameters, the regime model) stays private and lives nowhere in this folder. Each module is
self-contained and runs on its own.

| Module | What it is | Why it's here |
|---|---|---|
| [`tax_engine/`](tax_engine/) | Lot-true after-tax engine (per-realization IRS netting, character-preserving carryforward, compounding drag) | After-tax is where backtests quietly lie; this refuses the flattering shortcut |
| [`forensics_challenge/`](forensics_challenge/) | A backtest with four planted bugs + an audit challenge | Shows I can find what's wrong with a backtest, including my own |
| [`validation_stats/`](validation_stats/) | PBO/CSCV, Deflated Sharpe, cluster-robust event inference | The anti-overfitting math behind the methodology doc |
| [`execution_patterns/`](execution_patterns/) | Cash-account order sequencing + recovery (against an abstract broker interface) | The unglamorous engineering that separates a backtest from a live system |
| [`pit_fundamentals/`](pit_fundamentals/) | Point-in-time XBRL parsing + distress/quality formulas (Sloan, Altman Z″, Merton DD) | The filing-date discipline that makes a fundamental backtest honest |
| [`cash_sim/`](cash_sim/) | Honest cash-account sim skeleton (settlement, cash-earns-cash-rate, gap-through stops, conservation check) | The accounting most vectorized backtests get wrong |

Each folder has its own README with the war story that produced it. Most modules have a `python
<file>.py` self-demo you can run with no setup and no network.

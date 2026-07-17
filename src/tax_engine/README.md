# Lot-True Tax Engine

After-tax results are where backtests quietly lie. This module applies US federal capital-gains
treatment to a backtest **per realization** (lot-true), with annual IRS netting,
character-preserving loss carryforward, and a compounding year-end tax drag.

**Why I wrote it this way:** my first version classified each position's entire P&L by its final
exit date. Sounds reasonable — but partial profits taken short-term inside a >1-year position got
taxed at 15% instead of 32%, flattering after-tax CAGR by ~3 points. Worse, the per-lot ledger
feeding it turned out to have a basis-allocation bug that claimed **more realized profit than the
entire portfolio had gained** — caught by an accounting-identity check, not by eyeballing returns.
The current engine refuses position-level input via a schema guard, and its netting covers the
carryforward corner case ({one bucket zero, other negative}) that a naive branch chain silently
drops — I found that one with a four-year synthetic unit test.

Run it:
```
python tax_engine.py my-strategy lots.csv equity_curve.csv
```

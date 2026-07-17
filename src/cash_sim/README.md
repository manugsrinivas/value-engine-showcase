# Honest Cash-Account Simulator

Most backtests are one line: `weights @ returns`. For a defensive, cash-holding strategy that
shortcut quietly lies, and I care about the lies because they all point the same way — flattering:

- **Idle cash mis-compounding.** The vectorized method rides *all* your capital at the strategy's
  return, including the cash you're deliberately holding. A "diversified" variant sitting on 30%
  cash can look great purely because that cash compounded at 20%. Here, cash earns the *cash rate*.
- **Settlement.** Cash accounts settle T+1 — you can't spend today's sale proceeds today. Ignoring
  it lets a backtest deploy money it wouldn't have.
- **Gap-through stops.** A stop that gaps *through* its level fills at the open, not the stop price.
  Booking the stop price flatters drawdowns in exactly the crash windows a defensive book is judged
  on.

This skeleton does it the slow, correct way: positions followed one at a time, cash earning the
cash rate, settlement respected, stops filling at the gapped open — and a **conservation check**
every run (`start + realized + unrealized + interest − costs == final`) that must close to the
penny. A leak is a stop-everything bug, not a rounding tolerance.

The signal layer is a stub: `screen(date, closes_asof) -> [tickers]`. Bring your own strategy; this
is just the accounting engine it runs on.

```
python cash_sim.py     # 3 synthetic names, a trivial screen, conservation check -> OK
```

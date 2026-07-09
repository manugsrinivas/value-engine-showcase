# Execution Engineering — The Unglamorous Half of a Live Trading System

> Backtests assume fills happen and state stays consistent. Production doesn't. This document
> catalogs the execution-layer failure classes this system encountered (paper-trading against a real
> brokerage API) and the engineering that closed each one. This is where "systematic strategy" meets
> distributed-systems reality.

## Failure classes found and fixed

### 1. Buying-power reservation vs. sizing (order rejections)
**Failure:** new-entry sizing used the equity budget computed at run start; catch-up buy orders
placed moments earlier had *reserved* buying power the broker hadn't released. Orders sized off the
stale figure were rejected ("insufficient buying power") — leaving cash idle for days.
**Fix:** re-query live buying power after every order wave; maintain a running ledger decremented by
actual fills; cap every order at the ledger. Deploys what's actually spendable; the remainder waits
for settlement. Never over-orders, degrades gracefully under T+1 cash settlement.

### 2. Wash-trade collisions → silently naked positions
**Failure:** topping up a held name requires cancelling its protective stop first (same-symbol
opposite-side order). If the stop was re-armed while the buy was still open, the broker rejected the
stop ("opposite side order exists") — and the code logged "stop re-armed" anyway. Result: positions
holding overnight with **no stop**, invisibly.
**Fix (a two-sided terminal-state barrier):** the cash-account rule forbids a resting sell-stop and a
buy on the same symbol at once, so a top-up must sequence *cancel stop → await cancel terminal → IOC
buy → await buy terminal → re-arm stop*. The subtle second-order bug lived in the await itself: it
returned on the *first* transient API read error, re-arming the stop while the buy still read open →
wash-trade reject → naked. Hardened to **poll through transient errors to a deadline** (never re-arm
early) instead of bailing. Layered beneath it: a **final safety sweep at the end of every run** that
arms a stop on any position found naked, regardless of cause — the backstop even if a per-name await is
exhausted. Defense in depth: the sweep once caught 12 naked positions from a single run's collisions.

### 3. Corporate actions vs. stored state (the instant-liquidation bug)
**Failure:** on a stock split, the broker cancels resting stops and adjusts share counts. The
system's stored stop price was on the *pre-split* scale — re-arming a sell-stop at (say) $46 against
a post-split $25 market price would fire instantly and liquidate the position at the worst moment.
**Fix:** corporate-action detection via the value-conservation invariant (share count and average
entry price moving *reciprocally* identifies a split and distinguishes it from ordinary buys/sells),
then rescaling every stored price field by the split ratio before any stop is re-armed. Unit-tested
against forward splits, reverse splits, scale-ins, and partial exits.

### 4. Fill reporting races (phantom no-fills)
**Failure:** immediate-or-cancel orders sometimes report "no fill" under API lag when they *did*
fill — creating untracked positions (naked, unmanaged) and double-entry risk.
**Fix:** treat the **position** (broker truth), not the order report, as the source of fill quantity;
poll position deltas after every order; reconcile state to broker truth at every checkpoint.

### 5. Stale-data trading guards
**Failure class:** scoring on stale features, or executing entries against a data glitch.
**Fixes:** staleness gates (refuse to trade if engineered data lags), a data-sanity guard that
excludes names whose open price deviates implausibly from the scored reference, and holiday-calendar
guards on every scheduled task.

### 6. Scheduler resilience
**Failure:** a 12-hour weekend data job killed at hour 12 by a session logoff (Windows interactive
task constraint), losing the run.
**Fix:** block-resumable design — work divided into ~100-ticker blocks, each a fresh subprocess with
retry; a killed run resumes from the last completed block on the next trigger. A weekly full-universe
refresh became tolerant of arbitrary interruption.

## Design principles that fell out of this

1. **Broker state is the only truth.** Local state is a cache; reconcile every checkpoint.
2. **Every checkpoint ends with an invariant sweep** ("no position leaves this run unprotected") —
   catch-all safety nets beat perfect happy paths.
3. **Log what happened, not what was attempted.** Half these bugs hid behind optimistic logging.
4. **Fail toward protection.** When a fill is ambiguous, assume held and arm the stop; when data is
   stale, don't trade.
5. **Everything scheduled must be resumable and holiday-aware.** Cron is easy; recovery is the work.

## Monitoring layer

- **Weekly holdings thesis report** (auto-generated): per-position P&L, quality-gate status with
  explained n/a's, multi-model valuation agreement, rule-based "why held / why watch" flags, and a
  portfolio-level read (sector concentration as a macro-factor warning, deterioration roster,
  names approaching targets).
- **Daily signal/trade logs** as the forensic record; every execution anomaly above was diagnosed
  from them after the fact — observability is what made the fixes possible.

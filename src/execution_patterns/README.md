# Execution Patterns

The half of a live trading system that no backtest teaches you. These are the ordering and
recovery patterns I converged on after each failure class actually bit me — written against a tiny
abstract `Broker` interface, so there's no vendor SDK, no credentials, no account details, just the
mechanics.

Four patterns, four war stories:

- **`await_terminal`** — the one-character bug. A naive terminal-state check treats
  `PARTIALLY_FILLED` as done because the string `"filled"` is a substring of it. But a
  partially-filled order still holds its remaining shares, so the next same-symbol order races them.
  Excluding that substring is the entire fix.
- **`cancel_all_and_await`** — awaiting only the order id you're *tracking* isn't enough. If your
  recorded stop id is stale while a real stop rests at the broker, you cancel the real one and wait
  for nothing. Enumerate the symbol's open orders yourself.
- **`reduce_position`** — selling part of a protected position: cancel the stop, wait for it to
  release shares, sell, and on a rejected sell, **don't** book the reduction — re-arm full coverage
  and retry. State must never advance as if a sell happened that didn't.
- **`arm_stop_resilient`** — the never-worse guarantee. A single-shot re-arm can fail for the same
  reason the sell failed, leaving a position *more* naked than before. Retry, then arm whatever qty
  is actually available; never report a stop that doesn't rest.

None of this is glamorous, and all of it is why the difference between "backtest" and "live system"
is mostly execution engineering.

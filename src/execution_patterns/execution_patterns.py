"""Execution patterns for a cash-account trading loop.

Backtests assume fills happen and state stays consistent. A live cash account does neither. These
are the patterns I converged on after each failure class bit me in paper trading against a real
brokerage API. They're written against a small abstract `Broker` interface (below) so there's no
vendor SDK, no keys, no account specifics — just the mechanics.

The war stories, in order:
  - A protective stop and a same-symbol buy can't coexist on a cash account (wash-trade reject),
    so any top-up must sequence cancel -> await terminal -> buy -> await terminal -> re-arm stop.
  - The await had a substring bug: PARTIALLY_FILLED contains the string "filled", so a naive
    terminal-state check returned early while the order still held shares. One character of blast
    radius; overnight-naked positions of consequence.
  - A protective sweep that checked "does this symbol HAVE a stop?" missed positions whose stop
    covered FEWER shares than held (after a partial-fill that was booked as if complete). Coverage
    is a quantity question, not a presence question.
  - Re-arming a stop can fail for the same reason the reducing sell failed (shares still held by a
    pending cancel). A single-shot re-arm on a reject path can leave a position LESS protected than
    it started. The sweep must be never-worse: retry, then fall back to whatever qty is available.
"""
import time
from typing import Protocol, Optional


class Broker(Protocol):
    """Minimal brokerage surface these patterns need. Adapt to any SDK."""
    def get_order(self, order_id: str) -> dict: ...            # -> {"status": str, ...}
    def cancel_order(self, order_id: str) -> None: ...
    def list_open_orders(self, symbol: str) -> list: ...       # -> [{"id","qty","type","side"}]
    def submit_market_sell(self, symbol: str, qty: int) -> Optional[str]: ...   # -> order id | None
    def place_stop(self, symbol: str, qty: int, stop_price: float) -> Optional[str]: ...
    def position_qty_available(self, symbol: str) -> int: ...


_TERMINAL = ("filled", "canceled", "cancelled", "rejected", "expired", "done")


def await_terminal(broker: Broker, order_id: Optional[str], timeout: float = 10.0) -> bool:
    """Block until an order reaches a TRUE terminal state; return whether it did.

    The subtle part: PARTIALLY_FILLED is NOT terminal — it still holds its remaining shares — yet
    the string "filled" is a substring of it. Excluding that is the whole fix. A partially-filled
    or pending-cancel order that we treat as done lets the next same-symbol order race its shares.
    """
    if not order_id:
        return True
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            st = str(broker.get_order(order_id).get("status", "")).lower()
        except Exception:
            time.sleep(0.3)                # transient read error: keep polling, never assume done
            continue
        if "partially_filled" not in st and any(t in st for t in _TERMINAL):
            return True
        time.sleep(0.3)
    return False


def cancel_all_and_await(broker: Broker, symbol: str, extra_id: Optional[str] = None) -> None:
    """Cancel EVERY open order for a symbol and await each to terminal.

    Awaiting only the id you're tracking isn't enough: if your recorded stop id is stale/None while
    a real stop rests at the broker, cancel-by-symbol kills that real stop but nothing waits for it,
    and the follow-up order races the pending cancel to qty_available = 0. So enumerate the symbol's
    open orders yourself and await each one.
    """
    ids = []
    if extra_id:
        _try(broker.cancel_order, extra_id); ids.append(extra_id)
    for o in _safe(broker.list_open_orders, symbol):
        _try(broker.cancel_order, o["id"]); ids.append(o["id"])
    for oid in ids:
        await_terminal(broker, oid)


def reduce_position(broker: Broker, symbol: str, sell_qty: int,
                    stop_id: Optional[str], on_reject_stop_price: float, held_qty: int) -> bool:
    """Sell part of a position that's currently protected by a resting stop.

    Cancel the stop, WAIT for it to release its shares, then place the reducing sell. If the sell
    is rejected, DON'T book the reduction — re-arm a full-qty protective stop and report failure so
    the caller retries next cycle. (Same-side orders, so no post-sell await is needed before the
    runner stop.) Returns True iff the reduction was booked.
    """
    cancel_all_and_await(broker, symbol, extra_id=stop_id)
    if broker.submit_market_sell(symbol, sell_qty) is None:
        arm_stop_resilient(broker, symbol, held_qty, on_reject_stop_price)   # never leave it naked
        return False
    return True


def arm_stop_resilient(broker: Broker, symbol: str, qty: int, stop_price: float):
    """Arm a protective stop with a NEVER-WORSE guarantee.

    A single-shot place can fail because shares are still held by a pending cancel — leaving the
    position more naked than before, which is unacceptable for the last line of defense. Retry
    (the pending cancel releases within seconds), then fall back to arming whatever qty the broker
    reports available. Returns (order_id, armed_qty); (None, 0) means NOTHING rests — caller must
    escalate, never claim a stop exists that doesn't.
    """
    for _ in range(3):
        oid = broker.place_stop(symbol, qty, stop_price)
        if oid:
            return oid, qty
        time.sleep(1.0)
    avail = max(0, broker.position_qty_available(symbol))
    if avail >= 1:
        oid = broker.place_stop(symbol, avail, stop_price)
        if oid:
            return oid, avail
    return None, 0


def _try(fn, *a):
    try: fn(*a)
    except Exception: pass


def _safe(fn, *a):
    try: return list(fn(*a))
    except Exception: return []

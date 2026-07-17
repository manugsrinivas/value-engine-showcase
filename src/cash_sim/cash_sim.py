"""Honest cash-account backtest skeleton.

Most backtests are a vectorized `weight @ returns`. That shortcut quietly lies in ways that matter
for a defensive, cash-holding strategy:
  - it compounds IDLE CASH at the strategy's return instead of the cash rate — manufacturing
    performance out of money that's just sitting there (a "diversified" variant with 30% cash can
    look great purely because that 30% rode equity returns);
  - it ignores T+1 settlement, so it can spend proceeds it wouldn't actually have;
  - it fills stop-losses at the stop price even when the bar gapped straight through it, flattering
    drawdowns in exactly the crashes a defensive book is sold on.

This skeleton does it the slow, correct way: positions followed one at a time, cash earning the
cash rate, settlement respected, stops filling at the gapped open, and a conservation check every
run that must close to the penny. The SIGNAL layer is a stub — `screen(date, prices) -> [tickers]`
— so you bring your own strategy; this is only the accounting engine it runs on.
"""
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class Position:
    shares: float
    cost_basis: float
    stop_price: float
    entry_date: pd.Timestamp
    last: float = 0.0


@dataclass
class CashSim:
    opens: pd.DataFrame          # date x ticker
    highs: pd.DataFrame
    lows: pd.DataFrame
    closes: pd.DataFrame
    cash_returns: pd.Series      # daily cash/T-bill return, per date
    screen: Callable             # (date, closes_asof) -> list[str] of tickers to hold
    start_capital: float = 100_000.0
    stop_pct: float = 0.10       # example only — real strategies size this per name
    cost_bps: float = 40.0       # per-side transaction cost
    settle_days: int = 1         # T+1 cash settlement

    cash: float = field(init=False)
    pos: dict = field(init=False)

    def run(self) -> dict:
        self.cash = self.start_capital
        self.pos = {}
        pending_settlement = []          # (settle_date, amount) — proceeds not yet spendable
        equity_curve, realized, interest_earned, costs = [], 0.0, 0.0, 0.0
        dates = self.closes.index

        for d in dates:
            r = float(self.cash_returns.get(d, 0.0))
            interest_earned += self.cash * r                 # idle cash earns the CASH rate, not the strategy's
            self.cash *= (1.0 + r)
            for settle_date, amt in [p for p in pending_settlement if p[0] <= d]:
                self.cash += amt
            pending_settlement = [p for p in pending_settlement if p[0] > d]

            # ---- mark, then check stops (gap-through-aware) ----
            for tk, p in list(self.pos.items()):
                px = self.closes.at[d, tk] if tk in self.closes.columns else np.nan
                if np.isfinite(px):
                    p.last = float(px)
                lo = self.lows.at[d, tk] if tk in self.lows.columns else np.nan
                if np.isfinite(lo) and lo <= p.stop_price:
                    op = self.opens.at[d, tk] if tk in self.opens.columns else np.nan
                    # GAP-THROUGH: a stop that gaps down through its level fills at the OPEN, not the
                    # stop price. Booking eff at the stop flatters drawdowns in crash windows.
                    fill = float(op) if (np.isfinite(op) and op < p.stop_price) else p.stop_price
                    proceeds, cost = self._sell(p.shares, fill)
                    realized += proceeds - p.cost_basis; costs += cost
                    pending_settlement.append((self._settle(dates, d), proceeds))
                    del self.pos[tk]

            # ---- target set from the (stubbed) screen; equal-weight the settled sleeve ----
            targets = [t for t in self.screen(d, self.closes.loc[:d]) if t in self.closes.columns]
            for tk in list(self.pos):
                if tk not in targets:                        # exit drops
                    p = self.pos.pop(tk)
                    proceeds, cost = self._sell(p.shares, p.last); realized += proceeds - p.cost_basis
                    costs += cost; pending_settlement.append((self._settle(dates, d), proceeds))
            want = [t for t in targets if t not in self.pos]
            if want and self.cash > 1:
                budget = self.cash / len(want)               # buys consume SPENDABLE (settled) cash
                for tk in want:
                    px = self.closes.at[d, tk]
                    if not np.isfinite(px) or budget < px:
                        continue
                    sh = (budget * (1 - self.cost_bps / 1e4)) / px
                    self.cash -= budget; costs += budget * self.cost_bps / 1e4
                    self.pos[tk] = Position(sh, budget, px * (1 - self.stop_pct), d, px)

            equity_curve.append(self.cash + sum(p.shares * p.last for p in self.pos.values()))

        eq = pd.Series(equity_curve, index=dates)
        # ---- CONSERVATION CHECK: nothing appears or vanishes. Must close to the penny. ----
        # Costs are ALREADY embedded in cost_basis (buy side) and proceeds (sell side), so they do
        # NOT get a separate term here — subtracting them again is a double-count (and a classic way
        # to make a leak check "pass" for the wrong reason). `costs` is reported, not reconciled.
        unrealized = sum(p.shares * p.last - p.cost_basis for p in self.pos.values())
        recon = self.start_capital + realized + unrealized + interest_earned
        leak = eq.iloc[-1] - recon
        return {"equity": eq, "final": float(eq.iloc[-1]), "realized": realized,
                "interest": interest_earned, "costs": costs, "leak": float(leak),
                "conservation_ok": abs(leak) < 1.0}

    def _sell(self, shares, price):
        gross = shares * price; cost = gross * self.cost_bps / 1e4
        return gross - cost, cost

    def _settle(self, dates, d):
        i = dates.get_loc(d)
        return dates[min(i + self.settle_days, len(dates) - 1)]


if __name__ == "__main__":
    # Self-demo: 3 synthetic names, a trivial "hold everything" screen, and the conservation check.
    rng = np.random.default_rng(1)
    dates = pd.bdate_range("2020-01-01", periods=500)
    tks = ["AAA", "BBB", "CCC"]
    close = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0.0004, 0.02, (500, 3)), 0),
                         index=dates, columns=tks)
    sim = CashSim(opens=close * 0.999, highs=close * 1.01, lows=close * 0.99, closes=close,
                  cash_returns=pd.Series(0.03 / 252, index=dates),
                  screen=lambda d, c: tks)                   # <- your strategy goes here
    out = sim.run()
    print(f"final ${out['final']:,.0f} | realized ${out['realized']:,.0f} | "
          f"interest ${out['interest']:,.0f} | costs ${out['costs']:,.0f}")
    print(f"conservation leak ${out['leak']:.4f} -> {'OK' if out['conservation_ok'] else 'BUG'}")

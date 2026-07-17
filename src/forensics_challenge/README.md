# Backtest Audit Challenge

Most people show what their code does when it works. This shows whether I can find what's *wrong*
with a backtest — including my own.

`make_challenge.py` generates a small backtest project (`toy-strat/`) whose README quotes headline
returns. **Four of those numbers are wrong**, each a bug class I actually hit in real research and
had to catch before it reached a decision: a Sharpe on the wrong risk-free basis, a lot ledger that
claims more profit than the account ever made, one impossible bar in a "background" price series
that compounds into fake return, and an evaluation window that runs past the data's coverage.

Try it:
```
python make_challenge.py      # writes ./toy-strat/  (with a README that makes the claims)
# now audit ./toy-strat/ — find the four wrong numbers using identities + a basis audit
```
Solutions in [SOLUTIONS.md](SOLUTIONS.md) — after you've tried.

The point isn't the toy strategy; it's that none of these bugs are visible in the headline numbers.
Each is caught only by an accounting identity or a measurement-basis check — the habit of treating a
number as guilty until it survives independent scrutiny. I built this because a research process is
only as trustworthy as its ability to catch its own mistakes.

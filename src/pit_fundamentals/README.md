# Point-in-Time Fundamentals

The one rule that keeps a fundamental backtest honest: **a value is knowable only on the date it
was filed, never the period it describes.** Q4 numbers dated December don't become public until
February. Index your data by filing date and look-ahead bias is structurally impossible; index by
period date and every backtest silently cheats.

This module shows the mechanics — parsing SEC XBRL companyfacts by filing date, building
trailing-twelve-month sums point-in-time (flows are summed; balance-sheet levels are taken as the
latest point — mixing them up is a quiet, common error), and the standard distress/quality
**formulas** a value screen uses: Sloan accruals, Altman Z″, Merton distance-to-default.

The formulas are textbook and public. What a real strategy keeps private are the *thresholds*
applied to them — those live in config, not in code like this. SEC companyfacts is free and keyless
(it only asks for a descriptive User-Agent); set your own contact string at the top of the file.

```
python pit_fundamentals.py     # formula sanity checks, no network needed
```

The `asof()` helper is the whole philosophy in three lines: `filed + lag <= as_of`. If a value
can't pass that test, the model never saw it.

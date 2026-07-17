"""Anti-overfitting statistics for strategy research.

Three tools I run before believing any backtest result:

1. CSCV / PBO (Bailey, Borwein, Lopez de Prado, Zhu) — Probability of Backtest Overfitting:
   split the return matrix of N candidate configs into C(S, S/2) train/test combinations; PBO is
   the fraction of combinations where the in-sample winner lands in the out-of-sample bottom half.
   High PBO = your config ranking is noise, whatever the full-sample stats say.

2. Deflated Sharpe Ratio (Bailey & Lopez de Prado) — the probability that a Sharpe is positive
   after correcting for how many things you tried, non-normality, and track length. A great
   Sharpe found after 100 trials usually isn't.

3. Cluster-robust event inference — event studies (insider buys, analyst revisions, filings)
   have correlated observations: many events share a name or a date. Pooled t-stats overstate
   significance wildly (I watched a pooled t = +4.5 collapse to +0.4 under clustering — the
   signal died honestly). One-way cluster-robust standard errors on event returns.

All plain numpy/pandas; no strategy content. Self-demo at the bottom.
"""
import itertools

import numpy as np
import pandas as pd


def pbo_cscv(returns_matrix: pd.DataFrame, n_splits: int = 16):
    """CSCV Probability of Backtest Overfitting.

    returns_matrix: T x N (rows = periods, columns = candidate configs).
    n_splits: S — the matrix is cut into S contiguous blocks; all C(S, S/2) train/test
    partitions are evaluated. Returns dict with pbo and the logit distribution.
    """
    R = returns_matrix.dropna()
    blocks = np.array_split(np.arange(len(R)), n_splits)
    half = n_splits // 2
    logits = []
    for train_ids in itertools.combinations(range(n_splits), half):
        tr = np.concatenate([blocks[i] for i in train_ids])
        te = np.concatenate([blocks[i] for i in range(n_splits) if i not in train_ids])
        sr_tr = R.iloc[tr].mean() / R.iloc[tr].std()
        sr_te = R.iloc[te].mean() / R.iloc[te].std()
        best = sr_tr.idxmax()
        # out-of-sample RELATIVE rank of the in-sample winner, mapped to a logit
        w = (sr_te.rank().loc[best] - 1) / (len(sr_te) - 1) if len(sr_te) > 1 else 0.5
        w = min(max(w, 1e-6), 1 - 1e-6)
        logits.append(np.log(w / (1 - w)))
    logits = np.array(logits)
    return {"pbo": float((logits <= 0).mean()), "n_combinations": len(logits),
            "median_oos_logit": float(np.median(logits))}


def deflated_sharpe(observed_sr: float, n_trials: int, T: int,
                    skew: float = 0.0, kurt: float = 3.0, sr_std_across_trials: float = None):
    """Deflated Sharpe Ratio: P(true SR > 0 | multiple testing, non-normal returns, length T).

    observed_sr: per-period Sharpe of the SELECTED strategy (not annualized).
    n_trials: how many configs were effectively tried to find it (be honest).
    sr_std_across_trials: std of per-period SRs across trials (default: |observed|/2 heuristic —
    supply the real value when you have it).
    """
    from scipy.stats import norm
    s = sr_std_across_trials if sr_std_across_trials is not None else abs(observed_sr) / 2 or 1e-9
    emc = 0.5772156649
    # expected max SR under the null across n_trials (Bailey & Lopez de Prado approximation)
    sr0 = s * ((1 - emc) * norm.ppf(1 - 1 / n_trials) + emc * norm.ppf(1 - 1 / (n_trials * np.e)))
    num = (observed_sr - sr0) * np.sqrt(T - 1)
    den = np.sqrt(1 - skew * observed_sr + (kurt - 1) / 4 * observed_sr ** 2)
    return {"dsr": float(norm.cdf(num / den)), "expected_max_null_sr": float(sr0)}


def cluster_robust_t(event_returns: pd.Series, clusters: pd.Series):
    """One-way cluster-robust t-stat for the mean of event returns.

    event_returns: one forward return per event. clusters: cluster label per event
    (e.g. ticker, or event date). Run once per clustering dimension; trust the WORST t.
    """
    df = pd.DataFrame({"r": event_returns.values, "c": clusters.values}).dropna()
    mu = df["r"].mean()
    resid = df["r"] - mu
    # CRVE: sum within-cluster residuals, then sum of squares across clusters
    s = resid.groupby(df["c"]).sum()
    G, n = len(s), len(df)
    var_mu = (s ** 2).sum() / n ** 2 * G / (G - 1)
    return {"mean": float(mu), "t_cluster": float(mu / np.sqrt(var_mu)),
            "t_pooled_naive": float(mu / (df['r'].std() / np.sqrt(n))),
            "n_events": n, "n_clusters": G}


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    # PBO demo: 30 configs of pure noise — expect PBO near 0.5 (ranking is meaningless)
    noise = pd.DataFrame(rng.normal(0, 0.01, (1000, 30)))
    print("PBO on pure noise (expect ~0.5):", pbo_cscv(noise)["pbo"])
    # DSR demo: the best of 100 noise trials looks great, deflates to nothing
    best_sr = max(rng.normal(0, 0.01, (252, 1)).mean() / 0.01 for _ in range(100))
    print("DSR of best-of-100 noise:", round(deflated_sharpe(0.1, 100, 252)["dsr"], 3))
    # Clustering demo: 500 'events' on 10 tickers with a shared ticker effect
    tick = rng.integers(0, 10, 500)
    r = rng.normal(0, 0.02, 10)[tick] + rng.normal(0.001, 0.01, 500)
    out = cluster_robust_t(pd.Series(r), pd.Series(tick))
    print(f"pooled t {out['t_pooled_naive']:.1f} vs cluster-robust t {out['t_cluster']:.1f} "
          f"(the honest one)")

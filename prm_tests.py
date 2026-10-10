"""Fünf Zwei-Gruppen-Verfahren für viele Experimente zugleich (Form (R, n) je Arm): Welch, Mann-Whitney, Permutationstest der
Mittelwertdifferenz, Bootstrap-Perzentil-Intervall und Welch auf winsorisierten Werten. Zufall über SplitMix64 (`uniform_block`),
damit jede Zahl auf jeder Plattform gleich ist."""

import numpy as np
from scipy.special import ndtr
from scipy.stats import rankdata

from prm_rng import uniform_block
from prm_stats import welch_batch

METHODS = ("welch", "mw", "perm", "boot", "wins")
METHOD_LABELS = {"welch": "Welch-t-Test", "mw": "Mann-Whitney", "perm": "Permutationstest (Mittelwert)",
                 "boot": "Bootstrap (Perzentil-Intervall)", "wins": "Welch nach Winsorisieren"}
METHOD_SHORT = {"welch": "Welch", "mw": "Mann-Whitney", "perm": "Permutation", "boot": "Bootstrap", "wins": "Winsorisiert"}


def mann_whitney_batch(a, b):
    """Mann-Whitney-U-Test (zweiseitig, Normalnäherung mit Bindungskorrektur und Stetigkeitskorrektur) je Zeile.
    Rückgabe: p-Werte (R,). Identisch zu scipy.stats.mannwhitneyu(method='asymptotic')."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n1, n2 = a.shape[1], b.shape[1]
    n = n1 + n2
    both = np.concatenate([a, b], axis=1)
    ranks = rankdata(both, axis=1, method="average")
    r1 = ranks[:, :n1].sum(axis=1)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    srt = np.sort(both, axis=1)
    # Bindungsgruppen: Längen der Läufe gleicher Werte je Zeile
    tie_term = np.zeros(len(both))
    for i in range(len(both)):
        _, counts = np.unique(srt[i], return_counts=True)
        tie_term[i] = (counts**3 - counts).sum()
    sigma2 = n1 * n2 / 12.0 * ((n + 1) - tie_term / (n * (n - 1)))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (np.abs(u1 - mu) - 0.5) / np.sqrt(sigma2)
    z = np.where(sigma2 > 0, np.maximum(z, 0.0), 0.0)
    return np.minimum(2 * (1 - ndtr(z)), 1.0)


def permutation_batch(a, b, perms, seed, chunk=40):
    """Permutationstest der Mittelwertdifferenz (zweiseitig) mit `perms` zufälligen Umordnungen je Zeile. p = (1 + #(|d*| >=
    |d|)) / (perms + 1). Rückgabe: p-Werte (R,)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    r, n1 = a.shape
    n2 = b.shape[1]
    both = np.concatenate([a, b], axis=1)
    obs = np.abs(b.mean(axis=1) - a.mean(axis=1))
    p = np.empty(r)
    for start in range(0, r, chunk):
        sl = slice(start, min(start + chunk, r))
        x = both[sl]
        m = x.shape[0]
        u = uniform_block(seed + 104_729 * start, m * perms * (n1 + n2)).reshape(m, perms, n1 + n2)
        order = np.argsort(u, axis=2)
        perm_vals = np.take_along_axis(np.broadcast_to(x[:, None, :], u.shape), order, axis=2)
        d = np.abs(perm_vals[:, :, n1:].mean(axis=2) - perm_vals[:, :, :n1].mean(axis=2))
        p[sl] = (1 + (d >= obs[sl, None] - 1e-15).sum(axis=1)) / (perms + 1)
    return p


def bootstrap_batch(a, b, resamples, seed, conf=0.95, chunk=40):
    """Perzentil-Bootstrap-Intervall der Mittelwertdifferenz B minus A je Zeile (Arme getrennt gezogen).
    Rückgabe: (lo, hi) je (R,)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    r, n1 = a.shape
    n2 = b.shape[1]
    lo = np.empty(r)
    hi = np.empty(r)
    q = (1 - conf) / 2
    for start in range(0, r, chunk):
        sl = slice(start, min(start + chunk, r))
        m = a[sl].shape[0]
        ia = np.minimum((uniform_block(seed + 7_919 * start, m * resamples * n1).reshape(m, resamples, n1) * n1).astype(np.int64), n1 - 1)
        ib = np.minimum((uniform_block(seed + 7_919 * start + 3, m * resamples * n2).reshape(m, resamples, n2) * n2).astype(np.int64),
                        n2 - 1)
        ma = np.take_along_axis(a[sl][:, None, :].repeat(resamples, axis=1), ia, axis=2).mean(axis=2)
        mb = np.take_along_axis(b[sl][:, None, :].repeat(resamples, axis=1), ib, axis=2).mean(axis=2)
        d = mb - ma
        lo[sl] = np.quantile(d, q, axis=1)
        hi[sl] = np.quantile(d, 1 - q, axis=1)
    return lo, hi


def winsorize_lower(a, b, share=0.05):
    """Setzt in jedem Experiment die Werte unter dem `share`-Quantil der gemeinsamen Stichprobe auf dieses Quantil (untere
    Ausreißer; die Kennzahl ist nach oben durch 100 % begrenzt)."""
    both = np.concatenate([a, b], axis=1)
    q = np.quantile(both, share, axis=1, keepdims=True)
    return np.maximum(a, q), np.maximum(b, q)


def run_all(a, b, perms=399, boots=399, seed=0, methods=METHODS):
    """Die gewählten Verfahren auf (R, n)-Arrays. Rückgabe: {Verfahren: {"p": (R,), "diff": (R,), "lo": (R,) oder None, "hi": ...}}.
    Ein Verfahren findet einen Unterschied bei p < 0,05 (Bootstrap: bei einem Intervall, das 0 nicht enthält)."""
    w = welch_batch(a, b)
    out = {}
    if "welch" in methods:
        out["welch"] = {"p": w["p"], "diff": w["diff"], "lo": w["lo"], "hi": w["hi"]}
    if "mw" in methods:
        out["mw"] = {"p": mann_whitney_batch(a, b), "diff": w["diff"], "lo": None, "hi": None}
    if "perm" in methods:
        out["perm"] = {"p": permutation_batch(a, b, perms, seed), "diff": w["diff"], "lo": None, "hi": None}
    if "boot" in methods:
        lo, hi = bootstrap_batch(a, b, boots, seed + 11)
        out["boot"] = {"p": np.where((lo > 0) | (hi < 0), 0.0, 1.0), "diff": w["diff"], "lo": lo, "hi": hi}
    if "wins" in methods:
        wa, wb = winsorize_lower(a, b)
        ww = welch_batch(wa, wb)
        out["wins"] = {"p": ww["p"], "diff": w["diff"], "lo": ww["lo"], "hi": ww["hi"]}
    return out

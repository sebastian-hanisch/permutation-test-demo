"""Auswertung: fünf Verfahren auf schiefen Daten mit und ohne Ausreißer.

Wie in den Vorgängerstücken sind die Pools (je 10 000 simulierte Standort-Fenster je Sicherheitsfaktor, SplitMix64) die
Wahrheit. Neu: ein Anteil q der Fenster ist gestört (Lieferstörung: der Servicegrad liegt gleichverteilt zwischen 20 und
70 %), unabhängig von der Regel. Die gestörten Fenster verkleinern die mittlere Wirkung auf (1 - q) mal die saubere Wirkung."""

import json
from pathlib import Path

import numpy as np

import prm_constants as C
import prm_tests as T
from prm_rng import uniform_block

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_pools.json"


def load_pools(path=PRECOMPUTED):
    """{z: Array der Fenster-Servicegrade}; z auf eine Nachkommastelle gerundet."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): np.asarray(v, dtype=float) for k, v in data["pools"].items()}


def nearest_z(z):
    return min(C.Z_GRID, key=lambda g: abs(g - z))


def clean_effect(pools, z_b):
    """Wirkung ohne Störungen (Mittel der Pools, B minus A)."""
    return float(pools[nearest_z(z_b)].mean() - pools[nearest_z(C.Z_A)].mean())


def true_effect(pools, z_b, out_pct):
    """Wahre mittlere Wirkung bei einem Anteil gestörter Fenster: (1 - q) mal die saubere Wirkung, weil die Störungen in
    beiden Armen denselben Mittelwert haben."""
    return clean_effect(pools, z_b) * (1.0 - out_pct / 100.0)


def _indices(pool_size, count, seed):
    return np.minimum((uniform_block(seed, count) * pool_size).astype(np.int64), pool_size - 1)


def draw(pools, z_b, n, out_pct, reps, seed):
    """`reps` Experimente: n Fenster je Arm aus den Pools, danach wird jedes Fenster mit Wahrscheinlichkeit q durch eine
    Störung ersetzt. Rückgabe: a, b (Form (reps, n)) und die Störungsmasken."""
    pa, pb = pools[nearest_z(C.Z_A)], pools[nearest_z(z_b)]
    count = reps * n
    a = pa[_indices(len(pa), count, seed).reshape(reps, n)]
    b = pb[_indices(len(pb), count, seed + 1).reshape(reps, n)]
    q = out_pct / 100.0
    if q > 0:
        ma = uniform_block(seed + 2, count).reshape(reps, n) < q
        mb = uniform_block(seed + 3, count).reshape(reps, n) < q
        va = C.OUTLIER_LOW + (C.OUTLIER_HIGH - C.OUTLIER_LOW) * uniform_block(seed + 4, count).reshape(reps, n)
        vb = C.OUTLIER_LOW + (C.OUTLIER_HIGH - C.OUTLIER_LOW) * uniform_block(seed + 5, count).reshape(reps, n)
        a, b = np.where(ma, va, a), np.where(mb, vb, b)
    else:
        ma = mb = np.zeros((reps, n), dtype=bool)
    return a, b, ma, mb


def experiment_seed(z, n, out, tag=0):
    return 23_000_000 + 10_007 * int(round(z * 10)) + 131 * n + 17 * int(out) + 13 * tag


def summarize(pools, z_b, n, out_pct, reps=C.LIVE_REPS, tag=0, alpha=C.ALPHA, methods=T.METHODS):
    """Viele Experimente: je Verfahren Anteil mit Befund (ohne Wirkung der Fehlalarm), Abdeckung des Intervalls (Welch und
    Bootstrap) und mittlere Intervallbreite."""
    z_b = nearest_z(z_b)
    seed = experiment_seed(z_b, n, out_pct, tag)
    a, b, ma, mb = draw(pools, z_b, n, out_pct, reps, seed)
    res = T.run_all(a, b, C.PERMUTATIONS, C.BOOTSTRAPS, seed + 99, methods)
    truth = true_effect(pools, z_b, out_pct)
    rows = {}
    for m in methods:
        r = res[m]
        found = r["p"] < alpha
        row = {"reject": float(found.mean())}
        if r["lo"] is not None:
            row["coverage"] = float(((r["lo"] <= truth) & (truth <= r["hi"])).mean())
            row["width"] = float((r["hi"] - r["lo"]).mean())
        rows[m] = row
    return {"z": z_b, "n": n, "out": out_pct, "reps": reps, "truth": truth, "clean": clean_effect(pools, z_b), "rows": rows,
            "outlier_share": float(np.concatenate([ma, mb], axis=1).mean())}


def run_one(pools, settings):
    """Das eine Experiment der Seitenleiste mit allen Verfahren und der Permutationsverteilung."""
    seed = 1_000_003 * (settings["seed"] + 1) + 5
    a, b, ma, mb = draw(pools, settings["z"], settings["n"], settings["out"], 1, seed)
    res = T.run_all(a, b, C.PERMUTATIONS, C.BOOTSTRAPS, seed + 99)
    both = np.concatenate([a, b], axis=1)[0]
    n = settings["n"]
    u = uniform_block(seed + 7, C.PERMUTATIONS * 2 * n).reshape(C.PERMUTATIONS, 2 * n)
    order = np.argsort(u, axis=1)
    perm = both[order]
    null_d = perm[:, n:].mean(axis=1) - perm[:, :n].mean(axis=1)
    return {"a": a[0], "b": b[0], "out_a": ma[0], "out_b": mb[0], "null_diffs": null_d,
            "observed": float(b[0].mean() - a[0].mean()),
            "methods": {m: {k: (float(v[0]) if v is not None else None) for k, v in res[m].items()} for m in T.METHODS},
            "truth": true_effect(pools, settings["z"], settings["out"])}

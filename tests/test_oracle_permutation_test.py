"""Orakel-Tests: der Kern gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2).

1. Mann-Whitney gegen scipy.stats.mannwhitneyu (mit Bindungen).
2. Permutationstest gegen die exakte Aufzählung aller Umordnungen (scipy).
3. Welch gegen scipy.stats.ttest_ind.
4. Niveau aller Verfahren auf Normaldaten (5 %), Bootstrap-Abdeckung gegen scipy.stats.bootstrap-Größenordnung.
5. Wirkung gestörter Fenster auf den Mittelwert: (1 - q) mal die saubere Wirkung (Simulation gegen Formel)."""

import itertools

import numpy as np
import pytest
from scipy import stats

import prm_evaluation as E
import prm_tests as T


def test_mann_whitney_equals_scipy():
    rng = np.random.default_rng(31)
    for _ in range(20):
        a, b = np.round(rng.normal(0, 1, (1, 18)), 1), np.round(rng.normal(0.4, 1.3, (1, 22)), 1)
        ref = stats.mannwhitneyu(a[0], b[0], method="asymptotic", use_continuity=True)
        assert float(T.mann_whitney_batch(a, b)[0]) == pytest.approx(ref.pvalue, rel=1e-9, abs=1e-12)


def _exact_permutation_p(a, b):
    """Unabhängiger Weg: Aufzählung aller Zuordnungen (itertools), p = Anteil mit |d*| >= |d| (zweiseitig, Betrag)."""
    both = np.concatenate([a, b])
    n1 = len(a)
    obs = abs(b.mean() - a.mean())
    count = total = 0
    for idx in itertools.combinations(range(len(both)), n1):
        mask = np.zeros(len(both), dtype=bool)
        mask[list(idx)] = True
        d = abs(both[~mask].mean() - both[mask].mean())
        count += d >= obs - 1e-12
        total += 1
    return count / total


def test_permutation_equals_exact_enumeration_within_monte_carlo_error():
    rng = np.random.default_rng(32)
    for _ in range(4):
        a, b = rng.exponential(1.0, (1, 6)), rng.exponential(1.0, (1, 5)) + 0.6
        exact = _exact_permutation_p(a[0], b[0])
        assert float(T.permutation_batch(a, b, 4999, seed=9)[0]) == pytest.approx(exact, abs=0.025)


def test_welch_equals_scipy():
    rng = np.random.default_rng(33)
    a, b = rng.normal(0, 1, (5, 17)), rng.normal(0.3, 2, (5, 23))
    w = T.welch_batch(a, b)
    for i in range(5):
        ref = stats.ttest_ind(b[i], a[i], equal_var=False)
        assert w["p"][i] == pytest.approx(ref.pvalue, rel=1e-9)


def test_all_methods_keep_the_level_on_normal_data():
    rng = np.random.default_rng(34)
    a, b = rng.normal(0, 1, (700, 25)), rng.normal(0, 1, (700, 25))
    res = T.run_all(a, b, perms=199, boots=199, seed=2)
    for m in ("welch", "mw", "perm", "wins"):
        assert float((res[m]["p"] < 0.05).mean()) == pytest.approx(0.05, abs=0.025), m
    assert float((res["boot"]["p"] < 0.05).mean()) < 0.10


def test_disturbed_windows_shrink_the_mean_effect_by_one_minus_q(pools):
    for q in (5, 10):
        a, b, _ma, _mb = E.draw(pools, 1.4, 50, q, 4000, 77)
        measured = float((b.mean(axis=1) - a.mean(axis=1)).mean())
        assert measured == pytest.approx(E.true_effect(pools, 1.4, q), abs=0.0012)

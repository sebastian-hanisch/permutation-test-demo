"""Die fünf Verfahren: Handrechnung, Gegenproben gegen scipy, Eigenschaften."""

import numpy as np
import pytest
from scipy import stats

import prm_tests as T


def test_mann_whitney_by_hand_without_ties():
    # A = [1, 2, 3], B = [4, 5, 6]: Rangsumme B = 15, U_B = 15 - 6 = 9, mu = 4,5, sigma^2 = 3*3*7/12 = 5,25
    # z = (|9 - 4,5| - 0,5) / sqrt(5,25) = 4 / 2,2913 = 1,7457, p = 2 (1 - Phi(1,7457)) = 0,0809
    p = T.mann_whitney_batch(np.array([[1.0, 2.0, 3.0]]), np.array([[4.0, 5.0, 6.0]]))
    assert float(p[0]) == pytest.approx(0.0809, abs=1e-3)


def test_mann_whitney_equals_scipy_with_ties():
    rng = np.random.default_rng(1)
    for _ in range(25):
        a = np.round(rng.normal(0.9, 0.04, (1, 20)), 2).clip(max=0.97)
        b = np.round(rng.normal(0.92, 0.05, (1, 24)), 2).clip(max=0.97)    # viele Bindungen am Rand
        ref = stats.mannwhitneyu(a[0], b[0], alternative="two-sided", method="asymptotic", use_continuity=True)
        assert float(T.mann_whitney_batch(a, b)[0]) == pytest.approx(ref.pvalue, rel=1e-9, abs=1e-12)


def test_permutation_test_matches_the_exact_enumeration():
    """Gegenprobe: scipy zählt alle Umordnungen exakt (n = 5 je Arm: 252 Möglichkeiten), der zufällige Test nähert das an."""
    rng = np.random.default_rng(2)
    for _ in range(6):
        a, b = rng.normal(0, 1, (1, 5)), rng.normal(0.8, 1, (1, 5))
        exact = stats.permutation_test((b[0], a[0]), lambda x, y: np.mean(x) - np.mean(y), permutation_type="independent",
                                       n_resamples=np.inf, alternative="two-sided").pvalue
        mc = float(T.permutation_batch(a, b, 3999, seed=17)[0])
        assert mc == pytest.approx(exact, abs=0.03)


def test_permutation_p_value_is_one_under_identical_samples_and_small_for_a_clear_shift():
    a = np.tile(np.linspace(0.9, 0.95, 12), (1, 1))
    assert float(T.permutation_batch(a, a.copy(), 199, seed=1)[0]) == pytest.approx(1.0)
    assert float(T.permutation_batch(a, a + 0.2, 499, seed=1)[0]) < 0.01


def test_bootstrap_interval_is_close_to_the_normal_interval_on_normal_data():
    rng = np.random.default_rng(3)
    a, b = rng.normal(0, 1, (40, 60)), rng.normal(0.3, 1, (40, 60))
    lo, hi = T.bootstrap_batch(a, b, 499, seed=5)
    w = T.welch_batch(a, b)
    ratio = (hi - lo).mean() / (w["hi"] - w["lo"]).mean()
    assert ratio == pytest.approx(1.0, abs=0.06)
    assert np.all(lo < hi)
    assert np.mean((lo <= w["diff"]) & (w["diff"] <= hi)) == 1.0


def test_winsorize_lower_by_hand():
    a = np.array([[0.2, 0.9, 0.9, 0.9]])
    b = np.array([[0.9, 0.9, 0.9, 0.9]])
    # gemeinsame Stichprobe: ein Wert 0,2, sieben Werte 0,9; das 5-%-Quantil liegt bei 0,2 + 0,35 * 0,7 = 0,445
    wa, wb = T.winsorize_lower(a, b, 0.05)
    q = float(np.quantile(np.concatenate([a, b], axis=1), 0.05))
    assert q == pytest.approx(0.2 + 0.7 * 0.35, abs=1e-9)
    assert wa[0, 0] == pytest.approx(q)
    assert np.array_equal(wb, b)


def test_run_all_returns_every_method_and_respects_the_selection():
    rng = np.random.default_rng(4)
    a, b = rng.normal(0.9, 0.04, (6, 15)), rng.normal(0.93, 0.04, (6, 15))
    res = T.run_all(a, b, perms=99, boots=99, seed=1)
    assert set(res) == set(T.METHODS)
    sub = T.run_all(a, b, perms=99, boots=99, seed=1, methods=("welch", "mw"))
    assert set(sub) == {"welch", "mw"}
    assert np.array_equal(sub["welch"]["p"], res["welch"]["p"])


def test_results_are_deterministic():
    rng = np.random.default_rng(5)
    a, b = rng.normal(0.9, 0.04, (5, 12)), rng.normal(0.92, 0.04, (5, 12))
    r1 = T.run_all(a, b, 99, 99, seed=3)
    r2 = T.run_all(a, b, 99, 99, seed=3)
    for m in T.METHODS:
        assert np.array_equal(r1[m]["p"], r2[m]["p"])

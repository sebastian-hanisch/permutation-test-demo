"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Funktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Pools und -Ziehungen); die Bänder sind Rundungs- und Plattformreserve."""

import pytest

import prm_evaluation as E

REPS = 1500


def pct(x):
    return 100 * x


def rate(pools, z, n, out, method):
    return pct(E.summarize(pools, z, n, out, reps=REPS)["rows"][method]["reject"])


def test_clean_data_every_method_keeps_the_level_except_the_bootstrap(pools):
    s = E.summarize(pools, 1.0, 30, 0, reps=REPS)["rows"]
    for m, value in (("welch", 4.7), ("mw", 4.4), ("perm", 4.6), ("wins", 5.0)):
        assert pct(s[m]["reject"]) == pytest.approx(value, abs=1.2), m
    assert pct(s["boot"]["reject"]) == pytest.approx(6.1, abs=1.4)
    s10 = E.summarize(pools, 1.0, 10, 0, reps=REPS)["rows"]
    assert pct(s10["boot"]["reject"]) == pytest.approx(7.4, abs=1.4)
    assert pct(s10["welch"]["reject"]) == pytest.approx(3.7, abs=1.3)


def test_clean_data_power_is_about_the_same_for_all(pools):
    s = E.summarize(pools, 1.4, 30, 0, reps=REPS)["rows"]
    assert pct(s["welch"]["reject"]) == pytest.approx(84.5, abs=2.2)
    assert pct(s["perm"]["reject"]) == pytest.approx(83.9, abs=2.2)
    assert pct(s["mw"]["reject"]) == pytest.approx(84.9, abs=2.2)
    s10 = E.summarize(pools, 1.4, 10, 0, reps=REPS)["rows"]
    assert pct(s10["welch"]["reject"]) == pytest.approx(37.3, abs=2.5)
    assert pct(s10["mw"]["reject"]) == pytest.approx(35.1, abs=2.5)


def test_bootstrap_interval_is_too_narrow_with_little_data(pools):
    s = E.summarize(pools, 1.4, 10, 0, reps=REPS)["rows"]
    assert pct(s["welch"]["coverage"]) == pytest.approx(96.0, abs=1.5)
    assert pct(s["boot"]["coverage"]) == pytest.approx(91.9, abs=1.8)
    assert s["boot"]["width"] < s["welch"]["width"]


def test_five_percent_disturbed_windows_collapse_the_t_test(pools):
    s = E.summarize(pools, 1.4, 30, 5, reps=REPS)
    assert pct(s["clean"]) == pytest.approx(3.49, abs=0.06)
    assert pct(s["truth"]) == pytest.approx(3.32, abs=0.06)
    r = s["rows"]
    assert pct(r["welch"]["reject"]) == pytest.approx(25.4, abs=2.5)
    assert pct(r["perm"]["reject"]) == pytest.approx(27.4, abs=2.5)
    assert pct(r["boot"]["reject"]) == pytest.approx(30.3, abs=2.5)
    assert pct(r["mw"]["reject"]) == pytest.approx(77.9, abs=2.5)
    assert pct(r["wins"]["reject"]) == pytest.approx(54.4, abs=2.5)


def test_ten_percent_disturbed_windows(pools):
    r = E.summarize(pools, 1.4, 30, 10, reps=REPS)["rows"]
    assert pct(r["welch"]["reject"]) == pytest.approx(13.5, abs=2.2)
    assert pct(r["mw"]["reject"]) == pytest.approx(65.3, abs=2.5)
    assert pct(r["wins"]["reject"]) == pytest.approx(22.3, abs=2.5)


def test_more_data_do_not_rescue_the_t_test(pools):
    r = E.summarize(pools, 1.2, 100, 5, reps=REPS)["rows"]
    assert pct(r["welch"]["reject"]) == pytest.approx(21.5, abs=2.5)
    assert pct(r["mw"]["reject"]) == pytest.approx(73.6, abs=2.5)
    clean = E.summarize(pools, 1.2, 100, 0, reps=REPS)["rows"]
    assert pct(clean["welch"]["reject"]) == pytest.approx(83.7, abs=2.5)


def test_interval_width_grows_with_disturbances(pools):
    w0 = E.summarize(pools, 1.4, 30, 0, reps=REPS)["rows"]["welch"]["width"]
    w5 = E.summarize(pools, 1.4, 30, 5, reps=REPS)["rows"]["welch"]["width"]
    w10 = E.summarize(pools, 1.4, 30, 10, reps=REPS)["rows"]["welch"]["width"]
    assert pct(w0) == pytest.approx(4.61, abs=0.2)
    assert pct(w5) == pytest.approx(12.05, abs=0.5)
    assert pct(w10) == pytest.approx(16.31, abs=0.7)


def test_the_level_holds_with_disturbances_for_the_tests_not_the_bootstrap(pools):
    r = E.summarize(pools, 1.0, 30, 10, reps=REPS)["rows"]
    for m, value in (("welch", 4.9), ("mw", 5.4), ("perm", 5.7), ("wins", 5.8)):
        assert pct(r[m]["reject"]) == pytest.approx(value, abs=1.3), m
    assert pct(r["boot"]["reject"]) == pytest.approx(8.7, abs=1.8)

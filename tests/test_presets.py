"""Presets: Vollständigkeit, gültige Werte, Einrasten der Permalink-Werte."""

import prm_constants as C
import prm_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_on_the_grid():
    for preset in C.PRESETS.values():
        assert C.Z_MIN <= preset["z"] <= C.Z_MAX and preset["z"] in C.Z_GRID
        assert C.N_MIN <= preset["n"] <= C.N_MAX and (preset["n"] - C.N_MIN) % C.N_STEP == 0
        assert C.OUT_MIN <= preset["out"] <= C.OUT_MAX
        assert 0 <= preset["seed"] <= C.SEED_MAX


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_default_preset_matches_the_default_settings():
    first = C.PRESETS[C.PRESET_ORDER[0]]
    assert (first["z"], first["n"], first["out"], first["seed"]) == (C.DEFAULT_Z, C.DEFAULT_N, C.DEFAULT_OUT, C.DEFAULT_SEED)


def test_permalink_values_are_clamped_and_snapped_to_the_slider_grid():
    z_spec = P.SETTING_SPECS["z_slider"]
    assert P.clamp_to_spec(z_spec, 1.47) == 1.5 and P.clamp_to_spec(z_spec, 9.0) == 2.0
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P.clamp_to_spec(n_spec, 33) == 35 and P.clamp_to_spec(n_spec, 1) == 10 and P.clamp_to_spec(n_spec, 9999) == 100
    out_spec = P.SETTING_SPECS["out_slider"]
    assert P.clamp_to_spec(out_spec, -3) == 0 and P.clamp_to_spec(out_spec, 50) == 20

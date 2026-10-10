"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort-Fenster) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # Dispersion der negativ-binomialen Tagesnachfrage (ganzzahlig: Gamma(5) = Summe von 5 Exponentialzahlen)
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor dem Auswertefenster (gleiche Regel wie im Fenster)
WINDOW_DAYS = 28          # Auswertefenster: vier Wochen = ein "Standort-Fenster" = eine Einheit des Experiments
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A

Z_MIN, Z_MAX, DEFAULT_Z = 1.0, 2.0, 1.4      # Regel B: Sicherheitsfaktor (1,0 = identisch mit A = A/A-Test)
Z_STEP = 0.1
Z_GRID = tuple(round(Z_MIN + i * Z_STEP, 1) for i in range(int(round((Z_MAX - Z_MIN) / Z_STEP)) + 1))
POOL_SIZE = 10000         # Einheiten je Pool (je Sicherheitsfaktor)
ALPHA = 0.05

# Stück 7: Ausreißer und Verfahren
N_MIN, N_MAX, DEFAULT_N, N_STEP = 10, 100, 30, 5          # Fenster je Arm
OUT_MIN, OUT_MAX, DEFAULT_OUT, OUT_STEP = 0, 20, 0, 1     # Anteil gestörter Fenster in Prozent (unabhängig vom Arm)
OUTLIER_LOW, OUTLIER_HIGH = 0.20, 0.70                    # ein gestörtes Fenster hat einen Servicegrad gleichverteilt hierin
PERMUTATIONS = 399
BOOTSTRAPS = 399
WINSOR_SHARE = 0.05
SEED_MAX, DEFAULT_SEED = 999999, 35
LIVE_REPS = 400           # Wiederholungen der Live-Auswertung (Permutations- und Bootstrap-Verfahren sind teuer)

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"
METHOD_COLORS = {"welch": "#4c78a8", "mw": "#2F6B65", "perm": "#7570b3", "boot": "#d95f02", "wins": "#8c564b"}

PRESETS = {
    "Saubere Daten, mittlere Stichprobe (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "out": 0, "seed": DEFAULT_SEED},
    "Fünf Prozent gestörte Fenster": {"z": DEFAULT_Z, "n": DEFAULT_N, "out": 5, "seed": DEFAULT_SEED},
    "Zehn Prozent gestört, kein Effekt (A/A)": {"z": 1.0, "n": DEFAULT_N, "out": 10, "seed": DEFAULT_SEED},
    "Wenig Daten, saubere Daten": {"z": DEFAULT_Z, "n": 10, "out": 0, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Saubere Daten, mittlere Stichprobe (Voreinstellung)": "Keine Störungen, Sicherheitsfaktor 1,4: die Verteilung ist links-schief, aber harmlos.",
    "Fünf Prozent gestörte Fenster": "Jedes zwanzigste Fenster ist durch eine Lieferstörung stark eingebrochen, unabhängig von der Regel.",
    "Zehn Prozent gestört, kein Effekt (A/A)": "Beide Regeln gleich, jedes zehnte Fenster gestört: wie oft melden die Verfahren trotzdem etwas?",
    "Wenig Daten, saubere Daten": "Nur 10 Fenster je Arm: das Bootstrap-Intervall wird bei so wenig Daten zu eng.",
}


def fmt_pct(x, digits=1):
    """Anteil (0..1) als Prozentzahl mit Dezimalkomma, z. B. 0,934 -> '93,4 %'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def fmt_pp(x, digits=2):
    """Differenz in Prozentpunkten (aus Anteilen 0..1) mit Vorzeichen und Dezimalkomma."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_pkt(x, digits=1):
    """Kurzform für enge Kacheln: '+4,0 Pkt.' (Differenz in Prozentpunkten, aus Anteilen 0..1)."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Pkt."


def fmt_num(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(x):,}".replace(",", " ")

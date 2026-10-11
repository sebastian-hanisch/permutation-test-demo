"""Schiefe Daten und Ausreißer - Permutationstest und Co. - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Der Servicegrad ist links-schief und nach oben bei 100 %
gedeckelt, und gelegentlich bricht ein Fenster durch eine Störung ein. Fünf Verfahren (Welch, Mann-Whitney,
Permutationstest, Bootstrap, Welch nach Winsorisieren) werden gegeneinander gemessen: was bleibt gültig, was findet noch etwas.
Siehe README.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import prm_constants as C
import prm_tests as T
from prm_evaluation import load_pools, nearest_z, run_one, summarize, true_effect
from prm_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from prm_visualization import build_null, build_power_curve, build_rates, build_strip

st.set_page_config(page_title="Permutationstest – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _pools():
    return load_pools()


@st.cache_data(show_spinner=False)
def _one(z, n, out, seed):
    return run_one(_pools(), {"z": z, "n": n, "out": out, "seed": seed})


@st.cache_data(show_spinner=False)
def _many(z, n, out):
    r = summarize(_pools(), z, n, out, reps=C.LIVE_REPS)
    return {k: r[k] for k in ("rows", "truth", "clean", "outlier_share")}


@st.cache_data(show_spinner=False)
def _curve(z, n):
    pools = _pools()
    methods = ("welch", "mw", "wins")
    pts = {m: [] for m in methods}
    for out in (0, 2, 5, 10, 15, 20):
        rows = summarize(pools, z, n, out, reps=C.LIVE_REPS, tag=3, methods=methods)["rows"]
        for m in methods:
            pts[m].append((out, rows[m]["reject"]))
    return pts


st.title("🎲 Schiefe Daten und Ausreißer: Permutationstest und Co.")
st.markdown(
    """
Ein t-Test setzt bei kleinen Stichproben ungefähr normalverteilte Mittelwerte voraus. Der **Servicegrad** ist aber links-schief
und bei 100 % gedeckelt, und gelegentlich bricht ein Fenster durch eine **Lieferstörung** weit ein. Dann stellen sich
Fragen: **Hält der Test sein Niveau? Findet er noch etwas?** Verglichen werden fünf Verfahren: der **Welch-t-Test**, der
**Mann-Whitney-Test** (Rangtest), der **Permutationstest** der Mittelwertdifferenz, ein **Bootstrap**-Intervall und der Welch-Test
auf **winsorisierten** Werten (die schlechtesten 5 % werden auf die Schwelle angehoben). Die wahre Wirkung ist bekannt, deshalb
lässt sich beides messen.
"""
)
st.caption(
    "Siebtes Stück der Linie „Experimente und Wirkungsmessung“, aufbauend auf "
    "[ab-test-demo](https://sebastianhanisch-ab-test-demo.streamlit.app/) (gleiches Vehikel: Standort-Fenster, Servicegrad, "
    "Regel A gegen Regel B). Neu: ein Anteil der Fenster ist gestört, unabhängig von der Regel. Jedes Folgestück hebt eine der "
    "Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So unterscheiden sich die Verfahren", expanded=True):
    st.markdown(
        """
- **Welch-t-Test:** vergleicht Mittelwerte mit geschätzter Streuung. Ausreißer vergrößern die Streuung und nehmen dem
  Test die Kraft.
- **Permutationstest:** ordnet die Fenster zufällig neu auf A und B und fragt, wie selten eine so große Mittelwertdifferenz
  ist. Keine Normalannahme, aber dieselbe Mittelwertdifferenz: Ausreißer wirken genauso.
- **Mann-Whitney:** vergleicht **Ränge** statt Werte. Ein extremes Fenster zählt nur als „schlechtestes“, nicht als
  −60 Punkte. Er beantwortet aber eine andere Frage: nicht „ist der Mittelwert höher?“, sondern „ist ein zufälliges Fenster
  von B eher besser als eines von A?“.
- **Bootstrap-Intervall:** zieht die Fenster jedes Arms mit Zurücklegen neu und nimmt die mittleren 95 % der Differenzen. Bei
  wenig Daten ist es zu eng.
- **Winsorisieren:** hebt die schlechtesten 5 % der gemeinsamen Stichprobe auf deren Schwelle, bevor der Welch-Test läuft.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{i}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])
st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Wahrheit**")
    z = st.slider("Sicherheitsfaktor z von Regel B", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Regel A fährt z = 1,0. Bei z = 1,0 gibt es keine Wirkung: jede Meldung ist ein Fehlalarm.")
    out = st.slider("Gestörte Fenster in %", *bounds("out_slider"), step=C.OUT_STEP, key="out_slider",
                    help=f"Anteil der Fenster, die durch eine Lieferstörung einbrechen (Servicegrad gleichverteilt zwischen "
                         f"{int(100 * C.OUTLIER_LOW)} und {int(100 * C.OUTLIER_HIGH)} %), unabhängig von der Regel.")
    st.markdown("**Experiment**")
    n = st.slider("Fenster je Arm", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="So viele unabhängige Standort-Fenster hat jeder Arm.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt die Fenster des einen Experiments unten.")
    st.button("🎲 Neues Experiment würfeln", on_click=randomize_seed)

z, n, out, seed = nearest_z(float(z)), int(n), int(out), int(seed)
sync_query_params({"z_slider": z, "n_slider": n, "out_slider": out, "seed_input": seed})

pools = _pools()
truth = true_effect(pools, z, out)
aa = z <= C.Z_A

# --- Ein Experiment ---------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 🧪 Ein Experiment")
with st.spinner("Rechne …"):
    one = _one(z, n, out, seed)
st.caption(
    f"{n} Fenster je Arm, Regel B mit z = {C.fmt_num(z)}"
    + (" (gleich wie A)" if aa else f", wahre Wirkung auf den Mittelwert **{C.fmt_pp(truth)}**")
    + f", {out} % gestörte Fenster."
)
left, right = st.columns(2)
with left:
    st.plotly_chart(build_strip(one["a"], one["b"], one["out_a"], one["out_b"], seed), width="stretch",
                    key=f"strip_{z}_{n}_{out}_{seed}")
with right:
    st.plotly_chart(build_null(one["null_diffs"], one["observed"]), width="stretch", key=f"null_{z}_{n}_{out}_{seed}")
tbl = ["| Verfahren | p-Wert / Intervall | Ergebnis |", "|---|---|---|"]
for m in T.METHODS:
    r = one["methods"][m]
    if m == "boot":
        text = f"{C.fmt_pkt(r['lo'], 2)} bis {C.fmt_pkt(r['hi'], 2)}"
        found = not (r["lo"] <= 0 <= r["hi"])
    else:
        text = f"p = {r['p']:.3f}".replace(".", ",")
        found = r["p"] < C.ALPHA
    tbl.append(f"| {T.METHOD_LABELS[m]} | {text} | {'**Unterschied**' if found else 'kein Unterschied'} |")
st.markdown("\n".join(tbl))
st.caption(f"Beobachtete Mittelwertdifferenz: {C.fmt_pp(one['observed'])}; gestörte Fenster in diesem Experiment: "
           f"{int(one['out_a'].sum() + one['out_b'].sum())} von {2 * n}.")

# --- Viele Experimente -----------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📐 Viele Experimente: was bleibt gültig, was findet noch etwas?")
with st.spinner("Rechne die Wiederholungen …"):
    many = _many(z, n, out)
    null_many = _many(1.0, n, out) if not aa else many
rows = many["rows"]
st.plotly_chart(build_rates(rows, null_many["rows"]), width="stretch", key=f"rates_{z}_{n}_{out}")
tab = ["| Verfahren | Fehlalarm (ohne Wirkung) | Teststärke (mit Wirkung) | Abdeckung des Intervalls |", "|---|---|---|---|"]
for m in T.METHODS:
    cov = rows[m].get("coverage")
    tab.append(f"| {T.METHOD_LABELS[m]} | {C.fmt_pct(null_many['rows'][m]['reject'])} | "
               f"{C.fmt_pct(rows[m]['reject']) if not aa else '–'} | {C.fmt_pct(cov) if cov is not None else '–'} |")
st.markdown("\n".join(tab))
if out > 0 and not aa:
    st.error(
        f"**Mit {out} % gestörten Fenstern bricht die Teststärke ein:** der Welch-Test findet die Wirkung nur noch in "
        f"{C.fmt_pct(rows['welch']['reject'], 0)} der Experimente (ohne Störungen: "
        f"{C.fmt_pct(_many(z, n, 0)['rows']['welch']['reject'], 0)}), der Permutationstest in "
        f"{C.fmt_pct(rows['perm']['reject'], 0)}. Der Mann-Whitney-Test findet sie in {C.fmt_pct(rows['mw']['reject'], 0)}, "
        "weil er nur Ränge sieht: die Störungen sind nur die schlechtesten Fenster. Das Niveau halten alle (siehe Fehlalarm)."
    )
elif out == 0 and not aa:
    st.success(
        f"**Auf sauberen Daten ist die Schiefe harmlos:** Welch {C.fmt_pct(rows['welch']['reject'], 0)}, Permutation "
        f"{C.fmt_pct(rows['perm']['reject'], 0)}, Mann-Whitney {C.fmt_pct(rows['mw']['reject'], 0)} Teststärke, bei gleichem "
        f"Niveau. Das Bootstrap-Intervall ist bei wenig Daten dagegen zu eng (Abdeckung {C.fmt_pct(rows['boot']['coverage'])}, "
        f"Fehlalarm {C.fmt_pct(null_many['rows']['boot']['reject'])})."
    )
else:
    st.info(f"Ohne Wirkung melden die Verfahren je zwischen {C.fmt_pct(min(r['reject'] for r in rows.values()))} und "
            f"{C.fmt_pct(max(r['reject'] for r in rows.values()))} der Experimente einen Unterschied (Soll 5 %).")

st.markdown("---")
st.subheader("📉 Wie schnell verliert der Welch-Test an Kraft?")
if aa:
    st.info("Bei z = 1,0 gibt es keine Wirkung, die man verlieren könnte. Wählen Sie einen Sicherheitsfaktor über 1,0.")
else:
    with st.spinner("Rechne …"):
        curve = _curve(z, n)
    st.plotly_chart(build_power_curve(curve), width="stretch", key=f"curve_{z}_{n}")
    st.caption("Die Störungen sind unabhängig von der Regel: die mittlere Wirkung schrumpft um den gestörten Anteil, die Streuung "
               "wächst stark. Welch verliert die Kraft, Mann-Whitney und Winsorisieren behalten einen Teil.")

# --- Grenzen ---------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Frage ist „ist der Mittelwert höher?“** | Der Mann-Whitney-Test beantwortet eine andere Frage (Rangordnung); bei Ausreißern ist das oft die bessere, aber es ist nicht dasselbe. | (dieses Stück) |
| **Störungen sind unabhängig von der Regel** | Treffen sie einen Arm häufiger, verzerrt das den Mittelwert und der Zuteilungstest wird zuständig. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Fenster unabhängig und gleichartig** | Serienkorrelation oder Cluster machen jede dieser Auswertungen zu optimistisch. | Verhältniskennzahlen und Cluster |
| **Ein Test, eine Kennzahl** | Das Ausprobieren mehrerer Verfahren auf denselben Daten ist selbst ein Mehrfachtest. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Der Umfang steht vorher fest** | Dasselbe Verfahren mit Zwischenblicken braucht gültige Grenzen. | Zwischenblicke und dauerndes Hinsehen |
| **Genug Daten** | Bei sehr wenigen Fenstern sind Bootstrap und Rangtests ungenau; der exakte Permutationstest ist dort die sichere Wahl. | (dieses Stück) |
"""
)
st.caption(
    "Die Zahlen stammen aus dem erfundenen Vehikel dieses Stücks. Die Störung ist ein Modell (Servicegrad gleichverteilt "
    "zwischen 20 und 70 %), keine Beobachtung."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Permutationstest.** Unter der Nullhypothese „gleiche Verteilung“ ist jede Zuordnung der $2n$ Fenster zu A und B gleich
wahrscheinlich. Der p-Wert ist der Anteil der Zuordnungen mit $|\bar x_B^* - \bar x_A^*| \ge |\bar x_B - \bar x_A|$; hier mit
399 zufälligen Zuordnungen: $p = (1 + \#)/(399 + 1)$.

**Mann-Whitney.** $U = R_B - n(n+1)/2$ mit der Rangsumme $R_B$ von B in der gemeinsamen Rangfolge; Normalnäherung mit
Bindungs- und Stetigkeitskorrektur. Er prüft, ob $P(X_B > X_A) \ne 1/2$.

**Bootstrap-Perzentil.** Beide Arme getrennt mit Zurücklegen 399 Mal ziehen, die Differenz der Mittelwerte bilden und die
2,5- und 97,5-Prozent-Quantile nehmen.

**Winsorisieren.** Werte unter dem 5-%-Quantil $q$ der gemeinsamen Stichprobe werden auf $q$ gesetzt; danach Welch-Test. Das
verschiebt die Mittelwerte, hält aber die Streuung klein; die geschätzte Differenz ist nicht mehr die der Rohwerte.

**Störungen.** Ein Anteil $q$ der Fenster wird unabhängig vom Arm durch $U(0{,}2;\,0{,}7)$ ersetzt. Der Mittelwert beider Arme
ist $(1-q)\mu + q \cdot 0{,}45$: die mittlere Wirkung schrumpft auf $(1-q)\Delta$, die Varianz wächst um
$q(1-q)(\mu - 0{,}45)^2$.

Implementiert in `prm_tests.py` (alle Verfahren), `prm_evaluation.py` (Ziehung, Störungen, Zusammenfassungen), `prm_stats.py`
(Welch), `prm_vehicle.py` (Standort-Fenster), `generate_precomputed.py` (Pools).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html)."
)

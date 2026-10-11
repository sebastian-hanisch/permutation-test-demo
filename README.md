# Schiefe Daten und Ausreißer: Permutationstest und Co. – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-permutation-test-demo.streamlit.app/)**

Interaktive Demo zu **Verteilungsannahmen im Zwei-Gruppen-Test**. **Siebtes Stück der Konzepte-Linie „Experimente und
Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning), Kind des [A/B-Tests](https://github.com/sebastian-hanisch/ab-test-demo): dort hielt der Welch-Test trotz links-schiefer,
bei 100 % gedeckelter Verteilung. Hier kommt dazu, was in Praxisdaten fast immer auftritt: **gestörte Fenster**, die weit
einbrechen. Das Vehikel ist dasselbe: ein Standort mit täglicher Nachbestellung, Regel A (Sicherheitsfaktor 1,0) gegen Regel
B, Einheit ist ein Standort-Fenster von vier Wochen, Kennzahl der Servicegrad.

## Kernfrage

Hält der t-Test sein Niveau, wenn die Daten schief sind und einzelne Fenster einbrechen, und findet er dann noch etwas? Was
leisten Permutationstest, Rangtest, Bootstrap und Winsorisieren im Vergleich?

## Modell und Methodik

- **Daten:** n Fenster je Arm aus den Pools des ersten Stücks (SplitMix64). Danach wird jedes Fenster mit Wahrscheinlichkeit q
  durch eine **Störung** ersetzt (Lieferstörung: Servicegrad gleichverteilt zwischen 20 und 70 %), unabhängig von Arm und Regel.
  Die mittlere Wirkung schrumpft damit auf (1 − q) mal die saubere Wirkung.
- **Fünf Verfahren** (`prm_tests.py`): Welch-t-Test; Mann-Whitney (Normalnäherung mit Bindungs- und Stetigkeitskorrektur);
  Permutationstest der Mittelwertdifferenz (399 zufällige Umordnungen); Bootstrap-Perzentil-Intervall (399 Ziehungen je Arm);
  Welch nach Winsorisieren der schlechtesten 5 % der gemeinsamen Stichprobe.
- **Messgrößen:** Anteil der Experimente mit Befund (ohne Wirkung: Fehlalarm; mit Wirkung: Teststärke), Abdeckung und Breite
  der Intervalle.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (1 500 Experimente je Zelle, Fehler der Raten höchstens 1,3 Prozentpunkte).
Sicherheitsfaktor 1,4 (Wirkung **3,49 Prozentpunkte**), 30 Fenster je Arm, wenn nicht anders genannt.

| Frage | Befund |
|---|---|
| Hält jedes Verfahren sein Niveau auf sauberen schiefen Daten? | Bei 30 Fenstern je Arm: Welch **4,7 %**, Mann-Whitney **4,4 %**, Permutation **4,6 %**, Winsorisieren **5,0 %** (Soll 5 %). Das **Bootstrap-Intervall** ist zu liberal: **6,1 %** bei 30 Fenstern je Arm, **7,4 %** bei 10. |
| Wie sieht es mit der Abdeckung aus? | Bei 10 Fenstern je Arm deckt das Welch-Intervall in **96,0 %**, das Bootstrap-Intervall nur in **91,9 %** (und ist schmaler). |
| Findet Permutation oder Rangtest mehr als Welch? | **Nein.** Teststärke Welch **84,5 %**, Permutation **83,9 %**, Mann-Whitney **84,9 %** bei 30 Fenstern; bei 10 Fenstern **37,3 %** (Welch) gegen **35,1 %** (Mann-Whitney). Auf sauberen Daten ist die Schiefe harmlos. |
| Was machen gestörte Fenster? | Bei **5 %** gestörten Fenstern fällt die Teststärke des Welch-Tests von **84,5 %** auf **25,4 %**, die des Permutationstests auf **27,4 %**, die des Bootstraps auf **30,3 %**. |
| Was hält stand? | Mann-Whitney **77,9 %**; Winsorisieren **54,4 %**. Bei 10 % gestörten Fenstern: Welch **13,5 %**, Mann-Whitney **65,3 %**, Winsorisieren **22,3 %**. |
| Rettet mehr Daten den t-Test? | **Nein.** Mit 100 Fenstern je Arm, Faktor 1,2 und 5 % Störungen: Welch **21,5 %** (sauber **83,7 %**), Mann-Whitney **73,6 %**. |
| Wie breit wird das Intervall? | Das Welch-Intervall wächst von **4,6** auf **12,1** (5 %) und **16,3 Prozentpunkte** (10 % Störungen). |
| Und das Niveau mit Störungen? | Bei 10 % Störungen ohne Wirkung bleiben Welch, Mann-Whitney, Permutation und Winsorisieren zwischen **4,9 und 5,8 %**; der Bootstrap meldet **8,7 %**. |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vorab-Messreihe auf dem Terminal-Gate** fand denselben Typ von Befund: Welch konservativ mit Ausreißern, Mann-Whitney
  mit 69 % gegen 34 % Teststärke bei 100 Tagen. Dort war die Störung ein Zehnfaches der Wartezeit; hier ist es ein
  Servicegrad-Einbruch. Die Größenordnungen unterscheiden sich, die Reihenfolge der Verfahren nicht.
- **Die Kappung am 99. Perzentil war auf dem Gate wirkungslos.** Hier sind die Ausreißer nach unten, und das untere Winsorisieren
  wirkt (54,4 % gegen 25,4 %), bleibt aber weit hinter dem Rangtest.
- **Der Mann-Whitney-Test beantwortet eine andere Frage.** Er prüft, ob ein zufälliges Fenster von B eher besser ist als eines von
  A, nicht, ob der Mittelwert höher ist. Bei Störungen, die beide Arme gleich treffen, ist das die robustere Frage; wer die
  Mittelwertdifferenz braucht (z. B. für Kosten), hat sie damit nicht.
- **Saubere Daten sind der langweilige Teil.** Auf ihnen ändert kein Verfahren das Bild gegenüber dem ersten Stück; der Hook
  des Stücks liegt allein bei den Störungen.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Frage ist „ist der Mittelwert höher?“** | Der Rangtest beantwortet eine andere Frage; bei Ausreißern oft die bessere, aber nicht dieselbe. | (dieses Stück) |
| **Die Störungen sind unabhängig von der Regel** | Treffen sie einen Arm häufiger, verzerrt das den Mittelwert und der Zuteilungstest wird zuständig. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Fenster unabhängig und gleichartig** | Serienkorrelation oder Cluster machen jede dieser Auswertungen zu optimistisch. | Verhältniskennzahlen und Cluster |
| **Ein Test, eine Kennzahl** | Mehrere Verfahren auf denselben Daten sind selbst ein Mehrfachtest. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Der Umfang steht vorher fest** | Dasselbe Verfahren mit Zwischenblicken braucht gültige Grenzen. | Zwischenblicke und dauerndes Hinsehen |
| **Genug Daten** | Bei sehr wenigen Fenstern sind Bootstrap und Rangtests ungenau. | (dieses Stück) |

Die Störung ist ein Modell (Servicegrad gleichverteilt zwischen 20 und 70 %), keine Beobachtung.

## Bezug zu OR

Praxisdaten haben Ausreißer: ein Lieferausfall, ein Systemfehler, eine Sperrung. Wer eine Regel an der Mittelwertdifferenz
misst, verliert dabei fast alle Aussagekraft, ohne es am Fehlalarm zu merken. Die Demo zeigt, welche Verfahren das abfedern
und was man dafür an Aussage aufgibt.

## Verwandte Demos im Portfolio

- [ab-test-demo](https://github.com/sebastian-hanisch/ab-test-demo): das erste Stück (Vehikel, Welch-Test, Abdeckung).
- [test-power-demo](https://github.com/sebastian-hanisch/test-power-demo): Teststärke und Planung.
- [sample-ratio-demo](https://github.com/sebastian-hanisch/sample-ratio-demo): Datenverlust nach der Zuteilung (dort geht es
  um fehlende, hier um gestörte Fenster).

## Verifikation

- **Verfahren** (`tests/test_methods.py`, `tests/test_oracle_permutation_test.py`): Mann-Whitney von Hand und gegen
  `scipy.stats.mannwhitneyu` mit Bindungen; Permutationstest gegen die vollständige Aufzählung aller Umordnungen (itertools);
  Welch gegen scipy; Bootstrap-Intervall gegen das Normalintervall auf Normaldaten; Winsorisieren von Hand; Niveau aller
  Verfahren auf Normaldaten.
- **Störungen:** gemessene mittlere Wirkung gleich (1 − q) mal die saubere Wirkung.
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Experiment mit Streudiagramm und Permutationsverteilung, Wiederholungen, Störungskurve, Grenzen |
| `prm_constants.py` | Vehikel-Konstanten, Störungsmodell, Regler-Grenzen, Presets |
| `prm_rng.py`, `prm_vehicle.py`, `prm_formulas.py`, `prm_stats.py` | Zufall, Standort-Fenster, exakter Servicegrad, Welch-Test (aus dem ersten Stück) |
| `prm_tests.py` | Mann-Whitney, Permutationstest, Bootstrap, Winsorisieren, `run_all` |
| `prm_evaluation.py` | Ziehung mit Störungen, Zusammenfassungen, das eine Experiment |
| `prm_presets.py`, `prm_visualization.py` | Permalink, Presets; Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_pools.json` | vorgerechnete Pools (je 10 000 Fenster) |
| `tools/measure_stueck7.py` | die Messreihe vor dem Text |
| `tests/` | Vehikel, Orakel, Verfahren, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Getrimmte Mittel und Yuen-Test**, **Median-Differenz**, **Quantilregression:** nicht gebaut.
- **Exakte Tests für sehr kleine Stichproben:** der Permutationstest zieht zufällige Umordnungen, keine vollständige Aufzählung.
- **Störungen, die nur einen Arm treffen:** das ist ein Zuteilungsproblem (siehe oben), hier nicht modelliert.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Verteilungsfunktionen, Rangbildung).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html).

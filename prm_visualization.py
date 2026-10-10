"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import prm_constants as C
import prm_tests as T
from prm_rng import uniform_block

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=340, legend=dict(orientation="h", y=-0.25))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_strip(a, b, out_a, out_b, seed):
    """Die Fenster beider Arme als Punkte; gestörte Fenster als rote Kreuze. y in %, nach unten bis 0."""
    fig = go.Figure()
    for x0, vals, out, name, color in ((0, a, out_a, "Regel A", C.COLOR_A), (1, b, out_b, "Regel B", C.COLOR_B)):
        jitter = x0 + (uniform_block(seed + 10 + x0, len(vals)) - 0.5) * 0.4
        ok = ~np.asarray(out)
        fig.add_trace(go.Scatter(x=jitter[ok], y=100 * np.asarray(vals)[ok], mode="markers", name=name,
                                 marker=dict(color=color, size=8, opacity=0.7)))
        if (~ok).any():
            fig.add_trace(go.Scatter(x=jitter[~ok], y=100 * np.asarray(vals)[~ok], mode="markers", name="gestörtes Fenster",
                                     marker=dict(color=C.COLOR_MISS, size=11, symbol="x", line=dict(width=2)),
                                     showlegend=(x0 == 0)))
        fig.add_trace(go.Scatter(x=[x0], y=[100 * float(np.mean(vals))], mode="markers", showlegend=False,
                                 marker=dict(color=color, size=16, symbol="diamond", line=dict(color="white", width=2))))
    fig.update_xaxes(tickmode="array", tickvals=[0, 1], ticktext=["Regel A", "Regel B"], range=[-0.6, 1.6])
    return _finish(fig, "Servicegrad je Standort-Fenster (Raute: Mittelwert)", None, "Servicegrad in %")


def build_null(null_diffs, observed):
    """Verteilung der Mittelwertdifferenz unter 'kein Unterschied' (Umordnungen) mit der beobachteten Differenz."""
    fig = go.Figure(go.Histogram(x=100 * np.asarray(null_diffs), marker_color=C.COLOR_OK, nbinsx=40, name="Umordnungen"))
    fig.add_vline(x=100 * observed, line=dict(color=C.COLOR_B, width=3), annotation_text="beobachtet", annotation_position="top")
    fig.add_vline(x=-100 * observed, line=dict(color=C.COLOR_B, width=2, dash="dot"))
    return _finish(fig, "Mittelwertdifferenz bei zufälliger Umordnung der Fenster", "Prozentpunkte Servicegrad", "Umordnungen")


def build_rates(rows_effect, rows_null):
    """Anteil mit Befund je Verfahren: ohne Wirkung (Fehlalarm) und mit Wirkung (Teststärke), nebeneinander."""
    methods = [m for m in T.METHODS if m in rows_effect]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[T.METHOD_SHORT[m] for m in methods], y=[100 * rows_null[m]["reject"] for m in methods],
                         name="ohne Wirkung (Fehlalarm)", marker_color=C.COLOR_MISS))
    fig.add_trace(go.Bar(x=[T.METHOD_SHORT[m] for m in methods], y=[100 * rows_effect[m]["reject"] for m in methods],
                         name="mit Wirkung (Teststärke)", marker_color=C.COLOR_B))
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="5 %", annotation_position="top right")
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 100])
    return _finish(fig, "Was jedes Verfahren findet", None, "Anteil der Experimente in %")


def build_power_curve(points):
    """Teststärke gegen den Anteil gestörter Fenster, eine Linie je Verfahren. points: {Verfahren: [(Anteil %, Teststärke)]}."""
    fig = go.Figure()
    for m, pts in points.items():
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[100 * p[1] for p in pts], mode="lines+markers",
                                 name=T.METHOD_SHORT[m], line=dict(color=C.METHOD_COLORS[m], width=3)))
    fig.update_yaxes(range=[0, 100])
    return _finish(fig, "Teststärke gegen den Anteil gestörter Fenster", "gestörte Fenster in %", "Anteil der Experimente in %")

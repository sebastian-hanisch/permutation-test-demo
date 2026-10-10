"""Messreihe vor dem Text: fünf Verfahren auf schiefen Daten mit und ohne Störungen (Stück 7)."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import prm_constants as C  # noqa: E402
import prm_evaluation as E  # noqa: E402
import prm_tests as T  # noqa: E402

pools = E.load_pools()
t0 = time.time()
print("Anteil mit Befund je Verfahren (A/A = Fehlalarm, sonst Teststaerke); R = 1500")
print("z    n   out | " + " | ".join(f"{T.METHOD_SHORT[m]:>12s}" for m in T.METHODS))
for z, n, out in ((1.0, 10, 0), (1.0, 30, 0), (1.0, 100, 0), (1.0, 30, 5), (1.0, 30, 10), (1.0, 100, 10),
                  (1.4, 10, 0), (1.4, 30, 0), (1.2, 30, 0), (1.2, 100, 0), (1.4, 30, 5), (1.4, 30, 10), (1.2, 100, 5), (1.2, 100, 10)):
    s = E.summarize(pools, z, n, out, reps=1500)
    print(f"{z:.1f} {n:4d} {out:3d}% | " + " | ".join(f"{100*s['rows'][m]['reject']:11.1f}%" for m in T.METHODS)
          + f"   wahr {100*s['truth']:+.2f} (sauber {100*s['clean']:+.2f})")
print("\nAbdeckung des 95-%-Intervalls (Welch / Bootstrap), Breite; A/A und mit Wirkung")
for z, n, out in ((1.4, 10, 0), (1.4, 30, 0), (1.4, 100, 0), (1.4, 30, 5), (1.4, 30, 10)):
    s = E.summarize(pools, z, n, out, reps=1500)
    print(f"z={z} n={n:3d} out={out:2d}%: Welch {100*s['rows']['welch']['coverage']:.1f} % (Breite {100*s['rows']['welch']['width']:.2f}), "
          f"Bootstrap {100*s['rows']['boot']['coverage']:.1f} % (Breite {100*s['rows']['boot']['width']:.2f}), "
          f"winsorisiert {100*s['rows']['wins']['coverage']:.1f} %")
print(f"({time.time()-t0:.0f} s)")

#!/usr/bin/env python3
"""TOMBOLA: ignore keys played while AUX is held (octave A#/B, ball off, pause...), like STEP and ENDLESS."""
p = "gentomb.py"; s = open(p).read()
a = "tb.c(nSp2, thT)"
assert s.count(a) == 1
s = s.replace(a, '''nSpA = tb.obj(1100, 195, "spigot 1")                # AUX up only (apply_tombaux.py)
auxUp = tb.obj(1200, 165, "== 0")
tb.c(tb.obj(1200, 140, "r aux"), auxUp); tb.c(auxUp, nSpA, 0, 1)
tb.c(nSp2, nSpA); tb.c(nSpA, thT)''')
open(p, "w").write(s); print("ok")

#!/usr/bin/env python3
"""Loop start from the keys. AUX + G# (1st press) stored the start in the cold inlet of an [f] that was never
banged, so the loop computation always saw start = 0: every loop made with the keys began at the tape start
(since the first version). The start now goes into the [f]'s hot inlet, which passes it on to the loop end /
start expressions (their cold inlets)."""
import shutil
shutil.copy("gentape.py", "gentape.py.pre-loopstart")
s = open("gentape.py").read()
a = "t.c(l0, posIn, 1); t.c(posIn, inV, 0, 1); t.c(l0, m1, 0); t.c(m1, lsF, 0, 1)"
assert s.count(a) == 1
s = s.replace(a, "t.c(l0, posIn, 1); t.c(posIn, inV, 0, 0); t.c(l0, m1, 0); t.c(m1, lsF, 0, 1)   # start into inV's hot inlet (apply_loopstart.py)")
open("gentape.py", "w").write(s)
print("loop start fixed")

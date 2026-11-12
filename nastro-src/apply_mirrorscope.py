#!/usr/bin/env python3
"""VIS scope on the computer (genmirror.py): the WAVE scope is a /oled/gWaveform sent after each /oled/gFrame;
the mirror dropped it, so the right side of WAVE was black on the computer. Now the gWaveform that follows a
gFrame which got through the 200 ms gate goes out too (one-shot gate opened by the frame, closed by the scope)."""
import shutil

shutil.copy("genmirror.py", "genmirror.py.pre-mirrorscope")
s = open("genmirror.py").read()
a = "mi.c(frC, frD, 0); mi.c(frD, fr1); mi.c(fr1, frG, 0, 1)\n"
assert s.count(a) == 1
s = s.replace(a, a + '''# the scope that follows a frame which went out goes out too (apply_mirrorscope.py)
wvG = mi.obj(800, 360, "spigot 0")
wv1 = mi.msg(800, 420, "1")
mi.c(frC, wv1, 0); mi.c(wv1, wvG, 0, 1)
mi.c(rHv, wvG, 1)
wvT = mi.obj(800, 390, "t b a")                      # out first, then close
mi.c(wvG, wvT)
wvL = mi.obj(800, 450, "list prepend sendtyped /oled/gWaveform")
mi.c(wvT, wvL, 1); mi.c(wvL, lp)
wv0 = mi.msg(900, 420, "0")
mi.c(wvT, wv0, 0); mi.c(wv0, wvG, 0, 1)
''')
open("genmirror.py", "w").write(s)
t = open("test_mirrorthrottle.py").read()
a = "and not nW and"
assert t.count(a) == 1
t = t.replace(a, "and abs(len(nW) - len(nF)) <= 1 and all(len(m) == 132 for m in nW) and")
t = t.replace("no gWaveform, and the other", "a gWaveform (the scope) with each gFrame, and the other")
open("test_mirrorthrottle.py", "w").write(t)
print("mirror scope applied")

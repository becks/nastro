#!/usr/bin/env python3
"""Mirror diet (genmirror.py): the VIS page sends a 1024-byte /oled/gFrame + a 128-value /oled/gWaveform ~10 times a
second; relayed as FUDI text over Wi-Fi that made the Organelle glitch. Now the mirror lets through at most one
gFrame every 500 ms and drops gWaveform; every other command is relayed as before. The OLED itself is unchanged."""
import shutil

shutil.copy("genmirror.py", "genmirror.py.pre-mirrorthrottle")
s = open("genmirror.py").read()
a = 'mi.c(mi.obj(300, 360, "r oscOut"), lp)'
assert s.count(a) == 1
s = s.replace(a, '''# VIS frames are heavy: at most one gFrame every 500 ms, no gWaveform (apply_mirrorthrottle.py)
rTy = mi.obj(300, 330, "route sendtyped")
mi.c(mi.obj(300, 300, "r oscOut"), rTy)
mi.c(rTy, lp, 1)                                     # plain commands: as before
rHv = mi.obj(560, 330, "route /oled/gFrame /oled/gWaveform")
mi.c(rTy, rHv, 0)
lpT = mi.obj(760, 360, "list prepend sendtyped")     # other typed commands (gFlip ...): as before
mi.c(rHv, lpT, 2)
mi.c(lpT, lp)
frG = mi.obj(560, 360, "spigot 1")
mi.c(rHv, frG, 0)
frT = mi.obj(560, 390, "t b a")                      # a frame that got through goes out first, then the gate closes 500 ms
mi.c(frG, frT)
frL = mi.obj(560, 420, "list prepend sendtyped /oled/gFrame")
mi.c(frT, frL, 1)
mi.c(frL, lp)
frC = mi.obj(660, 420, "t b b")
mi.c(frT, frC, 0)
fr0 = mi.msg(760, 450, "0")
fr1 = mi.msg(660, 480, "1")
frD = mi.obj(660, 450, "delay 500")
mi.c(frC, fr0, 1); mi.c(fr0, frG, 0, 1)
mi.c(frC, frD, 0); mi.c(frD, fr1); mi.c(fr1, frG, 0, 1)
''')
open("genmirror.py", "w").write(s)
print("mirror throttle applied")

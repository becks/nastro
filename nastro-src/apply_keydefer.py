#!/usr/bin/env python3
"""Defer tape key/footswitch/track events with [pipe 0]. On the device, key presses arrive from the network after a
DSP tick but before that tick's [bang~] has updated the tape position, so rec started the writer one block (64
samples) behind the play head -> a 64-sample silent gap at every loop restart. [pipe 0] runs the event after the
position update, in the same logical time, so writer and head line up."""
p = "gentape.py"; s = open(p).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("t.c(rak, selk); t.c(rfs, fs1)",
    "kDf = t.obj(20, 115, \"pipe 0\"); fDf = t.obj(260, 115, \"pipe 0\")\n"
    "t.c(rak, kDf); t.c(kDf, selk); t.c(rfs, fDf); t.c(fDf, fs1)     # after the tape position update (apply_keydefer.py)")
rep("t.c(navK, navS);", "nDf = t.obj(1800, 715, \"pipe 0\")\nt.c(navK, nDf); t.c(nDf, navS);")
rep("t.c(krt, k2a, 1); t.c(k2a, k2c); t.c(k2c, k2t)",
    "k2D = t.obj(780, 305, \"pipe 0\")\nt.c(krt, k2a, 1); t.c(k2a, k2c); t.c(k2c, k2D); t.c(k2D, k2t)")
open(p, "w").write(s); print("ok")

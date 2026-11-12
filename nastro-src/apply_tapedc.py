#!/usr/bin/env python3
"""Tape DC (gentape.py): at speed 0 (after stop, or the continuous speed knob at 0) the read head rests on one
sample and the track outputs that value as a constant - DC on the output (inaudible, but it offsets the output,
and VIS showed a full-scale level). The playback of every track is now multiplied by a gain from the tape speed:
clip(|speed| * 20, 0, 1) - exactly 1 from 0.05x up (sound unchanged), fading to 0 over the last part of the
slow-down to a stop. The record path (overdub reads) is unchanged."""
import shutil

shutil.copy("gentape.py", "gentape.py.pre-tapedc")
s = open("gentape.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep("xAs, xBs, rds = [], [], []\n", '''xAs, xBs, rds = [], [], []
# speed gate (apply_tapedc.py): no output when the head rests
sgA = t.obj(1600, 470, "abs~"); sgM = t.obj(1600, 500, "*~ 20"); sgC = t.obj(1600, 530, "clip~ 0 1")
t.c(lspd, sgA); t.c(sgA, sgM); t.c(sgM, sgC)
''')
rep("    t.c(xA, xS, 0, 0); t.c(xB, xS, 0, 1); t.c(xS, lv)\n", '''    t.c(xA, xS, 0, 0); t.c(xB, xS, 0, 1)
    sgG = t.obj(x + 40, 840, "*~")                              # speed gate (apply_tapedc.py)
    t.c(xS, sgG, 0, 0); t.c(sgC, sgG, 0, 1); t.c(sgG, lv)
''')
open("gentape.py", "w").write(s)
print("tape dc applied")

#!/usr/bin/env python3
"""SMPL page: knobs feel slow because each frame sent ~55 OLED messages (42 waveform bars) up to 20x/s, about
1200 messages/s while a knob turns - more than the Organelle screen keeps up with, so values showed late.
Now: one baseline line for all flat bars (outside START..END or near-silent) and only the taller bars as
FillAreas, and the SYNTH page redraws at most ~7x/s while SMPL is the engine (20x/s for the others)."""


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gensmpl.py", [
    ('r.c(bP, r.msg(2000, 320, "\\\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\\\$1 \\\\$2 2 \\\\$3 1"))',
     '''bTall = r.obj(1900, 290, "> 1")                    # 1-px bars are covered by the baseline (apply_smplfast.py)
bGate = r.obj(2000, 305, "spigot")
r.c(bE, bTall, 2); r.c(bTall, bGate, 0, 1); r.c(bP, bGate)
r.c(bGate, r.msg(2000, 320, "\\\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\\\$1 \\\\$2 2 \\\\$3 1"))'''),
    ("r.c(dT, bT, 2); r.c(bT, bZ, 1); r.c(bZ, bC, 0, 1); r.c(bT, bN, 0)",
     '''bLine = r.obj(2100, 140, "t b b")                  # baseline first, then the tall bars
r.c(dT, bLine, 2); r.c(bLine, bT, 0)
r.c(bLine, r.msg(2200, 140, "\\\\; oscOut sendtyped /oled/gLine iiiiii 3 1 26 126 26 1"), 1)
r.c(bT, bZ, 1); r.c(bZ, bC, 0, 1); r.c(bT, bN, 0)'''),
])
edit("gensynth.py", [('mtr = s.obj(300, 170, "metro 50")',
                      '''mtr = s.obj(300, 170, "metro 50")
mtrI = s.obj(400, 140, "expr if($f1==4 \\\\, 150 \\\\, 50)")      # SMPL page: at most ~7 frames/s (apply_smplfast.py)
s.c(s.obj(400, 110, "r synth-engine"), mtrI); s.c(mtrI, mtr, 0, 1)''')])
print("SMPL page lighter")

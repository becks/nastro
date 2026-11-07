#!/usr/bin/env python3
"""SMPL live view while recording: instead of a full SYNTH page redraw every 100 ms (~60 OLED messages, it glitched
the Organelle), draw only the bar being written (clear its column, draw it, flip: 3 messages), fixed scale.
Only when the SYNTH page with the SMPL engine is shown. The normal full redraw happens when recording stops."""
import shutil

shutil.copy("gensmpl.py", "gensmpl.py.pre-smplive")
s = open("gensmpl.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('''liveV = r.msg(2600, 1000, f"\\\\; smp-dlen {SMAX} \\\\; smp-ds0 0 \\\\; smp-ds1 \\\\$1 \\\\; smp-live bang")''',
    '''liveV = r.msg(2600, 1000, f"\\\\; smp-dlen {SMAX} \\\\; smp-ds0 0 \\\\; smp-ds1 \\\\$1")
# incremental draw of the bar just measured (x = 1 + 3*bar, fixed scale), only on the SYNTH page with SMPL
pgE = r.obj(3000, 900, "expr $f1==0 && $f2==4")
pgM = r.obj(3000, 870, "t f")
r.c(r.obj(3000, 840, "r mode"), pgM); r.c(pgM, pgE, 0, 0)
pgN = r.obj(3100, 870, "t b f")
r.c(r.obj(3100, 840, "r synth-engine"), pgN); r.c(pgN, pgE, 1, 1); r.c(pgN, pgE, 0, 0)
barSp = r.obj(2900, 990, "spigot")
r.c(pgE, barSp, 0, 1)
barP = r.obj(2900, 960, "pack f f")
r.c(laT, barP, 0, 1)                                      # amplitude (cold)
r.c(lbI, barP, 0, 0)                                      # bar index (hot, last: after the amplitude)
r.c(barP, barSp)
barE = r.obj(2900, 1020, "expr 1+$f1*3 \\\\; 26-min(14 \\\\, int($f2*20)) \\\\; 2*min(14 \\\\, int($f2*20))+1")
r.c(barSp, barE)
barQ = r.obj(2900, 1050, "pack f f f")
for o in range(3):
    r.c(barE, barQ, o, o)
r.c(barQ, r.msg(2900, 1080, "\\\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\\\$1 11 2 31 0 "
                            "\\\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\\\$1 \\\\$2 2 \\\\$3 1 "
                            "\\\\; oscOut sendtyped /oled/gFlip i 3"))''')
# the bar index must reach [tabwrite smplwave] before its value: 3-way trigger (index, measure, draw)
rep('lbI = r.obj(2700, 780, "t f f")', 'lbI = r.obj(2700, 780, "t f f f")')
rep('r.c(lbI, lTw, 0, 1); r.c(laT, lTw, 0); r.c(laT, pkMax, 1)', 'r.c(lbI, lTw, 2, 1); r.c(laT, lTw, 0); r.c(laT, pkMax, 1)')
open("gensmpl.py", "w").write(s)
print("smplive applied")

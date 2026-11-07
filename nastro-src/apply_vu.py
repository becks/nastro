#!/usr/bin/env python3
"""MIX page: needles become VU meters (live track level), the level setting becomes a mark on the ring.
Needles are animated incrementally (erase old / draw new) so the OLED traffic stays small."""
import shutil

for f in ("genmix.py", "gentape.py"):
    shutil.copy(f, f + ".pre-vu")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# per-track level (post fader, pre pan) for the meters
edit("gentape.py", [
    (r'''    t.c(gLp, thL); t.c(gRp, thR)''',
     r'''    t.c(gLp, thL); t.c(gRp, thR)
    vuEnv = t.obj(x, 990, "env~ 2048 1024")
    t.c(lv, vuEnv); t.c(vuEnv, t.obj(x, 1020, f"s tape-vu{k+1}"))'''),
])

edit("genmix.py", [
    # full redraw of the MIX page, then (level view) force the meters to draw
    (r'''x_.c(psel, mixT, 0)''',
     r'''mixW = x_.obj(120, 470, "t b b")
x_.c(psel, mixW, 0); x_.c(mixW, mixT, 1)'''),
    # needle from dE only in the PAN view
    (r'''    x_.c(dT, x_.msg(200 + k * 160, 870, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1")), 1)''',
     r'''    ndSp = x_.obj(260 + k * 160, 860, "spigot")
    x_.c(rauxM, ndSp, 0, 1)
    x_.c(dT, ndSp, 1); x_.c(ndSp, x_.msg(200 + k * 160, 870, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1")))
    # level setting: a mark on the ring (level view only)
    mkE = x_.obj(330 + k * 160, 780,
                 f"expr int({cx}+13*sin((-135+270*$f1)*0.017453)) \\; int({CY}-13*cos((-135+270*$f1)*0.017453)) \\; "
                 f"int({cx}+16*sin((-135+270*$f1)*0.017453)) \\; int({CY}-16*cos((-135+270*$f1)*0.017453))")
    x_.c(lvF[k], mkE)
    mkP = x_.obj(330 + k * 160, 810, "pack f f f f")
    for o in range(4):
        x_.c(mkE, mkP, o, o)
    mkSp = x_.obj(330 + k * 160, 840, "spigot 1")
    mkNot = x_.obj(400 + k * 160, 810, "== 0")
    x_.c(rauxM, mkNot); x_.c(mkNot, mkSp, 0, 1)
    x_.c(mkP, mkSp); x_.c(mkSp, x_.msg(330 + k * 160, 870, osc2("gLine", "iiiiii", "\\$1 \\$2 \\$3 \\$4 1")))'''),
    (r'''# FX page: 4 horizontal bars + delay time in ms''',
     r'''# --- VU meters (level view): 10 fps, only needles that moved are erased and redrawn
vuOnE = x_.obj(1300, 700, "expr $f1==3 && $f2==0 && $f3==0")
x_.c(mt, vuOnE, 0)
vpB = x_.obj(1400, 670, "t b f"); x_.c(pgT, vpB, 0); x_.c(vpB, vuOnE, 1, 1); x_.c(vpB, vuOnE, 0, 0)
vaB = x_.obj(1500, 670, "t b f"); x_.c(rauxM, vaB); x_.c(vaB, vuOnE, 1, 2); x_.c(vaB, vuOnE, 0, 0)
vuM = x_.obj(1300, 730, "metro 100")
x_.c(vuOnE, vuM)
vuTick = x_.obj(1300, 760, "t b b b b b")
x_.c(vuM, vuTick)
flagF = x_.obj(1300, 1100, "f")
flagS = x_.obj(1300, 1130, "sel 1")
flagT = x_.obj(1300, 1160, "t b b")
flag0 = x_.msg(1400, 1160, "0")
flag1 = x_.msg(1400, 1100, "1")
x_.c(vuTick, flagF, 0); x_.c(flagF, flagS); x_.c(flagS, flagT)
x_.c(flagT, flag0, 1); x_.c(flag0, flagF, 0, 1); x_.c(flag1, flagF, 0, 1)
x_.c(flagT, x_.msg(1300, 1190, "\\; oscOut sendtyped /oled/gFlip i 3"), 0)
# after a full redraw in the level view: forget the drawn needles and draw them now
vfSp = x_.obj(120, 500, "spigot 1")
vfNot = x_.obj(60, 500, "== 0")
x_.c(rauxM, vfNot); x_.c(vfNot, vfSp, 0, 1)
x_.c(mixW, vfSp, 0)
vfT = x_.obj(120, 530, "t b b")
x_.c(vfSp, vfT); x_.c(vfT, vuTick, 0)
for k, cx in enumerate(DX):
    x = 1300 + k * 220
    raw = x_.obj(x, 800, "f")
    vuIn = x_.obj(x + 80, 770, f"r tape-vu{k+1}")
    vuN = x_.obj(x + 80, 800, "expr min(1 \\, max(0 \\, ($f1-50)/50))")
    x_.c(vuIn, vuN); x_.c(vuN, raw, 0, 1)
    vE = x_.obj(x, 830,
                f"expr max($f1 \\, $f2-0.12) \\; "
                f"int({cx}+{NEE}*sin((-135+270*max($f1 \\, $f2-0.12))*0.017453))*100+"
                f"int({CY}-{NEE}*cos((-135+270*max($f1 \\, $f2-0.12))*0.017453))")
    x_.c(vuTick, raw, 4 - k); x_.c(raw, vE)
    x_.c(vE, vE, 0, 1)                        # fall-back state (needle ballistics)
    chg = x_.obj(x, 860, "change")
    x_.c(vE, chg, 1)
    x_.c(vfT, x_.msg(x + 80, 860, "set -1"), 1) if False else None
    setM = x_.msg(x + 80, 860, "set -1")
    x_.c(vfT, setM, 1); x_.c(setM, chg)
    cT = x_.obj(x, 890, "t f f b")
    x_.c(chg, cT)
    prevF = x_.obj(x + 100, 920, f"f {cx * 100 + CY}")
    dec1 = x_.obj(x + 100, 950, "expr int($f1/100) \\; $f1%100")
    pk1 = x_.obj(x + 100, 980, "pack f f")
    x_.c(cT, prevF, 2); x_.c(prevF, dec1); x_.c(dec1, pk1, 1, 1); x_.c(dec1, pk1, 0, 0)
    x_.c(pk1, x_.msg(x + 100, 1010, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 0")))      # erase old needle
    dec2 = x_.obj(x, 950, "expr int($f1/100) \\; $f1%100")
    pk2 = x_.obj(x, 980, "pack f f")
    x_.c(cT, dec2, 1); x_.c(dec2, pk2, 1, 1); x_.c(dec2, pk2, 0, 0)
    x_.c(pk2, x_.msg(x, 1010, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1") + " " +
                     osc2("gFilledCircle", "iiiii", f"{cx} {CY} 2 1")))                           # draw new
    x_.c(cT, prevF, 0, 1); x_.c(cT, flag1, 0)

# FX page: 4 horizontal bars + delay time in ms'''),
])
s = open("genmix.py").read()
s = s.replace('    x_.c(vfT, x_.msg(x + 80, 860, "set -1"), 1) if False else None\n', "")
assert "if False" not in s
open("genmix.py", "w").write(s)
print("vu applied")

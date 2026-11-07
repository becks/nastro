#!/usr/bin/env python3
"""New master reverb (reverb.pd from genrev.py) replacing the 4-line one; AUX + knobs on the FX page edit it
(DECAY TONO PRE MOD, pickup ctx 16 -> pkval 68), its own screen while AUX is held, saved with the project."""
import shutil

for f in ("gen.py", "genmix.py", "genproj.py"):
    shutil.copy(f, f + ".pre-reverb")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


DEF = "0.5 0.6 0.15 0.3"          # decay ~2.2 s, tone ~5 kHz, pre 18 ms, mod 0.3

# ------------------------------------------------ master.pd: swap the reverb
s = open("genmix.py").read()
a = s.index("# --- reverb: 4-line feedback delay network")
b = s.index("# mono copy of the whole output")
s = s[:a] + '''# --- reverb (reverb.pd: diffusers + 8-line FDN, switches itself off when unused)
rmix = smooth(880, 40, "fx-rmix", 0)
rin = ms.obj(600, 400, "+~")
ms.c(dry, rin, 0, 0); ms.c(drd, rin, 0, 1)
rsend = ms.obj(600, 440, "*~")
ms.c(rin, rsend, 0, 0); ms.c(rmix, rsend, 0, 1)
rvb = ms.obj(600, 480, "reverb")
ms.c(rsend, rvb)
gL = ms.obj(600, 790, "*~ 0.5"); gR = ms.obj(760, 790, "*~ 0.5")
ms.c(rvb, gL, 0); ms.c(rvb, gR, 1); ms.c(gL, ol); ms.c(gR, orr)
''' + s[b:]
open("genmix.py", "w").write(s)

edit("genmix.py", [
    # knobs on the FX page: AUX held -> reverb parameters
    ('x_.c(rpg, rfx, 1)', '''fxAux = x_.obj(500, 120, "list prepend 0")
x_.c(x_.obj(560, 90, "r aux"), fxAux, 0, 1)
fxAuxR = x_.obj(500, 135, "route 0 1")
x_.c(rpg, fxAux, 1); x_.c(fxAux, fxAuxR); x_.c(fxAuxR, rfx, 0)
x_.c(fxAuxR, x_.obj(600, 150, "s rvb-knob"), 1)'''),
    # screen: FX page or, with AUX, the reverb page
    ('x_.c(psel, fxT, 1)', '''fxPgAux = x_.obj(900, 440, "f")
x_.c(x_.obj(960, 410, "r aux"), fxPgAux, 0, 1)
fxPgS = x_.obj(900, 455, "sel 0 1")
x_.c(psel, fxPgAux, 1); x_.c(fxPgAux, fxPgS); x_.c(fxPgS, fxT, 0)
# reverb page: title with the decay time, 4 bars
rvT = x_.obj(1600, 470, "t b b b b b b")
x_.c(fxPgS, rvT, 1)
x_.c(rvT, x_.msg(1600, 500, " ".join(
    [osc2("gPrintln", "iiiiis", "1 1 8 1 RIVERBERO")] +
    [osc2("gPrintln", "iiiiis", f"1 {15 + k * 12} 8 1 {nm}") for k, nm in enumerate(("DEC", "TONO", "PRE", "MOD"))] +
    [osc2("gBox", "iiiiii", f"34 {14 + k * 12} 93 9 1") for k in range(4)])), 5)
rvV = []
for k in range(4):
    f_ = x_.obj(1600 + k * 70, 560, "f")
    rvV.append(f_)
rvIn = x_.obj(1600, 530, "route 1 2 3 4")
x_.c(x_.obj(1600, 500, "r rvb-knob"), rvIn); x_.c(x_.obj(1700, 500, "r rvb-set"), rvIn)
rvDef = x_.msg(1800, 500, "1 0.5 \\\\, 2 0.6 \\\\, 3 0.15 \\\\, 4 0.3")
x_.c(x_.obj(1800, 470, "loadbang"), rvDef); x_.c(rvDef, rvIn)
for k in range(4):
    x_.c(rvIn, rvV[k], k, 1)
    e_ = x_.obj(1600 + k * 70, 600, "expr max(0 \\\\, int($f1*89))")
    x_.c(rvT, rvV[k], 4 - k); x_.c(rvV[k], e_)
    x_.c(e_, x_.msg(1600 + k * 70, 640 + k * 30, osc2("gFillArea", "iiiiii", f"36 {16 + k * 12} \\\\$1 5 1")))
# decay in seconds in the title (one decimal)
rvSec = x_.obj(1900, 560, "expr int(0.4*pow(30 \\\\, $f1)*10+0.5)/10.0")
rvTV = x_.obj(1900, 530, "t b")
x_.c(rvT, rvTV, 0)
rvD = x_.obj(1950, 530, "f")
x_.c(rvIn, rvD, 0, 1)
x_.c(rvTV, rvD); x_.c(rvD, rvSec)
x_.c(rvSec, x_.msg(1900, 590, osc2("gPrintln", "iiiiifs", "80 1 8 1 \\\\$1 s")))'''),
])

edit("gen.py", [
    ('m.obj(560, 530, "table pkval 64")', 'm.obj(560, 530, "table pkval 68")'),
    ('m.obj(680, 530, "table pkpick 64")', 'm.obj(680, 530, "table pkpick 68")'),
    ('if($f1==3 && $f2==1 \\\\, 5 \\\\,', 'if($f1==3 && $f2==1 \\\\, if($f5==1 \\\\, 16 \\\\, 5) \\\\,'),
    ('0.583 0.5 0.6 0.6 \\\\; pkphys', f'0.583 0.5 0.6 0.6 {DEF} \\\\; pkphys'),
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentomb.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentomb.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genrev.py")).read())'),
])

edit("genproj.py", [
    ('(15, "tomb-set")]', '(15, "tomb-set"), (16, "rvb-set")]'),
    ('p.c(fixT, fixE, 1); p.c(fixE, fixS); p.c(fixS, p.msg(900, 850, "\\\\; pkval 60 0.583 0.5 0.6 0.6"))',
     f'''p.c(fixT, fixE, 1); p.c(fixE, fixS); p.c(fixS, p.msg(900, 850, "\\\\; pkval 60 0.583 0.5 0.6 0.6"))
fixE2 = p.obj(800, 790, "expr pkval[64]+pkval[65]+pkval[66]+pkval[67]==0")
fixS2 = p.obj(800, 820, "sel 1")
p.c(fixT, fixE2, 1); p.c(fixE2, fixS2); p.c(fixS2, p.msg(800, 850, "\\\\; pkval 64 {DEF}"))'''),
])
print("reverb applied")

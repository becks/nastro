#!/usr/bin/env python3
"""DJ filter per tape track: MIX gets a 3rd page FILTER (AUX+D cycles MIX -> FX -> FILTER). Knob k = track k:
centre (dead zone 0.47..0.53) = off, left = low-pass (18 kHz .. 80 Hz), right = high-pass (20 Hz .. 8 kHz).
AUX + knob k = resonance of track k. One biquad~ per track after its level (coefficients computed only when a
knob moves; off = 0 0 1 0 0, transparent). Pickup contexts 20 (filter) / 21 (resonance), pkval 88."""
import shutil

for f in ("genmix.py", "gentape.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-trackfilter")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


def E(s):
    """expression text -> escaped text as it must appear inside a Python string of the generator source"""
    return s.replace(",", " \\\\, ").replace(";", " \\\\; ")


# ---------------- biquad coefficients (RBJ), expr inputs: $f1 knob value, $f2 resonance knob, $f3 sample rate
SR = "if($f3>0, $f3, 44100)"
F = "if($f1<0.47, 80*pow(225, $f1/0.47), 20*pow(400, ($f1-0.53)/0.47))"
W = f"(6.2831853*min({F}, 0.45*{SR})/{SR})"
C = f"cos({W})"
AL = f"(sin({W})/(2*(0.6+$f2*6)))"
LP = "($f1<0.47)"
ON = f"({LP} || ($f1>0.53))"
B0 = f"if({LP}, (1-{C})/2, (1+{C})/2)"
B1 = f"if({LP}, 1-{C}, -(1+{C}))"
COEF = [f"if({ON}, 2*{C}/(1+{AL}), 0)",                 # fb1
        f"if({ON}, -(1-{AL})/(1+{AL}), 0)",              # fb2
        f"if({ON}, {B0}/(1+{AL}), 1)",                   # ff1
        f"if({ON}, {B1}/(1+{AL}), 0)",                   # ff2
        f"if({ON}, {B0}/(1+{AL}), 0)"]                   # ff3 (= ff1 for LP and HP)
COEF_EXPR = "expr " + E("; ".join(COEF))

TAPE = f'''    # DJ filter (apply_trackfilter.py): one biquad~ after the level, before pan and VU
    bq = t.obj(x, 875, "biquad~ 0 0 1 0 0")
    t.c(lv, bq)
    cE = t.obj(x + 300, 1060, "{COEF_EXPR}")
    cP = t.obj(x + 300, 1090, "pack f f f f f")
    for o in range(5):
        t.c(cE, cP, o, o)
    t.c(cP, bq)
    t.c(srT, cE, 0, 2)
    vF = t.obj(x + 300, 1030, "f 0.5")
    fIn = t.obj(x + 300, 1000, "t f f")
    t.c(fRt, fIn, k); t.c(fIn, vF, 1, 1); t.c(fIn, cE, 0)
    rIn = t.obj(x + 400, 1000, "t b f")
    t.c(rRt, rIn, k); t.c(rIn, cE, 1, 1); t.c(rIn, vF, 0); t.c(vF, cE)
    t.c(bq, gLp, 0, 0); t.c(plL, gLp, 0, 1); t.c(bq, gRp, 0, 0); t.c(plR, gRp, 0, 1)'''

edit("gentape.py", [
    ('# --- tracks: read, level, overdub write', '''# --- DJ filter knobs per track (tfilt-knob / tfilt-set: k value ; tres-knob / tres-set: k resonance)
fRt = t.obj(1500, 950, "route 1 2 3 4")
t.c(t.obj(1500, 920, "r tfilt-knob"), fRt); t.c(t.obj(1600, 920, "r tfilt-set"), fRt)
rRt = t.obj(1700, 950, "route 1 2 3 4")
t.c(t.obj(1700, 920, "r tres-knob"), rRt); t.c(t.obj(1800, 920, "r tres-set"), rRt)
fDef = t.msg(1900, 920, "1 0.3 \\\\, 2 0.3 \\\\, 3 0.3 \\\\, 4 0.3")
t.c(t.obj(1900, 890, "loadbang"), fDef); t.c(fDef, rRt)
# --- tracks: read, level, overdub write'''),
    ('    t.c(lv, gLp, 0, 0); t.c(plL, gLp, 0, 1); t.c(lv, gRp, 0, 0); t.c(plR, gRp, 0, 1)', TAPE),
    ('    t.c(lv, vuEnv); t.c(vuEnv, t.obj(x, 1020, f"s tape-vu{k+1}"))',
     '    t.c(bq, vuEnv); t.c(vuEnv, t.obj(x, 1020, f"s tape-vu{k+1}"))'),
])

# ---------------- MIX: 3rd page, knob routing, screen
SCREEN = r'''
# ------------------------------------------------ FILTER page (apply_trackfilter.py): 4 dials, LP <- off -> HP
fltV, resV = [], []
fvR = x_.obj(2600, 520, "route 1 2 3 4"); frR = x_.obj(2800, 520, "route 1 2 3 4")
x_.c(x_.obj(2600, 490, "r tfilt-knob"), fvR); x_.c(x_.obj(2650, 470, "r tfilt-set"), fvR)
x_.c(x_.obj(2800, 490, "r tres-knob"), frR); x_.c(x_.obj(2850, 470, "r tres-set"), frR)
for k in range(4):
    a = x_.obj(2600 + k * 50, 550, "f 0.5"); b = x_.obj(2800 + k * 50, 550, "f 0.3")
    x_.c(fvR, a, k, 1); x_.c(frR, b, k, 1)
    fltV.append(a); resV.append(b)
x_.c(x_.obj(2900, 490, "r tres-knob"), dOne); x_.c(x_.obj(2950, 490, "r tfilt-set"), dOne)
x_.c(x_.obj(3000, 490, "r tfilt-knob"), dOne)
fiT = x_.obj(2600, 600, "t b b b b b")                 # 4 header (AUX state first), 3..0 tracks 1..4
x_.c(psel, fiT, 2)
fiAux = x_.obj(2500, 600, "f")
x_.c(x_.obj(2500, 570, "r aux"), fiAux, 0, 1)
fiHead = x_.obj(2500, 630, "sel 0 1")
x_.c(fiT, fiAux, 4); x_.c(fiAux, fiHead)
x_.c(fiHead, x_.msg(2500, 660, osc2("gPrintln", "iiiiis", "1 1 8 1 FILTER")), 0)
x_.c(fiHead, x_.msg(2650, 660, osc2("gFillArea", "iiiiii", "0 0 21 10 1") + " " + osc2("gPrintln", "iiiiis", "2 1 8 0 RES")), 1)
for k in range(4):
    cx = 16 + 32 * k
    X = 2600 + k * 260
    tb = x_.obj(X, 700, "t b b")
    x_.c(fiT, tb, 3 - k)
    # text expr: $f1 mode (hot) $f2 AUX $f3 resonance knob $f4 frequency
    txE = x_.obj(X, 880, "expr if($f2 \\, 5 \\, if($f1==0 \\, 0 \\, ($f1-1)*2+1)) \\; "
                         "if($f2 \\, int((0.6+$f3*6)*10)/10.0 \\, int($f4))")
    x_.c(fiAux, txE, 0, 1)
    x_.c(tb, resV[k], 1); x_.c(resV[k], txE, 0, 2)
    # dial: needle from -135 (full LP) through 0 (off, up) to +135 (full HP); outlets 0 x 1 y 2 mode 3 frequency
    dE = x_.obj(X, 760, "expr "
                f"int({cx}+9*sin((-135+270*$f1)*0.017453)) \\; int(28-9*cos((-135+270*$f1)*0.017453)) \\; "
                "if($f1<0.47 \\, 1 \\, if($f1>0.53 \\, 2 \\, 0)) \\; "
                "if($f1<0.47 \\, 80*pow(225 \\, $f1/0.47) \\, 20*pow(400 \\, ($f1-0.53)/0.47))")
    x_.c(tb, fltV[k], 0); x_.c(fltV[k], dE)
    x_.c(dE, txE, 3, 3)                                 # frequency (fires first, cold)
    x_.c(dE, txE, 2, 0)                                 # mode (hot)
    dP = x_.obj(X, 790, "pack f f")
    x_.c(dE, dP, 1, 1); x_.c(dE, dP, 0, 0)
    x_.c(dP, x_.msg(X, 820, osc2("gCircle", "iiiii", f"{cx} 28 11 1") + " " +
                    osc2("gLine", "iiiiii", f"{cx} 28 \\$1 \\$2 1")))
    tP = x_.obj(X, 910, "pack f f")
    x_.c(txE, tP, 1, 1); x_.c(txE, tP, 0, 0)
    tR = x_.obj(X, 940, "route 0 1 2 3 4 5")
    x_.c(tP, tR)
    L1 = lambda txt: osc2("gPrintln", "iiiiis", f"{cx - 12} 43 8 1 {k + 1} {txt}")
    V = lambda suf: osc2("gPrintln", "iiiiif" + ("s" if suf else ""), f"{cx - 12} 54 8 1 \\$1" + (f" {suf}" if suf else ""))
    x_.c(tR, x_.msg(X, 970, L1("--")), 0)
    x_.c(tR, x_.msg(X, 1000, L1("LP") + " " + V("")), 1)
    x_.c(tR, x_.msg(X, 1030, L1("LP") + " " + V("k")), 2)
    x_.c(tR, x_.msg(X + 130, 970, L1("HP") + " " + V("")), 3)
    x_.c(tR, x_.msg(X + 130, 1000, L1("HP") + " " + V("k")), 4)
    x_.c(tR, x_.msg(X + 130, 1030, L1("Q") + " " + V("")), 5)
'''
assert "if False" not in SCREEN

edit("genmix.py", [
    ('pgN = x_.obj(20, 220, "== 0")', 'pgN = x_.obj(20, 220, "expr ($f1+1)%3")             # MIX -> FX -> FILTER'),
    ('rpg = x_.obj(200, 120, "route 0 1")', 'rpg = x_.obj(200, 120, "route 0 1 2")'),
    ('x_.c(fxAuxR, x_.obj(600, 150, "s rvb-knob"), 1)', '''x_.c(fxAuxR, x_.obj(600, 150, "s rvb-knob"), 1)
# FILTER page: knob k -> track k filter, AUX held -> its resonance
fiK = x_.obj(700, 120, "list prepend 0")
x_.c(x_.obj(760, 90, "r aux"), fiK, 0, 1)
fiKR = x_.obj(700, 135, "route 0 1")
x_.c(rpg, fiK, 2); x_.c(fiK, fiKR)
x_.c(fiKR, x_.obj(700, 150, "s tfilt-knob"), 0); x_.c(fiKR, x_.obj(800, 150, "s tres-knob"), 1)'''),
    ('psel = x_.obj(200, 430, "sel 0 1")', 'psel = x_.obj(200, 430, "sel 0 1 2")'),
    ('x_.save("mix.pd")', SCREEN + 'x_.save("mix.pd")'),
])

DEF = "0.5 0.5 0.5 0.5 0.3 0.3 0.3 0.3"        # filters off, moderate resonance (pkval 80..87)
edit("gen.py", [
    ('m.obj(560, 530, "table pkval 80")', 'm.obj(560, 530, "table pkval 88")'),
    ('m.obj(680, 530, "table pkpick 80")', 'm.obj(680, 530, "table pkpick 88")'),
    ('if($f1==3 && $f2==1 \\\\, if($f5==1 \\\\, 16 \\\\, 5) \\\\,',
     'if($f1==3 && $f2==2 \\\\, if($f5==1 \\\\, 21 \\\\, 20) \\\\, if($f1==3 && $f2==1 \\\\, if($f5==1 \\\\, 16 \\\\, 5) \\\\,'),
    ('$f1)))))))))")', '$f1))))))))))")'),
    ('0.5 0.5 0.5 0.4 0.4 0.5 0.7 0.3 \\\\; pkphys', f'0.5 0.5 0.5 0.4 0.4 0.5 0.7 0.3 {DEF} \\\\; pkphys'),
])
edit("genproj.py", [
    ('(18, "air-knob"), (19, "bell-knob")]', '(18, "air-knob"), (19, "bell-knob"), (20, "tfilt-set"), (21, "tres-set")]'),
    ('p.c(fixT, fixE4, 1)', '''fixE5 = p.obj(500, 790, "expr pkval[80]+pkval[81]+pkval[82]+pkval[83]+pkval[84]+pkval[85]+pkval[86]+pkval[87]==0")
fixS5 = p.obj(500, 820, "sel 1")
p.c(fixT, fixE5, 1); p.c(fixE5, fixS5); p.c(fixS5, p.msg(500, 850, "\\\\; pkval 80 ''' + DEF + '''"))
p.c(fixT, fixE4, 1)'''),
])
print("trackfilter applied")

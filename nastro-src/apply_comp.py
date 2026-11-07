#!/usr/bin/env python3
"""Master compressor, before the limiter. MIX page 4 MASTER (AUX+D cycles MIX -> FX -> FILTER -> MASTER):
knob 1 COMP amount (0 = off; threshold -2 .. -30 dBFS RMS, ratio 4:1, auto make-up up to +8 dB),
knob 2 SPEED (attack 5..50 ms, release 50..800 ms). The screen shows the gain reduction (GR).
Feed-forward: env~ on (L+R)/2 every 128 samples -> gain target -> line~ ramp (attack when reducing more,
release otherwise). Off = gain 1 and no control work. Pickup ctx 22 (pkval 92)."""
import shutil

for f in ("genmix.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-comp")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


MASTER = r'''
# --- master compressor (apply_comp.py): feed-forward RMS, before the limiter
cpL = ms.obj(20, 835, "*~"); cpR = ms.obj(200, 835, "*~")
cpLn = ms.obj(400, 800, "line~")
ms.c(cpLn, cpL, 0, 1); ms.c(cpLn, cpR, 0, 1)
cpI = ms.msg(500, 770, "1")
ms.c(ms.obj(500, 740, "loadbang"), cpI); ms.c(cpI, cpLn)
cpSum = ms.obj(1300, 820, "+~")
ms.c(ol, cpSum, 0, 0); ms.c(orr, cpSum, 0, 1)
cpHalf = ms.obj(1300, 850, "*~ 0.5")
cpEnv = ms.obj(1300, 880, "env~ 1024 128")
ms.c(cpSum, cpHalf); ms.c(cpHalf, cpEnv)
cpSp = ms.obj(1300, 910, "spigot")
ms.c(cpEnv, cpSp)
# parameters: comp-knob / comp-set "k v": 1 amount, 2 speed
cpR_ = ms.obj(1500, 820, "route 1 2")
ms.c(ms.obj(1500, 790, "r comp-knob"), cpR_); ms.c(ms.obj(1600, 790, "r comp-set"), cpR_)
cpDef = ms.msg(1700, 790, "1 0 \\, 2 0.5")
ms.c(ms.obj(1700, 760, "loadbang"), cpDef); ms.c(cpDef, cpR_)
# gain expr: $f1 env dB (100 = 0 dBFS)  $f2 amount  $f3 speed  $f4 previous reduction (dB)
#   outlets: 0 reduction dB, 1 ramp ms, 2 linear gain
cpE = ms.obj(1300, 950, "expr max(0 \\, ($f1-100)-(-2-$f2*28))*0.75 \\; "
                        "if(max(0 \\, ($f1-100)-(-2-$f2*28))*0.75>$f4 \\, 5+45*$f3 \\, 50+750*$f3) \\; "
                        "pow(10 \\, ($f2*8-max(0 \\, ($f1-100)-(-2-$f2*28))*0.75)/20)")
ms.c(cpSp, cpE)
cpP = ms.obj(1300, 980, "pack f f f")
ms.c(cpE, cpP, 2, 2); ms.c(cpE, cpP, 1, 1); ms.c(cpE, cpP, 0, 0)
cpU = ms.obj(1300, 1010, "unpack f f f")
ms.c(cpP, cpU)
cpG = ms.obj(1400, 1040, "pack f f")                  # unpack fires gain (outlet 2) before ramp ms (outlet 1)
ms.c(cpU, cpG, 2, 1); ms.c(cpU, cpG, 1, 0)            # gain -> cold, ramp ms -> hot (last)
cpGM = ms.msg(1400, 1070, "\\$2 \\$1")                # line~ wants "target time"
ms.c(cpG, cpGM); ms.c(cpGM, cpLn)
ms.c(cpU, cpE, 0, 3)                                  # reduction -> state (cold inlet), after all outlets ran
ms.c(cpU, ms.obj(1300, 1040, "s comp-gr"), 0)
# amount: store it, open/close the detector, back to unity gain when off
cpAT = ms.obj(1500, 850, "t f f")
ms.c(cpR_, cpAT, 0)
ms.c(cpAT, cpE, 1, 1)
cpOn = ms.obj(1600, 880, "> 0.02")
ms.c(cpAT, cpOn, 0); ms.c(cpOn, cpSp, 0, 1)
cpOff = ms.obj(1600, 910, "sel 0")
cpUnity = ms.msg(1600, 940, "1 50")
cpZ = ms.msg(1700, 940, "\\; comp-gr 0")
ms.c(cpOn, cpOff); ms.c(cpOff, cpUnity); ms.c(cpUnity, cpLn); ms.c(cpOff, cpZ)
ms.c(cpR_, cpE, 1, 2)                                 # speed (cold)
'''

edit("genmix.py", [
    ('ms.c(ol, lgL); ms.c(orr, lgR); ms.c(lgL, lcL); ms.c(lgR, lcR)',
     'ms.c(lgL, lcL); ms.c(lgR, lcR)                             # (ol / orr reach lgL / lgR through the compressor)'),
    ('ms.c(ol, laL); ms.c(orr, laR); ms.c(laL, lmx, 0, 0); ms.c(laR, lmx, 0, 1)',
     'ms.c(laL, lmx, 0, 0); ms.c(laR, lmx, 0, 1)                 # (limiter detector fed after the compressor)'),
])
s = open("genmix.py").read()
anchor = "# mono copy of the whole output"
assert s.count(anchor) == 1
s = s.replace(anchor, MASTER.lstrip("\n") + '''ms.c(ol, cpL); ms.c(orr, cpR)
ms.c(cpL, lgL); ms.c(cpR, lgR)
ms.c(cpL, laL); ms.c(cpR, laR)
''' + anchor)
open("genmix.py", "w").write(s)

PAGE = r'''
# ------------------------------------------------ MASTER page (apply_comp.py): COMP, SPEED, gain reduction
cvR = x_.obj(3600, 520, "route 1 2")
x_.c(x_.obj(3600, 490, "r comp-knob"), cvR); x_.c(x_.obj(3700, 490, "r comp-set"), cvR)
cvA = x_.obj(3600, 550, "f 0"); cvS = x_.obj(3700, 550, "f 0.5"); cvG = x_.obj(3800, 550, "f 0")
x_.c(cvR, cvA, 0, 1); x_.c(cvR, cvS, 1, 1)
x_.c(x_.obj(3800, 520, "r comp-gr"), cvG, 0, 1)
x_.c(x_.obj(3900, 490, "r comp-knob"), dOne); x_.c(x_.obj(3950, 490, "r comp-set"), dOne)
# live GR while the page is shown: redraw 10x/s
mpOn = x_.obj(3600, 600, "expr $f1==3 && $f2==3")
mpM = x_.obj(3600, 580, "t f")
x_.c(x_.obj(3600, 560, "r mode"), mpM); x_.c(mpM, mpOn, 0, 0)
mpP = x_.obj(3700, 580, "t b f")
x_.c(x_.obj(3700, 560, "r mix-page"), mpP); x_.c(mpP, mpOn, 1, 1); x_.c(mpP, mpOn, 0, 0)
mpMet = x_.obj(3600, 630, "metro 100")
x_.c(mpOn, mpMet); x_.c(mpMet, dOne)
msT = x_.obj(3600, 660, "t b b b b")
x_.c(psel, msT, 3)
x_.c(msT, x_.msg(3600, 690, osc2("gPrintln", "iiiiis", "1 1 8 1 MASTER") + " " +
                 osc2("gPrintln", "iiiiis", "1 15 8 1 COMP") + " " + osc2("gPrintln", "iiiiis", "1 27 8 1 SPEED") + " " +
                 osc2("gPrintln", "iiiiis", "1 39 8 1 GR") + " " +
                 osc2("gBox", "iiiiii", "64 14 63 9 1") + " " + osc2("gBox", "iiiiii", "64 26 63 9 1") + " " +
                 osc2("gBox", "iiiiii", "64 38 63 9 1")), 3)
caE = x_.obj(3600, 720, "expr int($f1*100+0.5) \\; int($f1*59)")
x_.c(msT, cvA, 2); x_.c(cvA, caE)
caP = x_.obj(3600, 750, "pack f f")
x_.c(caE, caP, 1, 1); x_.c(caE, caP, 0, 0)
x_.c(caP, x_.msg(3600, 780, osc2("gPrintln", "iiiiif", "38 15 8 1 \\$1") + " " + osc2("gFillArea", "iiiiii", "66 16 \\$2 5 1")))
csE = x_.obj(3800, 720, "expr int($f1*100+0.5) \\; int($f1*59)")
x_.c(msT, cvS, 1); x_.c(cvS, csE)
csP = x_.obj(3800, 750, "pack f f")
x_.c(csE, csP, 1, 1); x_.c(csE, csP, 0, 0)
x_.c(csP, x_.msg(3800, 780, osc2("gPrintln", "iiiiif", "38 27 8 1 \\$1") + " " + osc2("gFillArea", "iiiiii", "66 28 \\$2 5 1")))
cgE = x_.obj(4000, 720, "expr int($f1*10+0.5)/10.0 \\; int(min(59 \\, $f1*59/20))")
x_.c(msT, cvG, 0); x_.c(cvG, cgE)
cgP = x_.obj(4000, 750, "pack f f")
x_.c(cgE, cgP, 1, 1); x_.c(cgE, cgP, 0, 0)
x_.c(cgP, x_.msg(4000, 780, osc2("gPrintln", "iiiiif", "26 39 8 1 -\\$1") + " " + osc2("gFillArea", "iiiiii", "66 40 \\$2 5 1")))
'''

edit("genmix.py", [
    ('pgN = x_.obj(20, 220, "expr ($f1+1)%3")             # MIX -> FX -> FILTER',
     'pgN = x_.obj(20, 220, "expr ($f1+1)%4")             # MIX -> FX -> FILTER -> MASTER'),
    ('rpg = x_.obj(200, 120, "route 0 1 2")', 'rpg = x_.obj(200, 120, "route 0 1 2 3")'),
    ('x_.c(fiKR, x_.obj(700, 150, "s tfilt-knob"), 0); x_.c(fiKR, x_.obj(800, 150, "s tres-knob"), 1)',
     'x_.c(fiKR, x_.obj(700, 150, "s tfilt-knob"), 0); x_.c(fiKR, x_.obj(800, 150, "s tres-knob"), 1)\n'
     'x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)                # MASTER page: knob 1 COMP, knob 2 SPEED'),
    ('psel = x_.obj(200, 430, "sel 0 1 2")', 'psel = x_.obj(200, 430, "sel 0 1 2 3")'),
    ('x_.save("mix.pd")', PAGE + 'x_.save("mix.pd")'),
])

DEF = "0 0.5 0 0"
edit("gen.py", [
    ('m.obj(560, 530, "table pkval 88")', 'm.obj(560, 530, "table pkval 92")'),
    ('m.obj(680, 530, "table pkpick 88")', 'm.obj(680, 530, "table pkpick 92")'),
    ('if($f1==3 && $f2==2 \\\\, if($f5==1 \\\\, 21 \\\\, 20) \\\\,',
     'if($f1==3 && $f2==3 \\\\, 22 \\\\, if($f1==3 && $f2==2 \\\\, if($f5==1 \\\\, 21 \\\\, 20) \\\\,'),
    ('$f1))))))))))")', '$f1)))))))))))")'),
    ('0.5 0.5 0.5 0.5 0.3 0.3 0.3 0.3 \\\\; pkphys', f'0.5 0.5 0.5 0.5 0.3 0.3 0.3 0.3 {DEF} \\\\; pkphys'),
])
edit("genproj.py", [
    ('(20, "tfilt-set"), (21, "tres-set")]', '(20, "tfilt-set"), (21, "tres-set"), (22, "comp-set")]'),
    ('p.c(fixT, fixE6, 1)', '''fixE7 = p.obj(300, 790, "expr pkval[88]+pkval[89]==0")
fixS7 = p.obj(300, 820, "sel 1")
p.c(fixT, fixE7, 1); p.c(fixE7, fixS7); p.c(fixS7, p.msg(300, 850, "\\\\; pkval 88 ''' + DEF + '''"))
p.c(fixT, fixE6, 1)'''),
])
print("comp applied")

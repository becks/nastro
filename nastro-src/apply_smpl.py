#!/usr/bin/env python3
"""Hook the SMPL engine + sample recorder into synth / main / master / mac-sim."""
import shutil

for f in ("gen.py", "gensynth.py", "genmix.py", "gensim.py"):
    shutil.copy(f, f + ".pre-smpl")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gensynth.py", [
    (r'''        ("SPRD", "expr $f1*25", "pd-spread", 0.5, "expr int($f1)"),
    ]),
]''', r'''        ("SPRD", "expr $f1*25", "pd-spread", 0.5, "expr int($f1)"),
    ]),
    ("smpl", 4, "smpl-voice", 0.8, [
        ("START", "t f", "smp-start", 0.0, "expr int($f1*100)"),
        ("END", "t f", "smp-end", 1.0, "expr int($f1*100)"),
        ("REL", "expr int(5+pow($f1 \\, 2)*2995)", "smp-rel", 0.3, "t f"),
        ("LOOP", "expr $f1>0.5", "smp-loop", 0.0, "t f"),
    ]),
]'''),
    (r'''NAMES = ["FM", "SUB", "PLUK", "PAD"]''', r'''NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL"]'''),
    (r'''md4 = s.obj(20, 290, "% 4")''', r'''md4 = s.obj(20, 290, "% 5")'''),
    (r'''    rt = s.obj(20, y + 60, "route 0 1 2 3")''', r'''    rt = s.obj(20, y + 60, "route 0 1 2 3 4")'''),
    (r'''nmS = s.obj(800, 370, "sel 0 1 2 3")''', r'''nmS = s.obj(800, 370, "sel 0 1 2 3 4")'''),
    (r'''octM = s.msg(1100, 370, osc5("gPrintln", "iiiiisf", "86 1 8 1 oct \\$1"))''',
     r'''octM = s.msg(1100, 370, osc5("gPrintln", "iiiiisf", "92 1 8 1 oct \\$1"))
# REC badge while sampling
fRec = s.obj(1250, 340, "f")
s.c(s.obj(1250, 310, "r smp-recording"), fRec, 0, 1)
s.c(s.obj(1350, 310, "r smp-recording"), dirty)
recS = s.obj(1250, 370, "sel 1")
recM = s.msg(1250, 400, osc5("gFillArea", "iiiiii", "67 0 21 10 1") + " " + osc5("gPrintln", "iiiiis", "69 1 8 0 REC"))
s.c(dT, fRec, 1); s.c(fRec, recS); s.c(recS, recM)'''),
])

edit("gen.py", [
    (r'''m.obj(1030, 680, "seq")''', r'''m.obj(1030, 680, "seq")
m.obj(1080, 680, "synth-smpl")
m.obj(1170, 680, "smpl")'''),
    (r'''m.obj(560, 530, "table pkval 40")''', r'''m.obj(560, 530, "table pkval 44")'''),
    (r'''m.obj(680, 530, "table pkpick 40")''', r'''m.obj(680, 530, "table pkpick 44")'''),
    (r'''0 1 0.47 0 \\; pkphys''', r'''0 1 0.47 0 0 1 0.3 0 \\; pkphys'''),
    (r'''if($f1==0 && $f3>0 \\, 5+$f3 \\, ''', r'''if($f1==0 && $f3>0 \\, if($f3==4 \\, 10 \\, 5+$f3) \\, '''),
    (r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genseq.py")).read())''',
     r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genseq.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gensmpl.py")).read())'''),
])

edit("genmix.py", [
    (r'''ms.c(outLr, gL); ms.c(outRr, gR); ms.c(gL, ol); ms.c(gR, orr)''',
     r'''ms.c(outLr, gL); ms.c(outRr, gR); ms.c(gL, ol); ms.c(gR, orr)
# mono copy of the whole output, for resampling (SMPL engine, AUX+F5)
mA = ms.obj(400, 860, "*~ 1"); mB = ms.obj(500, 860, "*~ 0.5"); mS = ms.obj(400, 890, "+~")
ms.c(dry, mA); ms.c(drd, mA); ms.c(gL, mB); ms.c(gR, mB); ms.c(mA, mS, 0, 0); ms.c(mB, mS, 0, 1)
ms.c(mS, ms.obj(400, 920, "s~ nst-master"))'''),
])

edit("gensim.py", [
    (r'''dac = add("obj", 600, 490, "dac~")''', r'''dac = add("obj", 600, 490, "dac~")
adc = add("obj", 700, 420, "adc~")
sinl = add("obj", 700, 450, "s~ inL")
sinr = add("obj", 760, 470, "s~ inR")
c(adc, sinl, 0, 0); c(adc, sinr, 1, 0)'''),
    (r'''codes += [ord("["), ord("]")]
notes_for += [82, 83]''', r'''codes += [ord("["), ord("]"), ord(";"), ord("'")]
notes_for += [82, 83, 76, 77]'''),
    (r'''[ ] = tasti 82-83 (Spazio+[ ] = ottava)")''', r'''[ ] = tasti 82-83 (Spazio+[ ] = ottava) / ; ' = tasti 76-77 (Spazio+; campiona ingresso / Spazio+' campiona uscita)")'''),
])
print("smpl hooked")

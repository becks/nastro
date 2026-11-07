#!/usr/bin/env python3
"""1) TAPE screen shows the overdub amount  2) synth volume: SYNTH page, AUX held + knob 1 (pickup ctx 13, saved)."""
import shutil

for f in ("gentape.py", "genscreen.py", "gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-vol")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# ---------------- 1) overdub on the TAPE screen
edit("gentape.py", [
    (r'''k3t = t.obj(960, 170, "t f f")''', r'''k3t = t.obj(960, 170, "t f f")
t.c(k3t, t.obj(1060, 200, "s tp-dub"), 1)'''),
])
edit("genscreen.py", [
    (r'''flip = g.msg(1150, 450, "\\; oscOut sendtyped /oled/gFlip i 3")
steps.append(flip)''', r'''# overdub amount, bottom left above the timeline
fDub = g.obj(1300, 330, "f 1")
g.c(g.obj(1300, 300, "r tp-dub"), fDub, 0, 1)
dubE = g.obj(1300, 360, "expr int($f1*100+0.5)")
g.c(fDub, dubE)
g.c(dubE, g.msg(1300, 390, osc("gPrintln", "iiiiisf", "1 45 8 1 DUB \\$1")))
steps.append(fDub)
flip = g.msg(1150, 450, "\\; oscOut sendtyped /oled/gFlip i 3")
steps.append(flip)'''),
    (r'''g.save("tape-screen.pd")''', r'''g.c(g.obj(1600, 90, "r tp-dub"), dOne)
g.save("tape-screen.pd")'''),
])

# ---------------- 2) synth volume
edit("gensynth.py", [
    # every engine: gain * synth volume (smoothed)
    (r'''    e.c(pk, cl); e.c(cl, g); e.c(g, cp); e.c(cp, th)''',
     r'''    vR = e.obj(160, 150, "r synth-vol"); vM = e.msg(160, 180, "\\$1 20"); vL = e.obj(160, 210, "line~")
    vG = e.obj(20, 195, "*~")
    e.c(vR, vM); e.c(vM, vL)
    e.c(pk, cl); e.c(cl, g); e.c(g, vG, 0, 0); e.c(vL, vG, 0, 1); e.c(vG, cp); e.c(cp, th)'''),
    # knobs: with AUX held, knob 1 is the volume; otherwise they go to the engine
    (r'''    s.c(r, lp); s.c(lp, rt)''',
     r'''    if suffix == "knob":
        axLp = s.obj(120, y, "list prepend 0")
        axRt = s.obj(120, y + 15, "route 0 1")
        s.c(s.obj(240, y - 30, "r aux"), axLp, 0, 1)
        s.c(r, axLp); s.c(axLp, axRt); s.c(axRt, lp, 0)
        s.c(axRt, volIn, 1)
    else:
        s.c(r, lp)
    s.c(lp, rt)'''),
    (r'''# notes / knobs to the active engine''', r'''# synth volume (knob 1 with AUX held): 0..1, 0.8 = unity gain
volIn = s.obj(700, 560, "route 1")
s.c(s.obj(700, 530, "r synth-vol-set"), volIn)
volT = s.obj(700, 590, "t f f f")
s.c(volIn, volT)
s.c(volT, s.obj(800, 620, "/ 0.8"), 2)
volSend = s.obj(800, 650, "s synth-vol")
fVol = s.obj(700, 620, "f 0.8")
volDef = s.msg(900, 590, "1 0.8")
s.c(s.obj(900, 560, "loadbang"), volDef); s.c(volDef, volIn)
# notes / knobs to the active engine'''),
    # with AUX held the SYNTH screen shows the volume instead of the rows
    (r'''s.c(engT, engF3, 2, 1); s.c(dT, engF3, 2)''', r'''s.c(engT, engF3, 2, 1)
auxD = s.obj(600, 420, "f")
s.c(s.obj(600, 390, "r aux"), auxD, 0, 1)
s.c(s.obj(520, 390, "r aux"), dirty)
s.c(s.obj(520, 360, "r synth-vol"), dirty)
auxDS = s.obj(600, 450, "sel 1 0")
s.c(dT, auxD, 2); s.c(auxD, auxDS); s.c(auxDS, engF3, 1)
volE = s.obj(600, 480, "expr int($f1*100+0.5) \\; int($f1*124)")
volP = s.obj(600, 510, "pack f f")
s.c(auxDS, fVol, 0); s.c(fVol, volE); s.c(volE, volP, 1, 1); s.c(volE, volP, 0, 0)
s.c(volP, s.msg(600, 540, osc5("gPrintln", "iiiiiss", "1 14 8 1 VOLUME SYNTH") + " " +
                osc5("gPrintln", "iiiiif", "4 24 24 1 \\$1") + " " + osc5("gBox", "iiiiii", "0 52 128 9 1") + " " +
                osc5("gFillArea", "iiiiii", "2 54 \\$2 5 1")))'''),
])
# the send / store connections need volSend / fVol defined before use: wire them at the end
s = open("gensynth.py").read()
s = s.replace('''s.save("synth.pd")''', '''s.c(volT, volSend, 2) if False else None
s.save("synth.pd")''')
s = s.replace('''s.c(volT, s.obj(800, 620, "/ 0.8"), 2)
volSend = s.obj(800, 650, "s synth-vol")
fVol = s.obj(700, 620, "f 0.8")''', '''volDiv = s.obj(800, 620, "/ 0.8")
volSend = s.obj(800, 650, "s synth-vol")
fVol = s.obj(700, 620, "f 0.8")
s.c(volT, volDiv, 2); s.c(volDiv, volSend); s.c(volT, fVol, 1, 1)''')
s = s.replace('''s.c(volT, volSend, 2) if False else None\n''', '')
assert "if False" not in s
open("gensynth.py", "w").write(s)

# ---------------- pickup context 13 (SYNTH + AUX), saved with the project
edit("gen.py", [
    (r'''m.obj(560, 530, "table pkval 52")''', r'''m.obj(560, 530, "table pkval 56")'''),
    (r'''m.obj(680, 530, "table pkpick 52")''', r'''m.obj(680, 530, "table pkpick 56")'''),
    (r'''0.5 0.5 0.5 0.5 0 0 0 0 \\; pkphys''', r'''0.5 0.5 0.5 0.5 0 0 0 0 0.8 0 0 0 \\; pkphys'''),
    (r'''if($f1==3 && $f2==0 && $f5==1 \\, 11 \\, ''', r'''if($f1==3 && $f2==0 && $f5==1 \\, 11 \\, if($f1==0 && $f5==1 \\, 13 \\, '''),
])
g = open("gen.py").read()
a = g.index('ctxE = m.obj(560, 660, "expr if($f1==5')
b = g.index('")', a)
g = g[:b] + ")" + g[b:]
open("gen.py", "w").write(g)
edit("genproj.py", [
    (r'''(3, "mix-lvl-set"), (11, "mix-pan-set"), (5, "mix-fx-set"), (4, "tempo-knob"), (9, "seq-step-set")]''',
     r'''(3, "mix-lvl-set"), (11, "mix-pan-set"), (5, "mix-fx-set"), (4, "tempo-knob"), (9, "seq-step-set"),
       (13, "synth-vol-set")]'''),
])
print("dub display + synth volume applied")

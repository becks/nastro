#!/usr/bin/env python3
"""Drum kit volume: DRUM page, AUX held + knob 1 (pickup ctx 14, saved with the project)."""
import shutil

for f in ("gendrum.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-drumvol")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gendrum.py", [
    # output: kit gain * drum volume (smoothed), 0.8 = unity
    (r'''d.c(cl, dg); d.c(dg, thr)''',
     r'''dvG = d.obj(600, 485, "*~")
dvR = d.obj(700, 440, "r drum-vol"); dvM = d.msg(700, 460, "\\$1 20"); dvL = d.obj(700, 480, "line~")
d.c(dvR, dvM); d.c(dvM, dvL)
d.c(cl, dg); d.c(dg, dvG, 0, 0); d.c(dvL, dvG, 0, 1); d.c(dvG, thr)'''),
    # knobs: with AUX held, knob 1 = kit volume
    (r'''d.c(rk, krt)''', r'''dkAx = d.obj(1000, 400, "list prepend 0")
dkAr = d.obj(1000, 415, "route 0 1")
d.c(d.obj(1100, 370, "r aux"), dkAx, 0, 1)
d.c(rk, dkAx); d.c(dkAx, dkAr); d.c(dkAr, krt, 0)
dvIn = d.obj(1200, 430, "route 1")
d.c(dkAr, dvIn, 1)
d.c(d.obj(1200, 400, "r drum-vol-set"), dvIn)
dvT = d.obj(1200, 460, "t f f")
dvDiv = d.obj(1300, 490, "/ 0.8")
fDVol = d.obj(1200, 490, "f 0.8")
d.c(dvIn, dvT); d.c(dvT, dvDiv, 1); d.c(dvDiv, d.obj(1300, 520, "s drum-vol")); d.c(dvT, fDVol, 0, 1)
dvDef = d.msg(1400, 460, "1 0.8")
d.c(d.obj(1400, 430, "loadbang"), dvDef); d.c(dvDef, dvIn)'''),
    # screen: with AUX held show the volume page instead of the kit page
    (r'''d.c(dSel, drT); d.c(drT, zero, 4); d.c(zero, fDirty, 0, 1)''',
     r'''auxDF = d.obj(120, 750, "f")
d.c(d.obj(120, 720, "r aux"), auxDF, 0, 1)
d.c(d.obj(200, 720, "r aux"), dirty)
d.c(d.obj(280, 720, "r drum-vol"), dirty)
auxDT = d.obj(20, 765, "t b b")
d.c(dSel, auxDT); d.c(auxDT, auxDF, 0)
auxDS = d.obj(120, 780, "sel 1 0")
d.c(auxDF, auxDS); d.c(auxDS, drT, 1)
dvPT = d.obj(250, 780, "t b b")
d.c(auxDS, dvPT, 0)
d.c(dvPT, zero, 1)
dvE = d.obj(250, 810, "expr int($f1*100+0.5) \\; int($f1*124)")
dvP = d.obj(250, 840, "pack f f")
d.c(dvPT, fDVol, 0); d.c(fDVol, dvE); d.c(dvE, dvP, 1, 1); d.c(dvE, dvP, 0, 0)
d.c(dvP, d.msg(250, 870, osc4("gShowInfoBar", "ii", "0") + " " + osc4("gClear", "ii", "1") + " " +
               osc4("gPrintln", "iiiiis", "1 1 8 1 DRUM") + " " + osc4("gPrintln", "iiiiiss", "1 14 8 1 VOLUME DRUM") + " " +
               osc4("gPrintln", "iiiiif", "4 24 24 1 \\$1") + " " + osc4("gBox", "iiiiii", "0 52 128 9 1") + " " +
               osc4("gFillArea", "iiiiii", "2 54 \\$2 5 1") + " \\; oscOut sendtyped /oled/gFlip i 3"))
d.c(drT, zero, 4); d.c(zero, fDirty, 0, 1)'''),
])
edit("gen.py", [
    (r'''m.obj(560, 530, "table pkval 56")''', r'''m.obj(560, 530, "table pkval 60")'''),
    (r'''m.obj(680, 530, "table pkpick 56")''', r'''m.obj(680, 530, "table pkpick 60")'''),
    (r'''0 0 0 0 0.8 0 0 0 \\; pkphys''', r'''0 0 0 0 0.8 0 0 0 0.8 0 0 0 \\; pkphys'''),
    (r'''if($f1==0 && $f5==1 \\, 13 \\, ''', r'''if($f1==0 && $f5==1 \\, 13 \\, if($f1==1 && $f5==1 \\, 14 \\, '''),
])
g = open("gen.py").read()
a = g.index('ctxE = m.obj(560, 660, "expr if($f1==5')
b = g.index('")', a)
g = g[:b] + ")" + g[b:]
open("gen.py", "w").write(g)
edit("genproj.py", [
    (r'''       (13, "synth-vol-set")]''', r'''       (13, "synth-vol-set"), (14, "drum-vol-set")]'''),
])
print("drum volume applied")

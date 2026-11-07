#!/usr/bin/env python3
"""Auto-start sampling (SMPL and DRUM): the first press arms the recorder (badge ATT), recording starts by itself
when the chosen source goes over the threshold. The recorder hears its source through a 15 ms delay, so the
attack is kept (pre-roll). Pressing again while armed cancels; once recording, pressing again stops as before.
Detection: [abs~] -> [threshold~] (no control traffic while idle). Only the input waits for sound: resampling
Nastro's own output (AUX+F5) starts at once, as before."""
import shutil

for f in ("gensmpl.py", "gendrum.py", "gensynth.py"):
    shutil.copy(f, f + ".pre-autorec")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


TH = "0.03 5 0.01 50"      # trigger at 0.03 (about -30 dBFS), rest below 0.01 for 50 ms

# ------------------------------------------------------------------ SMPL recorder
edit("gensmpl.py", [
    ('resz = r.msg(500, 300, f"\\\\; smpl resize {SMAX} \\\\; smp-recording 1")',
     'resz = r.msg(500, 300, "\\\\; smp-recording 1")                     # (table resized when arming)'),
    # pre-roll: the table hears the source 15 ms late; the detector hears it now
    ('r.c(inG, tw); r.c(mG, tw)',
     '''preW = r.obj(20, 190, "delwrite~ smp-pre 40")
r.c(inG, preW); r.c(mG, preW)
r.c(r.obj(20, 205, "delread~ smp-pre 15"), tw)
detA = r.obj(150, 190, "abs~")
r.c(inG, detA); r.c(mG, detA)
detT = r.obj(150, 220, "threshold~ %s")
r.c(detA, detT)''' % TH),
    # arming instead of starting; real start on the threshold
    ('''stT = r.obj(500, 240, "t b b b b")
r.c(recS, stT, 0)''',
     '''stT = r.obj(500, 240, "t b b b b")
armT = r.obj(400, 210, "t b b b b")
r.c(recS, armT, 0)
r.c(armT, srcStore, 3)                                   # source gains on, so the detector hears it
r.c(armT, r.msg(300, 240, f"\\\\; smp-armed 1 \\\\; smpl resize {SMAX}"), 2)   # resize now: at the onset it would glitch
armOne = r.msg(400, 240, "1")
r.c(armT, armOne, 1); r.c(armOne, recF, 0, 1)
detSp = r.obj(150, 250, "spigot 0")
r.c(detT, detSp)
arm1 = r.msg(250, 250, "1")
isMs = r.obj(250, 200, "f 0")                           # 1 = resampling Nastro's output: no waiting
isMsS = r.obj(250, 230, "sel 1 0")
r.c(armT, isMs, 0); r.c(isMs, isMsS)
r.c(isMsS, arm1, 1); r.c(arm1, detSp, 0, 1)
goT = r.obj(150, 280, "t b b b")
r.c(detSp, goT)
det0 = r.msg(250, 280, "0")
r.c(goT, det0, 2); r.c(det0, detSp, 0, 1)
startedF = r.obj(300, 310, "f 0")
st1 = r.msg(250, 310, "1")
r.c(goT, st1, 1); r.c(st1, startedF, 0, 1)
r.c(goT, r.msg(350, 280, "\\\\; smp-armed 0"), 1)
r.c(goT, stT, 0)
r.c(isMsS, goT, 0)'''),
    # stop: only if recording really started, otherwise cancel the arming
    ('r.c(srcStore, srcU); r.c(srcU, inG, 0, 1); r.c(srcU, mG, 1, 1)',
     'r.c(srcStore, srcU); r.c(srcU, inG, 0, 1); r.c(srcU, mG, 1, 1); r.c(srcU, isMs, 1, 1)'),
    ('r.c(recS, spT, 1); r.c(auto, spT)',
     '''stopQ = r.obj(800, 200, "t b")
r.c(recS, stopQ, 1)
r.c(stopQ, startedF)
stopS = r.obj(800, 215, "sel 1 0")
r.c(startedF, stopS)
r.c(stopS, spT, 0); r.c(auto, spT)
st0 = r.msg(900, 215, "0")
r.c(spT, st0, 0); r.c(st0, startedF, 0, 1)
cnT = r.obj(950, 240, "t b b")
r.c(stopS, cnT, 1)
cn0 = r.msg(1000, 270, "0")
r.c(cnT, cn0, 1); r.c(cn0, detSp, 0, 1); r.c(cn0, recF, 0, 1)
r.c(cnT, r.msg(950, 300, "\\\\; smp-armed 0"), 0)'''),
])

# ------------------------------------------------------------------ DRUM recorder
edit("gendrum.py", [
    ('d.c(dSt, d.msg(1950, 340, "\\\\; drec const 0 \\\\; drum-recording 1"), 3)',
     'd.c(dSt, d.msg(1950, 340, "\\\\; drum-recording 1"), 3)                  # (buffer cleared when arming)'),
    ('d.c(dinG, dtw); d.c(dmG, dtw)',
     '''dPreW = d.obj(1500, 230, "delwrite~ drm-pre 40")
d.c(dinG, dPreW); d.c(dmG, dPreW)
d.c(d.obj(1500, 240, "delread~ drm-pre 15"), dtw)
dDetA = d.obj(1650, 230, "abs~")
d.c(dinG, dDetA); d.c(dmG, dDetA)
dDetT = d.obj(1650, 260, "threshold~ %s")
d.c(dDetA, dDetT)''' % TH),
    ('''dSt = d.obj(1800, 310, "t b b b b")
d.c(dRS, dSt, 0)''',
     '''dSt = d.obj(1800, 310, "t b b b b")
dArmT = d.obj(1700, 290, "t b b b b")
d.c(dRS, dArmT, 0)
d.c(dArmT, dSrc, 3)                                      # source gains (and monitor) on
d.c(dArmT, d.msg(1600, 320, "\\\\; drum-armed 1 \\\\; drec const 0"), 2)            # clear now, not at the onset
dArmOne = d.msg(1700, 320, "1")
d.c(dArmT, dArmOne, 1); d.c(dArmOne, dRecF, 0, 1)
dDetSp = d.obj(1650, 290, "spigot 0")
d.c(dDetT, dDetSp)
dArm1 = d.msg(1600, 290, "1")
dIsMs = d.obj(1550, 260, "f 0")                          # 1 = resampling Nastro's output: no waiting
dIsMsS = d.obj(1550, 280, "sel 1 0")
d.c(dArmT, dIsMs, 0); d.c(dIsMs, dIsMsS)
d.c(dIsMsS, dArm1, 1); d.c(dArm1, dDetSp, 0, 1)
dGoT = d.obj(1650, 350, "t b b b")
d.c(dDetSp, dGoT)
dDet0 = d.msg(1750, 350, "0")
d.c(dGoT, dDet0, 2); d.c(dDet0, dDetSp, 0, 1)
dStarted = d.obj(1700, 380, "f 0")
dSt1 = d.msg(1650, 380, "1")
d.c(dGoT, dSt1, 1); d.c(dSt1, dStarted, 0, 1)
d.c(dGoT, d.msg(1750, 380, "\\\\; drum-armed 0"), 1)
d.c(dGoT, dSt, 0)
d.c(dIsMsS, dGoT, 0)'''),
    ('d.c(dSrcU, dinG, 0, 1); d.c(dSrcU, dmG, 1, 1)', 'd.c(dSrcU, dinG, 0, 1); d.c(dSrcU, dmG, 1, 1); d.c(dSrcU, dIsMs, 1, 1)'),
    ('d.c(dRS, dSp, 1); d.c(dAuto, dSp)',
     '''dStopQ = d.obj(2000, 400, "t b")
d.c(dRS, dStopQ, 1); d.c(dStopQ, dStarted)
dStopS = d.obj(2000, 415, "sel 1 0")
d.c(dStarted, dStopS)
d.c(dStopS, dSp, 0); d.c(dAuto, dSp)
dSt0 = d.msg(2100, 415, "0")
d.c(dSp, dSt0, 0); d.c(dSt0, dStarted, 0, 1)
dCnT = d.obj(2200, 400, "t b b")
d.c(dStopS, dCnT, 1)
dCn0 = d.msg(2250, 430, "0")
d.c(dCnT, dCn0, 1); d.c(dCn0, dDetSp, 0, 1); d.c(dCn0, dRecF, 0, 1)
d.c(dCnT, d.msg(2200, 430, "\\\\; drum-armed 0 \\\\; drum-recin 0"), 0)'''),
    # ATT badge on the DRUM screen while armed
    ('''d.c(fRecS, d.msg(300, 940, osc4("gFillArea", "iiiiii", "88 0 21 10 1") + " " + osc4("gPrintln", "iiiiis", "90 1 8 0 REC")))''',
     '''d.c(fRecS, d.msg(300, 940, osc4("gFillArea", "iiiiii", "88 0 21 10 1") + " " + osc4("gPrintln", "iiiiis", "90 1 8 0 REC")))
fArmD = d.obj(450, 910, "f")
d.c(d.obj(450, 850, "r drum-armed"), fArmD, 0, 1)
d.c(d.obj(530, 850, "r drum-armed"), dirty)
fArmB = d.obj(450, 880, "t b")                          # [sel 1] reject passes the float: turn it into a bang
d.c(fRecS, fArmB, 1); d.c(fArmB, fArmD)
fArmS = d.obj(450, 940, "sel 1")
d.c(fArmD, fArmS)
d.c(fArmS, d.msg(450, 970, osc4("gFillArea", "iiiiii", "88 0 21 10 1") + " " + osc4("gPrintln", "iiiiis", "90 1 8 0 ATT")))'''),
])

# ------------------------------------------------------------------ SMPL screen: ATT badge (instead of IN while armed)
edit("gensynth.py", [
    ('s.c(recS, fMon, 1); s.c(fMon, monS); s.c(monS, monM)',
     '''fArm = s.obj(1550, 340, "f")
s.c(s.obj(1550, 310, "r smp-armed"), fArm, 0, 1)
s.c(s.obj(1650, 310, "r smp-armed"), dirty)
armS = s.obj(1550, 370, "sel 1 0")
s.c(recS, fArm, 1); s.c(fArm, armS)
s.c(armS, s.msg(1550, 400, osc5("gFillArea", "iiiiii", "67 0 21 10 1") + " " + osc5("gPrintln", "iiiiis", "69 1 8 0 ATT")), 0)
s.c(armS, fMon, 1); s.c(fMon, monS); s.c(monS, monM)'''),
])
print("autorec applied")

#!/usr/bin/env python3
"""DRUM sampling: AUX+E5 (input) / AUX+F5 (Nastro output) record into the selected key's slot.
Recording goes to a temporary table (one slot long) and is copied into the kit when it stops.
The kit is saved per project (p<N>-drums.wav); a new project starts from drums.wav."""
import shutil

for f in ("gendrum.py", "gensmpl.py"):
    shutil.copy(f, f + ".pre-drumrec")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# SMPL keeps AUX+E5/F5 everywhere except in DRUM
edit("gensmpl.py", [
    (r'''r.c(rak, ks)''', r'''ksGate = r.obj(500, 75, "spigot 1")
ksNot = r.obj(560, 60, "!= 1")
r.c(r.obj(560, 30, "r mode"), ksNot); r.c(ksNot, ksGate, 0, 1)
r.c(rak, ksGate); r.c(ksGate, ks)'''),
    # input monitor also on while sampling the input into a drum key
    (r'''monE = r.obj(1100, 260, "expr $f1 || $f2")''', r'''monE = r.obj(1100, 260, "expr $f1 || $f2 || $f3")
drIn = r.obj(1250, 230, "t b f")
r.c(r.obj(1250, 200, "r drum-recin"), drIn); r.c(drIn, monE, 1, 2); r.c(drIn, monE, 0, 0)'''),
])

REC = r'''
# --- sampling into the selected key (AUX+E5 input / AUX+F5 Nastro output), DRUM mode only
d.obj(1500, 50, "table drec 22050")
slotF = d.obj(1500, 100, "f")
d.c(selT, slotF, 4, 1)
slF = d.obj(1600, 100, "f 22050")
d.c(slT, slF, 3, 1)
d.c(slT, d.msg(1700, 100, "\\; drec resize \\$1"), 3)
# sources
dinL = d.obj(1500, 150, "r~ inL"); dinR = d.obj(1600, 150, "r~ inR")
dinS = d.obj(1500, 180, "+~"); dinG = d.obj(1500, 210, "*~ 0")
d.c(dinL, dinS, 0, 0); d.c(dinR, dinS, 0, 1); d.c(dinS, dinG)
dms = d.obj(1700, 150, "r~ nst-master"); dmG = d.obj(1700, 210, "*~ 0")
d.c(dms, dmG)
dtw = d.obj(1500, 250, "tabwrite~ drec")
d.c(dinG, dtw); d.c(dmG, dtw)
# keys
dak = d.obj(1800, 100, "r aux-key")
dGate = d.obj(1800, 130, "spigot")
dIs1 = d.obj(1900, 100, "== 1")
d.c(d.obj(1900, 70, "r mode"), dIs1); d.c(dIs1, dGate, 0, 1); d.c(dak, dGate)
dks = d.obj(1800, 160, "sel 76 77")
d.c(dGate, dks)
dSrcIn = d.msg(1800, 190, "0.5 0 1"); dSrcMs = d.msg(1880, 190, "0 1 0")   # gains: input, master ; monitor flag
dTg = d.obj(1800, 220, "t b l")
d.c(dks, dSrcIn, 0); d.c(dks, dSrcMs, 1); d.c(dSrcIn, dTg); d.c(dSrcMs, dTg)
dSrc = d.obj(1950, 250, "list")
d.c(dTg, dSrc, 1, 1)
dRecF = d.obj(1800, 250, "f")
d.c(dTg, dRecF, 0)
dRS = d.obj(1800, 280, "sel 0 1")
d.c(dRecF, dRS)
# start: clear the buffer, set the source, write from 0; it stops by itself at the end of the slot
dSt = d.obj(1800, 310, "t b b b b")
d.c(dRS, dSt, 0)
d.c(dSt, d.msg(1950, 340, "\\; drec const 0 \\; drum-recording 1"), 3)
dSrcU = d.obj(1950, 280, "unpack f f f")
d.c(dSt, dSrc, 2); d.c(dSrc, dSrcU)
d.c(dSrcU, dinG, 0, 1); d.c(dSrcU, dmG, 1, 1); d.c(dSrcU, d.obj(2050, 310, "s drum-recin"), 2)
dAuto = d.obj(1800, 370, "delay 500")
dDur = d.obj(1900, 370, "expr $f1/44.1+30")
d.c(slF, dDur) if False else None
d.c(slT, dDur, 3); d.c(dDur, dAuto, 0, 1)
d.c(dSt, dAuto, 1)
d.c(dSt, d.msg(1850, 400, "1"), 0)
d.c(dSt, dtw, 0)
# stop (key again or end of the slot): copy the buffer into the slot, redraw
dSp = d.obj(2000, 430, "t b b b b b")
d.c(dRS, dSp, 1); d.c(dAuto, dSp)
d.c(dSp, d.msg(2000, 460, "stop"), 4)
d.c(d.msg(2000, 460, "stop"), dtw) if False else None
d.c(dSp, d.msg(2100, 460, "stop"), 3)
d.c(dSp, d.msg(2200, 460, "\\; drum-recording 0 \\; drum-recin 0"), 2)
dCp = d.obj(2000, 520, "t b f")
dOn = d.obj(2100, 520, "expr $f1*$f2")
d.c(dSp, slotF, 1); d.c(slotF, dCp); d.c(dCp, dOn, 1, 0); d.c(slT, dOn, 3, 1)
dGet = d.obj(2000, 560, "array get drec")
dSet = d.obj(2000, 590, "array set drums")
d.c(dOn, dSet, 0, 1); d.c(dCp, dGet, 0); d.c(dGet, dSet)
d.c(dSp, d.msg(2000, 620, "0"), 0)
dZero = d.msg(2000, 620, "0")
d.c(dSp, dZero, 0); d.c(dZero, dRecF, 0, 1)
dRedo = d.obj(2150, 620, "f")
d.c(selT, dRedo, 4, 1); d.c(dSp, dRedo, 0); d.c(dRedo, wvT)
d.c(dSp, dirty, 0)

# REC badge on the DRUM screen
fRecD = d.obj(300, 880, "f")
d.c(d.obj(300, 850, "r drum-recording"), fRecD, 0, 1)
d.c(d.obj(380, 850, "r drum-recording"), dirty)
d.c(selB, fRecD)
fRecS = d.obj(300, 910, "sel 1")
d.c(fRecD, fRecS)
d.c(fRecS, d.msg(300, 940, osc4("gFillArea", "iiiiii", "88 0 21 10 1") + " " + osc4("gPrintln", "iiiiis", "90 1 8 0 REC")))

# kit per project: save it, load the base kit then the project's kit (if there is one)
dkS = d.obj(2300, 100, "makefilename p%d-drums.wav")
d.c(d.obj(2300, 70, "r nst-save"), dkS)
d.c(dkS, d.msg(2300, 130, "write -wave -bytes 2 \\$1 drums"))
d.c(d.msg(2300, 130, "write -wave -bytes 2 \\$1 drums"), sf) if False else None
dkL = d.obj(2500, 100, "t f b")
d.c(d.obj(2500, 70, "r nst-load"), dkL)
d.c(dkL, rdm, 1)
dkLm = d.obj(2500, 130, "makefilename p%d-drums.wav")
d.c(dkL, dkLm, 0); d.c(dkLm, d.msg(2500, 160, "read -resize \\$1 drums"))
d.save("drum.pd")'''
s = open("gendrum.py").read()
# replace the placeholder 'if False' helper lines with real ones before writing
REC = REC.replace('d.c(slF, dDur) if False else None\n', '')
REC = REC.replace('d.c(dSp, d.msg(2000, 460, "stop"), 4)\nd.c(d.msg(2000, 460, "stop"), dtw) if False else None\n',
                  'dStopW = d.msg(2000, 460, "stop")\nd.c(dSp, dStopW, 4); d.c(dStopW, dtw)\n')
REC = REC.replace('d.c(dSp, d.msg(2100, 460, "stop"), 3)\n', 'dStopA = d.msg(2100, 460, "stop")\nd.c(dSp, dStopA, 3); d.c(dStopA, dAuto)\n')
REC = REC.replace('d.c(dSp, d.msg(2000, 620, "0"), 0)\n', '')
REC = REC.replace('d.c(dSt, d.msg(1850, 400, "1"), 0)\n', 'dOne = d.msg(1850, 400, "1")\nd.c(dSt, dOne, 0); d.c(dOne, dRecF, 0, 1)\n')
REC = REC.replace('''d.c(dkS, d.msg(2300, 130, "write -wave -bytes 2 \\\\$1 drums"))
d.c(d.msg(2300, 130, "write -wave -bytes 2 \\\\$1 drums"), sf) if False else None
''', '''dkW = d.msg(2300, 130, "write -wave -bytes 2 \\\\$1 drums")
d.c(dkS, dkW); d.c(dkW, sf)
''')
REC = REC.replace('d.c(dkLm, d.msg(2500, 160, "read -resize \\\\$1 drums"))',
                  'dkR = d.msg(2500, 160, "read -resize \\\\$1 drums")\nd.c(dkLm, dkR); d.c(dkR, sf)')
assert "if False" not in REC, [l for l in REC.split("\n") if "if False" in l]
a = '\nd.save("drum.pd")'
assert s.count(a) == 1
s = s.replace(a, REC)
open("gendrum.py", "w").write(s)
print("drum sampling applied")

#!/usr/bin/env python3
"""Album: AUX + A5 (from any page) records Nastro's output (after the limiter: tape, FX, live synth and drums) to a
stereo 24-bit WAV next to the patch: album-1.wav, album-2.wav, ... (counter in album.txt). If the tape is stopped
it is rewound and started. AUX + A5 again, or stopping the tape, closes the file (and stops the tape).
writesf~ streams to disk from its own thread: no big tables, no control bursts. The LED blinks while recording,
the TAPE page shows ALB in place of PLAY."""
import shutil

for f in ("gen.py", "genmix.py", "genscreen.py"):
    shutil.copy(f, f + ".pre-album")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


GEN = r'''# exec'd from gen.py: builds album.pd - AUX + A5 records the master output to album-N.wav (apply_album.py)
al = Patch(1000, 700)
al.text(20, 5, "album: AUX + A5 = record the output to album-N.wav next to the patch - again (or tape stop) = close it")
al.obj(700, 20, "table albn 1")
al.c(al.obj(700, 50, "loadbang"), al.msg(700, 80, "\\; albn read album.txt"))
# toggle: [f] holds the state, [sel 0 1]: 0 -> start, 1 -> stop
alKs = al.obj(20, 70, "sel 81")
alF = al.obj(20, 100, "f 0")
alSel = al.obj(20, 130, "sel 0 1")
al.c(al.obj(20, 40, "r aux-key"), alKs); al.c(alKs, alF); al.c(alF, alSel)
# start: 2) next number -> album-N.wav -> open + start  1) state 1  0) tape from the start if it is stopped
stT = al.obj(20, 170, "t b b b")
al.c(alSel, stT, 0)
nE = al.obj(200, 200, "expr albn[0]+1")
nT = al.obj(200, 230, "t f f")
al.c(stT, nE, 2); al.c(nE, nT)
al.c(nT, al.msg(300, 260, "\\; albn 0 \\$1 \\; albn write album.txt"), 1)
mkN = al.obj(200, 260, "makefilename album-%d.wav")
opM = al.msg(200, 290, "open -bytes 3 \\$1 \\, start")
wf = al.obj(200, 400, "writesf~ 2")
al.c(nT, mkN, 0); al.c(mkN, opM); al.c(opM, wf)
al.c(al.obj(150, 360, "r~ alb-L"), wf, 0, 0); al.c(al.obj(250, 360, "r~ alb-R"), wf, 0, 1)
on1 = al.msg(20, 230, "1")
al.c(stT, on1, 1); al.c(on1, alF, 0, 1); al.c(on1, al.obj(20, 260, "s album-rec"))
plF = al.obj(450, 200, "f 0")
al.c(al.obj(550, 170, "r tp-play"), plF, 0, 1)
plS = al.obj(450, 230, "sel 0")
al.c(stT, plF, 0); al.c(plF, plS)
al.c(plS, al.msg(450, 260, "\\; aux-key 67 \\; aux-key 65"), 0)     # rewind + play
# stop: 1) close the file, state 0  0) stop the tape
spT = al.obj(20, 320, "t b b")
al.c(alSel, spT, 1)
off0 = al.msg(20, 350, "0")
stM = al.msg(100, 350, "stop")
al.c(spT, stM, 1); al.c(stM, wf)
al.c(spT, off0, 1); al.c(off0, alF, 0, 1); al.c(off0, al.obj(20, 380, "s album-rec"))
al.c(spT, al.msg(100, 380, "\\; tp-stop bang"), 0)
# the tape stops (AUX + F, project load ...) while recording: close the file too
tpC = al.obj(600, 300, "change")
tpS = al.obj(600, 330, "sel 0")
tpG = al.obj(600, 360, "spigot")
al.c(al.obj(600, 270, "r tp-play"), tpC); al.c(tpC, tpS); al.c(tpS, tpG, 0)
al.c(al.obj(700, 330, "r album-rec"), tpG, 0, 1)
al.c(tpG, alF)                                                   # state 1 -> [sel 0 1] right outlet = stop
al.save("album.pd")
'''
open("genalbum.py", "w").write(GEN)

edit("gen.py", [
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmirror.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmirror.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genalbum.py")).read())'),
    ('m.obj(1700, 680, "synth-lfo")', 'm.obj(1700, 680, "synth-lfo")\nm.obj(1780, 680, "album")'),
    ('recE = m.obj(1300, 40, "expr $f1 || $f2 || $f3")', 'recE = m.obj(1300, 40, "expr $f1 || $f2 || $f3 || $f4")'),
    ('for k_, nm_ in ((1, "smp-recording"), (2, "drum-recording")):',
     'for k_, nm_ in ((1, "smp-recording"), (2, "drum-recording"), (3, "album-rec")):'),
])
edit("genmix.py", [
    ('ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))',
     'ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))\n'
     'ms.c(muL, ms.obj(100, 930, "s~ alb-L")); ms.c(muR, ms.obj(280, 930, "s~ alb-R"))     # album.pd (apply_album.py)'),
])
edit("genscreen.py", [
    ('steps.append(stT)\n', r'''steps.append(stT)
# album recording (apply_album.py): ALB in place of PLAY (tape REC keeps priority)
fAlb = store(1300, "album-rec")
abT = g.obj(1300, 260, "t b b")
abE = g.obj(1300, 290, "expr $f1 && !$f2")
g.c(abT, fRec, 1); g.c(fRec, abE, 0, 1); g.c(abT, fAlb, 0); g.c(fAlb, abE)
abS = g.obj(1300, 320, "sel 1")
g.c(abE, abS)
g.c(abS, g.msg(1300, 350, osc("gFillArea", "iiiiii", "0 0 25 10 1") + " " + osc("gPrintln", "iiiiis", "1 1 8 0 ALB")))
steps.append(abT)
'''),
    ('g.c(g.obj(1690, 90, "r tp-rec"), dOne)',
     'g.c(g.obj(1690, 90, "r tp-rec"), dOne)\ng.c(g.obj(1870, 90, "r album-rec"), dOne)'),
])
print("album applied")

# exec'd from gen.py: builds tempo.pd (TEMPO page in SEQ mode, metronome click)

def osc3(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


SYNC_LABELS = ["free", "1/16", "1/8", "1/8.", "1/4", "1/4.", "1/2"]

tp = Patch(1300, 900)
tp.text(20, 5, "tempo: knobs (AUX+E) 1 BPM 60-200 / 2 metronome level / 3 loop snap free-beat-bar / 4 delay sync")
tp.text(20, 25, "beat length is rounded to whole 64-sample blocks so tempo-snapped loops stay sample-exact")
lb = tp.obj(20, 60, "loadbang")
lbT = tp.obj(20, 90, "t b b")
srt = tp.obj(120, 120, "samplerate~")
srT = tp.obj(120, 150, "t f f f")
tp.c(lb, lbT); tp.c(lbT, srt, 1); tp.c(srt, srT)

rk = tp.obj(300, 60, "r tempo-knob")
defs = tp.msg(300, 90, "1 0.4286 \\, 2 0 \\, 3 1 \\, 4 0")
rt = tp.obj(300, 120, "route 1 2 3 4")
tp.c(rk, rt); tp.c(lbT, defs, 0); tp.c(defs, rt)

# 1 BPM -> beat length in samples (multiple of 64) -> beat in ms
bpmE = tp.obj(300, 160, "expr int(60+140*$f1)")
bpmC = tp.obj(300, 190, "change")
bpmT = tp.obj(300, 220, "t f f")
fBpm = tp.obj(400, 250, "f")
beatE = tp.obj(300, 250, "expr int($f2*60/$f1/64+0.5)*64")
beatT = tp.obj(300, 280, "t f f")
sBeat = tp.obj(400, 310, "s tempo-beat")
msE = tp.obj(300, 310, "expr $f1/$f2*1000")
sMs = tp.obj(300, 340, "s tempo-beatms")
tp.c(rt, bpmE, 0); tp.c(bpmE, bpmC); tp.c(bpmC, bpmT)
tp.c(bpmT, fBpm, 1, 1); tp.c(bpmT, beatE, 0)
tp.c(srT, beatE, 2, 1); tp.c(srT, msE, 1, 1)
tp.c(beatE, beatT); tp.c(beatT, sBeat, 1); tp.c(beatT, msE, 0); tp.c(msE, sMs)

# 2 metronome level
mT = tp.obj(500, 160, "t f f")
fMet = tp.obj(600, 190, "f")
sMet = tp.obj(500, 190, "s metro-lvl")
tp.c(rt, mT, 1); tp.c(mT, fMet, 1, 1); tp.c(mT, sMet, 0)

# 3 loop snap 0 free / 1 beat / 2 bar
qE = tp.obj(700, 160, "expr int($f1*2.99)")
qC = tp.obj(700, 190, "change")
qT = tp.obj(700, 220, "t f f")
fQ = tp.obj(800, 250, "f")
sQ = tp.obj(700, 250, "s loop-q")
tp.c(rt, qE, 2); tp.c(qE, qC); tp.c(qC, qT); tp.c(qT, fQ, 1, 1); tp.c(qT, sQ, 0)

# 4 delay sync index
dE = tp.obj(900, 160, "expr int($f1*6.99)")
dC = tp.obj(900, 190, "change")
dT = tp.obj(900, 220, "t f f")
fD = tp.obj(1000, 250, "f")
sD = tp.obj(900, 250, "s dly-sync")
tp.c(rt, dE, 3); tp.c(dE, dC); tp.c(dC, dT); tp.c(dT, fD, 1, 1); tp.c(dT, sD, 0)

# --- metronome click (output only, not recorded on tape)
rtick = tp.obj(20, 420, "r tick")
tkT = tp.obj(20, 450, "t f b")
env = tp.msg(120, 480, "1 \\, 0 25")
venv = tp.obj(120, 510, "vline~")
acc = tp.obj(20, 480, "sel 1 0")
fhi = tp.msg(20, 510, "1600")
flo = tp.msg(70, 510, "1000")
osc_ = tp.obj(20, 540, "osc~")
m1 = tp.obj(20, 570, "*~")
rml = tp.obj(220, 480, "r metro-lvl")
rmm = tp.msg(220, 510, "\\$1 20")
rmL = tp.obj(220, 540, "line~")
m2 = tp.obj(20, 600, "*~")
m3 = tp.obj(20, 630, "*~ 0.4")
oL = tp.obj(20, 670, "throw~ outL")
oR = tp.obj(130, 670, "throw~ outR")
tp.c(rtick, tkT); tp.c(tkT, env, 1); tp.c(env, venv); tp.c(tkT, acc, 0)
tp.c(acc, fhi, 0); tp.c(acc, flo, 1); tp.c(fhi, osc_); tp.c(flo, osc_)
tp.c(osc_, m1, 0, 0); tp.c(venv, m1, 0, 1)
tp.c(rml, rmm); tp.c(rmm, rmL); tp.c(m1, m2, 0, 0); tp.c(rmL, m2, 0, 1)
tp.c(m2, m3); tp.c(m3, oL); tp.c(m3, oR)

# LED flash on each beat while the metronome is on
gt0 = tp.obj(400, 450, "> 0")
lsp = tp.obj(400, 480, "spigot")
ltb = tp.obj(400, 510, "t b b")
lon = tp.msg(480, 540, "\\; led 7")
ldl = tp.obj(400, 540, "delay 80")
rmode = tp.obj(560, 420, "r mode")
mp1 = tp.obj(560, 450, "+ 1")
fled = tp.obj(400, 570, "f 1")
loff = tp.msg(400, 600, "\\; led \\$1")
tp.c(rml, gt0); tp.c(gt0, lsp, 0, 1); tp.c(rtick, lsp); tp.c(lsp, ltb)
tp.c(ltb, lon, 1); tp.c(ltb, ldl, 0); tp.c(ldl, fled); tp.c(fled, loff)
tp.c(rmode, mp1); tp.c(mp1, fled, 0, 1)

# --- screen (mode 4, 10 fps)
eq4 = tp.obj(700, 420, "expr $f1==4 && $f2==0")
spg = tp.obj(800, 390, "r seq-page")
spgT = tp.obj(800, 420, "t b f")
tp.c(spg, spgT); tp.c(spgT, eq4, 1, 1); tp.c(spgT, eq4, 0, 0)
mtr = tp.obj(700, 450, "metro 100")
tp.c(rmode, eq4); tp.c(eq4, mtr)
seq_ = tp.obj(700, 480, "t b b b b b b b")
clr = tp.msg(700, 520, osc3("gClear", "ii", "1"))
static = tp.msg(700, 550, " ".join(
    [osc3("gPrintln", "iiiiis", "1 1 8 1 TEMPO")] +
    [osc3("gBox", "iiiiii", f"{93 + i * 9} 1 7 7 1") for i in range(4)] +
    [osc3("gPrintln", "iiiiis", "6 42 8 1 bpm"),
     osc3("gLine", "iiiiii", "0 52 127 52 1"),
     osc3("gPrintln", "iiiiis", "1 55 8 1 BPM"),
     osc3("gPrintln", "iiiiis", "33 55 8 1 MET"),
     osc3("gPrintln", "iiiiis", "65 55 8 1 LOOP"),
     osc3("gPrintln", "iiiiis", "98 55 8 1 DLY")]))
bigM = tp.msg(700, 580, osc3("gPrintln", "iiiiif", "4 16 24 1 \\$1"))
# metronome value
metS = tp.obj(900, 610, "moses 0.005")
metOff = tp.msg(900, 640, osc3("gPrintln", "iiiiis", "66 14 8 1 MET off"))
metPct = tp.obj(1000, 640, "expr int($f1*100)")
metOn = tp.msg(1000, 670, osc3("gPrintln", "iiiiisf", "66 14 8 1 MET \\$1"))
tp.c(fMet, metS); tp.c(metS, metOff, 0); tp.c(metS, metPct, 1); tp.c(metPct, metOn)
# loop snap
qS = tp.obj(900, 710, "sel 0 1 2")
for i, nm in enumerate(["free", "beat", "bar"]):
    mm = tp.msg(900 + i * 130, 740, osc3("gPrintln", "iiiiiss", f"66 26 8 1 LOOP {nm}"))
    tp.c(qS, mm, i)
tp.c(fQ, qS)
# delay sync
dS = tp.obj(900, 780, "sel 0 1 2 3 4 5 6")
for i, nm in enumerate(SYNC_LABELS):
    mm = tp.msg(900 + (i % 4) * 110, 810 + (i // 4) * 30, osc3("gPrintln", "iiiiiss", f"66 38 8 1 DLY {nm}"))
    tp.c(dS, mm, i)
tp.c(fD, dS)
# beat squares
rpl = tp.obj(1150, 420, "r tp-play")
fPl = tp.obj(1150, 450, "f")
rbt = tp.obj(1250, 420, "r tp-beat")
fBt = tp.obj(1250, 480, "f")
tp.c(rpl, fPl, 0, 1); tp.c(rbt, fBt, 0, 1)
plS = tp.obj(1150, 480, "sel 1")
bq = tp.obj(1250, 510, "expr 94+$f1*9")
bqM = tp.msg(1250, 540, osc3("gFillArea", "iiiiii", "\\$1 2 5 5 1"))
tp.c(fPl, plS); tp.c(plS, fBt); tp.c(fBt, bq); tp.c(bq, bqM)
flip = tp.msg(700, 620, "\\; oscOut sendtyped /oled/gFlip i 3")
steps = [clr, static, fBpm, fMet, fQ, fD, fPl]
for i, st in enumerate(steps):
    tp.c(seq_, st, 6 - i)
tp.c(fBpm, bigM)
# flip after everything: chain it from a final trigger
fin = tp.obj(600, 480, "t b b")
tp.c(fin, seq_, 1); tp.c(fin, flip, 0)
dOne = tp.msg(1420, 600, "1")
dF = tp.obj(1300, 660, "f 1")
tp.c(dOne, dF, 0, 1)
dSel = tp.obj(1300, 690, "sel 1")
dTT = tp.obj(1300, 720, "t b b")
dZero = tp.msg(1420, 720, "0")
tp.c(dF, dSel); tp.c(dSel, dTT); tp.c(dTT, dZero, 1); tp.c(dZero, dF, 0, 1); tp.c(dTT, fin, 0)
tp.c(tp.obj(1500, 570, "r tempo-knob"), dOne)
tp.c(tp.obj(1590, 570, "r tp-beat"), dOne)
tp.c(tp.obj(1680, 570, "r tp-play"), dOne)
tp.c(tp.obj(1770, 570, "r mode"), dOne)
tp.c(tp.obj(1860, 570, "r seq-page"), dOne)
tp.c(tp.obj(1950, 570, "r nst-redraw"), dOne)
tp.c(mtr, dF)
tp.save("tempo.pd")

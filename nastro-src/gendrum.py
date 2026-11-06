# exec'd from gen.py: builds drum-voice.pd and drum.pd (DRUM mode: 24-slice sampler)

def osc4(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


NV = 6          # voices
NB = 42         # waveform bars on screen

# ---------------------------------------------------------------- drum-voice.pd
dv = Patch(700, 500)
dv.text(20, 5, "drum-voice: plays one slice. input: onset length(samples) dur(ms) hold(ms) gain cutoff")
inl = dv.obj(20, 40, "inlet")
up = dv.obj(20, 70, "unpack f f f f f f")
# right-to-left: cutoff, gain, hold, dur, length, onset(last = trigger)
lp = dv.obj(20, 330, "lop~ 20000")
fg = dv.obj(300, 120, "f")
fh = dv.obj(250, 120, "f")
fd = dv.obj(200, 120, "f")
fl = dv.obj(150, 120, "f")
ton = dv.obj(20, 120, "t b f")
dv.c(inl, up)
dv.c(up, lp, 5, 1); dv.c(up, fg, 4, 1); dv.c(up, fh, 3, 1); dv.c(up, fd, 2, 1); dv.c(up, fl, 1, 1)
dv.c(up, ton, 0)
rd = dv.obj(20, 240, "tabread4~ drums")
dv.c(ton, rd, 1, 1)                      # onset (control, double precision)
tb = dv.obj(20, 160, "t b b b")
dv.c(ton, tb, 0)
# playhead 0 -> length over dur ms
pk = dv.obj(150, 190, "pack f f")
dv.c(tb, fd, 2); dv.c(fd, pk, 0, 1); dv.c(tb, fl, 1); dv.c(fl, pk, 0, 0)
ph = dv.msg(150, 215, "0 \\, \\$1 \\$2")
vph = dv.obj(150, 240, "vline~")
dv.c(pk, ph); dv.c(ph, vph); dv.c(vph, rd)
# envelope: 1 ms attack, hold, 15 ms fade
dv.c(tb, fh, 0)
env = dv.msg(250, 215, "0 \\, 1 1 \\, 0 15 \\$1")
venv = dv.obj(250, 240, "vline~")
dv.c(fh, env); dv.c(env, venv)
m1 = dv.obj(20, 270, "*~")
m2 = dv.obj(20, 300, "*~ 0")
dv.c(rd, m1, 0, 0); dv.c(venv, m1, 0, 1)
dv.c(m1, m2, 0, 0); dv.c(fg, m2, 0, 1)
# gain arrives as a float into the right inlet of *~ via the stored value
dv.c(m2, lp)
out = dv.obj(20, 370, "outlet~")
dv.c(lp, out)
# trigger order: hold (env) after gain is set; gain [f] outputs when banged
dv.c(tb, fg, 0)
dv.save("drum-voice.pd")

# ---------------------------------------------------------------- drum.pd
d = Patch(1500, 1000)
d.text(20, 5, "drum: 24 slices of drums.wav on the keys. knobs edit the last played key: 1 pitch / 2 length / 3 tone / 4 level")
d.text(20, 25, "replace drums.wav with your own file: it is split into 24 equal slices")
for k in range(4):
    d.obj(20 + k * 110, 50, f"table dk{k+1} 24")
d.obj(470, 50, "table drums")
d.obj(570, 50, f"table dwave {NB}")
lb = d.obj(20, 90, "loadbang")
lbT = d.obj(20, 120, "t b b b")
init = d.msg(200, 120, "\\; dk1 const 0.5 \\; dk2 const 1 \\; dk3 const 1 \\; dk4 const 0.8")
rdm = d.msg(20, 150, "read -resize drums.wav drums")
sf = d.obj(20, 180, "soundfiler")
slE = d.obj(20, 210, "expr int($f1/24)")
slT = d.obj(20, 240, "t f f f f")
fSL = d.obj(160, 270, "f")
srt = d.obj(380, 150, "samplerate~")
d.c(lb, lbT); d.c(lbT, init, 2); d.c(lbT, srt, 1); d.c(lbT, rdm, 0)
d.c(rdm, sf); d.c(sf, slE); d.c(slE, slT); d.c(slT, fSL, 3, 1)

# --- notes -> slot
rn = d.obj(600, 90, "r drum-notes")
nu = d.obj(600, 120, "unpack f f")
von = d.obj(700, 150, "> 0")
nsp = d.obj(600, 180, "spigot")
nsl = d.obj(600, 210, "expr min(23 \\, max(0 \\, $f1-60))")
nT = d.obj(600, 240, "t f f")
d.c(rn, nu); d.c(nu, von, 1); d.c(von, nsp, 0, 1); d.c(nu, nsp, 0); d.c(nsp, nsl); d.c(nsl, nT)

# trigger: per-slot params from the tables
trE = d.obj(600, 300,
            "expr $f1*$f2 \\; $f2 \\; "
            "$f2/$f3*1000/pow(2 \\, floor((dk1[$f1]-0.5)*24+0.5)/12) \\; "
            "max(1 \\, min(dk2[$f1] \\, 1)*$f2/$f3*1000/pow(2 \\, floor((dk1[$f1]-0.5)*24+0.5)/12)-15) \\; "
            "dk4[$f1]*1.2 \\; 100*pow(2 \\, dk3[$f1]*8)")
d.c(nT, trE, 0)
d.c(slT, trE, 2, 1); d.c(srt, trE, 0, 2)
tpk = d.obj(600, 340, "pack f f f f f f")
for o in range(6):
    d.c(trE, tpk, o, o)
rr = d.obj(800, 340, "f")
rr1 = d.obj(840, 340, "+ 1")
rrm = d.obj(800, 370, f"% {NV}")
d.c(rr, rr1); d.c(rr1, rrm); d.c(rrm, rr, 0, 1)
vpre = d.obj(600, 400, "list prepend 0")
tpT = d.obj(600, 370, "t l b")
d.c(tpk, tpT); d.c(tpT, rr, 1); d.c(rrm, vpre, 0, 1); d.c(tpT, vpre, 0)
cl = d.obj(600, 430, f"clone -s 0 drum-voice {NV}")
d.c(vpre, cl)
dg = d.obj(600, 470, "*~ 0.5")
thr = d.obj(600, 500, "throw~ synth-bus")
d.c(cl, dg); d.c(dg, thr)

# --- selection: last played slot
selF = d.obj(900, 240, "f")
selT = d.obj(900, 270, "t f f f f f f")
selC = d.obj(800, 240, "change -1")
d.c(nT, selC, 1); d.c(selC, selT)
tws = []
for k in range(4):
    tw = d.obj(900 + k * 110, 330, f"tabwrite dk{k+1}")
    d.c(selT, tw, 5, 1)
    tws.append(tw)
d.c(selT, selF, 4, 1)
# push this slot's values into the pickup table (drum context = slots 4..7)
pkE = d.obj(1100, 270, "expr dk1[$f1] \\; dk2[$f1] \\; dk3[$f1] \\; dk4[$f1]")
pkP = d.obj(1100, 300, "pack f f f f")
pkM = d.msg(1100, 360, "\\; pkval 4 \\$1 \\$2 \\$3 \\$4 \\; pkpick 4 0 0 0 0")
d.c(selT, pkE, 3)
for o in range(4):
    d.c(pkE, pkP, o, o)
d.c(pkP, pkM)

# --- knobs -> tables at the selected slot
rk = d.obj(900, 400, "r drum-knob")
krt = d.obj(900, 430, "route 1 2 3 4")
d.c(rk, krt)
dirty = d.msg(1350, 430, "1")
for k in range(4):
    d.c(krt, tws[k], k)
    d.c(krt, dirty, k)

# --- waveform of the selected slice: NB bars of peak amplitude
wvT = d.obj(900, 470, "t b b b f")
d.c(selT, wvT, 2)
nb = d.msg(900, 500, f"{NB}")
until = d.obj(900, 530, "until")
cnt = d.obj(900, 560, "f")
cnt1 = d.obj(950, 560, "+ 1")
cnt0 = d.msg(980, 530, "0")
d.c(wvT, cnt0, 2); d.c(cnt0, cnt, 0, 1)
d.c(wvT, nb, 1); d.c(nb, until); d.c(until, cnt); d.c(cnt, cnt1); d.c(cnt1, cnt, 0, 1)
segT = d.obj(900, 590, "t f f")
d.c(cnt, segT)
segE = d.obj(900, 620, f"expr $f2*$f3+int($f1*$f3/{NB}) \\; max(1 \\, int($f3/{NB}))")
d.c(segT, segE, 0); d.c(wvT, segE, 3, 1); d.c(slT, segE, 1, 2)
amax = d.obj(900, 680, "array max drums")
amin = d.obj(1050, 680, "array min drums")
segT2 = d.obj(900, 650, "t f f")
d.c(segE, amax, 1, 1); d.c(segE, amin, 1, 1)
d.c(segE, segT2, 0); d.c(segT2, amin, 1, 0); d.c(segT2, amax, 0, 0)
hE = d.obj(900, 720, "expr int(max($f1 \\, -$f2)*13)")
d.c(amin, hE, 0, 1); d.c(amax, hE, 0, 0)
hw = d.obj(900, 750, "tabwrite dwave")
d.c(hE, hw); d.c(segT, hw, 1, 1)
d.c(wvT, dirty, 0)

# --- screen: redraw when dirty (max 20 fps) while in DRUM mode
rmd = d.obj(20, 600, "r mode")
mT = d.obj(20, 630, "t f f")
eq1 = d.obj(20, 660, "== 1")
mtr = d.obj(20, 690, "metro 50")
d.c(rmd, mT); d.c(mT, eq1, 0); d.c(eq1, mtr)
d.c(d.obj(120, 600, "r nst-redraw"), dirty)
fDirty = d.obj(20, 720, "f 1")
d.c(dirty, fDirty, 0, 1); d.c(mT, dirty, 1)
d.c(mtr, fDirty)
dSel = d.obj(20, 750, "sel 1")
d.c(fDirty, dSel)
drT = d.obj(20, 780, "t b b b b b")
zero = d.msg(120, 780, "0")
d.c(dSel, drT); d.c(drT, zero, 4); d.c(zero, fDirty, 0, 1)
clr = d.msg(150, 820, osc4("gShowInfoBar", "ii", "0") + " " + osc4("gClear", "ii", "1") + " " +
            osc4("gPrintln", "iiiiis", "1 1 8 1 DRUM") +
            " " + osc4("gLine", "iiiiii", "0 45 127 45 1") +
            " " + osc4("gPrintln", "iiiiis", "1 47 8 1 PIT") +
            " " + osc4("gPrintln", "iiiiis", "33 47 8 1 LEN") +
            " " + osc4("gPrintln", "iiiiis", "65 47 8 1 TON") +
            " " + osc4("gPrintln", "iiiiis", "97 47 8 1 LVL"))
d.c(drT, clr, 3)
# key number
keyM = d.msg(300, 860, osc4("gPrintln", "iiiiisi", "40 1 8 1 key \\$1"))
selK = d.obj(300, 830, "+ 1")
selB = d.obj(300, 800, "t b")
d.c(drT, selB, 2); d.c(selB, selF); d.c(selF, selK); d.c(selK, keyM)
# waveform bars + length marker
bars = d.obj(500, 800, "t b b")
d.c(drT, bars, 1)
nb2 = d.msg(500, 830, f"{NB}")
until2 = d.obj(500, 860, "until")
c2 = d.obj(500, 890, "f")
c21 = d.obj(550, 890, "+ 1")
c20 = d.msg(580, 860, "0")
d.c(bars, c20, 1); d.c(c20, c2, 0, 1); d.c(bars, nb2, 0); d.c(nb2, until2); d.c(until2, c2)
d.c(c2, c21); d.c(c21, c2, 0, 1)
bT = d.obj(500, 920, "t f f")
d.c(c2, bT)
bE = d.obj(500, 950, "expr 1+$f1*3 \\; 26-dwave[$f1] \\; 2*dwave[$f1]+1")
d.c(bT, bE, 0)
bP = d.obj(500, 980, "pack f f f")
for o in range(3):
    d.c(bE, bP, o, o)
bM = d.msg(500, 1010, osc4("gFillArea", "iiiiii", "\\$1 \\$2 2 \\$3 1"))
d.c(bP, bM)
# length marker + values
valT = d.obj(800, 800, "t b")
d.c(drT, valT, 0)
vE = d.obj(800, 860, "expr floor((dk1[$f1]-0.5)*24+0.5) \\; int(min(dk2[$f1] \\, 1)*100) \\; "
                     "int(dk3[$f1]*100) \\; int(dk4[$f1]*100) \\; 1+int(min(dk2[$f1] \\, 1)*125)")
selF2 = d.obj(800, 830, "f")
d.c(valT, selF2); d.c(selT, selF2, 0, 1); d.c(selF2, vE)
vP = d.obj(800, 890, "pack f f f f f")
for o in range(5):
    d.c(vE, vP, o, o)
vM = d.msg(800, 920, osc4("gLine", "iiiiii", "\\$5 10 \\$5 42 1") + " " +
           osc4("gPrintln", "iiiiif", "1 55 8 1 \\$1") + " " +
           osc4("gPrintln", "iiiiif", "33 55 8 1 \\$2") + " " +
           osc4("gPrintln", "iiiiif", "65 55 8 1 \\$3") + " " +
           osc4("gPrintln", "iiiiif", "97 55 8 1 \\$4") + " " +
           "\\; oscOut sendtyped /oled/gFlip i 3")
d.c(vP, vM)
# select slot 0 at start (after the sample is loaded)
s0 = d.msg(160, 210, "0")
d.c(slT, s0, 0); d.c(s0, selC)
d.save("drum.pd")

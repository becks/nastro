# exec'd from gen.py: builds master.pd and tape.pd (uses Patch, OUT)
N = 2646000  # 60 s @ 44.1 kHz per track

# ---------------------------------------------------------------- master.pd
# (built in genmix.py)

# ---------------------------------------------------------------- tape.pd
t = Patch(1400, 1000)
t.text(20, 5, "tape: 4 tracks x 60 s. AUX+F play/stop  AUX+F# rec  AUX+G rewind  AUX+G# loop  AUX+A save  AUX+C#5 / D#5 back / forward  footswitch = rec")
t.text(20, 25, "knobs (TAPE mode): 1 speed (-2..2 snaps to 1 / 0 / -1)  2 track  3 overdub (0 replace .. 1 add)  4 wow")
for k in range(4):
    t.obj(20 + k * 170, 50, f"table tape{k+1} {N}")

# --- transport keys
rak = t.obj(20, 100, "r aux-key")
selk = t.obj(20, 130, "sel 65 66 67 69 68")
rfs = t.obj(260, 100, "r fs")
fs1 = t.obj(260, 130, "sel 1")
kDf = t.obj(20, 115, "pipe 0"); fDf = t.obj(260, 115, "pipe 0")
t.c(rak, kDf); t.c(kDf, selk); t.c(rfs, fDf); t.c(fDf, fs1)     # after the tape position update (apply_keydefer.py)

# play toggle
pf = t.obj(20, 170, "f")
peq = t.obj(20, 200, "== 0")
pX = t.obj(20, 230, "t f f")
pon = t.msg(90, 200, "1")
playT = t.obj(20, 260, "t f f f")
psel0 = t.obj(120, 290, "sel 0")
t.c(selk, pf, 0); t.c(pf, peq); t.c(peq, pX); t.c(pon, pX)
t.c(pX, pf, 1, 1); t.c(pX, playT, 0)
pStop = t.msg(150, 200, "0")
t.c(t.obj(150, 170, "r tp-stop"), pStop); t.c(pStop, pX)          # stop from outside (save / load)

# rec toggle
rf = t.obj(260, 170, "f")
req = t.obj(260, 200, "== 0")
rX = t.obj(260, 230, "t f f")
roff = t.msg(330, 200, "0")
recT = t.obj(260, 260, "t f f f f f")
rsel1 = t.obj(420, 290, "sel 1")
t.c(selk, rf, 1); t.c(fs1, rf); t.c(rf, req); t.c(req, rX); t.c(roff, rX)
t.c(rX, rf, 1, 1); t.c(rX, recT, 0)
# interlocks: play off -> rec off, rec on -> play on
t.c(playT, psel0, 2); t.c(psel0, roff)
t.c(recT, rsel1, 4); t.c(rsel1, pon)

# --- speed target: play * (rec ? 1 : speed)
sx = t.obj(20, 340, "expr $f1*if($f3 \\, $f4 \\, $f2)")
rr = t.obj(20, 400, "expr if($f2 \\, 0 \\, if($f1==0 \\, 400 \\, 120))")
st = t.obj(20, 370, "t f f")
pk = t.obj(20, 430, "pack f f")
lspd = t.obj(20, 460, "line~")
t.c(playT, sx, 1, 0)
spdin = t.obj(180, 310, "t b f")      # speed from knob
recin = t.obj(420, 320, "t b f")      # rec into speed expr
t.c(spdin, sx, 1, 1); t.c(spdin, sx, 0, 0)
t.c(recT, rr, 3, 1)
rcT = t.obj(420, 290, "t f f")
t.c(recT, rcT, 2); t.c(rcT, recin, 0); t.c(recin, sx, 1, 2); t.c(recin, sx, 0, 0)
# rec factor (apply_varirec.py): frozen at rec start from the current speed
fSpd = t.obj(520, 320, "f 1")
t.c(spdin, fSpd, 1, 1)
rcOn = t.obj(520, 290, "sel 1")
t.c(rcT, rcOn, 1); t.c(rcOn, fSpd)
facE = t.obj(520, 350, "expr if($f1==0.5 || $f1==2 \\, $f1 \\, 1)")
t.c(fSpd, facE)
facT = t.obj(520, 380, "t f f f f")
t.c(facE, facT); t.c(facT, sx, 3, 3)
t.c(facT, t.obj(620, 410, "s tp-recf"), 0)
t.c(sx, st); t.c(st, rr, 1); t.c(rr, pk, 0, 1); t.c(st, pk, 0); t.c(pk, lspd)

# --- wow: depth = wow * (1 - rec) * 0.02
we = t.obj(600, 340, "expr $f1*(1-$f2)*0.02")
wrec = t.obj(600, 310, "t b f")
wt = t.obj(600, 370, "t f f")
wq = t.obj(700, 400, "* 0.25")
wo1 = t.obj(600, 430, "osc~ 0.55")
wo2 = t.obj(700, 430, "osc~ 4.7")
wm1 = t.obj(600, 460, "*~ 0")
wm2 = t.obj(700, 460, "*~ 0")
wsum = t.obj(600, 490, "+~")
wone = t.obj(600, 520, "+~ 1")
t.c(recT, wrec, 1); t.c(wrec, we, 1, 1); t.c(wrec, we, 0, 0)
t.c(we, wt); t.c(wt, wq, 1); t.c(wq, wm2, 0, 1); t.c(wt, wm1, 0, 1)
t.c(wo1, wm1); t.c(wo2, wm2); t.c(wm1, wsum, 0, 0); t.c(wm2, wsum, 0, 1); t.c(wsum, wone)

# --- playhead
# position = onset (integer, control) + rp (small fractional counter, signal).
# Every 5 ms the integer part of rp is moved into the onset, so the signal
# never holds large numbers and float32 precision stays sample-accurate.
mulw = t.obj(20, 550, "*~")
rp = t.obj(20, 580, "rpole~ 1")
idx = rp
t.c(lspd, mulw, 0, 0); t.c(wone, mulw, 0, 1); t.c(mulw, rp)
snapA = t.obj(1100, 220, "snapshot~")
t.c(rp, snapA)
aT = t.obj(1100, 250, "t f f")
aFr = t.obj(1250, 280, "expr $f1-floor($f1)")
aSet = t.msg(1250, 310, "set \\$1")
aFl = t.obj(1100, 280, "expr floor($f1)")
aAdd = t.obj(1100, 310, "+")
pT = t.obj(1100, 340, "t f f")
wrapE = t.obj(1100, 400, "expr if($f1>=$f3 || $f1<$f2 \\, $f2+fmod(fmod($f1-$f2 \\, $f3-$f2)+($f3-$f2) \\, $f3-$f2) \\, $f1)")
wflag = t.obj(1350, 370, "expr ($f1>=$f3)||($f1<$f2)")
wsel = t.obj(1350, 400, "sel 1")
T = t.obj(1100, 430, "t f f")
onsetF = t.obj(1100, 470, "f")
t.c(snapA, aT); t.c(aT, aFr, 1); t.c(aFr, aSet); t.c(aSet, rp)
t.c(aT, aFl, 0); t.c(aFl, aAdd); t.c(aAdd, pT)
t.c(pT, wrapE, 1); t.c(wrapE, T)
xT = t.obj(1350, 340, "t f f")
preF = t.obj(1450, 370, "f")
t.c(pT, xT, 0); t.c(xT, preF, 1, 1); t.c(xT, wflag, 0); t.c(wflag, wsel)
# second head onset = main onset + delta (delta = pre-wrap - post-wrap, set at each wrap)
postF = t.obj(1550, 370, "f")
bAdd = t.obj(1550, 460, "+ 0")
t.c(T, postF, 0, 1); t.c(T, bAdd, 0, 0)
xW = t.obj(1450, 430, "t b b")
t.c(wsel, xW)
dE = t.obj(1450, 490, "expr $f1-$f2")
t.c(xW, postF, 1); t.c(postF, dE, 0, 1)          # post first (cold inlet)
t.c(xW, preF, 0); t.c(preF, dE, 0, 0)           # then pre (hot) -> delta
dT = t.obj(1450, 520, "t b f")
t.c(dE, dT); t.c(dT, bAdd, 1, 1); t.c(dT, bAdd, 0, 0)
# block-aligned fades ([line~] starts on the next DSP block, the same block the jump takes effect)
gA = t.obj(1650, 520, "line~"); gB = t.obj(1750, 520, "line~")
fA = t.msg(1650, 490, "0 \\, 1 5"); fB = t.msg(1750, 490, "1 \\, 0 5")
t.c(xW, fA, 0); t.c(xW, fB, 0); t.c(fA, gA); t.c(fB, gB)
gA1 = t.msg(1650, 460, "1")
t.c(t.obj(1650, 430, "loadbang"), gA1); t.c(gA1, gA)
t.c(T, aAdd, 1, 1); t.c(T, onsetF, 0, 1)
set0 = t.msg(1250, 220, "set 0")
t.c(set0, rp)
bng = t.obj(1250, 160, "bang~")
t.c(bng, snapA)
# rewind: onset 0, counter 0 (and re-anchor the writer if recording)
rew = t.obj(140, 190, "f")
rewT = t.obj(140, 160, "t b b b")
t.c(selk, rewT, 2); t.c(rewT, rew, 2); t.c(rew, T); t.c(rewT, set0, 1)
lb = t.obj(180, 500, "loadbang")
tlb = t.obj(180, 530, "t b b b")
srt = t.obj(180, 560, "samplerate~")
srT = t.obj(180, 590, "t f f")
t.c(lb, tlb); t.c(tlb, srt, 2); t.c(srt, srT)

# --- DJ filter knobs per track (tfilt-knob / tfilt-set: k value ; tres-knob / tres-set: k resonance)
fRt = t.obj(1500, 950, "route 1 2 3 4")
t.c(t.obj(1500, 920, "r tfilt-knob"), fRt); t.c(t.obj(1600, 920, "r tfilt-set"), fRt)
rRt = t.obj(1700, 950, "route 1 2 3 4")
t.c(t.obj(1700, 920, "r tres-knob"), rRt); t.c(t.obj(1800, 920, "r tres-set"), rRt)
fDef = t.msg(1900, 920, "1 0.3 \\, 2 0.3 \\, 3 0.3 \\, 4 0.3")
t.c(t.obj(1900, 890, "loadbang"), fDef); t.c(fDef, rRt)
# --- tracks: read, level, overdub write
rin = t.obj(400, 680, "r~ tape-in")
thL = t.obj(20, 960, "throw~ tape-busL")
thR = t.obj(200, 960, "throw~ tape-busR")
stop_all = t.msg(900, 680, "stop")
tws, dubs = [], []
xAs, xBs, rds = [], [], []
# punch fade gain (apply_punchfade.py): written = old + g*(dub*old + in - old)
pG = t.obj(900, 640, "line~")
for k in range(4):
    x = 20 + k * 200
    rd = t.obj(x, 720, f"tabread4~ tape{k+1}")
    lv = t.obj(x, 860, "*~")
    rlm = t.msg(x + 70, 845, "\\$1 20")
    rll = t.obj(x + 130, 845, "line~")
    rl = t.obj(x + 70, 830, f"r tape-lvl{k+1}")
    db = t.obj(x + 70, 750, "*~ 1")
    ad = t.obj(x + 70, 780, "+~")
    tw = t.obj(x + 70, 810, f"tabwrite~ tape{k+1}")
    rdB = t.obj(x, 740, f"tabread4~ tape{k+1}")
    xA = t.obj(x, 790, "*~"); xB = t.obj(x + 40, 790, "*~"); xS = t.obj(x, 820, "+~")
    t.c(idx, rdB); t.c(bAdd, rdB, 0, 1)
    t.c(rd, xA, 0, 0); t.c(rdB, xB, 0, 0); xAs.append(xA); xBs.append(xB); rds.append(rd)
    t.c(xA, xS, 0, 0); t.c(xB, xS, 0, 1); t.c(xS, lv)
    t.c(rl, rlm); t.c(rlm, rll); t.c(rll, lv, 0, 1)
    # pan (balance law: centre = full level on both sides)
    rpan = t.obj(x + 130, 880, f"r tape-pan{k+1}")
    panE = t.obj(x + 130, 900, "expr min(1 \\, 2*(1-$f1)) \\; min(1 \\, 2*$f1)")
    pmL = t.msg(x + 130, 920, "\\$1 20"); pmR = t.msg(x + 170, 920, "\\$1 20")
    plL = t.obj(x + 130, 940, "line~"); plR = t.obj(x + 170, 940, "line~")
    gLp = t.obj(x, 930, "*~"); gRp = t.obj(x + 60, 930, "*~")
    t.c(rpan, panE); t.c(panE, pmL, 0); t.c(panE, pmR, 1); t.c(pmL, plL); t.c(pmR, plR)
    # DJ filter (apply_trackfilter.py): one biquad~ after the level, before pan and VU
    bq = t.obj(x, 875, "biquad~ 0 0 1 0 0")
    t.c(lv, bq)
    cE = t.obj(x + 300, 1060, "expr if((($f1<0.47) || ($f1>0.53)) \\,  2*cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(1+(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6)))) \\,  0) \\;  if((($f1<0.47) || ($f1>0.53)) \\,  -(1-(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6))))/(1+(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6)))) \\,  0) \\;  if((($f1<0.47) || ($f1>0.53)) \\,  if(($f1<0.47) \\,  (1-cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100))))/2 \\,  (1+cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100))))/2)/(1+(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6)))) \\,  1) \\;  if((($f1<0.47) || ($f1>0.53)) \\,  if(($f1<0.47) \\,  1-cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100))) \\,  -(1+cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))))/(1+(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6)))) \\,  0) \\;  if((($f1<0.47) || ($f1>0.53)) \\,  if(($f1<0.47) \\,  (1-cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100))))/2 \\,  (1+cos((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100))))/2)/(1+(sin((6.2831853*min(if($f1<0.47 \\,  80*pow(225 \\,  $f1/0.47) \\,  20*pow(400 \\,  ($f1-0.53)/0.47)) \\,  0.45*if($f3>0 \\,  $f3 \\,  44100))/if($f3>0 \\,  $f3 \\,  44100)))/(2*(0.6+$f2*6)))) \\,  0)")
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
    t.c(bq, gLp, 0, 0); t.c(plL, gLp, 0, 1); t.c(bq, gRp, 0, 0); t.c(plR, gRp, 0, 1)
    t.c(gLp, thL); t.c(gRp, thR)
    vuEnv = t.obj(x, 990, "env~ 2048 1024")
    t.c(bq, vuEnv); t.c(vuEnv, t.obj(x, 1020, f"s tape-vu{k+1}"))
    t.c(rd, db); t.c(db, ad, 0, 0); t.c(rin, ad, 0, 1)
    pD = t.obj(x + 70, 795, "-~"); pM = t.obj(x + 110, 795, "*~"); pS = t.obj(x + 150, 795, "+~")
    t.c(ad, pD, 0, 0); t.c(rd, pD, 0, 1); t.c(pD, pM, 0, 0); t.c(pG, pM, 0, 1)
    t.c(pM, pS, 0, 0); t.c(rd, pS, 0, 1); t.c(pS, tw)
    t.c(stop_all, tw); t.c(T, rd, 0, 1)
    tws.append(tw); dubs.append(db)

# --- rec start/stop logic
recst = t.obj(900, 300, "t b f")       # recT o0 -> store rec, update
rfst = t.obj(900, 360, "f")
ru = t.obj(900, 330, "t b b")
rsel = t.obj(900, 390, "sel 1")
recA = t.obj(900, 420, "t b b b")
wspA = t.obj(1000, 470, "+ 1")
lpre = t.obj(900, 540, "list prepend 1")
rte = t.obj(900, 570, "route 1 2 3 4")
t.c(recT, recst, 0); t.c(recst, rfst, 1, 1); t.c(recst, ru, 0)
t.c(ru, rfst, 0); t.c(rfst, rsel)
# stop: fade out, then stop the writers ; start: cancel a pending stop, stop now, fade in, then start
pOut = t.obj(1000, 330, "t b b")
pOutM = t.msg(1100, 360, "0 8")
pDl = t.obj(1000, 390, "delay 10")
t.c(ru, pOut, 1); t.c(pOut, pOutM, 1); t.c(pOutM, pG); t.c(pOut, pDl, 0); t.c(pDl, stop_all)
pIn = t.obj(800, 420, "t b b b b")
pInM = t.msg(860, 450, "0 \\, 1 8")
pStp = t.msg(820, 450, "stop")
t.c(rsel, pIn); t.c(pIn, pStp, 3); t.c(pStp, pDl); t.c(pIn, stop_all, 2); t.c(pIn, pInM, 1); t.c(pInM, pG)
t.c(pIn, recA, 0)
t.c(recA, set0, 1); t.c(recA, onsetF, 0)
vwT = t.obj(1000, 500, "t f f")
sp1 = t.obj(900, 525, "spigot 1"); spV = t.obj(1100, 525, "spigot 0")
t.c(onsetF, wspA); t.c(wspA, vwT); t.c(vwT, spV, 1); t.c(vwT, sp1, 0); t.c(sp1, lpre); t.c(lpre, rte)
f1E = t.obj(900, 440, "== 1"); fVE = t.obj(960, 440, "!= 1")
t.c(facT, f1E, 1); t.c(f1E, sp1, 0, 1); t.c(facT, fVE, 1); t.c(fVE, spV, 0, 1)
vw2 = t.obj(1100, 760, "tape-vw 128 2"); vw05 = t.obj(1250, 760, "tape-vw 32 0.5")
trkF = t.obj(1250, 525, "f 1")
vsT = t.obj(1100, 555, "t f b")
t.c(spV, vsT)
nmV = t.obj(1250, 585, "makefilename tape%d")
setV = t.msg(1250, 615, "set \\$1")
t.c(vsT, trkF, 1); t.c(trkF, nmV); t.c(nmV, setV); t.c(setV, vw2, 0, 2); t.c(setV, vw05, 0, 2)
stV = t.msg(1100, 615, "start \\$1")
t.c(vsT, stV, 0)
sp2 = t.obj(1100, 645, "spigot 0"); sp05 = t.obj(1200, 645, "spigot 0")
t.c(stV, sp2); t.c(stV, sp05); t.c(sp2, vw2, 0, 2); t.c(sp05, vw05, 0, 2)
f2E = t.obj(1100, 470, "== 2"); f05E = t.obj(1160, 470, "== 0.5")
t.c(facT, f2E, 2); t.c(f2E, sp2, 0, 1); t.c(facT, f05E, 2); t.c(f05E, sp05, 0, 1)
t.c(stop_all, vw2, 0, 2); t.c(stop_all, vw05, 0, 2)
aa1 = t.obj(1250, 700, "biquad~ 0.22665935 -0.05144118 0.20619546 0.41239092 0.20619546"); aa2 = t.obj(1250, 730, "biquad~ 0.31385897 -0.45594812 0.28552229 0.57104457 0.28552229")
t.c(rin, vw2, 0, 0); t.c(rin, aa1); t.c(aa1, aa2); t.c(aa2, vw05, 0, 0); t.c(pG, vw2, 0, 1); t.c(pG, vw05, 0, 1)
for k in range(4):
    sm = t.msg(900 + k * 90, 610, "start \\$1")
    t.c(rte, sm, k); t.c(sm, tws[k])
# wrap while recording -> restart writer at 0
wsp = t.obj(1350, 430, "spigot")
t.c(wsel, wsp)
wOn = t.obj(1450, 400, "sel 0")
t.c(recst, wOn, 1); t.c(wOn, wsp, 1, 1)                       # rec on -> open now
wOff = t.msg(1500, 400, "0")
t.c(pDl, wOff); t.c(wOff, wsp, 0, 1)                          # rec off -> close after the fade
t.c(wsp, onsetF); t.c(rewT, wsp, 0)

# --- knobs
rk = t.obj(600, 100, "r tape-knob")
kdef = t.msg(760, 100, "1 0.75 \\, 2 0 \\, 3 1 \\, 4 0")
krt = t.obj(600, 140, "route 1 2 3 4")
t.c(tlb, kdef, 1); t.c(kdef, krt); t.c(rk, krt)
# 1 speed
# speed: 7 steps (-2 -1 -0.5 0 0.5 1 2, octaves) ; with AUX held: continuous, magnets at 1 / 0 / -1
k1b = t.obj(600, 200, "expr if($f2 \\, if(abs(($f1*4-2)-1)<0.12 \\, 1 \\, if(abs(($f1*4-2)+1)<0.12 \\, -1 \\, if(abs(($f1*4-2))<0.06 \\, 0 \\, int(($f1*4-2)*100)/100.0))) \\, if(int($f1*6.999)==0 \\, -2 \\, if(int($f1*6.999)==1 \\, -1 \\, if(int($f1*6.999)==2 \\, -0.5 \\, if(int($f1*6.999)==3 \\, 0 \\, if(int($f1*6.999)==4 \\, 0.5 \\, if(int($f1*6.999)==5 \\, 1 \\, 2)))))))")
t.c(t.obj(700, 170, "r aux"), k1b, 0, 1)
k1t = t.obj(600, 230, "t f f")
# speed restored by a project load: exact value (stored +10), 1x for old projects
spSet = t.obj(700, 230, "expr if($f1>0 \\, $f1-10 \\, 1)")
t.c(t.obj(700, 200, "r tp-spd-set"), spSet); t.c(spSet, k1t)
t.c(krt, k1b, 0); t.c(k1b, k1t); t.c(k1t, spdin, 0)
# 2 track
k2a = t.obj(780, 260, "expr int($f1*3.99)+1")
k2c = t.obj(780, 290, "change")
k2t = t.obj(780, 320, "t b f f")
k2D = t.obj(780, 305, "pipe 0")
t.c(krt, k2a, 1); t.c(k2a, k2c); t.c(k2c, k2D); t.c(k2D, k2t)
t.c(k2t, lpre, 1, 1); t.c(k2t, trkF, 1, 1); t.c(k2t, ru, 0)
# 3 dub
k3t = t.obj(960, 170, "t f f")
t.c(k3t, t.obj(1060, 200, "s tp-dub"), 1)
t.c(krt, k3t, 2)
for db in dubs:
    t.c(k3t, db, 0, 1)
# 4 wow
k4t = t.obj(1100, 170, "t f f")
t.c(krt, k4t, 3); t.c(k4t, we, 0)

# --- publish state for tape-screen.pd
t.c(playT, t.obj(1000, 700, "s tp-play"), 0)
t.c(recst, t.obj(1100, 700, "s tp-rec"), 1)
t.c(k1t, t.obj(1200, 700, "s tp-spd"), 1)
t.c(k2t, t.obj(1300, 700, "s tp-trk"), 2)
rask = t.obj(1000, 740, "r tp-ask")
posD = t.obj(1000, 770, "f")
t.c(rask, posD); t.c(T, posD, 0, 1); t.c(posD, t.obj(1000, 800, "s tp-pos"))

# --- save / load with the project (project.pd sends nst-save / nst-load with the project number)
sf = t.obj(260, 420, "soundfiler")
sv = t.obj(260, 360, "t f f f f")
t.c(t.obj(260, 330, "r nst-save"), sv)
ld = t.obj(420, 360, "t b f f f f")
t.c(t.obj(420, 330, "r nst-load"), ld)
t.c(ld, t.obj(420, 390, "s tp-loaded"), 0)
for k in range(4):
    mw = t.obj(260, 450 + k * 50, f"makefilename p%d-tape-{k+1}.wav")
    w = t.msg(260, 475 + k * 50, f"write -wave -bytes 2 \\$1 tape{k+1}")
    lT = t.obj(560, 430 + k * 60, "t f b")
    mr = t.obj(560, 455 + k * 60, f"makefilename p%d-tape-{k+1}.wav")
    r = t.msg(560, 475 + k * 60, f"read \\$1 tape{k+1}")
    t.c(sv, mw, 3 - k); t.c(mw, w); t.c(w, sf)
    t.c(ld, lT, 4 - k); t.c(lT, t.msg(700, 430 + k * 60, f"\\; tape{k+1} const 0"), 1)     # new / missing = empty
    t.c(lT, mr, 0); t.c(mr, r); t.c(r, sf)
svp = t.obj(260, 560, "print tape-saved")
t.c(sf, svp)

# --- loop (AUX+G#): 1st press = loop start, 2nd = loop end (starts looping), 3rd = loop off
lsF = t.obj(600, 560, "f")
lsel = t.obj(600, 590, "sel 0 1 2")
t.c(selk, lsF, 4); t.c(lsF, lsel)
posIn = t.obj(600, 650, "f"); posOut = t.obj(700, 650, "f"); posW = t.obj(800, 650, "f")
inV = t.obj(600, 680, "f")
for o in (posIn, posOut, posW):
    t.c(T, o, 0, 1)
# state 0 -> mark start
l0 = t.obj(600, 620, "t b b")
m1 = t.msg(660, 620, "1")
t.c(lsel, l0, 0); t.c(l0, posIn, 1); t.c(posIn, inV, 0, 1); t.c(l0, m1, 0); t.c(m1, lsF, 0, 1)
# state 1 -> mark end, set lo/hi, wrap now
l1 = t.obj(700, 620, "t b b b")
m2 = t.msg(760, 590, "2")
oT = t.obj(700, 710, "t f f")
# loop end: snapped to whole beats/bars when loop snap is on ($f3 = unit in samples)
hiE = t.obj(700, 740, f"expr min({N} \\, if($f3>0 \\, min($f1 \\, $f2)+$f3*max(1 \\, int((max($f1 \\, $f2)-min($f1 \\, $f2))/$f3+0.5)) \\, max(max($f1 \\, $f2) \\, min($f1 \\, $f2)+64)))")
loE = t.obj(850, 740, "expr min($f1 \\, $f2)")
t.c(lsel, l1, 1); t.c(l1, posOut, 2); t.c(posOut, oT)
t.c(inV, hiE, 0, 1); t.c(inV, loE, 0, 1)
t.c(oT, hiE, 1); t.c(oT, loE, 0)
t.c(l1, m2, 1); t.c(m2, lsF, 0, 1)
t.c(l1, posW, 0); t.c(posW, pT)
# state 2 -> loop off
l2b = t.obj(800, 590, "t b b b")
m0 = t.msg(860, 620, "0")
mN = t.msg(900, 650, "%d" % N)
mz = t.msg(960, 650, "0")
t.c(lsel, l2b, 2); t.c(l2b, mN, 2); t.c(l2b, mz, 1); t.c(l2b, m0, 0); t.c(m0, lsF, 0, 1)
# lo / hi distribution
hiT = t.obj(700, 780, "t f f")
loT = t.obj(850, 780, "t f f f")
t.c(hiE, hiT); t.c(mN, hiT); t.c(loE, loT); t.c(mz, loT)
t.c(hiT, wrapE, 1, 2); t.c(hiT, wflag, 0, 2)
t.c(loT, wrapE, 2, 1); t.c(loT, wflag, 1, 1); t.c(loT, rew, 0, 1)
lbL = t.obj(960, 560, "loadbang")
t.c(lbL, mN); t.c(lbL, mz)
# loop state for the screen
sls = t.obj(1150, 560, "s tp-ls")
t.c(m1, sls); t.c(m2, sls); t.c(m0, sls); t.c(lbL, m0)
t.c(hiT, t.obj(1150, 600, "s tp-hi"), 0)
t.c(loT, t.obj(1250, 600, "s tp-lo"), 0)
t.c(posIn, t.obj(1350, 600, "s tp-in"))

# --- tempo: loop snap unit, beat ticks for the metronome and the screen
rlq = t.obj(1400, 700, "r loop-q")
rtb = t.obj(1500, 700, "r tempo-beat")
rtbT = t.obj(1500, 730, "t b f")
unitE = t.obj(1400, 760, "expr if($f1==1 \\, $f2 \\, if($f1==2 \\, 4*$f2 \\, 0))")
t.c(rlq, unitE); t.c(rtb, rtbT); t.c(rtbT, unitE, 1, 1); t.c(rtbT, unitE, 0, 0)
t.c(unitE, hiE, 0, 2)
beatE = t.obj(1400, 820, "expr floor(($f1-if($f4==2 \\, $f2 \\, 0))/max($f3 \\, 1))")
t.c(T, beatE, 0, 0); t.c(loT, beatE, 0, 1); t.c(rtb, beatE, 0, 2)
for mm in (m0, m1, m2):
    t.c(mm, beatE, 0, 3)
bC = t.obj(1400, 850, "change")
bSp = t.obj(1400, 880, "spigot")
t.c(beatE, bC); t.c(bC, bSp); t.c(playT, bSp, 0, 1)
bM = t.obj(1400, 910, "expr fmod(fmod($f1 \\, 4)+4 \\, 4)")
bTT = t.obj(1400, 940, "t f f")
t.c(bSp, bM); t.c(bM, bTT); t.c(bTT, t.obj(1500, 970, "s tp-beat"), 1)
bAcc = t.obj(1400, 970, "== 0")
t.c(bTT, bAcc, 0); t.c(bAcc, t.obj(1400, 1000, "s tick"))
# 16th-note index for the sequencer (same grid as the beat: loop start when looping)
s16E = t.obj(1600, 820, "expr floor(($f1-if($f4==2 \\, $f2 \\, 0))/max($f3/4 \\, 1))")
t.c(T, s16E, 0, 0); t.c(loT, s16E, 0, 1); t.c(rtb, s16E, 0, 2)
for mm in (m0, m1, m2):
    t.c(mm, s16E, 0, 3)
s16T = t.obj(1600, 850, "t f f")
s16F = t.obj(1700, 880, "f")
s16C = t.obj(1600, 880, "change")
s16Sp = t.obj(1600, 910, "spigot")
s16S = t.obj(1600, 940, "s tick16")
t.c(s16E, s16T); t.c(s16T, s16F, 1, 1); t.c(s16T, s16C, 0); t.c(s16C, s16Sp)
t.c(playT, s16Sp, 0, 1); t.c(s16Sp, s16S)
# when play starts, play the current step at once
plOn = t.obj(1700, 820, "sel 1")
t.c(playT, plOn, 0); t.c(plOn, s16F); t.c(s16F, s16S)
# --- navigation: AUX+C#5 (73) back / AUX+D#5 (75) forward
# no loop: jump to the previous / next bar. loop on: move the loop window by its own length
# (previous / next loop), keeping the playhead's place inside the loop.
navK = t.obj(1800, 700, "r aux-key")
navS = t.obj(1800, 730, "sel 73 75")
navB = t.msg(1800, 760, "-1")
navF = t.msg(1860, 760, "1")
nDf = t.obj(1800, 715, "pipe 0")
t.c(navK, nDf); t.c(nDf, navS); t.c(navS, navB, 0); t.c(navS, navF, 1)
navE = t.obj(1800, 800, f"expr $f5==2 \\; "
                        f"if($f5==2 \\, min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3)) \\, $f3) \\; "
                        f"if($f5==2 \\, min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3))+($f4-$f3) \\, $f4) \\; "
                        f"if($f5==2 \\, $f2+min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3))-$f3 \\, "
                        f"min(max(if($f1>0 \\, (floor($f2/max($f6 \\, 64)+0.01)+1) \\, (ceil($f2/max($f6 \\, 64)-0.01)-1))*max($f6 \\, 64) \\, 0) \\, {N}-1))")
t.c(navB, navE); t.c(navF, navE)
t.c(T, navE, 0, 1)                    # current position (onset, updated every block)
t.c(loT, navE, 0, 2)                  # loop start
t.c(hiT, navE, 0, 3)                  # loop end
for mm in (m0, m1, m2):               # loop state 0 / 1 / 2
    t.c(mm, navE, 0, 4)
navBar = t.obj(1950, 760, "* 4")
t.c(rtb, navBar); t.c(navBar, navE, 0, 5)
navP = t.obj(1800, 840, "pack f f f f")
for o in range(4):
    t.c(navE, navP, o, o)
navT = t.obj(1800, 870, "t l l")
t.c(navP, navT)
# 1) when looping: new loop bounds first
navR = t.obj(1900, 900, "route 1")
navU = t.obj(1900, 930, "unpack f f f")
t.c(navT, navR, 1); t.c(navR, navU, 0)
t.c(navU, hiT, 1); t.c(navU, loT, 0)
# 2) then move the playhead there (same path as rewind: onset, counter reset, writer restart if recording)
navU2 = t.obj(1800, 900, "unpack f f f f")
navSk = t.obj(1800, 930, "t b b f")
t.c(navT, navU2, 0); t.c(navU2, navSk, 3)
t.c(navSk, T, 2); t.c(navSk, set0, 1); t.c(navSk, wsp, 0)

# --- restore the loop from a project: "state start end"
tls = t.obj(2000, 700, "r tp-loop-set")
tlsU = t.obj(2000, 730, "unpack f f f")
t.c(tls, tlsU)
tlsS = t.obj(2000, 790, "sel 2")
tlsP = t.obj(2100, 760, "pack f f")
t.c(tlsU, tlsP, 2, 1); t.c(tlsU, tlsP, 1, 0)
tlsK = t.obj(2100, 790, "list")
t.c(tlsP, tlsK, 0, 1)
t.c(tlsU, tlsS, 0)
tlsOn = t.obj(2000, 820, "t b b")
t.c(tlsS, tlsOn, 0)
tlsU2 = t.obj(2100, 850, "unpack f f")
t.c(tlsOn, tlsK, 1); t.c(tlsK, tlsU2); t.c(tlsU2, hiT, 1); t.c(tlsU2, loT, 0)
t.c(tlsOn, m2, 0)
tlsOff = t.obj(2200, 820, "t b b b")
t.c(tlsS, tlsOff, 1)
t.c(tlsOff, mN, 2); t.c(tlsOff, mz, 1); t.c(tlsOff, m0, 0)

# --- loop recording seam fix (apply_loopseam.py)
t.obj(1600, 1480, "table seamsave 130")
smTrk = t.obj(1600, 1530, "f 1"); smLo = t.obj(1700, 1530, "f 0"); smHi = t.obj(1800, 1530, f"f {N}")
smLs = t.obj(1900, 1530, "f 0"); smDub = t.obj(2000, 1530, "f 1"); smT = t.obj(2100, 1530, "f 0")
t.c(t.obj(1600, 1500, "r tp-trk"), smTrk, 0, 1)
t.c(t.obj(1700, 1500, "r tp-lo"), smLo, 0, 1)
t.c(t.obj(1900, 1500, "r tp-ls"), smLs, 0, 1)
t.c(t.obj(2000, 1500, "r tp-dub"), smDub, 0, 1)
t.c(T, smT, 0, 1)                                           # wrapped onset of the next block
smName = t.obj(1600, 1560, "makefilename tape%d")
t.c(smTrk, smName)
# 1) save the 65 samples after the loop end (rec start, loop end moved)
svT = t.obj(1600, 1600, "t b b b")
smHiIn = t.obj(1800, 1560, "t b f")
t.c(t.obj(1800, 1500, "r tp-hi"), smHiIn)
smHiSv = t.obj(1900, 1600, f"f {N}")                       # own copy: the fix also reads smHi, it must not trigger a save
t.c(smHiIn, smHi, 1, 1); t.c(smHiIn, smHiSv, 1, 1); t.c(smHiIn, svT, 0)
t.c(recA, svT, 2)                                           # before the writer starts
svG = t.obj(1600, 1660, "array get tape1")
svS = t.obj(1600, 1690, "array set seamsave")
nmSym = t.obj(1600, 1585, "t s s s")
t.c(smName, nmSym)
t.c(nmSym, svG, 0, 2)                                       # table name -> right inlet of [array get]
n65 = t.msg(1700, 1630, "129")
t.c(svT, smTrk, 2)                                          # a) name
t.c(svT, n65, 1); t.c(n65, svG, 0, 1)                       # b) how many
t.c(svT, smHiSv, 0); t.c(smHiSv, svG, 0, 0)                 # c) from the loop end (hot)
t.c(svG, svS)
# 2) at each wrap while recording (wsp fires): move the overshoot to the loop start, restore after the end
fxT = t.obj(2200, 1600, "t b b b b b b")
t.c(wsp, fxT)
nE = t.obj(2200, 1660, f"expr if($f2==2 && $f4<{N}-140 \\, max(0 \\, min(129 \\, $f1-$f3+1)) \\, 0)")
valE = t.obj(2400, 1760, "expr if(xwm[$f7] && $f8==1 \\, $s2[$f4+$f1]+($s2[$f3+$f1]-if($f1==0 \\, seamsave[0] \\, $s2[$f3+$f1]))*(1-pgbuf[max(0 \\, int(64-($f6-$f1)/$f8))]*(1-$f5)) \\, $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+pgbuf[max(0 \\, int(64-($f6-$f1)/$f8))]*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1]))")
t.c(facT, valE, 0, 7)                                       # rec factor
smK = t.obj(2500, 1730, "- 1")
t.c(smTrk, smK); t.c(smK, valE, 0, 6)
loAdd = t.obj(2200, 1760, "+ 0"); hiAdd = t.obj(2300, 1760, "+ 0")
w1 = t.obj(2200, 1820, "tabwrite tape1"); w2 = t.obj(2350, 1820, "tabwrite tape1")
setM = t.msg(2500, 1700, "set \\$1")
t.c(nmSym, setM, 1); t.c(setM, w1); t.c(setM, w2)
t.c(nmSym, valE, 2, 1)                                      # $s2 table name
t.c(fxT, smTrk, 5)                                          # a) table names everywhere
t.c(fxT, smLs, 4); t.c(smLs, nE, 0, 1)                      # b) loop state
t.c(fxT, smLo, 3); t.c(smLo, nE, 0, 2); t.c(smLo, loAdd, 0, 1); t.c(smLo, valE, 0, 2)
t.c(fxT, smHi, 2); t.c(smHi, nE, 0, 3); t.c(smHi, hiAdd, 0, 1); t.c(smHi, valE, 0, 3)
t.c(fxT, smDub, 1); t.c(smDub, valE, 0, 4)
t.c(fxT, smT, 0); t.c(smT, nE, 0, 0)                        # c) n (hot)
# loop j = 0 .. n-1
nT = t.obj(2200, 1690, "t f b f")
t.c(nE, nT); t.c(nT, valE, 2, 5)
jz = t.msg(2300, 1690, "0")
jU = t.obj(2200, 1710, "until")
jF = t.obj(2200, 1730, "f")
jFT = t.obj(2200, 1745, "t f f")
jInc = t.obj(2260, 1745, "+ 1")
t.c(nT, jz, 1); t.c(jz, jF, 0, 1); t.c(nT, jU, 0)
t.c(jU, jF); t.c(jF, jFT); t.c(jFT, jInc, 1); t.c(jInc, jF, 0, 1)
jT = t.obj(2200, 1775, "t f f f f")
t.c(jFT, jT, 0)
t.c(jT, loAdd, 3); t.c(loAdd, w1, 0, 1)                     # write index lo+j
t.c(jT, hiAdd, 2); t.c(hiAdd, w2, 0, 1)                     # restore index hi+j
t.c(jT, valE, 1); t.c(valE, w1, 0, 0)                       # new value at lo+j (reads hi+j before it is restored)
sr = t.obj(2350, 1790, "tabread seamsave")
t.c(jT, sr, 0); t.c(sr, w2, 0, 0)                           # restore hi+j
t.obj(2600, 1480, "table pgbuf 64")
pgW = t.obj(2600, 1530, "tabwrite~ pgbuf")
t.c(pG, pgW)
pgSp = t.obj(2700, 1500, "spigot")
t.c(bng, pgSp); t.c(pgSp, pgW)
t.c(wOn, pgSp, 1, 1); t.c(wOff, pgSp, 0, 1)                    # only while the writer runs
# --- sample-accurate wrap / per-track crossfade (apply_xfadeauto.py)
# dW = offset that wraps the absolute read position (idx + onset) into [lo, hi)
dW = t.obj(2600, 1900, "expr~ ($v1+$f2>=$f3+1)*(-$f4)+($v1+$f2<$f5+1)*$f4")
t.c(idx, dW, 0, 0); t.c(T, dW, 0, 1)
wHi = t.obj(2600, 1640, f"f {N}"); wLo = t.obj(2700, 1640, "f 0")
wLen = t.obj(2800, 1640, "expr $f1-$f2")
wHT = t.obj(2600, 1610, "t f f f"); wLT = t.obj(2700, 1610, "t b f f")
t.c(hiT, wHT, 0); t.c(loT, wLT, 0)
t.c(wHT, dW, 2, 2); t.c(wHT, wHi, 1, 1); t.c(wHT, wLen, 0, 0)
t.c(wLT, dW, 2, 4); t.c(wLT, wLo, 1, 1); t.c(wLT, wLen, 1, 1); t.c(wLT, wHi, 0); t.c(wHi, wLen, 0, 0)
t.c(wLen, dW, 0, 3)
# decide before the block that crosses an edge: near hi when going forward, near lo when going backward
nearE = t.obj(2600, 1700, "expr if($f4>=0 \\, if($f1>$f2-200 \\, 1 \\, 0) \\, if($f1<$f3+200 \\, 2 \\, 0))")
t.c(T, nearE, 0, 0); t.c(wHT, nearE, 1, 1); t.c(wLT, nearE, 1, 2); t.c(st, nearE, 0, 3)   # direction = speed sign
nearC = t.obj(2600, 1730, "change")
nearS = t.obj(2600, 1760, "sel 1 2")
t.c(nearE, nearC)
dirF = t.msg(2600, 1790, "1"); dirR = t.msg(2650, 1790, "0")
t.c(nearS, dirF, 0); t.c(nearS, dirR, 1)
dP = t.obj(2600, 1850, "pack f f f")              # direction, hi, lo
dT = t.obj(2600, 1820, "t f b b")
t.c(dirF, dT); t.c(dirR, dT)
t.c(dT, wLo, 2); t.c(wLo, dP, 0, 2)
t.c(dT, wHi, 1); t.c(wHi, dP, 0, 1)
t.c(dT, dP, 0, 0)
t.obj(2600, 1580, "table xwm 4")                  # per-track wrap mode, read by the seam fix
# leaving the edge zone (after the wrap): restore the guarded samples first, then act on the new zone
nearT = t.obj(2800, 1760, "t f b")
restB = t.obj(2800, 1790, "t b")
t.c(nearC, nearT); t.c(nearT, restB, 1); t.c(nearT, nearS, 0)
# guard sample m: forward (index, source), backward (index, source), valid forward, valid backward
GUARD = (("$f2", "$f3", "$f2", "$f3", "1", "1"),
         ("$f2+1", "$f3+1", "$f2+1", "$f3+1", f"$f2+1<{N}", f"$f2+1<{N}"),
         ("$f2+2", "$f3+2", "$f2+2", "$f3+2", f"$f2+2<{N}", f"$f2+2<{N}"))
for k in range(4):
    x = 2900 + k * 400
    tb = f"tape{k+1}"
    # $f1 direction (1 forward), $f2 hi, $f3 lo. forward: e = hi-1, e2 = hi-2, wrapped = lo, past = hi
    # backward: e = lo, e2 = lo+1, wrapped = hi-1, past = lo-1
    e = "if($f1 \\, $f2-1 \\, $f3)"; e2 = "if($f1 \\, $f2-2 \\, $f3+1)"
    w = "if($f1 \\, $f3 \\, $f2-1)"; c = "if($f1 \\, $f2 \\, $f3-1)"
    pr = f"(2*{tb}[{e}]-{tb}[{e2}])"
    dPt = t.obj(x, 1860, "t l l")
    t.c(dP, dPt)
    dec = t.obj(x, 1880, f"expr abs({tb}[{w}]-{pr})<=abs({tb}[{c}]-{pr})+0.002")
    t.c(dPt, dec, 1)                                     # decision first
    decT = t.obj(x, 1905, "t f f f")
    t.c(dec, decT)
    xwmW = t.obj(x + 200, 1930, "tabwrite xwm")
    lbK = t.obj(x + 200, 1880, "loadbang"); mK = t.msg(x + 200, 1905, f"{k}")
    t.c(lbK, mK); t.c(mK, xwmW, 0, 1)                    # table index = track
    t.c(decT, xwmW, 2, 0)
    wF = t.obj(x, 1935, "f 0")
    t.c(decT, wF, 1, 1)
    mW = t.obj(x, 1990, "*~ 0"); aW = t.obj(x, 2020, "+~")
    t.c(decT, mW, 0, 1)
    t.c(dW, mW, 0, 0); t.c(mW, aW, 0, 0); t.c(idx, aW, 0, 1); t.c(aW, rds[k], 0, 0)   # read index: idx + w*dW
    # at the wrap: wrapped tracks play straight (A = 1, B = 0), the others crossfade
    lA = t.obj(x, 2110, "line~"); lB = t.obj(x + 80, 2110, "line~")
    sl = t.obj(x, 2050, "sel 0")
    mAx = t.msg(x, 2080, "0 \\, 1 5"); mBx = t.msg(x + 60, 2080, "1 \\, 0 5")
    tN = t.obj(x + 120, 2050, "t b b")
    mAn = t.msg(x + 120, 2080, "1"); mBn = t.msg(x + 160, 2080, "0")
    t.c(xW, wF, 0); t.c(wF, sl)
    t.c(sl, mAx, 0); t.c(sl, mBx, 0); t.c(sl, tN, 1); t.c(tN, mAn, 0); t.c(tN, mBn, 1)
    t.c(mAx, lA); t.c(mAn, lA); t.c(mBx, lB); t.c(mBn, lB)
    t.c(lA, xAs[k], 0, 1); t.c(lB, xBs[k], 0, 1)
    t.c(lbL, mAn); t.c(lbL, mBn)
    # interpolation guard
    for m, (fi, fs, ri, rs, okf, okr) in enumerate(GUARD):
        gx = x + m * 130
        # outlet 0: index to guard (-1 = none), outlet 1: where its continuation is. $f4 wrap mode, $f5 rec
        iE = t.obj(gx, 2160, f"expr if($f4 && !$f5 && if($f1 \\, {okf} \\, {okr}) \\, if($f1 \\, {fi} \\, {ri}) \\, -1) \\; if($f1 \\, {fs} \\, {rs})")
        t.c(dec, iE, 0, 3); t.c(recst, iE, 1, 4)              # rec state gates the guard
        t.c(dPt, iE, 0, 0)                               # after the decision (t l l: right outlet first)
        iP = t.obj(gx, 2190, "pack f f")                 # expr outlets are lazy: collect both
        t.c(iE, iP, 1, 1); t.c(iE, iP, 0, 0)
        iU = t.obj(gx, 2220, "unpack f f")
        t.c(iP, iU)
        srcF = t.obj(gx + 70, 2250, "f")
        t.c(iU, srcF, 1, 1)
        iS = t.obj(gx, 2250, "moses 0")
        t.c(iU, iS, 0, 0)
        gT = t.obj(gx, 2280, "t b f f f")               # 3: remember index, 2: save original, 1: write index, 0: copy
        t.c(iS, gT, 1)
        idxF = t.obj(gx, 2460, "f -1")
        t.c(gT, idxF, 3, 1)
        svR = t.obj(gx + 70, 2310, f"tabread {tb}"); svF = t.obj(gx + 70, 2340, "f")
        t.c(gT, svR, 2); t.c(svR, svF, 0, 1)
        wG = t.obj(gx, 2370, f"tabwrite {tb}")
        t.c(gT, wG, 1, 1)
        cpR = t.obj(gx, 2340, f"tabread {tb}")
        t.c(gT, srcF, 0); t.c(srcF, cpR); t.c(cpR, wG, 0, 0)
        # restore: idx >= 0 -> write the saved value back there, idx = -1
        t.c(restB, idxF, 0)
        rS = t.obj(gx, 2490, "moses 0")
        t.c(idxF, rS)
        rT = t.obj(gx, 2520, "t b b f")
        t.c(rS, rT, 1)
        wR = t.obj(gx, 2580, f"tabwrite {tb}")
        t.c(rT, wR, 2, 1); t.c(rT, svF, 1); t.c(svF, wR, 0, 0)
        mNone = t.msg(gx + 70, 2550, "-1")
        t.c(rT, mNone, 0); t.c(mNone, idxF, 0, 1)
t.save("tape.pd")

# ---------------------------------------------------------------- tape-vw.pd (apply_varirec.py)
# resampled tape writer: args block size, resampling factor (2 = two tape samples per audio sample, 0.5 = one per two)
# inlets: ~ input, ~ punch fade gain, messages: set <table> / start <index> / stop
w = Patch(800, 600)
w.text(20, 5, "tape-vw: tape writer at 2x or 0.5x the audio rate (switch~ on only while writing)")
wIn = w.obj(20, 40, "inlet~ lin"); wG = w.obj(200, 40, "inlet~ lin"); wC = w.obj(400, 40, "inlet")
wSw = w.obj(600, 400, "switch~ \$1 1 \$2")
wOn = w.msg(600, 370, "1"); wOff = w.msg(660, 370, "0")
w.c(wOn, wSw); w.c(wOff, wSw)
w.c(w.obj(660, 340, "loadbang"), wOff)                      # off until the first start
wRt = w.obj(400, 70, "route start stop")
w.c(wC, wRt)
wSet = w.obj(300, 100, "t a")                               # rejected = "set <table>": reader and writer
w.c(wRt, wSet, 2)
wStT = w.obj(500, 100, "t f f b")                           # start: 2) DSP on  1) index counter  0) writer
w.c(wRt, wStT, 0)
w.c(wStT, wOn, 2)
wM1 = w.obj(500, 130, "- 1"); wSetI = w.msg(500, 160, "set \$1")
w.c(wStT, wM1, 1); w.c(wM1, wSetI)
wStart = w.msg(400, 160, "start \$1")
w.c(wStT, wStart, 0)
wStopT = w.obj(700, 100, "t b b")                           # stop: 1) writer stop  0) DSP off
wStopM = w.msg(760, 130, "stop")
w.c(wRt, wStopT, 1); w.c(wStopT, wStopM, 1); w.c(wStopT, wOff, 0)
# write index: counts 1 per sample from <index>
one = w.obj(200, 200, "sig~ 1"); idx = w.obj(200, 230, "rpole~ 1")
w.c(one, idx); w.c(wSetI, idx)
rd = w.obj(200, 260, "tabread~ tape1"); w.c(wSet, rd); w.c(idx, rd)
# input: gentle low-pass (images when upsampling; a no-op at the halved rate)
l1 = w.obj(20, 230, "lop~ 16000"); l2 = w.obj(20, 260, "lop~ 16000")
w.c(wIn, l1); w.c(l1, l2)
# written = old + g * (dub * old + in - old)
dub = w.obj(300, 290, "*~ 1"); w.c(rd, dub); w.c(w.obj(400, 260, "r tp-dub"), dub, 0, 1)
a1 = w.obj(20, 320, "+~"); w.c(l2, a1, 0, 0); w.c(dub, a1, 0, 1)
d1 = w.obj(20, 350, "-~"); w.c(a1, d1, 0, 0); w.c(rd, d1, 0, 1)
m1 = w.obj(20, 380, "*~"); w.c(d1, m1, 0, 0); w.c(wG, m1, 0, 1)
a2 = w.obj(20, 410, "+~"); w.c(m1, a2, 0, 0); w.c(rd, a2, 0, 1)
tw = w.obj(20, 450, "tabwrite~ tape1")
w.c(a2, tw); w.c(wSet, tw); w.c(wStart, tw); w.c(wStopM, tw)
w.save("tape-vw.pd")

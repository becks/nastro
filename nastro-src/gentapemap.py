# exec'd from gen.py: builds tape-map.pd
# - occ1..occ4: per-track content map, 600 bins of 4410 samples (0.1 s)
# - rebuilt from the tape tables at load, updated from the real signal while recording
# - publishes the timeline view (tp-vs / tp-ve) and the 4 track lanes as
#   "x1 y x2" lines in [text define nst-lanes] for tape-screen.pd
N = 2646000
BINS = 600
BIN = N // BINS          # 4410
COLS = 63                # 2-px columns across the timeline

tm = Patch(1500, 1100)
tm.text(20, 5, "tape-map: where each tape track has audio (TAPE screen lanes)")
for k in range(4):
    tm.obj(20 + k * 110, 40, f"table occ{k+1} {BINS}")
tm.obj(470, 40, "text define nst-lanes")
tm.obj(650, 40, "text define nst-lanes-tmp")

# ------------------------------------------------ scanner: "track bin" -> occK[bin]
scan = tm.obj(20, 120, "route 1 2 3 4")
tm.c(tm.obj(20, 90, "r tp-rescan-bin"), scan)
lastMax = tm.obj(700, 270, "max")
lastF = tm.obj(700, 300, "f -1")
sLast = tm.obj(700, 330, "s tp-last")
tm.c(lastMax, lastF); tm.c(lastF, lastMax, 0, 1); tm.c(lastF, sLast)
for k in range(4):
    x = 20 + k * 160
    bT = tm.obj(x, 150, "t f f f")
    onMin = tm.obj(x + 60, 180, f"* {BIN}")
    amin = tm.obj(x + 60, 210, f"array min tape{k+1} 0 {BIN}")
    onMax = tm.obj(x, 180, f"* {BIN}")
    amax = tm.obj(x, 240, f"array max tape{k+1} 0 {BIN}")
    pk = tm.obj(x, 270, "expr max($f1 \\, -$f2)>0.004")
    pkT = tm.obj(x, 300, "t f f")
    tw = tm.obj(x, 330, f"tabwrite occ{k+1}")
    lk = tm.obj(x + 90, 330, "expr if($f1 \\, $f2 \\, -1)")
    tm.c(scan, bT, k)
    tm.c(bT, tw, 2, 1); tm.c(bT, lk, 2, 1)
    tm.c(bT, onMin, 1); tm.c(onMin, amin); tm.c(amin, pk, 0, 1)
    tm.c(bT, onMax, 0); tm.c(onMax, amax); tm.c(amax, pk, 0, 0)
    tm.c(pk, pkT); tm.c(pkT, tw, 1); tm.c(pkT, lk, 0); tm.c(lk, lastMax)

# ------------------------------------------------ full rescan after the tape files load
rld = tm.obj(20, 380, "r tp-loaded")
fT = tm.obj(20, 410, "t b b")
fz = tm.msg(120, 440, "0")
full = tm.msg(20, 440, f"{4 * BINS}")
fu = tm.obj(20, 470, "until")
fc = tm.obj(20, 500, "f")
fc1 = tm.obj(70, 500, "+ 1")
fE = tm.obj(20, 530, f"expr int($f1/{BINS})+1 \\; $f1%{BINS}")
fP = tm.obj(20, 560, "pack f f")
tm.c(rld, fT); tm.c(fT, fz, 1); tm.c(fz, fc, 0, 1); tm.c(fT, full, 0)
tm.c(full, fu); tm.c(fu, fc); tm.c(fc, fc1); tm.c(fc1, fc, 0, 1); tm.c(fc, fE)
tm.c(fE, fP, 1, 1); tm.c(fE, fP, 0, 0); tm.c(fP, scan)

# ------------------------------------------------ live update while recording (every 250 ms)
rrec = tm.obj(300, 380, "r tp-rec")
recT = tm.obj(300, 410, "t f f")
lmt = tm.obj(300, 440, "metro 250")                     # 4 lane updates/s while recording (was 50 ms: a full lanes rebuild + redraw 10x/s)
rec0 = tm.obj(400, 440, "sel 0")
tm.c(rrec, recT); tm.c(recT, rec0, 1); tm.c(recT, lmt, 0)
lT = tm.obj(300, 470, "t b b")
tm.c(lmt, lT); tm.c(rec0, lT)            # one last scan when recording stops
ask = tm.obj(400, 500, "s tp-ask")
fPos = tm.obj(300, 500, "f")
tm.c(tm.obj(480, 470, "r tp-pos"), fPos, 0, 1)
tm.c(lT, ask, 1); tm.c(lT, fPos, 0)
bE = tm.obj(300, 530, f"expr int($f1/{BIN}) \\; max(0 \\, int($f1/{BIN})-1)")
lp1 = tm.obj(300, 560, "list prepend 1")
lp2 = tm.obj(420, 560, "list prepend 1")
rtrk = tm.obj(540, 530, "r tp-trk")
tm.c(fPos, bE); tm.c(bE, lp2, 1); tm.c(bE, lp1, 0)
tm.c(rtrk, lp1, 0, 1); tm.c(rtrk, lp2, 0, 1)
tm.c(lp1, scan); tm.c(lp2, scan)

# ------------------------------------------------ view + lanes, 10 fps in TAPE mode
vF = {}
for i, (name, init) in enumerate((("tp-ls", "f"), ("tp-lo", "f"), ("tp-hi", f"f {N}"), ("tp-last", "f -1"))):
    r = tm.obj(700 + i * 110, 380, f"r {name}")
    f = tm.obj(700 + i * 110, 410, init)
    tm.c(r, f, 0, 1)
    vF[name] = f
fPos2 = tm.obj(1140, 410, "f")
tm.c(tm.obj(1140, 380, "r tp-pos"), fPos2, 0, 1)

rmode = tm.obj(700, 460, "r mode")
eq2 = tm.obj(700, 490, "== 2")
mt = tm.obj(700, 520, "metro 100")
tm.c(rmode, eq2); tm.c(eq2, mt)
seq = tm.obj(700, 550, "t b b b b b b b")
tm.c(mt, seq)
# view start / end in samples (end rounded up to whole seconds so it changes rarely)
vE = tm.obj(700, 620,
            f"expr if($f1==2 \\, $f2 \\, 0) \; "
            f"if($f1==2 \\, $f3 \\, min({N} \\, max(441000 \\, ceil(max(($f4+1)*{BIN} \\, $f5)*1.25/44100)*44100)))")
tm.c(seq, vF["tp-last"], 6); tm.c(vF["tp-last"], vE, 0, 3)
tm.c(seq, fPos2, 5); tm.c(fPos2, vE, 0, 4)
tm.c(seq, vF["tp-hi"], 4); tm.c(vF["tp-hi"], vE, 0, 2)
tm.c(seq, vF["tp-lo"], 3); tm.c(vF["tp-lo"], vE, 0, 1)
tm.c(seq, vF["tp-ls"], 2); tm.c(vF["tp-ls"], vE, 0, 0)
vsC = tm.obj(700, 650, "change -1")
veC = tm.obj(850, 650, "change -1")
vsT = tm.obj(700, 680, "t f f b")
veT = tm.obj(850, 680, "t f f b")
tm.c(vE, veC, 1); tm.c(vE, vsC, 0); tm.c(vsC, vsT); tm.c(veC, veT)
tm.c(vsT, tm.obj(700, 710, "s tp-vs"), 1)
tm.c(veT, tm.obj(850, 710, "s tp-ve"), 1)
# dirty flag: set by a view change, a content change (scan) or a load
dirty = tm.msg(1000, 470, "1")
fDirty = tm.obj(1000, 500, "f 1")
tm.c(dirty, fDirty, 0, 1); tm.c(vsT, dirty, 2); tm.c(veT, dirty, 2)
tm.c(rld, dirty); tm.c(lT, dirty, 0)
tm.c(tm.obj(1100, 470, "r tp-rescan-done"), dirty)
tm.c(seq, fDirty, 0)
dSel = tm.obj(1000, 530, "sel 1")
dT = tm.obj(1000, 560, "t b b b b")
d0 = tm.msg(1150, 560, "0")
tm.c(fDirty, dSel); tm.c(dSel, dT); tm.c(dT, d0, 2); tm.c(d0, fDirty, 0, 1)
clrM = tm.msg(1250, 590, "\; nst-lanes-tmp clear")
tm.c(dT, clrM, 1)
# loop over 4 lanes x (COLS + 1) columns (the extra column closes open runs)
lz = tm.msg(1100, 590, "0")
nloop = tm.msg(1000, 590, "32")
lu = tm.obj(1000, 620, "until")
lc = tm.obj(1000, 650, "f")
lc1 = tm.obj(1050, 650, "+ 1")
seq0 = tm.obj(1000, 530 + 60, "t b b")
tm.c(dT, seq0, 0); tm.c(seq0, lz, 1); tm.c(lz, lc, 0, 1)
# run the 256 iterations in chunks of 32, one chunk per scheduler tick
chT = tm.obj(1100, 530, "t b b")
ccF = tm.obj(1250, 650, "f")
ccA = tm.obj(1300, 650, "+ 1")
ccM = tm.obj(1250, 680, "moses 8")
ccZ = tm.msg(1350, 620, "0")
ccD = tm.obj(1250, 710, "delay 1")
tm.c(seq0, ccZ, 1); tm.c(ccZ, ccF, 0, 1); tm.c(seq0, chT, 0)
tm.c(chT, nloop, 1); tm.c(chT, ccF, 0); tm.c(ccF, ccA); tm.c(ccA, ccF, 0, 1); tm.c(ccA, ccM)
tm.c(ccM, ccD, 0); tm.c(ccD, chT)
# finished: copy the new lanes into the list the screen draws, then tell the screen
fin = tm.obj(1400, 680, "t b b b")
tm.c(ccM, fin, 1)
finClr = tm.msg(1500, 710, "\\; nst-lanes clear")
cpS = tm.obj(1400, 740, "text size nst-lanes-tmp")
cpU = tm.obj(1400, 770, "until")
cpC = tm.obj(1400, 800, "f")
cpC1 = tm.obj(1450, 800, "+ 1")
cpZ = tm.msg(1500, 740, "0")
cpG = tm.obj(1400, 830, "text get nst-lanes-tmp")
cpI = tm.obj(1400, 860, "text insert nst-lanes 1e+06")
cpT = tm.obj(1400, 710, "t b b")
tm.c(fin, finClr, 2); tm.c(fin, cpT, 1); tm.c(cpT, cpZ, 1); tm.c(cpZ, cpC, 0, 1); tm.c(cpT, cpS, 0)
tm.c(cpS, cpU); tm.c(cpU, cpC); tm.c(cpC, cpC1); tm.c(cpC1, cpC, 0, 1); tm.c(cpC, cpG); tm.c(cpG, cpI)
tm.c(fin, tm.obj(1550, 740, "s tp-lanes"), 0)
tm.c(nloop, lu); tm.c(lu, lc); tm.c(lc, lc1); tm.c(lc1, lc, 0, 1)
jE = tm.obj(1000, 680, f"expr int($f1/{COLS + 1}) \; $f1%{COLS + 1}")
jP = tm.obj(1000, 710, "pack f f")
tm.c(lc, jE); tm.c(jE, jP, 1, 1); tm.c(jE, jP, 0, 0)
jT = tm.obj(1000, 740, "t l l l")
tm.c(jP, jT)
# (first) new lane -> reset the change detector
c0 = tm.obj(1300, 770, "unpack f f")
c0s = tm.obj(1300, 800, "sel 0")
c0m = tm.msg(1300, 830, "set 0")
chg = tm.obj(1000, 860, "change")
tm.c(jT, c0, 2); tm.c(c0, c0s, 1); tm.c(c0s, c0m, 0); tm.c(c0m, chg)
# (second) remember lane and column
upk = tm.obj(1150, 770, "unpack f f")
colA = tm.obj(1150, 920, "f")       # column, for the run start
colB = tm.obj(1220, 920, "f")       # column, for the run end
laneF = tm.obj(1290, 920, "f")
tm.c(jT, upk, 1)
tm.c(upk, laneF, 0, 1); tm.c(upk, colA, 1, 1); tm.c(upk, colB, 1, 1)
# (third) bin range of this column (once), then the lane's occupancy over it
upk3 = tm.obj(1000, 770, "unpack f f")
abE = tm.obj(1060, 800,
             f"expr min({BINS - 1} \\, floor(($f2+$f1*($f3-$f2)/{COLS})/{BIN})) \; "
             f"if($f1>={COLS} \\, -1 \\, min({BINS - 1} \\, max(floor(($f2+$f1*($f3-$f2)/{COLS})/{BIN}) \\, "
             f"floor(($f2+($f1+1)*($f3-$f2)/{COLS}-1)/{BIN}))))")
tm.c(vsT, abE, 0, 1); tm.c(veT, abE, 0, 2)
abP = tm.obj(1000, 830, "pack f f f")
tm.c(jT, upk3, 0); tm.c(upk3, abE, 1, 0); tm.c(abE, abP, 1, 2); tm.c(abE, abP, 0, 1); tm.c(upk3, abP, 0, 0)
occR = tm.obj(1000, 860 - 0, "route 0 1 2 3")
tm.c(abP, occR)
for k in range(4):
    terms = [f"occ{k+1}[max(0 \\, min($f1+{i} \\, $f2))]" for i in range(10)]
    mx = terms[0]
    for tt in terms[1:]:
        mx = f"max({mx} \\, {tt})"
    e = tm.obj(1000 + k * 60, 890 + k * 15, f"expr if($f2<0 \\, 0 \\, {mx})")
    tm.c(occR, e, k)
    tm.c(e, chg)
rs = tm.obj(1000, 950, "sel 1 0")
tm.c(chg, rs)
startF = tm.obj(1150, 980, "f")
tm.c(rs, colA, 0); tm.c(colA, startF, 0, 1)          # run starts here
emitT = tm.obj(1000, 980, "t b b b")
tm.c(rs, emitT, 1)                                   # run ended at the previous column
runE = tm.obj(1000, 1010, "expr 1+2*$f2 \; 56+2*$f3 \; 2*$f1")
tm.c(emitT, laneF, 2); tm.c(laneF, runE, 0, 2)
tm.c(emitT, startF, 1); tm.c(startF, runE, 0, 1)
tm.c(emitT, colB, 0); tm.c(colB, runE, 0, 0)
runP = tm.obj(1000, 1040, "pack f f f")
for o in range(3):
    tm.c(runE, runP, o, o)
ins = tm.obj(1000, 1070, "text insert nst-lanes-tmp 1e+06")
tm.c(runP, ins)
tm.save("tape-map.pd")

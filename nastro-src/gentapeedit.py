# exec'd from gen.py: builds tapeedit.pd - tape editing on the selected track
# region = the loop when looping, otherwise the bar under the playhead.
# ops ([s tape-edit] 1..7): 1 cut 2 copy 3 paste 4 reverse 5 clear 6 duplicate 7 undo (swap = redo)
# Copies run in chunks (4096 samples per scheduler tick) so the Organelle never glitches.
N = 2646000
CH = 4096
BIN = 4410

te = Patch(2400, 1600)
te.text(20, 5, "tapeedit: CUT COPY PASTE REVERSE CLEAR DUPLICATE on the selected track - region = loop or current bar")
for i, nm in enumerate(("te-clip 1", "te-tmp 1", "te-rev 1", f"te-zero {CH}", "te-undo 1")):
    te.obj(20 + i * 130, 30, f"table {nm}")
TBL = ["te-zero", "tape1", "tape2", "tape3", "tape4", "te-clip", "te-tmp", "te-rev", "te-undo"]   # job table codes 0..8


def status(x, y, text):
    return te.msg(x, y, f"\\; nst-proj-status symbol {text}")


# ================================================= job runner
# [s te-job] "src srcStart dst dstStart len" (table codes; srcStart -1 = read zeros) -> [s te-done] when finished
jIn = te.obj(1200, 60, "r te-job")
jT = te.obj(1200, 90, "t b b l")
te.c(jIn, jT)
jU = te.obj(1300, 120, "unpack f f f f f")
te.c(jT, jU, 2)
aGet = te.obj(1200, 420, "array get te-zero")
aSet = te.obj(1200, 450, "array set te-zero")
srcSel = te.obj(1300, 160, "sel 0 1 2 3 4 5 6 7 8")
dstSel = te.obj(1550, 160, "sel 0 1 2 3 4 5 6 7 8")
te.c(jU, srcSel, 0); te.c(jU, dstSel, 2)
for i, nm in enumerate(TBL):
    ms_ = te.msg(1300 + (i % 4) * 60, 190 + (i // 4) * 20, f"symbol {nm}")
    md_ = te.msg(1550 + (i % 4) * 60, 190 + (i // 4) * 20, f"symbol {nm}")
    te.c(srcSel, ms_, i); te.c(ms_, aGet, 0, 2)      # array name goes to the rightmost inlet (Pd 0.49 has no 'set')
    te.c(dstSel, md_, i); te.c(md_, aSet, 0, 2)
# per chunk: $f1 done, $f2 len, $f3 dstStart, $f4 srcStart -> src onset, dst onset, n, new done
cE = te.obj(1200, 330, f"expr if($f4<0 \\, 0 \\, $f4+$f1) \\; $f3+$f1 \\; min({CH} \\, $f2-$f1) \\; $f1+min({CH} \\, $f2-$f1)")
te.c(jU, cE, 4, 1); te.c(jU, cE, 3, 2); te.c(jU, cE, 1, 3)
doneA = te.obj(1200, 300, "f"); doneB = te.obj(1400, 480, "f")
zero = te.msg(1100, 150, "0")
te.c(jT, zero, 1); te.c(zero, doneA, 0, 1); te.c(zero, doneB, 0, 1)
chunk = te.obj(1200, 270, "t b b")
te.c(jT, chunk, 0)
te.c(chunk, doneA, 1); te.c(doneA, cE)
te.c(cE, doneA, 3, 1); te.c(cE, doneB, 3, 1)
te.c(cE, aGet, 2, 1); te.c(cE, aSet, 1, 1); te.c(cE, aGet, 0, 0)
te.c(aGet, aSet)
chkE = te.obj(1400, 510, "expr $f1<$f2")
te.c(jU, chkE, 4, 1)
te.c(chunk, doneB, 0); te.c(doneB, chkE)
chkS = te.obj(1400, 540, "sel 1 0")
te.c(chkE, chkS)
nxt = te.obj(1400, 570, "delay 1")
te.c(chkS, nxt, 0); te.c(nxt, chunk)
te.c(chkS, te.obj(1500, 570, "s te-done"), 1)

# ================================================= lane rescan runner
# [s te-rescan] "track start length": rescans the touched 0.1 s bins (20 per tick), then shows the pending
# status, tells tape-map to redraw, and frees the editor.
pendS = te.obj(1900, 620, "symbol")
te.c(te.obj(1900, 590, "r te-pend"), pendS, 0, 1)
busyF = te.obj(700, 80, "f 0")
busy0 = te.msg(1800, 650, "0")
te.c(busy0, busyF, 0, 1)
rsIn = te.obj(1800, 60, "r te-rescan")
rsT = te.obj(1800, 90, "t b l")
te.c(rsIn, rsT)
rsE = te.obj(1800, 150, f"expr $f1 \\; int($f2/{BIN}) \\; int(($f2+max(1 \\, $f3)-1)/{BIN})+1")
te.c(rsT, rsE, 1)
rsLp = te.obj(2000, 380, "list prepend 1")
rsMos = te.obj(1900, 280, "moses 1")
rsCur = te.obj(1800, 250, "f")
rsC2 = te.obj(2100, 250, "f")
rsChkE = te.obj(2100, 280, "expr $f1<$f2")
te.c(rsE, rsMos, 2, 1); te.c(rsE, rsChkE, 2, 1)
te.c(rsE, rsCur, 1, 1); te.c(rsE, rsC2, 1, 1)
te.c(rsE, rsLp, 0, 1)
rsTick = te.obj(1800, 200, "t b b")
te.c(rsT, rsTick, 0)
rs20 = te.msg(1850, 220, "20")
rsU = te.obj(1850, 240, "until")
te.c(rsTick, rs20, 1); te.c(rs20, rsU); te.c(rsU, rsCur); te.c(rsCur, rsMos)
rsHit = te.obj(1900, 310, "t f f")
te.c(rsMos, rsHit, 0)
te.c(rsHit, rsLp, 1); te.c(rsLp, te.obj(2000, 410, "s tp-rescan-bin"))
rsInc = te.obj(1900, 340, "+ 1")
te.c(rsHit, rsInc, 0); te.c(rsInc, rsCur, 0, 1); te.c(rsInc, rsC2, 0, 1)
rsStop = te.obj(1950, 310, "t b")
te.c(rsMos, rsStop, 1); te.c(rsStop, rsU, 0, 1)
te.c(rsTick, rsC2, 0); te.c(rsC2, rsChkE)
rsChkS = te.obj(2100, 310, "sel 1 0")
te.c(rsChkE, rsChkS)
rsNext = te.obj(2100, 340, "delay 1")
te.c(rsChkS, rsNext, 0); te.c(rsNext, rsTick)
rsEnd = te.obj(2200, 340, "t b b b")
te.c(rsChkS, rsEnd, 1)
te.c(rsEnd, te.msg(2200, 370, "\\; tp-rescan-done bang"), 2)
te.c(rsEnd, pendS, 1); te.c(pendS, te.obj(2200, 400, "s nst-proj-status"))
te.c(rsEnd, busy0, 0)

# ================================================= parameters, fed straight into the cold inlets of the job / rescan
# expressions: $f2 track  $f3 region start  $f4 region length  $f5 clipboard length  ($f1 unused: bang re-evaluates)
rTrk = te.obj(20, 60, "r tp-trk")
te.obj(20, 30, "table teseq 2")
trkSrc = te.obj(20, 90, "t f")                  # track used by the ops (tp-trk, or the all-tracks sequence)
te.c(rTrk, trkSrc)
trkKeep = te.obj(120, 90, "f 1")
te.c(rTrk, trkKeep, 0, 1)
slotSrc = te.obj(220, 90, "t f")                # clipboard / undo slot (0 for one track, k-1 in the sequence)
clip4 = te.obj(320, 90, "t f")                  # 1 when the clipboard holds 4 tracks
regE = te.obj(200, 300, f"expr if($f1==2 \\, $f2 \\, int($f4/max(64 \\, $f5))*max(64 \\, $f5)) \\; "
                        f"if($f1==2 \\, $f3-$f2 \\, min(max(64 \\, $f5) \\, {N}-int($f4/max(64 \\, $f5))*max(64 \\, $f5)))")
for i, nm in enumerate(("tp-lo", "tp-hi", "tp-pos")):
    te.c(te.obj(300 + i * 80, 270, f"r {nm}"), regE, 0, i + 1)
barM = te.obj(540, 250, "* 4")
te.c(te.obj(540, 220, "r tempo-beat"), barM); te.c(barM, regE, 0, 4)
lsF = te.obj(200, 270, "f 0")
te.c(te.obj(200, 240, "r tp-ls"), lsF, 0, 1); te.c(lsF, regE)
LF = te.obj(400, 340, "f 0")
te.c(regE, LF, 1, 1)
clipIn = te.obj(600, 300, "t f f")              # set the clipboard length
clipF = te.obj(650, 330, "f 0")
te.c(clipIn, clipF, 1, 1)
srt = te.obj(800, 300, "samplerate~"); te.c(te.obj(800, 270, "loadbang"), srt)
params = []                                     # every parametric expr gets the 4 parameters


def pexpr(x, y, text):
    e = te.obj(x, y, text.replace("expr ", "expr 0*$f5+0*$f6+0*$f7+", 1))
    te.c(trkSrc, e, 0, 1); te.c(regE, e, 0, 2); te.c(regE, e, 1, 3); te.c(clipIn, e, 0, 4)
    te.c(slotSrc, e, 0, 5); te.c(clip4, e, 0, 6)
    return e


def job(x, y, outs):
    """bang -> "src srcStart dst dstStart len" to the job runner"""
    e = pexpr(x, y, "expr 0 \\; " + " \\; ".join(outs))
    pk = te.obj(x, y + 30, "pack f f f f f")
    for o in range(5):
        te.c(e, pk, o + 1, o)
    te.c(pk, te.obj(x, y + 60, "s te-job"))
    return e


def go(x, y, cont, target):
    """bang -> set the continuation, then start the job"""
    t = te.obj(x, y, "t b b")
    cm = te.msg(x + 60, y, f"{cont}")
    te.c(t, cm, 1); te.c(cm, contF, 0, 1); te.c(t, target, 0)
    return t


def rescan(x, y, outs, pend):
    """bang -> remember the status to show at the end, rescan "track start length" """
    t = te.obj(x, y, "t b b")
    te.c(t, te.msg(x + 60, y + 25, f"\\; te-pend symbol {pend}"), 1)
    e = pexpr(x, y + 50, "expr 0 \\; " + " \\; ".join(outs))
    pk = te.obj(x, y + 80, "pack f f f")
    for o in range(3):
        te.c(e, pk, o + 1, o)
    te.c(pk, te.obj(x, y + 110, "s te-rescan"))
    te.c(t, e, 0)
    return t


contF = te.obj(1200, 700, "f 0")
J_TO_CLIP = job(20, 800, ["$f2", "$f3", "5", "$f6*$f4", "$f4"])
J_ZERO = job(220, 800, ["0", "-1", "$f2", "$f3", "$f4"])
J_PASTE = job(420, 800, ["5", "$f7*($f2-1)*$f5", "$f2", "$f3", f"min($f5 \\, {N}-$f3)"])
J_TO_TMP = job(620, 800, ["$f2", "$f3", "6", "0", "$f4"])
J_REV_BACK = job(820, 800, ["7", "0", "$f2", "$f3", "$f4"])
J_DUP = job(1020, 800, ["$f2", "$f3", "$f2", "$f3+$f4", f"min($f4 \\, {N}-$f3-$f4)"])
# ---- undo: the region about to change ("track start length") is copied into te-undo first
BK_REGION = ["$f2", "$f3", "$f4"]
BK_PASTE = ["$f2", "$f3", "min($f5 \\, 2646000-$f3)"]
BK_DUP = ["$f2", "$f3+$f4", "min($f4 \\, 2646000-$f3-$f4)"]


def uv(x, y, nm):
    return te.obj(x, y, f"v te-u-{nm}")


def backup(x, y, cont, outs):
    """bang -> remember the target region, size te-undo, copy region -> te-undo, then continuation cont"""
    t = te.obj(x, y, "t b b")
    e = pexpr(x + 100, y + 400, "expr 0 \\; " + " \\; ".join(outs + [f"$f6*({outs[2]})", f"({outs[2]})*if(teseq[0]>0 \\, 4 \\, 1)", "teseq[0]>0"]))
    te.c(t, e, 1)
    te.c(e, uv(x + 100, y + 430, "trk"), 1); te.c(e, uv(x + 160, y + 430, "st"), 2); te.c(e, uv(x + 220, y + 430, "len"), 3)
    te.c(e, uv(x + 280, y + 430, "off"), 4); te.c(e, uv(x + 340, y + 430, "all"), 6)
    te.c(e, te.msg(x + 100, y + 460, "\\; te-undo resize \\$1"), 5)
    te.c(t, go(x, y + 490, cont, J_TO_UNDO), 0)
    return t


def ujob(x, y, outs):
    """bang -> job over the remembered undo region: $f2 track $f3 start $f4 length"""
    tb = te.obj(x, y, "t b b b b b")
    e = te.obj(x, y + 60, "expr 0*$f1+0*$f2+0*$f3+0*$f4+0*$f5 \\; " + " \\; ".join(outs))
    for o, nm in ((4, "trk"), (3, "st"), (2, "len"), (1, "off")):
        r = uv(x + (5 - o) * 50, y + 30, nm)
        te.c(tb, r, o); te.c(r, e, 0, {"trk": 1, "st": 2, "len": 3, "off": 4}[nm])
    te.c(tb, e, 0)
    pk = te.obj(x, y + 90, "pack f f f f f")
    for o in range(5):
        te.c(e, pk, o + 1, o)
    te.c(pk, te.obj(x, y + 120, "s te-job"))
    return tb


J_TO_UNDO = ujob(2300, 760, ["$f2", "$f3", "8", "$f5", "$f4"])        # tape region -> te-undo
J_UNDO_A = ujob(2300, 900, ["$f2", "$f3", "6", "0", "$f4"])         # swap: tape -> te-tmp
J_UNDO_B = ujob(2500, 900, ["8", "$f5", "$f2", "$f3", "$f4"])         #       te-undo -> tape
J_UNDO_C = ujob(2700, 900, ["6", "0", "8", "$f5", "$f4"])             #       te-tmp -> te-undo
R = {}
for i, (pend, outs) in enumerate((("CUT", ["$f2", "$f3", "$f4"]), ("PASTED", ["$f2", "$f3", f"min($f5 \\, {N}-$f3)"]),
                                  ("REVERSED", ["$f2", "$f3", "$f4"]), ("CLEARED", ["$f2", "$f3", "$f4"]),
                                  ("DUPLICATED", ["$f2", "$f3+$f4", f"min($f4 \\, {N}-$f3-$f4)"]))):
    R[pend] = rescan(20 + i * 220, 1000, outs, pend)

# ================================================= requests
rq = te.obj(20, 120, "r te-op")
rqT = te.obj(20, 150, "t f b")
te.c(rq, rqT)
bsy = te.obj(20, 180, "== 0")
gate = te.obj(20, 210, "spigot")
te.c(rqT, busyF, 1); te.c(busyF, bsy); te.c(bsy, gate, 0, 1); te.c(rqT, gate, 0)
opT = te.obj(20, 240, "t f b b b")
te.c(gate, opT)
rgE = te.obj(120, 255, "expr teseq[0]==0 || teseq[1]==1")
rgS = te.obj(120, 270, "sel 1")
rgT = te.obj(120, 285, "t b b")
te.c(opT, rgE, 3); te.c(rgE, rgS); te.c(rgS, rgT)
te.c(rgT, te.msg(220, 285, "\\; tp-ask bang"), 1)                # refresh tp-pos
te.c(rgT, lsF, 0)                                                  # region -> every expression
busy1 = te.msg(100, 270, "1")
te.c(opT, busy1, 1); te.c(busy1, busyF, 0, 1)
opS = te.obj(20, 600, "sel 1 2 3 4 5 6 7")
te.c(opT, opS, 0)
# 1 CUT / 2 COPY: clipboard = region (size and length), then copy
for k, (label, cont) in enumerate((("CUTTING", 11), ("COPYING", 21))):
    x = 20 + k * 250
    t = te.obj(x, 640, "t b b b")
    te.c(opS, t, k)
    te.c(t, status(x + 100, 640, label), 2)
    lb = te.obj(x + 100, 700, "f")
    te.c(regE, lb, 1, 1)
    lbT = te.obj(x + 100, 715, "t f f f")
    te.c(t, lb, 1); te.c(lb, lbT)
    cszE = te.obj(x + 160, 730, "expr $f1*if(teseq[0]>0 \\, 4 \\, 1)")      # 4 slots when copying all tracks
    te.c(lbT, cszE, 2); te.c(cszE, te.msg(x + 160, 760, "\\; te-clip resize \\$1"))
    c4E = te.obj(x + 100, 745, "expr teseq[0]>0")                      # the clipboard will hold 4 tracks
    te.c(lbT, c4E, 1); te.c(c4E, clip4)
    te.c(lbT, clipIn, 0)
    te.c(t, backup(x, 670, 10, BK_REGION) if cont == 11 else go(x, 670, cont, J_TO_CLIP), 0)
# 3 PASTE (needs something in the clipboard)
psT = te.obj(520, 640, "t b")
te.c(opS, psT, 2)
te.c(psT, clipF)
psE = te.obj(520, 670, "> 0")
psS = te.obj(520, 700, "sel 1 0")
te.c(clipF, psE); te.c(psE, psS)
psGo = te.obj(520, 730, "t b b")
te.c(psS, psGo, 0); te.c(psGo, status(620, 730, "PASTING"), 1); te.c(psGo, backup(520, 760, 30, BK_PASTE), 0)
psNo = te.obj(700, 730, "t b b")
te.c(psS, psNo, 1); te.c(psNo, status(760, 760, "CLIP-EMPTY"), 1); te.c(psNo, busy0, 0)
# 4 REVERSE: region -> te-tmp ; play te-tmp backwards into te-rev (real time) ; te-rev -> region
rvT = te.obj(800, 640, "t b b b")
te.c(opS, rvT, 3)
te.c(rvT, status(900, 640, "REVERSING"), 2)
rvL = te.obj(900, 670, "f")
te.c(regE, rvL, 1, 1)
te.c(rvT, rvL, 1); te.c(rvL, te.msg(900, 700, "\\; te-tmp resize \\$1 \\; te-rev resize \\$1"))
te.c(rvT, backup(800, 700, 40, BK_REGION), 0)
# the backwards pass
# block-exact: [rpole~] counter reset with "set 0" and [tabwrite~] both start on the next DSP block,
# so the first written sample reads index L-1, the last index 0 (vline~ starts mid-block and drifts)
rvCnt = te.obj(1500, 840, "rpole~ 1")
te.c(te.obj(1500, 810, "sig~ 1"), rvCnt)
rvLen = te.obj(1600, 840, "sig~")
rvIdx = te.obj(1600, 870, "-~")
te.c(rvLen, rvIdx); te.c(rvCnt, rvIdx, 0, 1)
rvRd = te.obj(1600, 900, "tabread~ te-tmp")
rvWr = te.obj(1600, 930, "tabwrite~ te-rev")
te.c(rvIdx, rvRd); te.c(rvRd, rvWr)
rvPass = te.obj(1600, 760, "t b b")
rvL2 = te.obj(1700, 760, "f")
te.c(regE, rvL2, 1, 1)
rvE = te.obj(1700, 790, "expr $f1-1 \\; $f1/$f2*1000")
te.c(srt, rvE, 0, 1)
te.c(rvPass, rvL2, 0); te.c(rvL2, rvE)
te.c(rvPass, srt, 1)                                                 # fresh sample rate before computing the duration
rvP = te.obj(1700, 820, "pack f f")
te.c(rvE, rvP, 1, 1); te.c(rvE, rvP, 0, 0)
rvGo = te.obj(1700, 850, "t l l b")
te.c(rvP, rvGo)
te.c(rvGo, rvWr, 2)                                                    # start writing
rvMsg = te.msg(1500, 780, "set 0")
te.c(rvGo, rvMsg, 1); te.c(rvMsg, rvCnt)
rvLu = te.obj(1650, 790, "unpack f f")
rvLp1 = te.obj(1650, 810, "+ 1")                                       # L = (L-1) + 1
te.c(rvGo, rvLu, 1); te.c(rvLu, rvLp1); te.c(rvLp1, rvLen)
rvU = te.obj(1800, 880, "unpack f f")
te.c(rvGo, rvU, 0)
rvD = te.obj(1800, 910, "+ 30")
rvDel = te.obj(1800, 940, "delay")
te.c(rvU, rvD, 1); te.c(rvD, rvDel)
te.c(rvDel, go(1800, 970, 42, J_REV_BACK))
# 5 CLEAR
clT = te.obj(1100, 640, "t b b")
te.c(opS, clT, 4)
te.c(clT, status(1200, 640, "CLEARING"), 1)
te.c(clT, backup(1100, 670, 50, BK_REGION), 0)
# 6 DUPLICATE (needs room after the region)
dpE = pexpr(1350, 640, f"expr {N}-$f3-$f4>64")
dpB = te.obj(1350, 610, "t b")
te.c(opS, dpB, 5); te.c(dpB, dpE)
dpS = te.obj(1350, 700, "sel 1 0")
te.c(dpE, dpS)
dpGo = te.obj(1350, 730, "t b b")
te.c(dpS, dpGo, 0); te.c(dpGo, status(1450, 730, "DUPLICATING"), 1); te.c(dpGo, backup(1350, 760, 60, BK_DUP), 0)
dpNo = te.obj(1500, 730, "t b b")
te.c(dpS, dpNo, 1); te.c(dpNo, status(1560, 760, "TAPE-END"), 1); te.c(dpNo, busy0, 0)

# 7 UNDO (swap te-undo <-> tape region; pressed again = redo)
unB = te.obj(1700, 610, "t b")
te.c(opS, unB, 6)
unV = uv(1700, 625, "len")
unE = te.obj(1700, 640, "> 0")
te.c(unB, unV); te.c(unV, unE)
unS = te.obj(1700, 670, "sel 1 0")
te.c(unE, unS)
unGo = te.obj(1700, 700, "t b b b")
te.c(unS, unGo, 0)
te.c(unGo, status(1800, 700, "UNDOING"), 2)
unV2 = uv(1800, 715, "len")
te.c(unGo, unV2, 1); te.c(unV2, te.msg(1800, 730, "\\; te-tmp resize \\$1"))
te.c(unGo, go(1700, 760, 71, J_UNDO_A), 0)
unNo = te.obj(1900, 670, "t b b")
te.c(unS, unNo, 1); te.c(unNo, status(1950, 700, "NO-UNDO"), 1); te.c(unNo, busy0, 0)
# recording or loading a project makes the backup meaningless: forget it
unF0 = te.msg(2000, 600, "0")
te.c(unF0, uv(2000, 630, "len"))
unRec = te.obj(2000, 540, "sel 1")
te.c(te.obj(2000, 510, "r tp-rec"), unRec); te.c(unRec, unF0)
te.c(te.obj(2100, 540, "r nst-load"), unF0)

# ================================================= continuations (when a job has finished)
cd = te.obj(1200, 1200, "sel 11 12 21 31 41 42 51 61")
cdB = te.obj(2300, 1200, "sel 10 30 40 50 60 71 72 73")
te.c(cd, cdB, 8)
te.c(cdB, go(2300, 1230, 11, J_TO_CLIP), 0)       # backups done -> the original first step of each op
te.c(cdB, go(2400, 1230, 31, J_PASTE), 1)
te.c(cdB, go(2500, 1230, 41, J_TO_TMP), 2)
te.c(cdB, go(2600, 1230, 51, J_ZERO), 3)
te.c(cdB, go(2700, 1230, 61, J_DUP), 4)
te.c(cdB, go(2300, 1290, 72, J_UNDO_B), 5)        # undo swap steps
te.c(cdB, go(2400, 1290, 73, J_UNDO_C), 6)
unDone = te.obj(2500, 1290, "t b b b b")
te.c(cdB, unDone, 7)
te.c(unDone, te.msg(2600, 1320, "\\; te-pend symbol UNDONE"), 3)
unRs = te.obj(2500, 1380, "pack f f f")
for o, nm, inl in ((2, "len", 2), (1, "st", 1), (0, "trk", 0)):
    r = uv(2500 + (2 - o) * 50, 1350, nm)
    te.c(unDone, r, o); te.c(r, unRs, 0, inl)
te.c(unRs, te.obj(2500, 1410, "s te-rescan"))
te.c(te.obj(1200, 1150, "r te-done"), contF); te.c(contF, cd)
te.c(cd, go(1200, 1230, 12, J_ZERO), 0)                              # cut: now clear the region
te.c(cd, R["CUT"], 1)
cpDone = te.obj(1300, 1260, "t b b")
te.c(cd, cpDone, 2); te.c(cpDone, status(1300, 1290, "COPIED"), 1); te.c(cpDone, busy0, 0)
te.c(cd, R["PASTED"], 3)
te.c(cd, rvPass, 4)                                                  # reverse: backwards pass
te.c(cd, R["REVERSED"], 5)
te.c(cd, R["CLEARED"], 6)
# duplicate: move the loop onto the copy (when looping), then rescan
dpDone = te.obj(1600, 1230, "t b b")
te.c(cd, dpDone, 7)
lsD = te.obj(1700, 1260, "f 0")
te.c(te.obj(1700, 1230, "r tp-ls"), lsD, 0, 1)
lsDs = te.obj(1700, 1290, "sel 2")
mvG = te.obj(1800, 1290, "expr teseq[0]==0 || teseq[1]==4")
mvGs = te.obj(1800, 1305, "sel 1")
te.c(dpDone, mvG, 1); te.c(mvG, mvGs); te.c(mvGs, lsD); te.c(lsD, lsDs)
mvE = pexpr(1700, 1320, "expr $f3+$f4 \\; $f3+2*$f4")
te.c(lsDs, mvE)
mvP = te.obj(1700, 1350, "pack f f")
te.c(mvE, mvP, 1, 1); te.c(mvE, mvP, 0, 0)
te.c(mvP, te.msg(1700, 1380, "\\; tp-loop-set 2 \\$1 \\$2"))
te.c(dpDone, R["DUPLICATED"], 0)

# ================================================= menu opened from TAPE: say what the edit will act on
ctxS = te.obj(20, 1300, "sel 1")
te.c(te.obj(20, 1270, "r pm-ctx"), ctxS)
lsM = te.obj(20, 1330, "f 0")
te.c(te.obj(100, 1300, "r tp-ls"), lsM, 0, 1)
te.c(ctxS, lsM)
lsMs = te.obj(20, 1360, "sel 2")
te.c(lsM, lsMs)
te.c(lsMs, status(20, 1390, "ON-LOOP"), 0)
te.c(lsMs, status(150, 1390, "ON-BAR"), 1)

# ================================================= all-tracks driver
# [r tape-edit] op -> 8 toggles the mode; 1..6 with TUTTE (and 7 after an all-tracks op) run for tracks 1..4
allF = te.obj(2600, 60, "f 0")
dIn = te.obj(2600, 30, "r tape-edit")
dT = te.obj(2600, 90, "t f f")
te.c(dIn, dT)
opKeep = te.obj(2800, 120, "f 0")
te.c(dT, opKeep, 1, 1)
# 8: toggle
s8 = te.obj(2600, 120, "sel 8")
te.c(dT, s8, 0)
tg = te.obj(2600, 150, "== 0")
te.c(s8, allF); te.c(allF, tg); te.c(tg, allF, 0, 1)
tgT = te.obj(2600, 180, "t f f")
te.c(tg, tgT)
te.c(tgT, te.obj(2700, 210, "s te-all"), 1)
tgS = te.obj(2600, 210, "sel 1 0")
te.c(tgT, tgS, 0)
te.c(tgS, status(2600, 240, "ALL-TRACKS"), 0)
te.c(tgS, status(2750, 240, "1-TRACK"), 1)
# other ops: sequence or straight through.  seqE: $f1 op, $f2 TUTTE on, $f3 last undo was all-tracks
seqE = te.obj(2600, 280, "expr if($f1>=1 && $f1<=6 \\, $f2 \\, if($f1==7 \\, $f3 \\, 0))")
te.c(tgT, seqE, 1, 1)                              # TUTTE on/off -> cold
other = te.obj(2600, 250, "t f f b")
te.c(s8, other, 1)
uAll = uv(2700, 265, "all")
te.c(other, uAll, 2); te.c(uAll, seqE, 0, 2)       # 1) undo flag (cold)
fwd = te.obj(2600, 340, "f")
te.c(other, fwd, 1, 1)                             # 2) remember the op for the straight path
te.c(other, seqE, 0)                               # 3) decide
seqS = te.obj(2600, 310, "sel 0 1")
te.c(seqE, seqS)
fwdB = te.obj(2600, 370, "t b")
te.c(seqS, fwdB, 0); te.c(fwdB, fwd); te.c(fwd, te.obj(2600, 400, "s te-op"))
# start a sequence at track 1
stT = te.obj(2800, 340, "t b b")
te.c(seqS, stT, 1)
te.c(stT, te.msg(2900, 370, "\\; teseq 0 1 1"), 1)
iter_ = te.obj(2800, 400, "t b b")                 # set the parameters of track k, then run the op
te.c(stT, iter_, 0)
kE = te.obj(2900, 430, "expr teseq[1] \\; teseq[1]-1")
te.c(iter_, kE, 1)
kP = te.obj(2900, 460, "pack f f")
te.c(kE, kP, 1, 1); te.c(kE, kP, 0, 0)
kU = te.obj(2900, 490, "unpack f f")
te.c(kP, kU)
te.c(kU, slotSrc, 1); te.c(kU, trkSrc, 0)          # slot k-1, then track k
# undo sequence: te-u-trk = k, te-u-off = (k-1) * te-u-len
uLenV = uv(3100, 460, "len")
ukT = te.obj(3100, 430, "t b")
te.c(iter_, ukT, 1); te.c(ukT, uLenV)
ukE = te.obj(3100, 490, "expr teseq[1] \\; (teseq[1]-1)*$f1")
te.c(uLenV, ukE)
ukP = te.obj(3100, 520, "pack f f")
te.c(ukE, ukP, 1, 1); te.c(ukE, ukP, 0, 0)
ukU = te.obj(3100, 550, "unpack f f")
te.c(ukP, ukU)
te.c(ukU, uv(3150, 580, "off"), 1); te.c(ukU, uv(3100, 580, "trk"), 0)
te.c(iter_, opKeep, 0); te.c(opKeep, te.obj(2800, 520, "s te-op"))
# when an op has finished (busy back to 0): next track, or the end
nxB = te.obj(2800, 600, "t b")
te.c(busy0, nxB)
nxD = te.obj(2800, 630, "delay 1")
te.c(nxB, nxD)
nxE = te.obj(2800, 660, "expr if(teseq[0]>0 \\, if(teseq[1]<4 \\, 1 \\, 2) \\, 0)")
te.c(nxD, nxE)
nxS = te.obj(2800, 690, "sel 1 2")
te.c(nxE, nxS)
nxInc = te.obj(2800, 720, "expr teseq[1]+1")
te.c(nxS, nxInc, 0)
nxT = te.obj(2800, 750, "t b f")
te.c(nxInc, nxT)
te.c(nxT, te.msg(2900, 780, "\\; teseq 1 \\$1"), 1)
te.c(nxT, iter_, 0)
endT = te.obj(3000, 720, "t b b")
te.c(nxS, endT, 1)
te.c(endT, te.msg(3100, 750, "\\; teseq 0 0 0"), 1)
z0 = te.msg(3000, 750, "0")
te.c(endT, trkKeep, 0); te.c(trkKeep, trkSrc); te.c(endT, z0); te.c(z0, slotSrc)
te.save("tapeedit.pd")

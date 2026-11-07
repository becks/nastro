#!/usr/bin/env python3
"""Tape edit on ALL tracks: menu op 8 toggles '1 TRACCIA' / 'TUTTE'. With TUTTE every op (1..6) runs 4 times,
track 1 -> 4, reusing the single-track code: the track parameter is driven by the sequence, the clipboard and the
undo buffer hold 4 slots (slot k-1 at offset (k-1)*length). The region is computed once (first track), the loop
moves after a DUPLICA only at the last track. ANNULLA after an all-tracks op undoes all 4.
State table 'teseq': 0 sequence running, 1 current track k (no '-' in the name: expr reads it)."""
import shutil

for f in ("gentapeedit.py", "genproj.py"):
    shutil.copy(f, f + ".pre-editall")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


N = 2646000
edit("gentapeedit.py", [
    # ---- track / slot / clip-has-4 parameters for every parametric expr ($f2 track, $f6 slot, $f7 clip has 4)
    ('rTrk = te.obj(20, 60, "r tp-trk")', '''rTrk = te.obj(20, 60, "r tp-trk")
te.obj(20, 30, "table teseq 2")
trkSrc = te.obj(20, 90, "t f")                  # track used by the ops (tp-trk, or the all-tracks sequence)
te.c(rTrk, trkSrc)
trkKeep = te.obj(120, 90, "f 1")
te.c(rTrk, trkKeep, 0, 1)
slotSrc = te.obj(220, 90, "t f")                # clipboard / undo slot (0 for one track, k-1 in the sequence)
clip4 = te.obj(320, 90, "t f")                  # 1 when the clipboard holds 4 tracks'''),
    ('''    e = te.obj(x, y, text.replace("expr ", "expr 0*$f5+", 1))
    te.c(rTrk, e, 0, 1); te.c(regE, e, 0, 2); te.c(regE, e, 1, 3); te.c(clipIn, e, 0, 4)''',
     '''    e = te.obj(x, y, text.replace("expr ", "expr 0*$f5+0*$f6+0*$f7+", 1))
    te.c(trkSrc, e, 0, 1); te.c(regE, e, 0, 2); te.c(regE, e, 1, 3); te.c(clipIn, e, 0, 4)
    te.c(slotSrc, e, 0, 5); te.c(clip4, e, 0, 6)'''),
    # ---- clipboard slots
    ('J_TO_CLIP = job(20, 800, ["$f2", "$f3", "5", "0", "$f4"])', 'J_TO_CLIP = job(20, 800, ["$f2", "$f3", "5", "$f6*$f4", "$f4"])'),
    (f'J_PASTE = job(420, 800, ["5", "0", "$f2", "$f3", f"min($f5 \\\\, {{N}}-$f3)"])',
     f'J_PASTE = job(420, 800, ["5", "$f7*($f2-1)*$f5", "$f2", "$f3", f"min($f5 \\\\, {{N}}-$f3)"])'),
    ('''    te.c(t, lb, 1); te.c(lb, te.msg(x + 100, 730, "\\\\; te-clip resize \\\\$1")); te.c(lb, clipIn)''',
     '''    lbT = te.obj(x + 100, 715, "t f f f")
    te.c(t, lb, 1); te.c(lb, lbT)
    cszE = te.obj(x + 160, 730, "expr $f1*if(teseq[0]>0 \\\\, 4 \\\\, 1)")      # 4 slots when copying all tracks
    te.c(lbT, cszE, 2); te.c(cszE, te.msg(x + 160, 760, "\\\\; te-clip resize \\\\$1"))
    c4E = te.obj(x + 100, 745, "expr teseq[0]>0")                      # the clipboard will hold 4 tracks
    te.c(lbT, c4E, 1); te.c(c4E, clip4)
    te.c(lbT, clipIn, 0)'''),
    # ---- undo slots
    ('''    e = pexpr(x + 100, y + 400, "expr 0 \\\\; " + " \\\\; ".join(outs))
    te.c(t, e, 1)
    te.c(e, uv(x + 100, y + 430, "trk"), 1); te.c(e, uv(x + 160, y + 430, "st"), 2); te.c(e, uv(x + 220, y + 430, "len"), 3)
    te.c(e, te.msg(x + 100, y + 460, "\\\\; te-undo resize \\\\$1"), 3)''',
     '''    e = pexpr(x + 100, y + 400, "expr 0 \\\\; " + " \\\\; ".join(outs + [f"$f6*({outs[2]})", f"({outs[2]})*if(teseq[0]>0 \\\\, 4 \\\\, 1)", "teseq[0]>0"]))
    te.c(t, e, 1)
    te.c(e, uv(x + 100, y + 430, "trk"), 1); te.c(e, uv(x + 160, y + 430, "st"), 2); te.c(e, uv(x + 220, y + 430, "len"), 3)
    te.c(e, uv(x + 280, y + 430, "off"), 4); te.c(e, uv(x + 340, y + 430, "all"), 6)
    te.c(e, te.msg(x + 100, y + 460, "\\\\; te-undo resize \\\\$1"), 5)'''),
    ('''    tb = te.obj(x, y, "t b b b b")
    e = te.obj(x, y + 60, "expr 0*$f1+0*$f2+0*$f3+0*$f4 \\\\; " + " \\\\; ".join(outs))
    for o, nm in ((3, "trk"), (2, "st"), (1, "len")):
        r = uv(x + (4 - o) * 50, y + 30, nm)
        te.c(tb, r, o); te.c(r, e, 0, {"trk": 1, "st": 2, "len": 3}[nm])''',
     '''    tb = te.obj(x, y, "t b b b b b")
    e = te.obj(x, y + 60, "expr 0*$f1+0*$f2+0*$f3+0*$f4+0*$f5 \\\\; " + " \\\\; ".join(outs))
    for o, nm in ((4, "trk"), (3, "st"), (2, "len"), (1, "off")):
        r = uv(x + (5 - o) * 50, y + 30, nm)
        te.c(tb, r, o); te.c(r, e, 0, {"trk": 1, "st": 2, "len": 3, "off": 4}[nm])'''),
    ('J_TO_UNDO = ujob(2300, 760, ["$f2", "$f3", "8", "0", "$f4"])', 'J_TO_UNDO = ujob(2300, 760, ["$f2", "$f3", "8", "$f5", "$f4"])'),
    ('J_UNDO_B = ujob(2500, 900, ["8", "0", "$f2", "$f3", "$f4"])', 'J_UNDO_B = ujob(2500, 900, ["8", "$f5", "$f2", "$f3", "$f4"])'),
    ('J_UNDO_C = ujob(2700, 900, ["6", "0", "8", "0", "$f4"])', 'J_UNDO_C = ujob(2700, 900, ["6", "0", "8", "$f5", "$f4"])'),
    # ---- requests now come from the all-tracks driver
    ('rq = te.obj(20, 120, "r tape-edit")', 'rq = te.obj(20, 120, "r te-op")'),
    ('opS = te.obj(20, 600, "sel 1 2 3 4 5 6 7")', 'opS = te.obj(20, 600, "sel 1 2 3 4 5 6 7")'),
    # region and playhead read only for the first track of a sequence
    ('''te.c(opT, te.msg(120, 240, "\\\\; tp-ask bang"), 3)                 # refresh tp-pos
te.c(opT, lsF, 2)                                                  # region -> every expression''',
     '''rgE = te.obj(120, 255, "expr teseq[0]==0 || teseq[1]==1")
rgS = te.obj(120, 270, "sel 1")
rgT = te.obj(120, 285, "t b b")
te.c(opT, rgE, 3); te.c(rgE, rgS); te.c(rgS, rgT)
te.c(rgT, te.msg(220, 285, "\\\\; tp-ask bang"), 1)                # refresh tp-pos
te.c(rgT, lsF, 0)                                                  # region -> every expression'''),
    # duplicate moves the loop only after the last track
    ('te.c(dpDone, lsD, 1); te.c(lsD, lsDs)', '''mvG = te.obj(1800, 1290, "expr teseq[0]==0 || teseq[1]==4")
mvGs = te.obj(1800, 1305, "sel 1")
te.c(dpDone, mvG, 1); te.c(mvG, mvGs); te.c(mvGs, lsD); te.c(lsD, lsDs)'''),
    ('te.save("tapeedit.pd")', r'''
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
te.c(tgS, status(2600, 240, "TUTTE"), 0)
te.c(tgS, status(2750, 240, "1-TRACCIA"), 1)
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
te.save("tapeedit.pd")'''),
])
print("editall (tapeedit) applied")

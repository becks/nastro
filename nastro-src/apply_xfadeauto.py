#!/usr/bin/env python3
"""Sample-accurate loop wrap for tracks recorded in loop mode.

The wrap is decided once per DSP block, so in the block that crosses the loop end the play head read up to 63
samples PAST the end. For a track recorded in loop mode that region is silence (or old audio): a gap at every
restart. Now, just before the head reaches a loop edge, each track is checked: if the loop start continues the audio
at the loop end at least as well as what lies past the end, that track's read index wraps per sample (no gap, no
crossfade). Otherwise (audio recorded straight through, then looped) it reads past the end and crossfades as before.

tabread4~ reads one sample before and two after the read point, across the edge. For wrapped tracks the 3 samples
just outside the loop are temporarily replaced with the loop's continuation (originals saved, restored right after
the wrap). Not while recording (the writer and the seam fix own those samples then).

While recording a wrapped track, what the writer put past the end is already the right value for the loop start
(the head read the loop start), so the seam fix copies it, corrected only where tabread4~ read x[1] for x[0]
(it cannot read index 0)."""
p = "gentape.py"; s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep("t.c(rd, xA, 0, 0); t.c(gA, xA, 0, 1); t.c(rdB, xB, 0, 0); t.c(gB, xB, 0, 1)",
    "t.c(rd, xA, 0, 0); t.c(rdB, xB, 0, 0); xAs.append(xA); xBs.append(xB); rds.append(rd)")
rep("t.c(idx, rd); t.c(rl, rlm)", "t.c(rl, rlm)")
rep("tws, dubs = [], []\n", "tws, dubs = [], []\nxAs, xBs, rds = [], [], []\n")
# seam fix: wrapped track -> copy the overshoot as written ($f6 = n, $f7 = track index 0..3)
rep('valE = t.obj(2400, 1760, "expr $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+pgbuf[64-$f6+$f1]*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1])")',
    'valE = t.obj(2400, 1760, "expr if(xwm[$f7] \\\\, $s2[$f4+$f1]+($s2[$f3+$f1]-$s2[max($f3+$f1 \\\\, 1)])*(1-pgbuf[64-$f6+$f1]*(1-$f5)) \\\\, $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+pgbuf[64-$f6+$f1]*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1]))")\n'
    'smK = t.obj(2500, 1730, "- 1")\n'
    't.c(smTrk, smK); t.c(smK, valE, 0, 6)')

TAIL = r'''# --- sample-accurate wrap / per-track crossfade (apply_xfadeauto.py)
# dW = offset that wraps the absolute read position (idx + onset) into [lo, hi)
dW = t.obj(2600, 1900, "expr~ ($v1+$f2>=$f3)*(-$f4)+($v1+$f2<$f5)*$f4")
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
GUARD = (("$f2", "$f3", "$f3-1", "$f2-1", "1", "$f3>0"),
         ("$f2+1", "$f3+1", "$f3-2", "$f2-2", f"$f2+1<{N}", "$f3>1"),
         ("$f3-1", "$f2-1", "$f2", "$f3", "$f3>0", "1"))
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
t.save("tape.pd")'''
rep('t.save("tape.pd")', TAIL)
open(p, "w").write(s)
print("ok")

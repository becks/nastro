#!/usr/bin/env python3
"""Master output limiter, no added latency: per-block peak (tabsend~ + array max) -> gain with instant attack
and ~150 ms release, applied from the next block; a final clip~ catches the first block of a sudden peak.
The metronome (tempo.pd) and the tape recording feed are outside the limiter."""
import shutil

shutil.copy("genmix.py", "genmix.py.pre-lim")
s = open("genmix.py").read()
A = '''ol = ms.obj(20, 820, "throw~ outL")
orr = ms.obj(200, 820, "throw~ outR")'''
B = r'''# --- output limiter
ol = ms.obj(20, 820, "*~ 1")                 # sums everything going to the left output
orr = ms.obj(200, 820, "*~ 1")
LIM_T = 0.89                                # about -1 dBFS
REL = 0.0097                                # per 64-sample block: ~150 ms release
lgL = ms.obj(20, 850, "*~"); lgR = ms.obj(200, 850, "*~")
lcL = ms.obj(20, 880, "clip~ -1 1"); lcR = ms.obj(200, 880, "clip~ -1 1")
ms.c(ol, lgL); ms.c(orr, lgR); ms.c(lgL, lcL); ms.c(lgR, lcR)
ms.c(lcL, ms.obj(20, 910, "throw~ outL")); ms.c(lcR, ms.obj(200, 910, "throw~ outR"))
# detector: max(|L|, |R|) -> 64-sample table every block -> peak
laL = ms.obj(1000, 820, "abs~"); laR = ms.obj(1100, 820, "abs~"); lmx = ms.obj(1000, 850, "max~")
ms.c(ol, laL); ms.c(orr, laR); ms.c(laL, lmx, 0, 0); ms.c(laR, lmx, 0, 1)
ms.obj(1000, 790, "table nst-lim 64")
ms.c(lmx, ms.obj(1000, 880, "tabsend~ nst-lim"))
lbg = ms.obj(1150, 790, "bang~")
lam = ms.obj(1150, 820, "array max nst-lim")
ms.c(lbg, lam)
# gain: g = min(target, g + (1-g)*REL)   target = min(1, T/peak)
lgE = ms.obj(1150, 850, "expr min(1 \\, %s/max($f1 \\, 0.001))" % LIM_T)
lgN = ms.obj(1150, 880, "expr min($f1 \\, $f2+(1-$f2)*%s)" % REL)
lgT = ms.obj(1150, 910, "t f f")
ms.c(lam, lgE); ms.c(lgE, lgN)
ms.c(lgN, lgT); ms.c(lgT, lgN, 1, 1)          # previous gain -> cold inlet
# to the gain line~ only when it changes (3 decimals)
lgQ = ms.obj(1150, 940, "expr int($f1*1000+0.5)/1000.0")
lgC = ms.obj(1150, 970, "change 1")
lgM = ms.msg(1150, 1000, "\\$1 1")
lgLn = ms.obj(1150, 1030, "line~")
ms.c(lgT, lgQ, 0); ms.c(lgQ, lgC); ms.c(lgC, lgM); ms.c(lgM, lgLn)
lgI = ms.msg(1300, 1000, "1")
ms.c(ms.obj(1300, 970, "loadbang"), lgI); ms.c(lgI, lgLn); ms.c(lgI, lgN, 0, 1)
ms.c(lgLn, lgL, 0, 1); ms.c(lgLn, lgR, 0, 1)
ms.c(lgC, ms.obj(1250, 1060, "s nst-lim-gain"))'''
assert s.count(A) == 1
s = s.replace(A, B)
open("genmix.py", "w").write(s)
print("limiter applied")

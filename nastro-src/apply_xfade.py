#!/usr/bin/env python3
"""Loop wrap crossfade: when the playhead wraps (loop end -> start, or any jump through wrapE), a second read head
per track keeps playing the pre-jump continuation and fades out over XF ms while the main head fades in.
Only the monitored output is crossfaded; the overdub path keeps reading the main head."""
import shutil

shutil.copy("gentape.py", "gentape.py.pre-xfade")
s = open("gentape.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


XF = 5
# 1) keep the pre-wrap position: pT -> [t f f] -> (preF, wflag)
rep('''t.c(pT, wrapE, 1); t.c(wrapE, T); t.c(pT, wflag, 0); t.c(wflag, wsel)''',
    f'''t.c(pT, wrapE, 1); t.c(wrapE, T)
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
fA = t.msg(1650, 490, "0 \\\\, 1 {XF}"); fB = t.msg(1750, 490, "1 \\\\, 0 {XF}")
t.c(xW, fA, 0); t.c(xW, fB, 0); t.c(fA, gA); t.c(fB, gB)
gA1 = t.msg(1650, 460, "1")
t.c(t.obj(1650, 430, "loadbang"), gA1); t.c(gA1, gA)''')

# 2) per track: second head + crossfade into the level stage
rep('''    t.c(idx, rd); t.c(rd, lv); t.c(rl, rlm)''',
    '''    rdB = t.obj(x, 740, f"tabread4~ tape{k+1}")
    xA = t.obj(x, 790, "*~"); xB = t.obj(x + 40, 790, "*~"); xS = t.obj(x, 820, "+~")
    t.c(idx, rdB); t.c(bAdd, rdB, 0, 1)
    t.c(rd, xA, 0, 0); t.c(gA, xA, 0, 1); t.c(rdB, xB, 0, 0); t.c(gB, xB, 0, 1)
    t.c(xA, xS, 0, 0); t.c(xB, xS, 0, 1); t.c(xS, lv)
    t.c(idx, rd); t.c(rl, rlm)''')
open("gentape.py", "w").write(s)
print("xfade applied")

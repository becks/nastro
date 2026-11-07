#!/usr/bin/env python3
"""Track DJ filter without clicks when the knobs move. biquad~ (direct form II) clicks for a sample whenever its
coefficients change while audio runs, and Pd 0.49 has no modulation-safe biquad. Now each track has two biquad~s:
new coefficients go to the silent one, then a 5 ms crossfade moves to it, so the switch transient happens while
its gain is still 0. While a knob turns, updates follow one per crossfade (at most every 6 ms); the latest value
is always applied."""
p = "gentape.py"; s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('''    bq = t.obj(x, 875, "biquad~ 0 0 1 0 0")
    t.c(lv, bq)''', '''    # two filters, crossfaded (apply_filterxfade.py); bq = their sum, feeds pan and VU as before
    bq = t.obj(x, 875, "+~")
    bqA = t.obj(x + 1000, 860, "biquad~ 0 0 1 0 0"); bqB = t.obj(x + 1100, 860, "biquad~ 0 0 1 0 0")
    lnA = t.obj(x + 1000, 830, "line~"); lnB = t.obj(x + 1100, 830, "line~")
    mA = t.obj(x + 1000, 890, "*~"); mB = t.obj(x + 1100, 890, "*~")
    t.c(lv, bqA); t.c(lv, bqB)
    t.c(bqA, mA, 0, 0); t.c(lnA, mA, 0, 1); t.c(bqB, mB, 0, 0); t.c(lnB, mB, 0, 1)
    t.c(mA, bq, 0, 0); t.c(mB, bq, 0, 1)
    lbA = t.obj(x + 1200, 800, "loadbang"); oneA = t.msg(x + 1200, 815, "1")
    t.c(lbA, oneA); t.c(oneA, lnA)                                # A plays first''')
rep("    t.c(cP, bq)\n", '''    # coefficient scheduler: store the latest list, fire when not crossfading
    cpT = t.obj(x + 1000, 1120, "t b b l")
    pend = t.obj(x + 1200, 1150, "list")
    m1d = t.msg(x + 1100, 1150, "1"); dirtyF = t.obj(x + 1000, 1180, "f 0")
    busySp = t.obj(x + 1000, 1150, "spigot 1")
    t.c(cP, cpT); t.c(cpT, pend, 2, 1); t.c(cpT, m1d, 1); t.c(m1d, dirtyF, 0, 1); t.c(cpT, busySp, 0)
    t.c(busySp, dirtyF)
    dS = t.obj(x + 1000, 1210, "sel 1")
    fire = t.obj(x + 1000, 1240, "t b b b")                      # 2) clear dirty  1) busy 6 ms  0) apply
    t.c(dirtyF, dS); t.c(dS, fire)
    m0d = t.msg(x + 1150, 1270, "0"); t.c(fire, m0d, 2); t.c(m0d, dirtyF, 0, 1)
    m0b = t.msg(x + 1100, 1270, "0"); dl = t.obj(x + 1100, 1300, "delay 6")
    t.c(fire, m0b, 1); t.c(m0b, busySp, 0, 1); t.c(fire, dl, 1)
    dlT = t.obj(x + 1100, 1330, "t b b"); m1b = t.msg(x + 1150, 1360, "1")
    t.c(dl, dlT); t.c(dlT, m1b, 1); t.c(m1b, busySp, 0, 1); t.c(dlT, busySp, 0)   # free again, apply what came meanwhile
    sideF = t.obj(x + 1000, 1270, "f 0")                         # active filter: 0 = A, 1 = B
    idE = t.obj(x + 1000, 1300, "expr 1-$f1")
    idT = t.obj(x + 1000, 1330, "t f f f")                      # 2) new active  1) list prefix  0) send + fade
    t.c(fire, sideF, 0); t.c(sideF, idE); t.c(idE, idT); t.c(idT, sideF, 2, 1)
    lpp = t.obj(x + 1200, 1360, "list prepend 0"); rtq = t.obj(x + 1200, 1390, "route 0 1")
    t.c(idT, lpp, 1, 1); t.c(pend, lpp); t.c(lpp, rtq); t.c(rtq, bqA, 0); t.c(rtq, bqB, 1)
    fT = t.obj(x + 1000, 1360, "t f b")                          # coefficients first, then the crossfade
    t.c(idT, fT, 0); t.c(fT, pend, 1)
    fS = t.obj(x + 1000, 1390, "sel 0 1")
    t.c(fT, fS, 0)
    a1 = t.msg(x + 1000, 1420, "1 5"); b0 = t.msg(x + 1050, 1420, "0 5")
    b1 = t.msg(x + 1100, 1420, "1 5"); a0 = t.msg(x + 1150, 1420, "0 5")
    t.c(fS, a1, 0); t.c(fS, b0, 0); t.c(fS, b1, 1); t.c(fS, a0, 1)
    t.c(a1, lnA); t.c(a0, lnA); t.c(b1, lnB); t.c(b0, lnB)
''')
open(p, "w").write(s)
print("filter crossfade applied")

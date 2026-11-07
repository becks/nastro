#!/usr/bin/env python3
"""Punch-in/out fades: the tape writer blends old -> new over 8 ms at rec start and new -> old at rec stop
(the writer keeps running until the fade-out is done), so starting or stopping a recording leaves no step on tape."""
p = "gentape.py"; s = open(p).read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("tws, dubs = [], []\n", """tws, dubs = [], []
# punch fade gain (apply_punchfade.py): written = old + g*(dub*old + in - old)
pG = t.obj(900, 640, "line~")
""")
rep("t.c(rd, db); t.c(db, ad, 0, 0); t.c(rin, ad, 0, 1); t.c(ad, tw)",
    """t.c(rd, db); t.c(db, ad, 0, 0); t.c(rin, ad, 0, 1)
    pD = t.obj(x + 70, 795, "-~"); pM = t.obj(x + 110, 795, "*~"); pS = t.obj(x + 150, 795, "+~")
    t.c(ad, pD, 0, 0); t.c(rd, pD, 0, 1); t.c(pD, pM, 0, 0); t.c(pG, pM, 0, 1)
    t.c(pM, pS, 0, 0); t.c(rd, pS, 0, 1); t.c(pS, tw)""")
rep("t.c(ru, stop_all, 1); t.c(ru, rfst, 0); t.c(rfst, rsel); t.c(rsel, recA)",
    """t.c(ru, rfst, 0); t.c(rfst, rsel)
# stop: fade out, then stop the writers ; start: cancel a pending stop, stop now, fade in, then start
pOut = t.obj(1000, 330, "t b b")
pOutM = t.msg(1100, 360, "0 8")
pDl = t.obj(1000, 390, "delay 10")
t.c(ru, pOut, 1); t.c(pOut, pOutM, 1); t.c(pOutM, pG); t.c(pOut, pDl, 0); t.c(pDl, stop_all)
pIn = t.obj(800, 420, "t b b b b")
pInM = t.msg(860, 450, "0 \\\\, 1 8")
pStp = t.msg(820, 450, "stop")
t.c(rsel, pIn); t.c(pIn, pStp, 3); t.c(pStp, pDl); t.c(pIn, stop_all, 2); t.c(pIn, pInM, 1); t.c(pInM, pG)
t.c(pIn, recA, 0)""")
# keep re-anchoring the writer at loop wraps until the fade-out is over (else the tail is written past the loop end)
rep("t.c(wsel, wsp); t.c(recst, wsp, 1, 1); ",
    """t.c(wsel, wsp)
wOn = t.obj(1450, 400, "sel 0")
t.c(recst, wOn, 1); t.c(wOn, wsp, 1, 1)                       # rec on -> open now
wOff = t.msg(1500, 400, "0")
t.c(pDl, wOff); t.c(wOff, wsp, 0, 1)                          # rec off -> close after the fade
""")
# exact seam fix while the gain ramps (fade across a wrap): keep the last block of g in [table pgbuf 64]
# written = S + g*(dub*S + in - S) at hi+j  ->  new lo+j = w - S + old + g*(1-dub)*(S - old)
rep("t.save(\"tape.pd\")", """t.obj(2600, 1480, "table pgbuf 64")
pgW = t.obj(2600, 1530, "tabwrite~ pgbuf")
t.c(pG, pgW)
pgSp = t.obj(2700, 1500, "spigot")
t.c(bng, pgSp); t.c(pgSp, pgW)
t.c(wOn, pgSp, 1, 1); t.c(wOff, pgSp, 0, 1)                    # only while the writer runs
t.save("tape.pd")""")
rep('valE = t.obj(2400, 1760, "expr $s2[$f4+$f1]-$f5*seamsave[$f1]+$f5*$s2[$f3+$f1]")',
    'valE = t.obj(2400, 1760, "expr $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+pgbuf[64-$f6+$f1]*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1])")')
rep('nT = t.obj(2200, 1690, "t f b")\nt.c(nE, nT)', 'nT = t.obj(2200, 1690, "t f b f")\nt.c(nE, nT); t.c(nT, valE, 2, 5)')
open(p, "w").write(s)
print("ok")

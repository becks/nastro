#!/usr/bin/env python3
"""Output meter on the MIX page: meter.pd (genmeter.py) + small hooks: master sends the output level
(env~ after limiter and mute), the MIX page tells the meter when it clears the screen, 'aux=PAN' hint removed."""
import shutil

for f in ("genmix.py", "gen.py"):
    shutil.copy(f, f + ".pre-meter")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("genmix.py", [
    # master: output level for the meter (after limiter and mute)
    ('ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))',
     '''ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))
enL = ms.obj(20, 940, "env~ 1024 512"); enR = ms.obj(200, 940, "env~ 1024 512")
ms.c(muL, enL); ms.c(muR, enR)
ms.c(enL, ms.obj(20, 970, "s nst-outL")); ms.c(enR, ms.obj(200, 970, "s nst-outR"))'''),
])

edit("genmix.py", [
    # the MIX screen clears the display: the meter must redraw its lights
    ('x_.c(seq, clr, 2); x_.c(seq, pgS, 1); x_.c(seq, flip, 0)',
     'x_.c(seq, clr, 2); x_.c(seq, pgS, 1); x_.c(seq, flip, 0)\n'
     'x_.c(seq, x_.msg(100, 430, "\\\\; mt-reset bang"), 2)'),
    # title: no more 'aux=PAN' hint (the meter lives there)
    ('osc2("gPrintln", "iiiiis", "1 1 8 1 MIX") + " " + osc2("gPrintln", "iiiiis", "58 1 8 1 aux=PAN")',
     'osc2("gPrintln", "iiiiis", "1 1 8 1 MIX")'),
])

edit("gen.py", [
    ('m.obj(1380, 680, "tomb")', 'm.obj(1380, 680, "tomb")\nm.obj(1460, 680, "meter")'),
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genrev.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genrev.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmeter.py")).read())'),
])
print("meter applied")

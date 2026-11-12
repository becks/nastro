#!/usr/bin/env python3
"""On-screen messages (gentoast.py -> toast.pd, [s nst-toast] words): gen.py builds it and puts [toast] in main.pd.
Used by: DRUM KIT mode (AUX+G#5: WHOLE KIT ON / OFF; after a kit take: KIT 24 SLICES) and the input monitor
(AUX+F#5, any page: INPUT MONITOR ON / OFF)."""
import shutil

for f in ("gen.py", "gendrum.py", "gensmpl.py"):
    shutil.copy(f, f + ".pre-toast")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gen.py", [
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genvis.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genvis.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentoast.py")).read())'),
    ('m.obj(1920, 680, "vis")', 'm.obj(1920, 680, "vis")\nm.obj(1990, 680, "toast")'),
])
edit("gendrum.py", [
    ('d.c(kitT, d.obj(2400, 250, "s drum-kit"), 0)',
     '''d.c(kitT, d.obj(2400, 250, "s drum-kit"), 0)
kitTs = d.obj(2300, 250, "sel 0 1")                   # message on the screen (apply_toast.py)
d.c(kitT, kitTs, 0)
d.c(kitTs, d.msg(2300, 280, "\\\\; nst-toast WHOLE KIT OFF"), 0); d.c(kitTs, d.msg(2300, 300, "\\\\; nst-toast WHOLE KIT ON"), 1)'''),
    ('d.c(kitDo, kitOff, 0)', 'd.c(kitDo, kitOff, 0)\nd.c(kitDo, d.msg(2300, 520, "\\\\; nst-toast KIT 24 SLICES"), 0)'),
])
edit("gensmpl.py", [
    ('r.c(monN, monE, 0, 0)',
     '''r.c(monN, monE, 0, 0)
monTs = r.obj(1000, 220, "sel 0 1")                   # message on the screen (apply_toast.py)
r.c(monN, monTs)
r.c(monTs, r.msg(900, 250, "\\\\; nst-toast INPUT MONITOR OFF"), 0); r.c(monTs, r.msg(1000, 250, "\\\\; nst-toast INPUT MONITOR ON"), 1)'''),
])
print("toast applied")

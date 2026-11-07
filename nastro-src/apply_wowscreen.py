#!/usr/bin/env python3
"""TAPE screen shows the wow amount (knob 4) as WOW 0..100, bottom row between DUB and LOOP. The row moves down
2 px (y 47) so WOW clears the tape head."""


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gentape.py", [("t.c(krt, k4t, 3); t.c(k4t, we, 0)",
                     't.c(krt, k4t, 3); t.c(k4t, we, 0); t.c(k4t, t.obj(1200, 200, "s tp-wow"), 1)')])
edit("genscreen.py", [('''steps.append(fDub)
''', '''steps.append(fDub)
# wow amount, bottom row middle (apply_wowscreen.py)
fWow = g.obj(1450, 330, "f 0")
g.c(g.obj(1450, 300, "r tp-wow"), fWow, 0, 1)
wowE = g.obj(1450, 360, "expr int($f1*100+0.5)")
g.c(fWow, wowE)
g.c(wowE, g.msg(1450, 390, osc("gPrintln", "iiiiisf", "52 47 8 1 WOW \\\\$1")))
steps.append(fWow)
'''), ('g.c(g.obj(1600, 90, "r tp-dub"), dOne)', 'g.c(g.obj(1600, 90, "r tp-dub"), dOne)\ng.c(g.obj(1650, 60, "r tp-wow"), dOne)')])
edit("genscreen.py", [('"104 45 8 1 LOOP"', '"104 47 8 1 LOOP"'), ('"1 45 8 1 DUB \\\\$1"', '"1 47 8 1 DUB \\\\$1"')])
print("wow on tape screen")

#!/usr/bin/env python3
"""Fixes from the review:
- mirror: the toggle state is stored BEFORE acting (a missing mirror.txt used to leave the switch inverted)
- smpl: when recording stops, the display spigots open BEFORE the latest values are pushed (relied on creation order)
- tomb: an unused [pack] removed"""
import shutil

for f in ("genmirror.py", "gensmpl.py", "gentomb.py"):
    shutil.copy(f, f + ".pre-reviewfixes")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("genmirror.py", [
    ('''mi.c(onF, tg)
mi.c(tg, onF, 0, 1)
tgS = mi.obj(20, 150, "sel 1 0")
mi.c(tg, tgS)''', '''mi.c(onF, tg)
tgT = mi.obj(20, 135, "t f f")                      # store the new state first, then act on it
mi.c(tg, tgT)
mi.c(tgT, onF, 1, 1)
tgS = mi.obj(20, 150, "sel 1 0")
mi.c(tgT, tgS, 0)'''),
])
edit("gensmpl.py", [
    ('''recNot = r.obj(2600, 430, "== 0")
r.c(recOn, recNot)''', '''recNot0 = r.obj(2600, 430, "== 0")
r.c(recOn, recNot0)
recNot = r.obj(2600, 445, "t f f")                  # 1) open / close the display spigots  0) push the latest values
r.c(recNot0, recNot)'''),
    ('r.c(rr, keep, 0, 1); r.c(rr, sp); r.c(recNot, sp, 0, 1)', 'r.c(rr, keep, 0, 1); r.c(rr, sp); r.c(recNot, sp, 1, 1)'),
    ('r.c(recNot, back); r.c(back, keep); r.c(keep, sp)', 'r.c(recNot, back, 0); r.c(back, keep); r.c(keep, sp)'),
])
edit("gentomb.py", [
    ('thP = tb.obj(1100, 270, "pack f f f f f")\n', ''),
])
print("review fixes applied")

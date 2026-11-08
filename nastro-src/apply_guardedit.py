#!/usr/bin/env python3
"""Tape editor vs loop interpolation guard. Near the loop end tape.pd writes 3 guard samples after hi (copies of
lo..lo+2) and puts the saved originals back after the wrap. An edit that wrote there in between (DUPLICATE on a
loop copies the loop to hi..) got its first 3 samples overwritten by the stale originals: a click at every
restart of the duplicated loop (seen in a saved project). Now an edit first restores the guard
([s tp-guard-restore]) and the guard stays off while the editor is busy ([v tebusy])."""
import shutil

for f in ("gentape.py", "gentapeedit.py"):
    shutil.copy(f, f + ".pre-guardedit")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gentape.py", [
    ('iE = t.obj(gx, 2160, f"expr if($f4 && !$f5 && if($f1',
     'iE = t.obj(gx, 2160, f"expr if($f4 && !$f5 && tebusy==0 && if($f1'),        # no guard while editing
    ('restB = t.obj(2800, 1790, "t b")',
     'restB = t.obj(2800, 1790, "t b")\n'
     't.obj(2900, 1730, "v tebusy")\n'
     't.c(t.obj(2900, 1760, "r tp-guard-restore"), restB)         # an edit starts: guarded samples back first (apply_guardedit.py)'),
])
edit("gentapeedit.py", [
    ('busy1 = te.msg(100, 270, "1")',
     'busy1 = te.msg(100, 270, "1")\n'
     'te.c(busy1, te.msg(100, 300, "\\\\; tp-guard-restore bang"))      # apply_guardedit.py: loop guard back, then off\n'
     'te.c(busy1, te.obj(180, 300, "v tebusy"))'),
    ('busy0 = te.msg(1800, 650, "0")',
     'busy0 = te.msg(1800, 650, "0")\n'
     'te.c(busy0, te.obj(1800, 680, "v tebusy"))'),
])
print("guard / editor fixed")

#!/usr/bin/env python3
"""Tape edit UNDO (menu item ANNULLA, op 7).
Before every destructive edit (cut, paste, reverse, clear, duplicate) the region that is about to change is copied
into te-undo. ANNULLA swaps te-undo with the tape (so pressing it again redoes). Recording or loading a project
forgets the undo. Undo region lives in [value te-u-trk / te-u-st / te-u-len] (each reader its own [v], so a bang
never fans out to other consumers)."""
import shutil

for f in ("gentapeedit.py", "genproj.py"):
    shutil.copy(f, f + ".pre-undo")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("genproj.py", [
    ('EDIT_OPS = ["TAGLIA", "COPIA", "INCOLLA", "INVERTI", "CANCELLA", "DUPLICA"]',
     'EDIT_OPS = ["TAGLIA", "COPIA", "INCOLLA", "INVERTI", "CANCELLA", "DUPLICA", "ANNULLA"]'),
    ('for i in range(6)) + " \\\\, list 6 0")', 'for i in range(7)) + " \\\\, list 6 0")'),
    ('opR = p.obj(X0 + 260, 1830, "route 1 2 3 4 5 6")', 'opR = p.obj(X0 + 260, 1830, "route 1 2 3 4 5 6 7")'),
])

HELPERS = r'''# ---- undo: the region about to change ("track start length") is copied into te-undo first
BK_REGION = ["$f2", "$f3", "$f4"]
BK_PASTE = ["$f2", "$f3", "min($f5 \\, %(N)d-$f3)"]
BK_DUP = ["$f2", "$f3+$f4", "min($f4 \\, %(N)d-$f3-$f4)"]


def uv(x, y, nm):
    return te.obj(x, y, f"v te-u-{nm}")


def backup(x, y, cont, outs):
    """bang -> remember the target region, size te-undo, copy region -> te-undo, then continuation cont"""
    t = te.obj(x, y, "t b b")
    e = pexpr(x + 100, y + 400, "expr 0 \\; " + " \\; ".join(outs))
    te.c(t, e, 1)
    te.c(e, uv(x + 100, y + 430, "trk"), 1); te.c(e, uv(x + 160, y + 430, "st"), 2); te.c(e, uv(x + 220, y + 430, "len"), 3)
    te.c(e, te.msg(x + 100, y + 460, "\\; te-undo resize \\$1"), 3)
    te.c(t, go(x, y + 490, cont, J_TO_UNDO), 0)
    return t


def ujob(x, y, outs):
    """bang -> job over the remembered undo region: $f2 track $f3 start $f4 length"""
    tb = te.obj(x, y, "t b b b b")
    e = te.obj(x, y + 60, "expr 0*$f1+0*$f2+0*$f3+0*$f4 \\; " + " \\; ".join(outs))
    for o, nm in ((3, "trk"), (2, "st"), (1, "len")):
        r = uv(x + (4 - o) * 50, y + 30, nm)
        te.c(tb, r, o); te.c(r, e, 0, {"trk": 1, "st": 2, "len": 3}[nm])
    te.c(tb, e, 0)
    pk = te.obj(x, y + 90, "pack f f f f f")
    for o in range(5):
        te.c(e, pk, o + 1, o)
    te.c(pk, te.obj(x, y + 120, "s te-job"))
    return tb


J_TO_UNDO = ujob(2300, 760, ["$f2", "$f3", "8", "0", "$f4"])        # tape region -> te-undo
J_UNDO_A = ujob(2300, 900, ["$f2", "$f3", "6", "0", "$f4"])         # swap: tape -> te-tmp
J_UNDO_B = ujob(2500, 900, ["8", "0", "$f2", "$f3", "$f4"])         #       te-undo -> tape
J_UNDO_C = ujob(2700, 900, ["6", "0", "8", "0", "$f4"])             #       te-tmp -> te-undo
R = {}
for i, (pend, outs)''' % {"N": 2646000}

CONT = r'''cd = te.obj(1200, 1200, "sel 11 12 21 31 41 42 51 61")
cdB = te.obj(2300, 1200, "sel 10 30 40 50 60 71 72 73")
te.c(cd, cdB, 8)
te.c(cdB, go(2300, 1230, 11, J_TO_CLIP), 0)       # backups done -> the original first step of each op
te.c(cdB, go(2400, 1230, 31, J_PASTE), 1)
te.c(cdB, go(2500, 1230, 41, J_TO_TMP), 2)
te.c(cdB, go(2600, 1230, 51, J_ZERO), 3)
te.c(cdB, go(2700, 1230, 61, J_DUP), 4)
te.c(cdB, go(2300, 1290, 72, J_UNDO_B), 5)        # undo swap steps
te.c(cdB, go(2400, 1290, 73, J_UNDO_C), 6)
unDone = te.obj(2500, 1290, "t b b b b")
te.c(cdB, unDone, 7)
te.c(unDone, te.msg(2600, 1320, "\\; te-pend symbol ANNULLATO"), 3)
unRs = te.obj(2500, 1380, "pack f f f")
for o, nm, inl in ((2, "len", 2), (1, "st", 1), (0, "trk", 0)):
    r = uv(2500 + (2 - o) * 50, 1350, nm)
    te.c(unDone, r, o); te.c(r, unRs, 0, inl)
te.c(unRs, te.obj(2500, 1410, "s te-rescan"))'''

UNDO_OP = r'''# 7 UNDO (swap te-undo <-> tape region; pressed again = redo)
unB = te.obj(1700, 610, "t b")
te.c(opS, unB, 6)
unV = uv(1700, 625, "len")
unE = te.obj(1700, 640, "> 0")
te.c(unB, unV); te.c(unV, unE)
unS = te.obj(1700, 670, "sel 1 0")
te.c(unE, unS)
unGo = te.obj(1700, 700, "t b b b")
te.c(unS, unGo, 0)
te.c(unGo, status(1800, 700, "ANNULLO..."), 2)
unV2 = uv(1800, 715, "len")
te.c(unGo, unV2, 1); te.c(unV2, te.msg(1800, 730, "\\; te-tmp resize \\$1"))
te.c(unGo, go(1700, 760, 71, J_UNDO_A), 0)
unNo = te.obj(1900, 670, "t b b")
te.c(unS, unNo, 1); te.c(unNo, status(1950, 700, "NIENTE-DA-ANNULLARE"), 1); te.c(unNo, busy0, 0)
# recording or loading a project makes the backup meaningless: forget it
unF0 = te.msg(2000, 600, "0")
te.c(unF0, uv(2000, 630, "len"))
unRec = te.obj(2000, 540, "sel 1")
te.c(te.obj(2000, 510, "r tp-rec"), unRec); te.c(unRec, unF0)
te.c(te.obj(2100, 540, "r nst-load"), unF0)

# ================================================= continuations'''

edit("gentapeedit.py", [
    ('for i, nm in enumerate(("te-clip 1", "te-tmp 1", "te-rev 1", f"te-zero {CH}")):',
     'for i, nm in enumerate(("te-clip 1", "te-tmp 1", "te-rev 1", f"te-zero {CH}", "te-undo 1")):'),
    ('TBL = ["te-zero", "tape1", "tape2", "tape3", "tape4", "te-clip", "te-tmp", "te-rev"]   # job table codes 0..7',
     'TBL = ["te-zero", "tape1", "tape2", "tape3", "tape4", "te-clip", "te-tmp", "te-rev", "te-undo"]   # job table codes 0..8'),
    ('srcSel = te.obj(1300, 160, "sel 0 1 2 3 4 5 6 7")\ndstSel = te.obj(1550, 160, "sel 0 1 2 3 4 5 6 7")',
     'srcSel = te.obj(1300, 160, "sel 0 1 2 3 4 5 6 7 8")\ndstSel = te.obj(1550, 160, "sel 0 1 2 3 4 5 6 7 8")'),
    ('opS = te.obj(20, 600, "sel 1 2 3 4 5 6")', 'opS = te.obj(20, 600, "sel 1 2 3 4 5 6 7")'),
    ('    te.c(t, go(x, 670, cont, J_TO_CLIP), 0)',
     '    te.c(t, backup(x, 670, 10, BK_REGION) if cont == 11 else go(x, 670, cont, J_TO_CLIP), 0)'),
    ('te.c(psGo, go(520, 760, 31, J_PASTE), 0)', 'te.c(psGo, backup(520, 760, 30, BK_PASTE), 0)'),
    ('te.c(rvT, go(800, 700, 41, J_TO_TMP), 0)', 'te.c(rvT, backup(800, 700, 40, BK_REGION), 0)'),
    ('te.c(clT, go(1100, 670, 51, J_ZERO), 0)', 'te.c(clT, backup(1100, 670, 50, BK_REGION), 0)'),
    ('te.c(dpGo, go(1350, 760, 61, J_DUP), 0)', 'te.c(dpGo, backup(1350, 760, 60, BK_DUP), 0)'),
    ('R = {}\nfor i, (pend, outs)', HELPERS),
    ('cd = te.obj(1200, 1200, "sel 11 12 21 31 41 42 51 61")', CONT),
    ('# ================================================= continuations', UNDO_OP),
    ('# ops ([s tape-edit] 1..6): 1 cut 2 copy 3 paste 4 reverse 5 clear 6 duplicate',
     '# ops ([s tape-edit] 1..7): 1 cut 2 copy 3 paste 4 reverse 5 clear 6 duplicate 7 undo (swap = redo)'),
])
print("undo applied")

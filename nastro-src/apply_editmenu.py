#!/usr/bin/env python3
"""Encoder menu: opened from TAPE it shows the tape EDIT list (cut/copy/paste/reverse/clear/duplicate),
from anywhere else the projects list. Also tape-map gets a per-bin rescan input, main gets tapeedit.pd."""
import shutil

for f in ("genproj.py", "gentapemap.py", "gen.py"):
    shutil.copy(f, f + ".pre-edit")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


EDIT_OPS = ["TAGLIA", "COPIA", "INCOLLA", "INVERTI", "CANCELLA", "DUPLICA"]

edit("genproj.py", [
    # --- list content depends on the menu context (0 projects, 1 tape edit)
    (r'''p.c(rebuild, fixed, 3); p.c(fixed, ins)''',
     r'''ctxF = p.obj(500, 120, "f 0")
p.c(p.obj(500, 90, "r pm-ctx"), ctxF, 0, 1)
spP1 = p.obj(150, 165, "spigot 1"); spP2 = p.obj(100, 195, "spigot 1"); spE = p.obj(400, 165, "spigot 0")
ctxNot = p.obj(600, 120, "== 0")
p.c(p.obj(600, 90, "r pm-ctx"), ctxNot); p.c(ctxNot, spP1, 0, 1); p.c(ctxNot, spP2, 0, 1)
p.c(p.obj(700, 90, "r pm-ctx"), spE, 0, 1)
p.c(rebuild, spP1, 3); p.c(spP1, fixed); p.c(fixed, ins)
editL = p.msg(400, 195, "list 0 0 \\, " + " \\, ".join(f"list 5 {i + 1}" for i in range(6)) + " \\, list 6 0")
p.c(rebuild, spE, 3); p.c(spE, editL); p.c(editL, ins)'''),
    (r'''p.c(rebuild, lz, 2); p.c(lz, lc, 0, 1); p.c(rebuild, lN, 2)''',
     r'''lzT = p.obj(100, 205, "t b b")
p.c(rebuild, spP2, 2); p.c(spP2, lzT); p.c(lzT, lz, 1); p.c(lz, lc, 0, 1); p.c(lzT, lN, 0)'''),
    # --- opening: decide the context from the page we came from, rebuild, reset the selection
    (r'''p.c(openT, mdKeep, 1); p.c(mdKeep, prevF, 0, 1)     # remember the page we came from''',
     r'''p.c(openT, mdKeep, 1); p.c(mdKeep, prevF, 0, 1)     # remember the page we came from
ctxOpen = p.obj(350, 850, "== 2")
p.c(mdKeep, ctxOpen)
p.c(ctxOpen, p.msg(350, 880, "\\; pm-ctx \\$1 \\; pm-rebuild bang \\; pm-reset bang"))'''),
    (r'''p.c(topE, p.obj(400, 1000, "s pm-top"))''',
     r'''p.c(topE, p.obj(400, 1000, "s pm-top"))
rstT = p.obj(500, 940, "t b b")
p.c(p.obj(500, 910, "r pm-reset"), rstT)
rs1 = p.msg(500, 970, "1"); rs0 = p.msg(560, 970, "0")
p.c(rstT, rs1, 1); p.c(rs1, selE, 0, 1); p.c(rs1, p.obj(500, 1000 + 30, "s pm-sel"))
p.c(rstT, rs0, 0); p.c(rs0, topE, 0, 1); p.c(rs0, p.obj(560, 1030, "s pm-top"))'''),
    # --- actions 5 (tape edit op) and 6 (go to the projects list)
    (r'''actR = p.obj(800, 1030, "route 0 1 2 3 4")''', r'''actR = p.obj(800, 1030, "route 0 1 2 3 4 5 6")'''),
    (r'''p.c(actR, p.msg(1700, 1060, "\\; goHome bang"), 4)''',
     r'''p.c(actR, p.msg(1700, 1060, "\\; goHome bang"), 4)
p.c(actR, p.obj(1700, 1090, "s tape-edit"), 5)
p.c(actR, p.msg(1700, 1120, "\\; pm-ctx 0 \\; pm-rebuild bang \\; pm-reset bang"), 6)'''),
    # --- title depends on the context
    (r'''oscp("gPrintln", "iiiiis", "1 1 8 1 PROGETTI") + " " + oscp("gLine", "iiiiii", "0 10 127 10 1")), 3)''',
     r'''oscp("gLine", "iiiiii", "0 10 127 10 1")), 3)
ttT = p.obj(250, 1420, "t b")
p.c(dT, ttT, 3)
ttF = p.obj(250, 1480, "f")
p.c(p.obj(250, 1450, "r pm-ctx"), ttF, 0, 1)
ttS = p.obj(250, 1510, "sel 0 1")
p.c(ttT, ttF); p.c(ttF, ttS)
p.c(ttS, p.msg(250, 1540, oscp("gPrintln", "iiiiis", "1 1 8 1 PROGETTI")), 0)
trkF = p.obj(350, 1540, "f 1")
p.c(p.obj(350, 1510, "r tp-trk"), trkF, 0, 1)
p.c(ttS, trkF, 1)
p.c(trkF, p.msg(350, 1570, oscp("gPrintln", "iiiiisf", "1 1 8 1 EDIT-T \\$1")))'''),
    # --- row labels for the new codes
    (r'''    lblR = p.obj(X0, 1830, "route 0 1 2 3 4")''', r'''    lblR = p.obj(X0, 1830, "route 0 1 2 3 4 5 6")
    opR = p.obj(X0 + 260, 1830, "route 1 2 3 4 5 6")
    p.c(lblR, opR, 5)
    for j, nm in enumerate(EDIT_OPS):
        p.c(opR, p.msg(X0 + 260 + (j % 3) * 70, 1860 + (j // 3) * 30, oscp("gPrintln", "iiiiis", f"4 {Y} 8 \\$1 {nm}")), j)
    p.c(lblR, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\$2 PROGETTI >")), 6)'''),
    (r'''NP = 99''', r'''NP = 99
EDIT_OPS = ["TAGLIA", "COPIA", "INCOLLA", "INVERTI", "CANCELLA", "DUPLICA"]'''),
])

# tape-map: rescan single bins after an edit ("track bin" lists), and redraw the lanes
edit("gentapemap.py", [
    (r'''scan = tm.obj(20, 120, "route 1 2 3 4")''', r'''scan = tm.obj(20, 120, "route 1 2 3 4")
tm.c(tm.obj(20, 90, "r tp-rescan-bin"), scan)'''),
    (r'''tm.c(rld, dirty); tm.c(lT, dirty, 0)''', r'''tm.c(rld, dirty); tm.c(lT, dirty, 0)
tm.c(tm.obj(1100, 470, "r tp-rescan-done"), dirty)'''),
])

edit("gen.py", [
    (r'''m.obj(1220, 680, "project")''', r'''m.obj(1220, 680, "project")
m.obj(1300, 680, "tapeedit")'''),
    (r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genproj.py")).read())''',
     r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genproj.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentapeedit.py")).read())'''),
])
print("edit menu applied")

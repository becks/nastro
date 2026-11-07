#!/usr/bin/env python3
"""Projects menu: item 'SCHERMO SU MAC: OFF / ON' (code 7, just before SISTEMA) toggles the OLED mirror."""
import shutil

shutil.copy("genproj.py", "genproj.py.pre-mirrormenu")
s = open("genproj.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


# the item, only in the projects list, right before SISTEMA
rep('p.c(rebuild, sysL, 1); p.c(sysL, ins)', '''sysT = p.obj(300, 225, "t b b")
p.c(rebuild, sysT, 1)
spM = p.obj(380, 240, "spigot 1")
p.c(p.obj(450, 210, "r pm-ctx"), p.obj(450, 225, "== 0"))
mirL = p.msg(380, 255, "list 7 0")
p.c(sysT, spM, 1); p.c(spM, mirL); p.c(mirL, ins)
p.c(sysT, sysL, 0); p.c(sysL, ins)''')
open("genproj.py", "w").write(s)
s = open("genproj.py").read()
# wire the ctx gate (the == 0 object created above) -> spigot right inlet
rep('''p.c(p.obj(450, 210, "r pm-ctx"), p.obj(450, 225, "== 0"))''', '''ctxN2 = p.obj(450, 225, "== 0")
p.c(p.obj(450, 210, "r pm-ctx"), ctxN2); p.c(ctxN2, spM, 0, 1)''')
# action
rep('actR = p.obj(800, 1030, "route 0 1 2 3 4 5 6")', 'actR = p.obj(800, 1030, "route 0 1 2 3 4 5 6 7")')
rep('p.c(actR, p.msg(1700, 1060, "\\\\; goHome bang"), 4)',
    'p.c(actR, p.msg(1700, 1060, "\\\\; goHome bang"), 4)\n'
    'p.c(actR, p.msg(1800, 1060, "\\\\; nst-mirror-toggle bang"), 7)')
# label, from the mirror state
rep('    lblR = p.obj(X0, 1830, "route 0 1 2 3 4 5 6")', '''    lblR = p.obj(X0, 1830, "route 0 1 2 3 4 5 6 7")
    mrT = p.obj(X0 + 500, 1860, "unpack f f f")
    p.c(lblR, mrT, 7)
    mrA = p.obj(X0 + 500, 1890, "spigot 1"); mrB = p.obj(X0 + 570, 1890, "spigot 0")
    p.c(mrT, mrA, 1); p.c(mrT, mrB, 1)
    mrN = p.obj(X0 + 640, 1860, "== 0")
    p.c(p.obj(X0 + 640, 1830, "r nst-mirror-on"), mrN); p.c(mrN, mrA, 0, 1)
    p.c(p.obj(X0 + 570, 1830, "r nst-mirror-on"), mrB, 0, 1)
    p.c(mrA, p.msg(X0 + 500, 1920, oscp("gPrintln", "iiiiis", f"4 {Y} 8 \\\\$1 SCHERMO SU MAC: OFF")))
    p.c(mrB, p.msg(X0 + 570, 1920, oscp("gPrintln", "iiiiis", f"4 {Y} 8 \\\\$1 SCHERMO SU MAC: ON")))''')
open("genproj.py", "w").write(s)
print("mirror menu applied")

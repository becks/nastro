#!/usr/bin/env python3
"""Menu reorganised (genproj.py): the encoder menu (context 0, title MENU) now holds only short fixed entries -
< BACK, SAVE, + NEW, PROJECTS >, ALBUMS >, SCREEN TO MAC, SYSTEM - so they no longer sit below a long project
list. The projects are in their own page (context 3, title PROJECTS): < BACK + the list (load / AUX+press remove).
"6 N" now opens context N: "6 3" = PROJECTS > in the menu, "6 0" = MENU > in the tape editor."""
import shutil

shutil.copy("genproj.py", "genproj.py.pre-menutop")
s = open("genproj.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


rep('fixed = p.msg(150, 180, "list 0 0 \\\\, list 1 0 \\\\, list 2 0")',
    'fixed = p.msg(150, 180, "list 0 0 \\\\, list 1 0 \\\\, list 2 0 \\\\, list 6 3 \\\\, list 8 0 \\\\, list 7 0 \\\\, list 4 0")')
rep('spP2 = p.obj(100, 195, "spigot 1")', 'spP2 = p.obj(100, 195, "spigot 0")')
rep('p.c(ctxNot, spP1, 0, 1); p.c(ctxNot, spP2, 0, 1)',
    '''p.c(ctxNot, spP1, 0, 1)
# context 3 = the PROJECTS page: < BACK, then the project list (apply_menutop.py)
ctx3 = p.obj(650, 105, "== 3")
p.c(p.obj(650, 90, "r pm-ctx"), ctx3); p.c(ctx3, spP2, 0, 1)
spB3 = p.obj(250, 165, "spigot 0")
p.c(ctx3, spB3, 0, 1)
bk3 = p.msg(250, 180, "list 0 0")
p.c(spB3, bk3); p.c(bk3, ins)''')
rep('p.c(rebuild, spP1, 3); p.c(spP1, fixed); p.c(fixed, ins)',
    'p.c(rebuild, spP1, 3); p.c(spP1, fixed); p.c(fixed, ins)\np.c(rebuild, spB3, 3)')
rep('''spM = p.obj(380, 240, "spigot 1")
ctxN2 = p.obj(450, 225, "== 0")
p.c(p.obj(450, 210, "r pm-ctx"), ctxN2); p.c(ctxN2, spM, 0, 1)
mirL = p.msg(380, 255, "list 8 0 \\\\, list 7 0")
p.c(sysT, spM, 1); p.c(spM, mirL); p.c(mirL, ins)
''', '')
rep('sysNa = p.obj(220, 240, "!= 2")', 'sysNa = p.obj(220, 240, "== 1")              # SYSTEM after the tape editor list (the menu has its own)')
rep('p.c(actR, p.msg(1700, 1120, "\\\\; nst-proj-status symbol \\\\; pm-ctx 0 \\\\; pm-rebuild bang \\\\; pm-reset bang"), 6)',
    'p.c(actR, p.msg(1700, 1120, "\\\\; nst-proj-status symbol \\\\; pm-ctx \\\\$1 \\\\; pm-rebuild bang \\\\; pm-reset bang"), 6)')
rep('ttS = p.obj(250, 1510, "sel 0 1 2")', 'ttS = p.obj(250, 1510, "sel 0 1 2 3")')
rep('p.c(ttS, p.msg(250, 1540, oscp("gPrintln", "iiiiis", "1 1 8 1 PROJECTS")), 0)',
    'p.c(ttS, p.msg(250, 1540, oscp("gPrintln", "iiiiis", "1 1 8 1 MENU")), 0)\n'
    'p.c(ttS, p.msg(250, 1600, oscp("gPrintln", "iiiiis", "1 1 8 1 PROJECTS")), 3)')
rep('    p.c(lblR, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$2 PROJECTS >")), 6)',
    '''    r6 = p.obj(X0 + 260, 1935, "route 0 3")                 # "6 N": MENU > (tape editor) / PROJECTS > (menu)
    p.c(lblR, r6, 6)
    p.c(r6, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$1 MENU >")), 0)
    p.c(r6, p.msg(X0 + 330, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$1 PROJECTS >")), 1)''')
open("genproj.py", "w").write(s)
print("menu top applied")

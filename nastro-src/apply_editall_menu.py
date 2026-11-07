#!/usr/bin/env python3
"""Menu side of the all-tracks edit: item op 8 'MODO: 1 TRACCIA / MODO: TUTTE' (before PROGETTI >),
title EDIT-TUTTE when the mode is on. (Run after apply_editall.py.)"""
import shutil

shutil.copy("genproj.py", "genproj.py.pre-editall-menu")
s = open("genproj.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('for i in range(7)) + " \\\\, list 6 0")', 'for i in range(8)) + " \\\\, list 6 0")')
rep('opR = p.obj(X0 + 260, 1830, "route 1 2 3 4 5 6 7")', 'opR = p.obj(X0 + 260, 1830, "route 1 2 3 4 5 6 7 8")')

OLD_PROG = '    p.c(lblR, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$2 PROGETTI >")), 6)'
NEW_PROG = OLD_PROG + '''
    # op 8: the mode switch; its label shows the current mode
    m8T = p.obj(X0 + 260, 1980, "t f f")
    p.c(opR, m8T, 7)
    m8a = p.obj(X0 + 260, 2010, "spigot 1"); m8b = p.obj(X0 + 330, 2010, "spigot 0")
    p.c(m8T, m8b, 0); p.c(m8T, m8a, 1)
    m8n = p.obj(X0 + 400, 1980, "== 0")
    p.c(p.obj(X0 + 400, 1950, "r te-all"), m8n); p.c(m8n, m8a, 0, 1)
    p.c(p.obj(X0 + 330, 1950, "r te-all"), m8b, 0, 1)
    p.c(m8a, p.msg(X0 + 260, 2040, oscp("gPrintln", "iiiiis", f"4 {Y} 8 \\\\$1 MODO: 1 TRACCIA")))
    p.c(m8b, p.msg(X0 + 330, 2040, oscp("gPrintln", "iiiiis", f"4 {Y} 8 \\\\$1 MODO: TUTTE")))'''
rep(OLD_PROG, NEW_PROG)

rep('p.c(ttS, trkF, 1)', '''allT = p.obj(450, 1540, "f 0")
p.c(p.obj(450, 1510, "r te-all"), allT, 0, 1)
allS = p.obj(450, 1570, "sel 0 1")
p.c(ttS, allT, 1); p.c(allT, allS); p.c(allS, trkF, 0)
p.c(allS, p.msg(450, 1600, oscp("gPrintln", "iiiiis", "1 1 8 1 EDIT-1234")), 1)''')
open("genproj.py", "w").write(s)
print("editall menu applied")

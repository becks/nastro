#!/usr/bin/env python3
"""Projects, new behaviour (asked by the user): Nastro starts EMPTY (project 0 = no files = all defaults),
'+ NUOVO' resets everything (loads project 0), a project is only loaded when chosen from the list.
Saving project 0 (AUX+A or SALVA) gives it the first free number and adds it to the list."""
import shutil

for f in ("genproj.py", "gentomb.py"):
    shutil.copy(f, f + ".pre-projnew")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("genproj.py", [
    # start empty
    ('lbE = p.obj(20, 690, f"expr max(1 \\\\, min({NP} \\\\, int(nstcur[0])))")',
     'lbE = p.obj(20, 690, "f 0")                      # start empty: project 0 has no files -> defaults'),
    # + NUOVO = load project 0
    ('nwT = p.obj(1000, 1060, "t b b")', 'nwT = p.obj(1000, 1060, "t b b")\np.c(svGate, nwT, 0)                              # unsaved new project: take the first free number'),
    ('p.c(actR, nwT, 2)', '''nw0 = p.msg(1000, 1030, "0")
p.c(actR, nw0, 2); p.c(nw0, p.obj(1000, 1045, "s pm-load"))       # + NUOVO: everything back to zero'''),
    # saving project 0 -> first free number (the old "new" search), otherwise save the open one
    ('p.c(s69, curF); p.c(curF, doSave)', '''svGate = p.obj(400, 640, "moses 1")
p.c(s69, curF); p.c(curF, svGate)
p.c(svGate, doSave, 1)'''),
    ('p.c(actR, svTb, 1); p.c(svTb, svB); p.c(svB, doSave)', 'p.c(actR, svTb, 1); p.c(svTb, svB); p.c(svB, svGate)'),
    # status after a load: NUOVO for project 0
    ('p.c(apT0, ldSt, 1)', '''ldMo = p.obj(1150, 715, "moses 1")
p.c(apT0, ldMo, 1); p.c(ldMo, ldSt, 1)
p.c(ldMo, p.msg(1250, 730, "\\\\; nst-proj-status symbol NUOVO"), 0)'''),
    # menu row "SALVA": SALVA NUOVO when the open project is not saved yet
    ('''    for code in range(5):
        types, text = TXT[code]
        m = p.msg(X0 + (code % 3) * 100, 1860 + (code // 3) * 30, oscp("gPrintln", types, f"4 {Y} 8 \\\\$2 {text}"))
        p.c(lblR, m, code)''', '''    for code in range(5):
        types, text = TXT[code]
        m = p.msg(X0 + (code % 3) * 100, 1860 + (code // 3) * 30, oscp("gPrintln", types, f"4 {Y} 8 \\\\$2 {text}"))
        if code == 1:
            r0 = p.obj(X0 + 100, 1845, "route 0")
            p.c(lblR, r0, 1); p.c(r0, m, 1)
            p.c(r0, p.msg(X0 + 100, 1875, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$1 SALVA NUOVO")), 0)
        else:
            p.c(lblR, m, code)'''),
])

# a new / loaded project also removes the TOMBOLA balls
edit("gentomb.py", [
    ('tb.c(lbT, init, 1)', '''tb.c(lbT, init, 1)
tb.c(tb.obj(300, 60, "r nst-load"), tb.msg(300, 90, "\\\\; tmbnt const 0 \\\\; tomb-count bang"))'''),
])
print("projnew applied")

#!/usr/bin/env python3
"""TOMBOLA wiring: SEQ pages cycle TEMPO -> STEP -> TOMBOLA (AUX+E), knob context 15 (pkval grows to 64),
project apply sends ctx 15 to tomb-set (old project files without it get the defaults), main gets tomb.pd."""
import shutil

for f in ("gen.py", "genseq.py", "genproj.py"):
    shutil.copy(f, f + ".pre-tomb")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


DEF = "0.583 0.5 0.6 0.6"       # spin ~0.02 rad/tick, gravity 0.3, bounce 0.72, 6 sides

edit("genseq.py", [
    ('pgN = q.obj(20, 330, "== 0")', 'pgN = q.obj(20, 330, "expr ($f1+1)%3")              # TEMPO -> STEP -> TOMBOLA'),
    ('rp = q.obj(300, 240, "route 0 1")', 'rp = q.obj(300, 240, "route 0 1 2")'),
    ('q.c(rp, q.obj(300, 270, "s tempo-knob"), 0)',
     'q.c(rp, q.obj(300, 270, "s tempo-knob"), 0)\nq.c(rp, q.obj(380, 270, "s tomb-knob"), 2)'),
])

edit("gen.py", [
    ('m.obj(560, 530, "table pkval 60")', 'm.obj(560, 530, "table pkval 64")'),
    ('m.obj(680, 530, "table pkpick 60")', 'm.obj(680, 530, "table pkpick 64")'),
    ('if($f1==4 && $f4==1 \\\\, 9 \\\\, $f1)', 'if($f1==4 && $f4==1 \\\\, 9 \\\\, if($f1==4 && $f4==2 \\\\, 15 \\\\, $f1))'),
    ('0.8 0 0 0 0.8 0 0 0 \\\\; pkphys', f'0.8 0 0 0 0.8 0 0 0 {DEF} \\\\; pkphys'),
    ('m.obj(1300, 680, "tapeedit")', 'm.obj(1300, 680, "tapeedit")\nm.obj(1380, 680, "tomb")'),
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentapeedit.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentapeedit.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentomb.py")).read())'),
])

edit("genproj.py", [
    ('(13, "synth-vol-set"), (14, "drum-vol-set")]', '(13, "synth-vol-set"), (14, "drum-vol-set"), (15, "tomb-set")]'),
    ('p.c(apT0, apT, 0)', f'''fixT = p.obj(900, 760, "t b b")
p.c(apT0, fixT, 0); p.c(fixT, apT, 0)
# projects saved before TOMBOLA have no values for ctx 15 (read as zeros): use the defaults
fixE = p.obj(900, 790, "expr pkval[60]+pkval[61]+pkval[62]+pkval[63]==0")
fixS = p.obj(900, 820, "sel 1")
p.c(fixT, fixE, 1); p.c(fixE, fixS); p.c(fixS, p.msg(900, 850, "\\\\; pkval 60 {DEF}"))'''),
])
print("tomb wiring applied")

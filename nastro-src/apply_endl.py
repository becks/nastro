#!/usr/bin/env python3
"""ENDLESS wiring: SEQ pages cycle TEMPO -> STEP -> TOMBOLA -> ENDLESS, knob context 17 (pkval 72),
project apply sends ctx 17 to endl-set (old projects get the defaults), main gets endl.pd."""
import shutil

for f in ("gen.py", "genseq.py", "genproj.py"):
    shutil.copy(f, f + ".pre-endl")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


DEF = "0.6 0.45 0.1 1"          # rate 1/16, gate ~50 %, direction forward, prob 100 %

edit("genseq.py", [
    ('pgN = q.obj(20, 330, "expr ($f1+1)%3")', 'pgN = q.obj(20, 330, "expr ($f1+1)%4")'),
    ('rp = q.obj(300, 240, "route 0 1 2")', 'rp = q.obj(300, 240, "route 0 1 2 3")'),
    ('q.c(rp, q.obj(380, 270, "s tomb-knob"), 2)',
     'q.c(rp, q.obj(380, 270, "s tomb-knob"), 2)\nq.c(rp, q.obj(460, 270, "s endl-knob"), 3)'),
])

edit("gen.py", [
    ('m.obj(560, 530, "table pkval 68")', 'm.obj(560, 530, "table pkval 72")'),
    ('m.obj(680, 530, "table pkpick 68")', 'm.obj(680, 530, "table pkpick 72")'),
    ('if($f1==4 && $f4==2 \\\\, 15 \\\\, $f1)', 'if($f1==4 && $f4==2 \\\\, 15 \\\\, if($f1==4 && $f4==3 \\\\, 17 \\\\, $f1))'),
    ('0.5 0.6 0.15 0.3 \\\\; pkphys', f'0.5 0.6 0.15 0.3 {DEF} \\\\; pkphys'),
    ('m.obj(1460, 680, "meter")', 'm.obj(1460, 680, "meter")\nm.obj(1540, 680, "endl")'),
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmeter.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmeter.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genendl.py")).read())'),
])

edit("genproj.py", [
    ('(16, "rvb-set")]', '(16, "rvb-set"), (17, "endl-set")]'),
    ('p.c(fixT, fixE2, 1); p.c(fixE2, fixS2)', '''fixE3 = p.obj(700, 790, "expr pkval[68]+pkval[69]+pkval[70]+pkval[71]==0")
fixS3 = p.obj(700, 820, "sel 1")
p.c(fixT, fixE3, 1); p.c(fixE3, fixS3); p.c(fixS3, p.msg(700, 850, "\\\\; pkval 68 ''' + DEF + '''"))
p.c(fixT, fixE2, 1); p.c(fixE2, fixS2)'''),
])
print("endl wiring applied")

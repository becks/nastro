#!/usr/bin/env python3
"""VIS, the 6th page of MIX (genvis.py -> vis.pd): a picture of the output, one /oled/gFrame per frame.
- genmix.py: AUX+D# cycles 6 pages; knobs of page 5 go to vis-knob; mix.pd's own frames (clear / draw / flip)
  are held while VIS is shown (vis.pd draws the whole screen there).
- gen.py: exec genvis.py, [vis] in main.pd; knob context 47 for mode 3 page 5 (pkval / pkpick 192).
- genproj.py: context 47 loaded as vis-set; older projects (188 values) get the defaults."""
import shutil

for f in ("gen.py", "genmix.py", "genproj.py"):
    shutil.copy(f, f + ".pre-vis")


def edit(p, pairs):
    with open(p) as f_:
        s = f_.read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    with open(p, "w") as f_:
        f_.write(s)


VDEF = "0 0.6 0.5 0"
edit("genmix.py", [
    ('pgN = x_.obj(20, 220, "expr ($f1+1)%5")             # MIX -> FX -> FILTER -> MASTER -> SEND',
     'pgN = x_.obj(20, 220, "expr ($f1+1)%6")             # MIX -> FX -> FILTER -> MASTER -> SEND -> VIS (apply_vis.py)'),
    ('rpg = x_.obj(200, 120, "route 0 1 2 3 4")', 'rpg = x_.obj(200, 120, "route 0 1 2 3 4 5")'),
    ('x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)', 'x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)\nx_.c(rpg, x_.obj(1200, 150, "s vis-knob"), 5)              # VIS page (apply_vis.py)'),
    ('x_.c(dF, dSel); x_.c(dSel, dTT); x_.c(dTT, dZero, 1); x_.c(dZero, dF, 0, 1); x_.c(dTT, seq, 0)',
     '''x_.c(dF, dSel); x_.c(dSel, dTT); x_.c(dTT, dZero, 1); x_.c(dZero, dF, 0, 1)
visHold = x_.obj(1300, 640, "spigot 1")                    # VIS draws the whole screen itself (apply_vis.py)
visNo = x_.obj(1400, 640, "!= 5")
x_.c(x_.obj(1400, 610, "r mix-page"), visNo); x_.c(visNo, visHold, 0, 1)
x_.c(dTT, visHold, 0); x_.c(visHold, seq)'''),
])
s = open("gen.py").read()
i0 = s.index('ctxE = m.obj(560, 660, "expr ')
i1 = s.index('")\n', i0)
line = s[i0:i1]
a = "if($f1==3 && $f2==4 \\\\, if($f5==1 \\\\, 28 \\\\, 27) \\\\,"
assert line.count(a) == 1
line = line.replace(a, "if($f1==3 && $f2==5 \\\\, 47 \\\\, " + a) + ")"
s = s[:i0] + line + s[i1:]
with open("gen.py", "w") as f_:
    f_.write(s)
edit("gen.py", [
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genarp.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genarp.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genvis.py")).read())'),
    ('m.obj(1850, 680, "arp")', 'm.obj(1850, 680, "arp")\nm.obj(1920, 680, "vis")'),
    ('m.obj(560, 530, "table pkval 188")', 'm.obj(560, 530, "table pkval 192")'),
    ('m.obj(680, 530, "table pkpick 188")', 'm.obj(680, 530, "table pkpick 192")'),
    (' 0.05 0.5 0.5 1 0 0.3 0.5 0 \\\\; pkphys', f' 0.05 0.5 0.5 1 0 0.3 0.5 0 {VDEF} \\\\; pkphys'),
])
s = open("genproj.py").read()
a = '(45, "mallet-knob"), (46, "mallet-lfo-knob")]'
assert s.count(a) == 1
s = s.replace(a, '(45, "mallet-knob"), (46, "mallet-lfo-knob"), (47, "vis-set")]')
a = "# projects saved before MALLET:"
assert s.count(a) == 1
SUM = "+".join(f"abs(pkval[{i}]-pkval[188])" for i in range(189, 192))
s = s.replace(a, f'''# projects saved before VIS: slots 188..191 all equal (Pd repeats the last value) -> defaults (apply_vis.py)
fixE15 = p.obj(-500, 790, "expr {SUM}==0")
fixS15 = p.obj(-500, 820, "sel 1")
p.c(fixT, fixE15, 1); p.c(fixE15, fixS15); p.c(fixS15, p.msg(-500, 850, "\\\\; pkval 188 {VDEF}"))
''' + a)
with open("genproj.py", "w") as f_:
    f_.write(s)
print("vis applied")

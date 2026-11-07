#!/usr/bin/env python3
"""Projects save the actual tape speed (misc slot 5, stored as speed+10 so 0 = 'not saved'), and loading restores
it exactly. Before, only the knob position was saved and re-read with the quantized steps (a 0.3 set with AUX came
back as a step, e.g. 0). Old projects without the value start at 1x."""
import shutil

for f in ("genproj.py", "gentape.py"):
    shutil.copy(f, f + ".pre-speedsave")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("genproj.py", [
    ('for i, nm in enumerate(("synth-engine", "nst-oct", "tp-ls", "tp-lo", "tp-hi")):',
     '''spd10 = p.obj(1150, 50, "+ 10")                   # tape speed, stored +10 (0 = old project without it)
p.c(p.obj(1150, 20, "r tp-spd"), spd10); p.c(spd10, p.msg(1150, 80, "\\\\; nstmisc 5 \\\\$1"))
for i, nm in enumerate(("synth-engine", "nst-oct", "tp-ls", "tp-lo", "tp-hi")):'''),
    ('nstmisc 0 0 0 0 0 2646000"), 3)', 'nstmisc 0 0 0 0 0 2646000 0"), 3)'),
    ('misc = p.obj(1000, 1170, "expr nstmisc[0] \\\\; nstmisc[1] \\\\; nstmisc[2] \\\\; nstmisc[3] \\\\; nstmisc[4]")\nmpk = p.obj(1000, 1200, "pack f f f f f")\nfor o in range(5):',
     'misc = p.obj(1000, 1170, "expr nstmisc[0] \\\\; nstmisc[1] \\\\; nstmisc[2] \\\\; nstmisc[3] \\\\; nstmisc[4] \\\\; nstmisc[5]")\nmpk = p.obj(1000, 1200, "pack f f f f f f")\nfor o in range(6):'),
    ('tp-loop-set \\\\$3 \\\\$4 \\\\$5 \\\\; pkpick const 0', 'tp-loop-set \\\\$3 \\\\$4 \\\\$5 \\\\; tp-spd-set \\\\$6 \\\\; pkpick const 0'),
])
edit("gentape.py", [
    ('k1t = t.obj(600, 230, "t f f")', '''k1t = t.obj(600, 230, "t f f")
# speed restored by a project load: exact value (stored +10), 1x for old projects
spSet = t.obj(700, 230, "expr if($f1>0 \\\\, $f1-10 \\\\, 1)")
t.c(t.obj(700, 200, "r tp-spd-set"), spSet); t.c(spSet, k1t)'''),
])
# the knob apply rewrites nstmisc[5] live (tp-spd) before the misc apply reads it: snapshot it into slot 6
# right after the files are read, and apply slot 6
edit("genproj.py", [
    ('p.c(loadT, p.obj(1300, 600, "s nst-load"), 1)', '''ldSnap = p.obj(1300, 585, "t f b")                     # right after the files are read: keep the saved speed
p.c(loadT, ldSnap, 1); p.c(ldSnap, p.obj(1300, 600, "s nst-load"), 0)
spSnap = p.obj(1400, 600, "expr nstmisc[5]")
p.c(ldSnap, spSnap, 1); p.c(spSnap, p.msg(1400, 630, "\\\\; nstmisc 6 \\\\$1"))'''),
    ('\\\\; nstmisc[4] \\\\; nstmisc[5]")', '\\\\; nstmisc[4] \\\\; nstmisc[6]")'),
])
print("speedsave applied")

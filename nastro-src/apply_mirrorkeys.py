#!/usr/bin/env python3
"""Virtual Organelle for tutorials: the mirror (genmirror.py) and the Mac simulator (gensim.py) also relay the
controls and the page state (inrelay.py), so oled-sim.py can draw the keys, knobs, AUX, encoder, footswitch and
name the function of each AUX combination."""
import shutil

for f in ("genmirror.py", "gensim.py"):
    shutil.copy(f, f + ".pre-mirrorkeys")


def edit(p, a, b):
    s = open(p).read()
    assert s.count(a) == 1, (p, a)
    open(p, "w").write(s.replace(a, b))


edit("genmirror.py", "mi.c(lt, ok)\n", '''mi.c(lt, ok)
# controls + page state for the virtual Organelle in oled-sim.py (apply_mirrorkeys.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inrelay import relay_inputs
relay_inputs(mi.obj, mi.msg, mi.c, lt, 900, 300, resend=dl)
''')
edit("gensim.py", "c(rl, lpl); c(lpl, lt)\n", '''c(rl, lpl); c(lpl, lt)
# controls + page state for the virtual Organelle in oled-sim.py (apply_mirrorkeys.py)
from inrelay import relay_inputs
relay_inputs(lambda x, y, t: add("obj", x, y, t), lambda x, y, t: add("msg", x, y, t), c, lt, 20, 900, resend=tb2)
''')
print("mirror keys applied")

#!/usr/bin/env python3
"""More on-screen messages (toast.pd): reverb freeze (AUX+G5), arpeggiator HOLD (AUX+C5 on ARP), octave
(AUX+A#5 / B5: the keyboard's lowest C, OCTAVE C2..C6). Texts carry no bare numbers: a number word would reach
the OLED as a float ("24.000000"), so the kit message is now KIT SLICED: ALL KEYS."""
import shutil

for f in ("gen.py", "genrev.py", "genarp.py", "gendrum.py"):
    shutil.copy(f, f + ".pre-toast2")
BS2 = "\\" * 2          # what the generators write before ";" in a message box


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    open(p, "w").write(s)


def toast(text):
    return f'"{BS2}; nst-toast {text}"'


edit("gendrum.py", [(f'{BS2}; nst-toast KIT 24 SLICES', f'{BS2}; nst-toast KIT SLICED: ALL KEYS')])
edit("genrev.py", [('rv.c(fzNot, rv.obj(1700, 410, "s rvb-freeze"))',
                    f'''rv.c(fzNot, rv.obj(1700, 410, "s rvb-freeze"))
fzTs = rv.obj(1600, 410, "sel 0 1")                   # message on the screen (apply_toast2.py)
rv.c(fzNot, fzTs)
rv.c(fzTs, rv.msg(1500, 440, {toast("REVERB FREEZE OFF")}), 0); rv.c(fzTs, rv.msg(1600, 440, {toast("REVERB FREEZE ON")}), 1)''')])
edit("genarp.py", [('ar.c(akS, hoE, 0); ar.c(hoE, hoT)',
                    f'''ar.c(akS, hoE, 0); ar.c(hoE, hoT)
hoTs = ar.obj(200, 1090, "sel 0 1")                   # message on the screen (apply_toast2.py)
ar.c(hoE, hoTs)
ar.c(hoTs, ar.msg(200, 1120, {toast("ARP HOLD OFF")}), 0); ar.c(hoTs, ar.msg(300, 1120, {toast("ARP HOLD ON")}), 1)''')])
edit("gen.py", [('m.c(toct, m.obj(620, 470, "s nst-oct"), 0)',
                 f'''m.c(toct, m.obj(620, 470, "s nst-oct"), 0)
# octave keys: say the keyboard's lowest C once the new octave is set (apply_toast2.py)
octD = m.obj(760, 320, "delay 0")
m.c(sel_oct, octD, 0); m.c(sel_oct, octD, 1)
octF = m.obj(760, 350, "f")
m.c(clp, octF, 0, 1); m.c(octD, octF)
octS = m.obj(760, 380, "sel -2 -1 0 1 2")
m.c(octF, octS)
for k_, nm_ in enumerate(("C2", "C3", "C4", "C5", "C6")):
    m.c(octS, m.msg(760 + k_ * 90, 410, "{BS2}; nst-toast OCTAVE " + nm_), k_)''')])
print("toast2 applied")

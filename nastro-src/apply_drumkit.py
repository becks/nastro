#!/usr/bin/env python3
"""DRUM: record a whole kit (gendrum.py). AUX+G#5 (DRUM only) toggles KIT mode ("KIT" on the screen); the next
AUX+E5 (input, waits for the threshold) / AUX+F5 (Nastro's output) recording then goes straight into the kit table
[drums] instead of the selected key: up to 12 s, and whatever length was recorded is split into 24 equal slices
(the slice length follows the table size, as when a kit file is loaded). At the onset: [drums] resized to 12 s and
cleared, [tabwrite~] set to it, auto stop after 12 s. At the stop: [drums] cut to the recorded length (no copy),
the slices recomputed, the key parameters back to neutral, [tabwrite~] back to [drec], KIT mode off.
The page state "drum-kit" is published for the virtual Organelle (inrelay.py)."""
import shutil

shutil.copy("gendrum.py", "gendrum.py.pre-drumkit")
s = open("gendrum.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


KIT = 529200                      # 12 s at 44.1 kHz
rep('dks = d.obj(1800, 160, "sel 76 77")',
    'dks = d.obj(1800, 160, "sel 76 77 80")              # 80 = AUX+G#5: KIT mode (apply_drumkit.py)')
# the stop's slot copy now goes through the KIT switch below
rep('d.c(dSp, slotF, 1); d.c(slotF, dCp)', 'd.c(slotF, dCp)')

KITCODE = r'''# ---- KIT mode (apply_drumkit.py)
kitF = d.obj(2400, 160, "f 0")
kitN = d.obj(2400, 190, "== 0")
kitT = d.obj(2400, 220, "t f f")
d.c(dks, kitF, 2); d.c(kitF, kitN); d.c(kitN, kitT); d.c(kitT, kitF, 1, 1)
d.c(kitT, d.obj(2400, 250, "s drum-kit"), 0)
d.c(d.obj(2500, 220, "r drum-kit"), dirty)
kitOff = d.msg(2500, 160, "0")
d.c(kitOff, kitF, 0, 1); d.c(kitOff, d.obj(2500, 190, "s drum-kit"))
# onset in KIT mode: whole table, cleared; writer to [drums]; auto stop at 12 s; the take is timed
kitSt = d.obj(2400, 300, "spigot")
d.c(kitT, kitSt, 0, 1); d.c(kitOff, kitSt, 0, 1)
d.c(dSt, kitSt, 3)
kitStT = d.obj(2400, 330, "t b b b")
d.c(kitSt, kitStT)
d.c(kitStT, d.msg(2400, 360, "\\; drums resize KITN \\; drums const 0"), 2)
kitAu = d.msg(2550, 360, "KITMS")
d.c(kitStT, kitAu, 1); d.c(kitAu, dAuto, 0, 1)
kitSet = d.msg(2650, 360, "set drums")
d.c(kitStT, kitSet, 0); d.c(kitSet, dtw)
kitTm = d.obj(2750, 330, "timer")
d.c(dSt, kitTm, 3)
# stop: KIT mode -> finish the kit, otherwise -> copy into the key (as before)
kitSpT = d.obj(2400, 430, "t b b")
d.c(dSp, kitSpT, 1)
kitA = d.obj(2400, 460, "spigot")
kitB = d.obj(2500, 460, "spigot 1")
kitBn = d.obj(2550, 430, "== 0")
d.c(kitT, kitA, 0, 1); d.c(kitOff, kitA, 0, 1); d.c(kitT, kitBn, 0); d.c(kitBn, kitB, 0, 1)
kitOn1 = d.msg(2600, 400, "1")
d.c(kitOff, kitOn1); d.c(kitOn1, kitB, 0, 1)
d.c(kitSpT, kitA, 1); d.c(kitSpT, kitB, 0)
d.c(kitB, slotF)
kitDo = d.obj(2400, 490, "t b b b b")      # 3) length + slices  2) writer back to [drec]  1) neutral keys  0) KIT off
d.c(kitA, kitDo)
d.c(kitDo, kitTm, 3, 1)
kitLen = d.obj(2750, 520, "expr int(min(KITN \\, max(24 \\, $f1*44.1)))")
d.c(kitTm, kitLen)
kitLT = d.obj(2750, 550, "t f f")
d.c(kitLen, kitLT)
d.c(kitLT, d.msg(2850, 580, "\\; drums resize \\$1"), 1)
d.c(kitLT, slE, 0)                          # slices = new length / 24 -> players, drec, auto stop, waveform
kitDrec = d.msg(2650, 520, "set drec")
d.c(kitDo, kitDrec, 2); d.c(kitDrec, dtw)
d.c(kitDo, init, 1)
d.c(kitDo, kitOff, 0)
# KIT badge
fKit = d.obj(600, 880, "f")
d.c(d.obj(600, 850, "r drum-kit"), fKit, 0, 1)
d.c(selB, fKit)
fKitS = d.obj(600, 910, "sel 1")
d.c(fKit, fKitS)
d.c(fKitS, d.msg(600, 940, osc4("gFillArea", "iiiiii", "110 0 18 10 1") + " " + osc4("gPrintln", "iiiiis", "111 1 8 0 KIT")))

'''.replace("KITN", str(KIT)).replace("KITMS", str(int(KIT / 44.1) + 30))
rep("# REC badge on the DRUM screen", KITCODE + "# REC badge on the DRUM screen")
open("gendrum.py", "w").write(s)
print("drum kit applied")

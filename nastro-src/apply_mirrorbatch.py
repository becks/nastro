#!/usr/bin/env python3
"""Mirror batching (genmirror.py): every OLED command used to go out as its own UDP packet, so a full redraw
(DRUM on a new slot: ~55 commands in one tick) meant ~55 Wi-Fi packets at once and an audio glitch on the
Organelle 1. Now the commands of one logical time are collected and sent as ONE packet at the end of it
([delay 0]): "cmd1 ; cmd2 ; ..." - the separator is a ";" symbol, which oled-sim.py splits like any FUDI message."""
import shutil

shutil.copy("genmirror.py", "genmirror.py.pre-mirrorbatch")
s = open("genmirror.py").read()
a = "mi.c(ok, ns)\n"
assert s.count(a) == 1
s = s.replace(a, '''# one packet per logical time (apply_mirrorbatch.py)
bR = mi.obj(300, 520, "route send")                 # the command without "send"
bSep = mi.obj(450, 520, "list append")              # + the ";" separator (a symbol, made at load)
mi.c(ok, bR); mi.c(bR, bSep)
semi = mi.obj(450, 460, "makefilename %c")
semiM = mi.msg(450, 430, "59")
mi.c(mi.obj(450, 400, "loadbang"), semiM); mi.c(semiM, semi); mi.c(semi, bSep, 0, 1)
bT = mi.obj(300, 550, "t b a")                      # append first, then (re)arm the flush at the end of this tick
mi.c(bSep, bT)
acc = mi.obj(400, 580, "list prepend")              # the pending batch: old + new
mi.c(bT, acc, 1, 0); mi.c(acc, acc, 0, 1)
fl = mi.obj(300, 580, "delay 0")
mi.c(bT, fl, 0)
flT = mi.obj(300, 610, "t b b")                     # send the batch, then empty it
mi.c(fl, flT)
hold = mi.obj(300, 640, "list")
mi.c(acc, hold, 0, 1); mi.c(flT, hold, 1)
emp = mi.msg(400, 640, "list")
mi.c(flT, emp, 0); mi.c(emp, acc, 0, 1); mi.c(emp, hold, 0, 1)
bS = mi.obj(300, 670, "list prepend send")
bL = mi.obj(300, 700, "list trim")
mi.c(hold, bS); mi.c(bS, bL); mi.c(bL, ns)
''')
open("genmirror.py", "w").write(s)
print("mirror batch applied")

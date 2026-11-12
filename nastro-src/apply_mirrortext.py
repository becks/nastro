#!/usr/bin/env python3
"""Mirror batching, cheaper (genmirror.py, after apply_mirrorbatch.py). Measured on the device: a DRUM redraw
(57 commands) took ~5.4 ms in one tick with the mirror on (6 ms audio buffer): the list batch copied the whole
growing list for every command, and the 1 ms netsend ran in the same tick. Now each command is appended to a
[text] buffer (cheap), and the buffer goes out as one packet 3 ms later ([text tolist] keeps the ";" between
the commands), in a later scheduler tick."""
import shutil

shutil.copy("genmirror.py", "genmirror.py.pre-mirrortext")
s = open("genmirror.py").read()
i0 = s.index("# one packet per logical time (apply_mirrorbatch.py)")
i1 = s.index('mi.save("mirror.pd")')
s = s[:i0] + '''# one packet per burst: commands go into a text buffer, sent 3 ms later in a later tick (apply_mirrortext.py)
tdef = mi.obj(450, 520, "text define mirq")
bR = mi.obj(300, 520, "route send")                 # the command without "send"
mi.c(ok, bR)
bT = mi.obj(300, 550, "t b a")                      # store first, then (re)arm the flush
mi.c(bR, bT)
ins = mi.obj(400, 580, "text insert mirq 1e+06")
toL = mi.obj(400, 555, "list")                     # "/oled/... args" as a list for [text insert]
mi.c(bT, toL, 1); mi.c(toL, ins)
fl = mi.obj(300, 580, "delay 3")
mi.c(bT, fl, 0)
flT = mi.obj(300, 610, "t b b")                     # send the buffer, then empty it
mi.c(fl, flT)
tl = mi.obj(300, 640, "text tolist mirq")
mi.c(flT, tl, 1)
clr = mi.msg(450, 640, "clear")
mi.c(flT, clr, 0); mi.c(clr, tdef)
bS = mi.obj(300, 670, "list prepend send")
bL = mi.obj(300, 700, "list trim")
mi.c(tl, bS); mi.c(bS, bL)
mi.c(bL, ns)
''' + s[i1:]
open("genmirror.py", "w").write(s)
print("mirror text applied")

#!/usr/bin/env python3
"""The Organelle LED blinks while recording (tape, sampler or drum recording): 250 ms off / 250 ms on in the
current colour (page colour, or white while the reverb is frozen). Back to steady when recording stops."""
import shutil

shutil.copy("gen.py", "gen.py.pre-recblink")
s = open("gen.py").read()
a = '''ledm = m.msg(900, 100, "\\\; led \\\\$1")
m.c(tff, ledp, 1); m.c(ledp, ledm)'''
assert s.count(a) == 1
s = s.replace(a, '''ledm = m.msg(900, 100, "\\\; led \\\\$1")
m.c(tff, ledp, 1)
# blink while recording (apply_recblink.py): colour -> [rec && off-phase ? 0 : colour] -> led
ledO = m.obj(1100, 100, "expr if($f2 && $f3 \\\\, 0 \\\\, $f1)")
ledCT = m.obj(1100, 70, "t f f"); ledCol = m.obj(1200, 70, "f")
m.c(ledp, ledCT); m.c(ledCT, ledCol, 1, 1); m.c(ledCT, ledO, 0, 0); m.c(ledO, ledm)
recE = m.obj(1300, 40, "expr $f1 || $f2 || $f3")
m.c(m.obj(1300, 10, "r tp-rec"), recE, 0, 0)
for k_, nm_ in ((1, "smp-recording"), (2, "drum-recording")):
    tb_ = m.obj(1400 + k_ * 100, 25, "t b f")
    m.c(m.obj(1400 + k_ * 100, 0, f"r {nm_}"), tb_); m.c(tb_, recE, 1, k_); m.c(tb_, recE, 0, 0)
recC = m.obj(1300, 70, "change"); recT = m.obj(1300, 100, "t f f")
m.c(recE, recC); m.c(recC, recT); m.c(recT, ledO, 1, 1)
recS = m.obj(1300, 130, "sel 0")
m.c(recT, recS, 0)
blM = m.obj(1400, 160, "metro 250")
blStop = m.msg(1300, 160, "stop")
m.c(recS, blStop, 0); m.c(blStop, blM)
m.c(recS, blM, 1)                                                     # non-zero: start (ticks at once)
blPh = m.obj(1400, 190, "f 0"); blNot = m.obj(1460, 190, "== 0")
m.c(blM, blPh); m.c(blPh, blNot); m.c(blNot, blPh, 0, 1)
blT = m.obj(1400, 220, "t b f")
m.c(blNot, blT); m.c(blT, ledO, 1, 2); m.c(blT, ledCol, 0)
bl0 = m.msg(1300, 190, "0")                                           # stopped: phase on, colour back
bl0b = m.obj(1300, 220, "t b f f")                                   # 2) phase  1) off-phase flag  0) colour again
m.c(recS, bl0, 0); m.c(bl0, bl0b); m.c(bl0b, blPh, 2, 1); m.c(bl0b, ledO, 1, 2); m.c(bl0b, ledCol, 0)
m.c(ledCol, ledO, 0, 0)''')
open("gen.py", "w").write(s)
print("rec blink applied")

#!/usr/bin/env python3
"""Reverb freeze, AUX + G5 (toggle). Frozen: the reverb input closes (50 ms), every FDN line gain goes to
1/sqrt(8) (the Hadamard network becomes lossless) and the damping low-passes open, so the tail hangs like a pad
while new sound stays out of the reverb. DEC / TONE knob moves are stored and applied when it is released; the
reverb DSP stays on while frozen. Released: normal gains and damping, input open again, the tail decays with DEC.
Loading a project releases it. The Organelle LED turns white while frozen; FX and REVERB pages show FRZ."""
import shutil

for f in ("genrev.py", "gen.py", "genmix.py"):
    shutil.copy(f, f + ".pre-freeze")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


FROZEN_GAIN = 0.3535          # just under 1/sqrt(8) = 0.353553: no growth, a decay of many minutes

edit("genrev.py", [
    # input gate before the pre-delay
    ('''preW = rv.obj(20, 80, "delwrite~ rvb-pre 130")
rv.c(inl, preW)''', '''preW = rv.obj(20, 80, "delwrite~ rvb-pre 130")
inG = rv.obj(20, 60, "*~")                                    # freeze: input closed (apply_freeze.py); signal gain
rv.c(inl, inG); rv.c(inG, preW)
fzIn = rv.obj(1700, 40, "r rvb-freeze")
fzT = rv.obj(1700, 70, "t f f f f")
fzInv = rv.obj(1700, 100, "expr 1-$f1"); fzInM = rv.msg(1700, 130, "\\\\$1 50"); fzInL = rv.obj(1700, 160, "line~")
rv.c(fzIn, fzT); rv.c(fzT, fzInv, 3); rv.c(fzInv, fzInM); rv.c(fzInM, fzInL); rv.c(fzInL, inG, 0, 1)
lbG1 = rv.msg(1800, 130, "1")
rv.c(rv.obj(1800, 100, "loadbang"), lbG1); rv.c(lbG1, fzInL)'''),
    # DEC -> gains through a gate closed while frozen
    ("rv.c(t60T, gE, 0)", '''gGate = rv.obj(600, 230, "spigot 1")
rv.c(t60T, gGate, 0); rv.c(gGate, gE)'''),
    # on / off: keep the reverb on while frozen; when released with the send at 0, switch off after the tail
    ("rv.c(onOff, offB, 1)", '''offGate = rv.obj(1400, 145, "spigot 1")                  # REV to 0 while frozen: stay on
rv.c(onOff, offGate, 1); rv.c(offGate, offB)'''),
    ("rv.c(rmx, rmxS); rv.c(rmxS, rmxC)", '''rv.c(rmx, rmxS); rv.c(rmxS, rmxC)
rmxF = rv.obj(1400, 70, "f 0")
rv.c(rmxS, rmxF, 0, 1)'''),
])

s = open("genrev.py").read()
tail = f'''
# ---------------- freeze (apply_freeze.py): gains, damping, on/off
fzSel = rv.obj(1700, 200, "sel 1 0")
rv.c(fzT, fzSel, 0)
gOpen = rv.obj(1850, 200, "== 0")
rv.c(fzT, gOpen, 2); rv.c(gOpen, gGate, 0, 1)                  # DEC gate: closed while frozen
rv.c(gOpen, offGate, 0, 1)                                     # no switch-off while frozen
tGate = rv.obj(750, 200, "spigot 1")
rv.c(gOpen, tGate, 0, 1)
toneF = rv.obj(850, 200, "f 4800")
rv.c(toneE, toneF, 0, 1); rv.c(toneE, tGate)
fzOn = rv.obj(1700, 230, "t b b b")                             # frozen: 2) DSP on  1) lossless gains  0) damping open
rv.c(fzSel, fzOn, 0)
rv.c(fzOn, on1, 2); rv.c(fzOn, offStop, 2)
fzG = rv.msg(1700, 260, "{FROZEN_GAIN}")
rv.c(fzOn, fzG, 1)
fzTone = rv.msg(1800, 260, "20000")
rv.c(fzOn, fzTone, 0)
fzOff = rv.obj(1900, 230, "t b b b")                            # released: 2) gains from DEC  1) damping from TONE  0) off?
rv.c(fzSel, fzOff, 1)
offT2 = rv.obj(1950, 260, "v rvb-t60")
rv.c(fzOff, offT2, 2); rv.c(offT2, gE)
rv.c(fzOff, toneF, 1)
offChk = rv.obj(2050, 260, "sel 0")
rv.c(fzOff, rmxF, 0); rv.c(rmxF, offChk); rv.c(offChk, offB)
for i in range(8):
    rv.c(fzG, damped[i], 0, 1)
for lp_ in lps:
    rv.c(fzTone, lp_, 0, 1); rv.c(toneF, lp_, 0, 1); rv.c(tGate, lp_, 0, 1)
# AUX + G5 toggles; loading a project releases it
fzK = rv.obj(1700, 320, "r aux-key")
fzKs = rv.obj(1700, 350, "sel 79")
fzState = rv.obj(1700, 380, "f 0")
fzNot = rv.obj(1750, 380, "== 0")
rv.c(fzK, fzKs); rv.c(fzKs, fzState); rv.c(fzState, fzNot); rv.c(fzNot, fzState, 0, 1)
rv.c(fzNot, rv.obj(1700, 410, "s rvb-freeze"))
fzRel = rv.msg(1850, 350, "0")
rv.c(rv.obj(1850, 320, "r nst-load"), fzRel); rv.c(fzRel, fzState, 0, 1); rv.c(fzRel, rv.obj(1850, 380, "s rvb-freeze"))
'''
s = s.replace('rv.save("reverb.pd")', tail + 'rv.save("reverb.pd")')
# collect the damping low-passes and stop wiring TONE straight to them (it goes through the gate)
a = '''    lp = rv.obj(X, 500, "lop~ 5000")
    rv.c(toneE, lp, 0, 1)'''
assert s.count(a) == 1
s = s.replace(a, '''    lp = rv.obj(X, 500, "lop~ 5000")
    lps.append(lp)''')
a = "sums, damped = [], []"
assert s.count(a) == 1
s = s.replace(a, "sums, damped, lps = [], [], []")
open("genrev.py", "w").write(s)

# LED: white while frozen, else the mode colour
edit("gen.py", [('''ledp = m.obj(900, 70, "+ 1")
ledm = m.msg(900, 100, "\\\\; led \\\\$1")
m.c(tff, ledp, 1); m.c(ledp, ledm)''', '''ledp = m.obj(900, 70, "expr if($f2 \\\\, 7 \\\\, $f1+1)")              # white while the reverb is frozen
ledm = m.msg(900, 100, "\\\\; led \\\\$1")
m.c(tff, ledp, 1); m.c(ledp, ledm)
ledFz = m.obj(1000, 40, "t b f")
m.c(m.obj(1000, 10, "r rvb-freeze"), ledFz); m.c(ledFz, ledp, 1, 1); m.c(ledFz, ledp, 0, 0)''')])

# FRZ badge on the FX and REVERB pages
edit("genmix.py", [('''x_.c(fxT, fxStatic, 5)''', '''x_.c(fxT, fxStatic, 5)
# FRZ badge while the reverb is frozen (apply_freeze.py): FX title at x 24, REVERB title at x 44
x_.c(x_.obj(2200, 440, "r rvb-freeze"), dOne)
for trig, outl, bx in ((fxT, 5, 24), (rvT, 5, 44)):
    fzB = x_.obj(2100 + bx * 5, 500, "f 0")
    x_.c(x_.obj(2100 + bx * 5, 470, "r rvb-freeze"), fzB, 0, 1)        # freeze state, read at each redraw
    fzS = x_.obj(2100 + bx * 5, 530, "sel 1")
    x_.c(trig, fzB, outl); x_.c(fzB, fzS)
    x_.c(fzS, x_.msg(2100 + bx * 5, 560, osc2("gFillArea", "iiiiii", f"{bx - 2} 0 21 10 1") + " " +
                     osc2("gPrintln", "iiiiis", f"{bx} 1 8 0 FRZ")))''')])
print("reverb freeze applied")

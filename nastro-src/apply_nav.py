#!/usr/bin/env python3
"""TAPE navigation: AUX+C#5 back / AUX+D#5 forward (1 bar, or one whole loop when looping)."""
import shutil

shutil.copy("gentape.py", "gentape.py.pre-nav")
s = open("gentape.py").read()

NAV = r'''
# --- navigation: AUX+C#5 (73) back / AUX+D#5 (75) forward
# no loop: jump to the previous / next bar. loop on: move the loop window by its own length
# (previous / next loop), keeping the playhead's place inside the loop.
navK = t.obj(1800, 700, "r aux-key")
navS = t.obj(1800, 730, "sel 73 75")
navB = t.msg(1800, 760, "-1")
navF = t.msg(1860, 760, "1")
t.c(navK, navS); t.c(navS, navB, 0); t.c(navS, navF, 1)
navE = t.obj(1800, 800, f"expr $f5==2 \\; "
                        f"if($f5==2 \\, min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3)) \\, $f3) \\; "
                        f"if($f5==2 \\, min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3))+($f4-$f3) \\, $f4) \\; "
                        f"if($f5==2 \\, $f2+min(max($f3+$f1*($f4-$f3) \\, 0) \\, {N}-($f4-$f3))-$f3 \\, "
                        f"min(max(if($f1>0 \\, (floor($f2/max($f6 \\, 64)+0.01)+1) \\, (ceil($f2/max($f6 \\, 64)-0.01)-1))*max($f6 \\, 64) \\, 0) \\, {N}-1))")
t.c(navB, navE); t.c(navF, navE)
t.c(T, navE, 0, 1)                    # current position (onset, updated every block)
t.c(loT, navE, 0, 2)                  # loop start
t.c(hiT, navE, 0, 3)                  # loop end
for mm in (m0, m1, m2):               # loop state 0 / 1 / 2
    t.c(mm, navE, 0, 4)
navBar = t.obj(1950, 760, "* 4")
t.c(rtb, navBar); t.c(navBar, navE, 0, 5)
navP = t.obj(1800, 840, "pack f f f f")
for o in range(4):
    t.c(navE, navP, o, o)
navT = t.obj(1800, 870, "t l l")
t.c(navP, navT)
# 1) when looping: new loop bounds first
navR = t.obj(1900, 900, "route 1")
navU = t.obj(1900, 930, "unpack f f f")
t.c(navT, navR, 1); t.c(navR, navU, 0)
t.c(navU, hiT, 1); t.c(navU, loT, 0)
# 2) then move the playhead there (same path as rewind: onset, counter reset, writer restart if recording)
navU2 = t.obj(1800, 900, "unpack f f f f")
navSk = t.obj(1800, 930, "t b b f")
t.c(navT, navU2, 0); t.c(navU2, navSk, 3)
t.c(navSk, T, 2); t.c(navSk, set0, 1); t.c(navSk, wsp, 0)
t.save("tape.pd")'''
a = '\nt.save("tape.pd")'
assert s.count(a) == 1
s = s.replace(a, NAV)
a = 't.text(20, 5, "tape: 4 tracks x 60 s. AUX+F play/stop  AUX+F# rec  AUX+G rewind  AUX+G# loop  AUX+A save  footswitch = rec")'
assert s.count(a) == 1
s = s.replace(a, 't.text(20, 5, "tape: 4 tracks x 60 s. AUX+F play/stop  AUX+F# rec  AUX+G rewind  AUX+G# loop  AUX+A save  AUX+C#5 / D#5 back / forward  footswitch = rec")')
open("gentape.py", "w").write(s)
print("nav applied")

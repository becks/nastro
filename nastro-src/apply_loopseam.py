#!/usr/bin/env python3
"""Recording in a loop: the wrap is handled once per 64-sample block, so at every pass the last ovs+1 (<= 65)
samples are written past the loop end, the loop start keeps a sliver of the previous pass (a seam that clicks, at
a different place every pass) and the audio after the loop end gets overwritten.
Fix (only while recording a loop): the 65 samples after the loop end are saved when recording starts or the loop
end moves; at each wrap, for j in 0..n-1 (n = wrapped onset - lo + 1):
    tape[lo+j] = tape[hi+j] - dub*saved[j] + dub*tape[lo+j]      (the samples written past the end, re-mixed)
    tape[hi+j] = saved[j]                                         (restore what was after the loop end)"""
import shutil

shutil.copy("gentape.py", "gentape.py.pre-loopseam")
s = open("gentape.py").read()
BLOCK = r'''
# --- loop recording seam fix (apply_loopseam.py)
t.obj(1600, 1480, "table seamsave 65")
smTrk = t.obj(1600, 1530, "f 1"); smLo = t.obj(1700, 1530, "f 0"); smHi = t.obj(1800, 1530, f"f {N}")
smLs = t.obj(1900, 1530, "f 0"); smDub = t.obj(2000, 1530, "f 1"); smT = t.obj(2100, 1530, "f 0")
t.c(t.obj(1600, 1500, "r tp-trk"), smTrk, 0, 1)
t.c(t.obj(1700, 1500, "r tp-lo"), smLo, 0, 1)
t.c(t.obj(1900, 1500, "r tp-ls"), smLs, 0, 1)
t.c(t.obj(2000, 1500, "r tp-dub"), smDub, 0, 1)
t.c(T, smT, 0, 1)                                           # wrapped onset of the next block
smName = t.obj(1600, 1560, "makefilename tape%d")
t.c(smTrk, smName)
# 1) save the 65 samples after the loop end (rec start, loop end moved)
svT = t.obj(1600, 1600, "t b b b")
smHiIn = t.obj(1800, 1560, "t b f")
t.c(t.obj(1800, 1500, "r tp-hi"), smHiIn)
smHiSv = t.obj(1900, 1600, f"f {N}")                       # own copy: the fix also reads smHi, it must not trigger a save
t.c(smHiIn, smHi, 1, 1); t.c(smHiIn, smHiSv, 1, 1); t.c(smHiIn, svT, 0)
t.c(recA, svT, 2)                                           # before the writer starts
svG = t.obj(1600, 1660, "array get tape1")
svS = t.obj(1600, 1690, "array set seamsave")
nmSym = t.obj(1600, 1585, "t s s s")
t.c(smName, nmSym)
t.c(nmSym, svG, 0, 2)                                       # table name -> right inlet of [array get]
n65 = t.msg(1700, 1630, "65")
t.c(svT, smTrk, 2)                                          # a) name
t.c(svT, n65, 1); t.c(n65, svG, 0, 1)                       # b) how many
t.c(svT, smHiSv, 0); t.c(smHiSv, svG, 0, 0)                 # c) from the loop end (hot)
t.c(svG, svS)
# 2) at each wrap while recording (wsp fires): move the overshoot to the loop start, restore after the end
fxT = t.obj(2200, 1600, "t b b b b b b")
t.c(wsp, fxT)
nE = t.obj(2200, 1660, f"expr if($f2==2 && $f4<{N}-70 \\, max(0 \\, min(65 \\, $f1-$f3+1)) \\, 0)")
valE = t.obj(2400, 1760, "expr $s2[$f4+$f1]-$f5*seamsave[$f1]+$f5*$s2[$f3+$f1]")
loAdd = t.obj(2200, 1760, "+ 0"); hiAdd = t.obj(2300, 1760, "+ 0")
w1 = t.obj(2200, 1820, "tabwrite tape1"); w2 = t.obj(2350, 1820, "tabwrite tape1")
setM = t.msg(2500, 1700, "set \\$1")
t.c(nmSym, setM, 1); t.c(setM, w1); t.c(setM, w2)
t.c(nmSym, valE, 2, 1)                                      # $s2 table name
t.c(fxT, smTrk, 5)                                          # a) table names everywhere
t.c(fxT, smLs, 4); t.c(smLs, nE, 0, 1)                      # b) loop state
t.c(fxT, smLo, 3); t.c(smLo, nE, 0, 2); t.c(smLo, loAdd, 0, 1); t.c(smLo, valE, 0, 2)
t.c(fxT, smHi, 2); t.c(smHi, nE, 0, 3); t.c(smHi, hiAdd, 0, 1); t.c(smHi, valE, 0, 3)
t.c(fxT, smDub, 1); t.c(smDub, valE, 0, 4)
t.c(fxT, smT, 0); t.c(smT, nE, 0, 0)                        # c) n (hot)
# loop j = 0 .. n-1
nT = t.obj(2200, 1690, "t f b")
t.c(nE, nT)
jz = t.msg(2300, 1690, "0")
jU = t.obj(2200, 1710, "until")
jF = t.obj(2200, 1730, "f")
jFT = t.obj(2200, 1745, "t f f")
jInc = t.obj(2260, 1745, "+ 1")
t.c(nT, jz, 1); t.c(jz, jF, 0, 1); t.c(nT, jU, 0)
t.c(jU, jF); t.c(jF, jFT); t.c(jFT, jInc, 1); t.c(jInc, jF, 0, 1)
jT = t.obj(2200, 1775, "t f f f f")
t.c(jFT, jT, 0)
t.c(jT, loAdd, 3); t.c(loAdd, w1, 0, 1)                     # write index lo+j
t.c(jT, hiAdd, 2); t.c(hiAdd, w2, 0, 1)                     # restore index hi+j
t.c(jT, valE, 1); t.c(valE, w1, 0, 0)                       # new value at lo+j (reads hi+j before it is restored)
sr = t.obj(2350, 1790, "tabread seamsave")
t.c(jT, sr, 0); t.c(sr, w2, 0, 0)                           # restore hi+j
'''
a = 't.save("tape.pd")'
assert s.count(a) == 1
s = s.replace(a, BLOCK + a)
open("gentape.py", "w").write(s)
print("loopseam applied")

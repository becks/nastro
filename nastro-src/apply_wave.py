#!/usr/bin/env python3
"""SMPL page on the SYNTH screen: waveform (computed in chunks), selected region, markers, values."""

s = open("gensmpl.py").read()
WAVE = r'''
# --- SMPL page on the SYNTH screen (drawn when synth.pd sends [syn-extra] inside its frame)
NB = 42
r.obj(1500, 50, f"table smplwave {NB}")
fLen2 = r.obj(1500, 80, "r smp-len")
# waveform: NB bars of peak amplitude, recomputed 60 ms after a new sample, 6 bars per tick
wStart = r.obj(1600, 50, "delay 60")
wB = r.obj(1600, 20, "t b")
r.c(r.obj(1660, 20, "r smp-len"), wB); r.c(wB, wStart)
wT = r.obj(1600, 80, "t b b b")
r.c(wStart, wT)
wZ = r.msg(1700, 110, "0")
wCnt = r.obj(1600, 200, "f")
wCnt1 = r.obj(1650, 200, "+ 1")
wPkZ = r.msg(1800, 80, "0")
r.c(wT, wZ, 2); r.c(wZ, wCnt, 0, 1); r.c(wT, wPkZ, 1)
wChunk = r.obj(1600, 140, "t b b")
r.c(wT, wChunk, 0)
w6 = r.msg(1660, 170, "6")
wU = r.obj(1660, 200, "until")
r.c(wChunk, w6, 1); r.c(w6, wU); r.c(wU, wCnt); r.c(wCnt, wCnt1); r.c(wCnt1, wCnt, 0, 1)
wM = r.obj(1600, 230, f"moses {NB}")
r.c(wCnt, wM)
r.c(wM, wU, 1, 1)                                     # past the last bar: stop
wI = r.obj(1600, 260, "t f f")
r.c(wM, wI, 0)
wE = r.obj(1600, 290, f"expr int($f1*$f2/{NB}) \\; max(1 \\, int($f2/{NB}))")
r.c(wI, wE, 0); r.c(fLen2, wE, 0, 1)
amx = r.obj(1600, 350, "array max smpl")
amn = r.obj(1750, 350, "array min smpl")
r.c(wE, amx, 1, 1); r.c(wE, amn, 1, 1)
wOn = r.obj(1600, 320, "t f f")
r.c(wE, wOn, 0); r.c(wOn, amn, 1, 0); r.c(wOn, amx, 0, 0)
aE = r.obj(1600, 380, "expr max($f1 \\, -$f2)")
r.c(amn, aE, 0, 1); r.c(amx, aE, 0, 0)
aT = r.obj(1600, 410, "t f f")
r.c(aE, aT)
wTw = r.obj(1600, 440, "tabwrite smplwave")
r.c(wI, wTw, 1, 1); r.c(aT, wTw, 0)
pkMax = r.obj(1750, 440, "max")
pkT = r.obj(1750, 470, "t f f")
r.c(aT, pkMax, 1); r.c(pkMax, pkT); r.c(pkT, pkMax, 1, 1)
r.c(wT, pkMax, 1, 1) if False else None
# after each chunk: continue, or finish (tell the screens to redraw)
wChk = r.obj(1600, 470, "t b")
r.c(wChunk, wChk, 0)
wCF = r.obj(1600, 500, "f")
r.c(wCnt, wCF, 0, 1); r.c(wChk, wCF)
wDone = r.obj(1600, 530, f"moses {NB}")
r.c(wCF, wDone)
wNext = r.obj(1600, 560, "delay 1")
r.c(wDone, wNext, 0); r.c(wNext, wChunk)
r.c(wDone, r.msg(1700, 560, "\\; nst-redraw bang"), 1)
# zero-crossing results move the markers: redraw
for nm in ("smp-s0", "smp-s1"):
    r.c(r.obj(1850 + ("smp-s0", "smp-s1").index(nm) * 90, 470, f"r {nm}"), r.msg(1850, 500, "\\; nst-redraw bang"))

# drawing
fS0 = r.obj(2000, 80, "f 0"); fS1 = r.obj(2080, 80, f"f {SMAX}")
r.c(r.obj(2000, 50, "r smp-s0"), fS0, 0, 1); r.c(r.obj(2080, 50, "r smp-s1"), fS1, 0, 1)
dT = r.obj(2000, 140, "t b b b")
r.c(r.obj(2000, 110, "r syn-extra"), dT)
# 1) bars: inside START..END full height, outside a 1-px line
bZ = r.msg(2100, 170, "0")
bN = r.msg(2000, 170, f"{NB}")
bU = r.obj(2000, 200, "until")
bC = r.obj(2000, 230, "f")
bC1 = r.obj(2050, 230, "+ 1")
bT = r.obj(2000, 160, "t b b")
r.c(dT, bT, 2); r.c(bT, bZ, 1); r.c(bZ, bC, 0, 1); r.c(bT, bN, 0)
r.c(bN, bU); r.c(bU, bC); r.c(bC, bC1); r.c(bC1, bC, 0, 1)
bE = r.obj(2000, 260,
           f"expr 1+$f1*3 \\; "
           f"if(($f1+1)*$f2/{NB}>$f3 && $f1*$f2/{NB}<$f4 \\, 26-int(smplwave[$f1]/max($f5 \\, 0.001)*14) \\, 26) \\; "
           f"if(($f1+1)*$f2/{NB}>$f3 && $f1*$f2/{NB}<$f4 \\, 2*int(smplwave[$f1]/max($f5 \\, 0.001)*14)+1 \\, 1)")
r.c(bC, bE); r.c(fLen2, bE, 0, 1); r.c(r.obj(2150, 230, "r smp-s0"), bE, 0, 2); r.c(r.obj(2240, 230, "r smp-s1"), bE, 0, 3)
r.c(pkT, bE, 0, 4)
bP = r.obj(2000, 290, "pack f f f")
for o in range(3):
    r.c(bE, bP, o, o)
r.c(bP, r.msg(2000, 320, "\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\$1 \\$2 2 \\$3 1"))
# 2) START / END markers
mB = r.obj(2300, 160, "t b b")
r.c(dT, mB, 1)
mE = r.obj(2300, 220, "expr 1+int($f1/max(1 \\, $f3)*125) \\; 1+int($f2/max(1 \\, $f3)*125)")
r.c(mB, fS1, 1); r.c(fS1, mE, 0, 1)
r.c(fLen2, mE, 0, 2)
r.c(mB, fS0, 1) if False else None
mF0 = r.obj(2300, 190, "t b")
r.c(mB, mF0, 0)
fS0b = r.obj(2400, 190, "f 0")
r.c(r.obj(2400, 160, "r smp-s0"), fS0b, 0, 1); r.c(mF0, fS0b); r.c(fS0b, mE, 0, 0)
mP = r.obj(2300, 250, "pack f f")
r.c(mE, mP, 0, 0); r.c(mE, mP, 1, 1)
r.c(mP, r.msg(2300, 280, "\\; oscOut sendtyped /oled/gLine iiiiii 3 \\$1 10 \\$1 42 1 \\; oscOut sendtyped /oled/gLine iiiiii 3 \\$2 10 \\$2 42 1"))
# 3) labels and values
vB = r.obj(2500, 160, "t b b b b b")
r.c(dT, vB, 0)
r.c(vB, r.msg(2500, 190, "\\; oscOut sendtyped /oled/gPrintln iiiiis 3 1 45 8 1 STA \\; oscOut sendtyped /oled/gPrintln iiiiis 3 33 45 8 1 END "
                         "\\; oscOut sendtyped /oled/gPrintln iiiiis 3 65 45 8 1 REL \\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 45 8 1 LOOP"), 4)
vals = [("smp-start", "expr int($f1*100)", 1), ("smp-end", "expr int($f1*100)", 33), ("smp-rel", "int", 65)]
for i, (nm, ex, x) in enumerate(vals):
    f = r.obj(2500 + i * 120, 220, "f")
    r.c(r.obj(2500 + i * 120, 190 + 60, f"r {nm}"), f, 0, 1)
    e = r.obj(2500 + i * 120, 280, ex)
    r.c(vB, f, 3 - i); r.c(f, e)
    r.c(e, r.msg(2500 + i * 120, 310, f"\\; oscOut sendtyped /oled/gPrintln iiiiif 3 {x} 55 8 1 \\$1"))
fLp = r.obj(2900, 220, "f")
r.c(r.obj(2900, 250, "r smp-loop"), fLp, 0, 1)
lpS = r.obj(2900, 280, "sel 0")
r.c(vB, fLp, 0); r.c(fLp, lpS)
r.c(lpS, r.msg(2900, 310, "\\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 55 8 1 off"), 0)
r.c(lpS, r.msg(2980, 310, "\\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 55 8 1 on"), 1)
r.save("smpl.pd")'''
WAVE = WAVE.replace("r.c(wT, pkMax, 1, 1) if False else None\n", "r.c(wPkZ, pkMax, 0, 1)\n")
WAVE = WAVE.replace("r.c(mB, fS0, 1) if False else None\n", "")
assert "if False" not in WAVE
a = '\nr.save("smpl.pd")'
assert s.count(a) == 1
s = s.replace(a, WAVE)
open("gensmpl.py", "w").write(s)
print("wave page added")

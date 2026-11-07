#!/usr/bin/env python3
"""Tape recording at 0.5x and 2x (OP-1 style: record slowed down, play back at 1x an octave up - or the reverse).

Before, rec forced the tape to 1x. Now, when the speed is on one of the octave steps 0.5 or 2, the tape keeps that
speed while recording (the factor is frozen at rec start); any other speed records at 1x as before.

The 1x writers are plain [tabwrite~]s (one tape sample per audio sample). For 2x and 0.5x a resampled writer
abstraction (tape-vw.pd: [switch~ 128 1 2] / [switch~ 32 1 0.5], on only while recording) writes two tape samples
per audio sample, or one every two, in real time. It reads the old tape at its own write index, so overdub and the
punch fades work as at 1x. Before halving the rate, the input goes through a 4-pole low-pass (anti-aliasing).

Loop seam fix: at 2x one block moves the head 128 samples, so the overshoot can be up to 128 samples (save buffer
65 -> 129), and the fade gain of an overshoot sample is looked up at its own time in the block."""
import math
import shutil

shutil.copy("gentape.py", "gentape.py.pre-varirec")
p = "gentape.py"; s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


# --- speed: rec keeps an octave-step speed (frozen factor $f4), otherwise 1x
rep('sx = t.obj(20, 340, "expr $f1*if($f3 \\\\, 1 \\\\, $f2)")',
    'sx = t.obj(20, 340, "expr $f1*if($f3 \\\\, $f4 \\\\, $f2)")')
rep("t.c(recT, recin, 2); t.c(recin, sx, 1, 2); t.c(recin, sx, 0, 0)",
    """rcT = t.obj(420, 290, "t f f")
t.c(recT, rcT, 2); t.c(rcT, recin, 0); t.c(recin, sx, 1, 2); t.c(recin, sx, 0, 0)
# rec factor (apply_varirec.py): frozen at rec start from the current speed
fSpd = t.obj(520, 320, "f 1")
t.c(spdin, fSpd, 1, 1)
rcOn = t.obj(520, 290, "sel 1")
t.c(rcT, rcOn, 1); t.c(rcOn, fSpd)
facE = t.obj(520, 350, "expr if($f1==0.5 || $f1==2 \\\\, $f1 \\\\, 1)")
t.c(fSpd, facE)
facT = t.obj(520, 380, "t f f f f")
t.c(facE, facT); t.c(facT, sx, 3, 3)
t.c(facT, t.obj(620, 410, "s tp-recf"), 0)""")

# --- writer routing: 1x -> per-track tabwrite~ (as before), 2x / 0.5x -> resampled writers
rep("t.c(onsetF, wspA); t.c(wspA, lpre); t.c(lpre, rte)",
    """vwT = t.obj(1000, 500, "t f f")
sp1 = t.obj(900, 525, "spigot 1"); spV = t.obj(1100, 525, "spigot 0")
t.c(onsetF, wspA); t.c(wspA, vwT); t.c(vwT, spV, 1); t.c(vwT, sp1, 0); t.c(sp1, lpre); t.c(lpre, rte)
f1E = t.obj(900, 440, "== 1"); fVE = t.obj(960, 440, "!= 1")
t.c(facT, f1E, 1); t.c(f1E, sp1, 0, 1); t.c(facT, fVE, 1); t.c(fVE, spV, 0, 1)
vw2 = t.obj(1100, 760, "tape-vw 128 2"); vw05 = t.obj(1250, 760, "tape-vw 32 0.5")
trkF = t.obj(1250, 525, "f 1")
vsT = t.obj(1100, 555, "t f b")
t.c(spV, vsT)
nmV = t.obj(1250, 585, "makefilename tape%d")
setV = t.msg(1250, 615, "set \\\\$1")
t.c(vsT, trkF, 1); t.c(trkF, nmV); t.c(nmV, setV); t.c(setV, vw2, 0, 2); t.c(setV, vw05, 0, 2)
stV = t.msg(1100, 615, "start \\\\$1")
t.c(vsT, stV, 0)
sp2 = t.obj(1100, 645, "spigot 0"); sp05 = t.obj(1200, 645, "spigot 0")
t.c(stV, sp2); t.c(stV, sp05); t.c(sp2, vw2, 0, 2); t.c(sp05, vw05, 0, 2)
f2E = t.obj(1100, 470, "== 2"); f05E = t.obj(1160, 470, "== 0.5")
t.c(facT, f2E, 2); t.c(f2E, sp2, 0, 1); t.c(facT, f05E, 2); t.c(f05E, sp05, 0, 1)
t.c(stop_all, vw2, 0, 2); t.c(stop_all, vw05, 0, 2)
t.c(rin, vw2, 0, 0); t.c(pG, vw2, 0, 1); t.c(pG, vw05, 0, 1)""")

# anti-aliasing before 0.5x: 4-pole Butterworth low-pass at 9.5 kHz (RBJ biquads, Q 0.541 and 1.307)
def lpf(fc, q, sr=44100.0):
    w = 2 * math.pi * fc / sr; al = math.sin(w) / (2 * q); cw = math.cos(w); a0 = 1 + al
    b0 = (1 - cw) / 2 / a0; b1 = (1 - cw) / a0
    return f"{2 * cw / a0:.8f} {-(1 - al) / a0:.8f} {b0:.8f} {b1:.8f} {b0:.8f}"

rep("t.c(rin, vw2, 0, 0); t.c(pG, vw2, 0, 1); t.c(pG, vw05, 0, 1)",
    f"""aa1 = t.obj(1250, 700, "biquad~ {lpf(9500, 0.5412)}"); aa2 = t.obj(1250, 730, "biquad~ {lpf(9500, 1.3066)}")
t.c(rin, vw2, 0, 0); t.c(rin, aa1); t.c(aa1, aa2); t.c(aa2, vw05, 0, 0); t.c(pG, vw2, 0, 1); t.c(pG, vw05, 0, 1)""")

rep("t.c(k2t, lpre, 1, 1); t.c(k2t, ru, 0)", "t.c(k2t, lpre, 1, 1); t.c(k2t, trkF, 1, 1); t.c(k2t, ru, 0)")

# --- seam fix: overshoot up to 128 samples at 2x; fade gain looked up per overshoot sample; $f8 = rec factor
rep('t.obj(1600, 1480, "table seamsave 65")', 't.obj(1600, 1480, "table seamsave 130")')
rep('n65 = t.msg(1700, 1630, "65")', 'n65 = t.msg(1700, 1630, "129")')
rep(f'nE = t.obj(2200, 1660, f"expr if($f2==2 && $f4<{{N}}-70 \\\\, max(0 \\\\, min(65 \\\\, $f1-$f3+1)) \\\\, 0)")',
    f'nE = t.obj(2200, 1660, f"expr if($f2==2 && $f4<{{N}}-140 \\\\, max(0 \\\\, min(129 \\\\, $f1-$f3+1)) \\\\, 0)")')
old_val = ('valE = t.obj(2400, 1760, "expr if(xwm[$f7] \\\\, $s2[$f4+$f1]+($s2[$f3+$f1]-$s2[max($f3+$f1 \\\\, 1)])*(1-pgbuf[64-$f6+$f1]*(1-$f5)) '
           '\\\\, $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+pgbuf[64-$f6+$f1]*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1]))")')
G = "pgbuf[max(0 \\\\, int(64-($f6-$f1)/$f8))]"
new_val = ('valE = t.obj(2400, 1760, "expr if(xwm[$f7] && $f8==1 \\\\, $s2[$f4+$f1]+($s2[$f3+$f1]-$s2[max($f3+$f1 \\\\, 1)])*(1-' + G + '*(1-$f5)) '
           '\\\\, $s2[$f4+$f1]-seamsave[$f1]+$s2[$f3+$f1]+' + G + '*(1-$f5)*(seamsave[$f1]-$s2[$f3+$f1]))")\n'
           't.c(facT, valE, 0, 7)                                       # rec factor')
rep(old_val, new_val)
assert "facT = " in s and s.index("facT = ") < s.index("t.c(facT, valE")

# --- the resampled writer abstraction
rep('t.save("tape.pd")', '''t.save("tape.pd")

# ---------------------------------------------------------------- tape-vw.pd (apply_varirec.py)
# resampled tape writer: args block size, resampling factor (2 = two tape samples per audio sample, 0.5 = one per two)
# inlets: ~ input, ~ punch fade gain, messages: set <table> / start <index> / stop
w = Patch(800, 600)
w.text(20, 5, "tape-vw: tape writer at 2x or 0.5x the audio rate (switch~ on only while writing)")
wIn = w.obj(20, 40, "inlet~ lin"); wG = w.obj(200, 40, "inlet~ lin"); wC = w.obj(400, 40, "inlet")
wSw = w.obj(600, 400, "switch~ \\$1 1 \\$2")
wOn = w.msg(600, 370, "1"); wOff = w.msg(660, 370, "0")
w.c(wOn, wSw); w.c(wOff, wSw)
w.c(w.obj(660, 340, "loadbang"), wOff)                      # off until the first start
wRt = w.obj(400, 70, "route start stop")
w.c(wC, wRt)
wSet = w.obj(300, 100, "t a")                               # rejected = "set <table>": reader and writer
w.c(wRt, wSet, 2)
wStT = w.obj(500, 100, "t f f b")                           # start: 2) DSP on  1) index counter  0) writer
w.c(wRt, wStT, 0)
w.c(wStT, wOn, 2)
wM1 = w.obj(500, 130, "- 1"); wSetI = w.msg(500, 160, "set \\$1")
w.c(wStT, wM1, 1); w.c(wM1, wSetI)
wStart = w.msg(400, 160, "start \\$1")
w.c(wStT, wStart, 0)
wStopT = w.obj(700, 100, "t b b")                           # stop: 1) writer stop  0) DSP off
wStopM = w.msg(760, 130, "stop")
w.c(wRt, wStopT, 1); w.c(wStopT, wStopM, 1); w.c(wStopT, wOff, 0)
# write index: counts 1 per sample from <index>
one = w.obj(200, 200, "sig~ 1"); idx = w.obj(200, 230, "rpole~ 1")
w.c(one, idx); w.c(wSetI, idx)
rd = w.obj(200, 260, "tabread~ tape1"); w.c(wSet, rd); w.c(idx, rd)
# input: gentle low-pass (images when upsampling; a no-op at the halved rate)
l1 = w.obj(20, 230, "lop~ 16000"); l2 = w.obj(20, 260, "lop~ 16000")
w.c(wIn, l1); w.c(l1, l2)
# written = old + g * (dub * old + in - old)
dub = w.obj(300, 290, "*~ 1"); w.c(rd, dub); w.c(w.obj(400, 260, "r tp-dub"), dub, 0, 1)
a1 = w.obj(20, 320, "+~"); w.c(l2, a1, 0, 0); w.c(dub, a1, 0, 1)
d1 = w.obj(20, 350, "-~"); w.c(a1, d1, 0, 0); w.c(rd, d1, 0, 1)
m1 = w.obj(20, 380, "*~"); w.c(d1, m1, 0, 0); w.c(wG, m1, 0, 1)
a2 = w.obj(20, 410, "+~"); w.c(m1, a2, 0, 0); w.c(rd, a2, 0, 1)
tw = w.obj(20, 450, "tabwrite~ tape1")
w.c(a2, tw); w.c(wSet, tw); w.c(wStart, tw); w.c(wStopM, tw)
w.save("tape-vw.pd")''')
open(p, "w").write(s)
print("varirec applied")

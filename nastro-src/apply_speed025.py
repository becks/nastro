#!/usr/bin/env python3
"""Tape speed steps +-0.25 (9 steps: -2 -1 -0.5 -0.25 0 0.25 0.5 1 2) and recording at 0.25x: a third resampled
writer (tape-vw 16 0.25: one tape sample every four audio samples) behind a 4-pole 4.5 kHz anti-aliasing low-pass.
Recorded at 0.25x, the new part plays two octaves up at 1x. Negative speeds still record at 1x."""
import math
p = "gentape.py"; s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


def lpf(fc, q, sr=44100.0):
    w = 2 * math.pi * fc / sr; al = math.sin(w) / (2 * q); cw = math.cos(w); a0 = 1 + al
    b0 = (1 - cw) / 2 / a0; b1 = (1 - cw) / a0
    return f"{2 * cw / a0:.8f} {-(1 - al) / a0:.8f} {b0:.8f} {b1:.8f} {b0:.8f}"


old7 = (r"if(int($f1*6.999)==0 \\, -2 \\, if(int($f1*6.999)==1 \\, -1 \\, if(int($f1*6.999)==2 \\, -0.5 \\, "
        r"if(int($f1*6.999)==3 \\, 0 \\, if(int($f1*6.999)==4 \\, 0.5 \\, if(int($f1*6.999)==5 \\, 1 \\, 2))))))")
steps = [-2, -1, -0.5, -0.25, 0, 0.25, 0.5, 1]
new9 = "".join(rf"if(int($f1*8.999)=={i} \\, {v} \\, " for i, v in enumerate(steps)) + "2" + ")" * len(steps)
rep(old7, new9)
rep("# speed: 7 steps (-2 -1 -0.5 0 0.5 1 2, octaves) ;", "# speed: 9 steps (-2 -1 -0.5 -0.25 0 0.25 0.5 1 2) ;")
rep(r'facE = t.obj(520, 350, "expr if($f1==0.5 || $f1==2 \\, $f1 \\, 1)")',
    r'facE = t.obj(520, 350, "expr if($f1==0.25 || $f1==0.5 || $f1==2 \\, $f1 \\, 1)")')
rep("t.c(stop_all, vw2, 0, 2); t.c(stop_all, vw05, 0, 2)",
    f'''t.c(stop_all, vw2, 0, 2); t.c(stop_all, vw05, 0, 2)
# 0.25x writer (apply_speed025.py): one tape sample every 4 audio samples, 4.5 kHz anti-aliasing
vw025 = t.obj(1400, 760, "tape-vw 16 0.25")
t.c(setV, vw025, 0, 2); t.c(stop_all, vw025, 0, 2); t.c(pG, vw025, 0, 1)
sp025 = t.obj(1300, 645, "spigot 0")
t.c(stV, sp025); t.c(sp025, vw025, 0, 2)
f025E = t.obj(1220, 470, "== 0.25")
t.c(facT, f025E, 2); t.c(f025E, sp025, 0, 1)
aq1 = t.obj(1400, 700, "biquad~ {lpf(4500, 0.5412)}"); aq2 = t.obj(1400, 730, "biquad~ {lpf(4500, 1.3066)}")
t.c(rin, aq1); t.c(aq1, aq2); t.c(aq2, vw025, 0, 0)''')
open(p, "w").write(s)

p = "genscreen.py"; s = open(p).read()
a = '"62 1 8 1 x \\\\$1"'
assert s.count(a) == 1, a
s = s.replace(a, '"56 1 8 1 x\\\\$1"')             # "x-0.25" (no space) ends at x 92, before the time at x 100
open(p, "w").write(s)
print("speed +-0.25 and 0.25x recording")

#!/usr/bin/env python3
"""SMPL time-stretch option. Knob 4 (was LOOP on/off) is now MODE: one / str / s+lp / loop
(0-25 % one-shot, 25-50 % stretch, 50-75 % stretch + loop, 75-100 % loop; old projects keep off = one,
on (knob up) = loop). With stretch, a note lasts as long as the sample at any pitch: the sample is read at its
original speed and two 50 ms grains (Hann windows, half a grain apart) re-read it at the note's pitch
(granular pitch shift). Without stretch the grain offset is 0, both heads read the same point and the windows
sum to 1, so the sound is exactly the old one."""
import shutil

for f in ("gensynth.py", "gensmpl.py"):
    shutil.copy(f, f + ".pre-stretch")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


G = 2205          # grain length in samples (50 ms)

edit("gensynth.py", [('("LOOP", "expr $f1>0.5", "smp-loop", 0.0, "t f"),',
                      '("MODE", "expr int(min($f1 \\\\, 0.999)*4)", "smp-mode", 0.0, "t f"),')])

edit("gensmpl.py", [
    # onset expr: time rate = 1 when stretching; 5th outlet = grain offset factor (pitch - 1)
    ('''onE = v.obj(250, 220,
            "expr $f2 \\; max(64 \\\\, $f3-$f2) \\; $f1*$f4/max(64 \\\\, $f3-$f2) \\; "
            "if($f5 \\\\, 1e+09 \\\\, max(1 \\\\, max(64 \\\\, $f3-$f2)/$f4*1000/$f1-15))+3")''',
     f'''onE = v.obj(250, 220,
            "expr $f2 \\; max(64 \\\\, $f3-$f2) \\; if($f6 \\\\, 1 \\\\, $f1)*$f4/max(64 \\\\, $f3-$f2) \\; "
            "if($f5 \\\\, 1e+09 \\\\, max(1 \\\\, max(64 \\\\, $f3-$f2)/$f4*1000/if($f6 \\\\, 1 \\\\, $f1)-15))+3 \\; "
            "if($f6 \\\\, ($f1-1)*{G} \\\\, 0)")
v.c(v.obj(700, 130, "r smp-stretch"), onE, 0, 5)                   # apply_smplstretch.py'''),
    ('''pk = v.obj(250, 260, "pack f f f")
v.c(onE, pk, 2, 2); v.c(onE, pk, 1, 1); v.c(onE, pk, 0, 0)''',
     '''pk = v.obj(250, 260, "pack f f f f")
v.c(onE, pk, 4, 3); v.c(onE, pk, 2, 2); v.c(onE, pk, 1, 1); v.c(onE, pk, 0, 0)'''),
    ('apU = v.obj(250, 320, "unpack f f f")', 'apU = v.obj(250, 320, "unpack f f f f")'),
    # two grain heads instead of one read
    ('''v.c(ph, ln); v.c(ln, rd)''', f'''v.c(ph, ln)
# grains (apply_smplstretch.py): idx = position + grain phase x offset, two heads half a grain apart
gph = v.obj(450, 400, "phasor~ {44100 / G:.4f}")
v.c(z, gph, 0, 1)                                                # grains restart with the note
gD = v.obj(450, 430, "*~ 0"); v.c(apU, gD, 3, 1); v.c(gph, gD)
gB0 = v.obj(560, 430, "+~ 0.5"); gBw = v.obj(560, 460, "wrap~"); gDB = v.obj(560, 490, "*~ 0")
v.c(gph, gB0); v.c(gB0, gBw); v.c(gBw, gDB); v.c(apU, gDB, 3, 1)
iA = v.obj(150, 460, "+~"); iB = v.obj(300, 460, "+~")
v.c(ln, iA, 0, 0); v.c(gD, iA, 0, 1); v.c(ln, iB, 0, 0); v.c(gDB, iB, 0, 1)
rdB = v.obj(300, 490, "tabread4~ smpl")
v.c(apT, rdB, 1, 1)
v.c(iA, rd); v.c(iB, rdB)
gc = v.obj(650, 430, "cos~"); v.c(gph, gc)
wA = v.obj(650, 460, "*~ -0.5"); wA1 = v.obj(650, 490, "+~ 0.5")       # 0.5 - 0.5 cos
wB = v.obj(750, 460, "*~ 0.5"); wB1 = v.obj(750, 490, "+~ 0.5")        # 0.5 + 0.5 cos (half a grain later)
v.c(gc, wA); v.c(wA, wA1); v.c(gc, wB); v.c(wB, wB1)
mA = v.obj(20, 480, "*~"); mB = v.obj(300, 520, "*~"); gSum = v.obj(20, 490, "+~")
v.c(rd, mA, 0, 0); v.c(wA1, mA, 0, 1); v.c(rdB, mB, 0, 0); v.c(wB1, mB, 0, 1)
v.c(mA, gSum, 0, 0); v.c(mB, gSum, 0, 1)'''),
    ("v.c(rd, vca, 0, 0); v.c(venv, vca, 0, 1)", "v.c(gSum, vca, 0, 0); v.c(venv, vca, 0, 1)"),
    # page: MODE label and values
    ("\\\\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 45 8 1 LOOP", "\\\\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 45 8 1 MODE"),
    ('''fLp = r.obj(2900, 220, "f")
r.c(r.obj(2900, 250, "r smp-loop"), fLp, 0, 1)''', '''fLp = r.obj(2900, 220, "f")
r.c(r.obj(2900, 250, "r smp-mode"), fLp, 0, 1)'''),
])

s = open("gensmpl.py").read()
a = s[s.index('lpS = r.obj(2900, 280, "sel 0")'):s.index('\n', s.index('97 55 8 1 on"'))]
s = s.replace(a, '''lpS = r.obj(2900, 280, "sel 0 1 2 3")
r.c(vB, fLp, 0); r.c(fLp, lpS)
for i_, nm_ in enumerate(("one", "str", "s+lp", "loop")):
    r.c(lpS, r.msg(2900 + i_ * 80, 310, f"\\\\; oscOut sendtyped /oled/gPrintln iiiiis 3 97 55 8 1 {nm_}"), i_)
# mode -> loop / stretch flags for the voices
mdR = r.obj(3300, 220, "r smp-mode")
mdT = r.obj(3300, 250, "t f f")
r.c(mdR, mdT)
lpE = r.obj(3300, 280, "expr $f1>=2"); stE_ = r.obj(3400, 280, "expr $f1==1 || $f1==2")
r.c(mdT, stE_, 1); r.c(mdT, lpE, 0)
r.c(lpE, r.obj(3300, 310, "s smp-loop")); r.c(stE_, r.obj(3400, 310, "s smp-stretch"))''')
open("gensmpl.py", "w").write(s)
print("stretch applied")

#!/usr/bin/env python3
"""SUB engine ADSR. In SYNTH with AUX held and SUB active: knob 1 = synth volume (as before), knob 2 = ATTACK
(1..3000 ms), knob 3 = DECAY, also used as RELEASE (10..5000 ms), knob 4 = SUSTAIN (0..100 %).
Amp: ADSR. Filter envelope: attack + decay to 0 (keeps SUB's plucky filter). Defaults reproduce the old sound
(5 ms, ~400 ms, 100 %). Values live in pickup ctx 13 slots 2..4 (pkval 53..55), saved with the project; old
projects get the defaults. The voice switch-off now follows the release."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-subadsr")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


DEF_RAW = "0.04 0.28 1"          # knob values for 5 ms / ~400 ms / 100 %

VOICE_ENV = r'''    # amp env: ADSR (attack to 1, decay to sustain, release = decay time)  (apply_subadsr.py)
    pA = [v.obj(560 + i * 70, 60, f"f {d}") for i, d in enumerate((5, 400, 1))]      # values for the amp
    pF = [v.obj(560 + i * 70, 90, f"f {d}") for i, d in enumerate((5, 400))]         # values for the filter
    pR = v.obj(770, 90, "f 400")                                                     # value for the release
    for i, nm in enumerate(("sub-atk", "sub-dr", "sub-sus")):
        r = v.obj(560 + i * 70, 30, f"r {nm}")
        v.c(r, pA[i], 0, 1)
        if i < 2:
            v.c(r, pF[i], 0, 1)
        if i == 1:
            v.c(r, pR, 0, 1)
    on = v.obj(110, 160, "t b b")
    v.c(mos, on, 1)
    aT = v.obj(110, 185, "t b b b")
    aP = v.obj(110, 215, "pack f f f")
    aM = v.msg(110, 240, "1 \\$1 \\, \\$3 \\$2 \\$1")
    aenv = v.obj(20, 270, "vline~")
    v.c(on, aT, 1)
    v.c(aT, pA[2], 2); v.c(pA[2], aP, 0, 2)
    v.c(aT, pA[1], 1); v.c(pA[1], aP, 0, 1)
    v.c(aT, pA[0], 0); v.c(pA[0], aP, 0, 0)
    v.c(aP, aM); v.c(aM, aenv)
    offB = v.obj(20, 160, "t b")
    rM = v.msg(20, 220, "0 \\$1")
    v.c(mos, offB, 0); v.c(offB, pR); v.c(pR, rM); v.c(rM, aenv)
    # filter env: attack, then decay to 0 (SUB's plucky filter)
    fT = v.obj(160, 200, "t b b")
    fP = v.obj(160, 225, "pack f f")
    fM = v.msg(160, 250, "1 \\$1 \\, 0 \\$2 \\$1")
    fenv = v.obj(160, 280, "vline~")
    v.c(on, fT, 0)
    v.c(fT, pF[1], 1); v.c(pF[1], fP, 0, 1)
    v.c(fT, pF[0], 0); v.c(pF[0], fP, 0, 0)
    v.c(fP, fM); v.c(fM, fenv)'''

OLD_ENV = '''    # amp env
    on = v.obj(110, 160, "t b b")
    atk = v.msg(110, 190, "1 5"); rel = v.msg(20, 190, "0 250")
    aenv = v.obj(20, 220, "line~")
    v.c(mos, on, 1); v.c(on, atk, 1); v.c(atk, aenv); v.c(mos, rel, 0); v.c(rel, aenv)
    # filter env: jump to 1, decay over 400 ms
    fe = v.msg(160, 220, "1 \\\\, 0 400")
    fenv = v.obj(160, 250, "vline~")
    v.c(on, fe, 0); v.c(fe, fenv)'''

SCREEN = r'''
# ---- SUB ADSR (apply_subadsr.py): knob values (raw) for the screen, mapping to the voices
adR = s.obj(1700, 560, "route 2 3 4")
s.c(s.obj(1700, 530, "r sub-adsr"), adR)
adDef = s.msg(1850, 530, "2 0.04 \\, 3 0.28 \\, 4 1")
s.c(s.obj(1850, 500, "loadbang"), adDef); s.c(adDef, adR)
adRaw = []
for i, (ex, snd) in enumerate((("expr int(1+pow($f1 \\, 2)*2999)", "sub-atk"),
                               ("expr int(10+pow($f1 \\, 2)*4990)", "sub-dr"),
                               ("t f", "sub-sus"))):
    raw = s.obj(1700 + i * 120, 620, "f")
    mp = s.obj(1700 + i * 120, 590, ex)
    tt = s.obj(1700 + i * 120, 575, "t f f")
    s.c(adR, tt, i); s.c(tt, raw, 1, 1); s.c(tt, mp, 0)
    s.c(mp, s.obj(1700 + i * 120, 650, f"s {snd}"))
    adRaw.append(raw)
s.c(s.obj(1700, 680, "r sub-adsr"), dirty)
# AUX knobs 2..4 -> SUB ADSR, only while SUB is the active engine
adKsp = s.obj(1500, 600, "spigot")
adIs1 = s.obj(1500, 570, "== 1")
s.c(s.obj(1500, 540, "r synth-engine"), adIs1); s.c(adIs1, adKsp, 0, 1)
s.c(volIn, adKsp, 1)                                   # [route 1] reject = "k v" with k = 2..4
s.c(adKsp, s.obj(1500, 630, "s sub-adsr"))
# project load: ctx 13 knobs 2..4 always reach the ADSR (the engine may not be set yet)
adSet = s.obj(1600, 600, "route 1")
s.c(s.obj(1600, 570, "r synth-vol-set"), adSet)
s.c(adSet, s.obj(1600, 630, "s sub-adsr"), 1)
'''

ROWS_OLD = '''s.c(auxDS, fVol, 0); s.c(fVol, volE); s.c(volE, volP, 1, 1); s.c(volE, volP, 0, 0)'''
ROWS_NEW = r'''auxEng = s.obj(500, 480, "f")
s.c(engT, auxEng, 2, 1)
auxEngS = s.obj(500, 510, "sel 1")
s.c(auxDS, auxEng, 0); s.c(auxEng, auxEngS)
auxNo = s.obj(560, 525, "t b")                         # [sel] reject passes the number: make it a bang
s.c(auxEngS, auxNo, 1); s.c(auxNo, fVol); s.c(fVol, volE); s.c(volE, volP, 1, 1); s.c(volE, volP, 0, 0)
# SUB with AUX: 4 rows VOL ATK D/R SUS (label, value, bar like the engine rows)
fVolRow = s.obj(200, 540, "f 0.8")                     # own copy: banging fVol would also draw the volume page
s.c(volT, fVolRow, 1, 1)
adT = s.obj(300, 540, "t b b b b")
s.c(auxEngS, adT, 0)
ROWDEF = [("VOL", None, "expr int($f1*100+0.5) \\; int($f1*59)"),
          ("ATK", 0, "expr int(1+pow($f1 \\, 2)*2999) \\; int($f1*59)"),
          ("D/R", 1, "expr int(10+pow($f1 \\, 2)*4990) \\; int($f1*59)"),
          ("SUS", 2, "expr int($f1*100+0.5) \\; int($f1*59)")]
for k, (lab, idx, ex) in enumerate(ROWDEF):
    yt, yb, yf = 14 + 12 * k, 13 + 12 * k, 15 + 12 * k
    src = fVolRow if idx is None else adRaw[idx]
    rB = s.obj(300 + k * 110, 570, "t b")
    s.c(adT, rB, 3 - k); s.c(rB, src)
    rE = s.obj(300 + k * 110, 600, ex)
    s.c(src, rE)
    rP = s.obj(300 + k * 110, 630, "pack f f")
    s.c(rE, rP, 1, 1); s.c(rE, rP, 0, 0)
    s.c(rP, s.msg(300 + k * 110, 660 + k * 30,
                  osc5("gPrintln", "iiiiis", f"1 {yt} 8 1 {lab}") + " " +
                  osc5("gPrintln", "iiiiif", f"34 {yt} 8 1 \\$1") + " " +
                  osc5("gBox", "iiiiii", f"64 {yb} 63 9 1") + " " +
                  osc5("gFillArea", "iiiiii", f"66 {yf} \\$2 5 1")))'''

s = open("gensynth.py").read()
assert s.count(OLD_ENV) == 1, "old env"
s = s.replace(OLD_ENV, VOICE_ENV)
assert s.count("    voice_switch(v, inl, fixed=2000)") == 1
s = s.replace("    voice_switch(v, inl, fixed=2000)", '    voice_switch(v, inl, rel="sub-dr")')
# the SUB ADSR block needs volIn and dirty (defined before the screen) and adRaw before the rows
assert s.count(ROWS_OLD) == 1
i = s.index("# 4 parameter rows: label, value, bar")
s = s[:i] + SCREEN.lstrip("\n") + "\n" + s[i:]
s = s.replace(ROWS_OLD, ROWS_NEW)
assert "if False" not in s
open("gensynth.py", "w").write(s)

# pkval defaults for ctx 13 knobs 2..4, legacy projects
edit("gen.py", [(' 0.8 0 0 0 0.8 0 0 0 ', f' 0.8 {DEF_RAW} 0.8 0 0 0 ')])
edit("genproj.py", [
    ('p.c(fixT, fixE5, 1)', '''fixE6 = p.obj(400, 790, "expr pkval[53]+pkval[54]+pkval[55]==0")
fixS6 = p.obj(400, 820, "sel 1")
p.c(fixT, fixE6, 1); p.c(fixE6, fixS6); p.c(fixS6, p.msg(400, 850, "\\\\; pkval 53 ''' + DEF_RAW + '''"))
p.c(fixT, fixE5, 1)'''),
])
print("subadsr applied")

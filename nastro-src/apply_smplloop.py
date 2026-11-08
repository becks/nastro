#!/usr/bin/env python3
"""SMPL sustain loop points and playheads.
- AUX + knob 2 = LOOP START, AUX + knob 3 = LOOP END, relative to START..END (0..100 %), defaults 0 / 100 = the
  old loop over the whole START..END. In MODE loop / s+lp a note plays from START, and from LOOP END on it repeats
  LOOP START..LOOP END while held. The points snap to upward zero crossings like START / END (same chunked search).
- Voice: the read position is a counter ([rpole~] of the time rate): idx = c while c < E, then
  ls + fmod(c - E, B) (E = loop end - START, ls = loop start - START, B = loop length). Every block the counter
  is folded back by B once it is past E + B, so a note held for minutes keeps its precision. Without loop E = 1e9.
- Playheads: each frame of the SMPL page asks the voices ([s smp-ph-ask]); a sounding voice answers with its
  position ([s smp-ph]) and gets an inverted column; while any voice sounds the page asks for the next frame
  ([s smp-phd] -> synth.pd dirty). Loop points: short ticks at the top and bottom of the waveform (loop modes).
- AUX on SMPL: the SMPL page stays (not the volume page), labels VOL / L-ST / L-END. Knob context 42
  (pkval / pkpick 172); knob 1 there is still the synth volume: its raw value is copied into both pickup slots
  (ctx 13 and 42) so the knob picks up correctly in either. Projects: ctx 42 loaded as smp-aux-set (knobs 2, 3);
  older projects (168 values) get the defaults."""
import shutil

for f in ("gensmpl.py", "gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-smplloop")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    open(p, "w").write(s)


# ------------------------------------------------------------------ voice
s = open("gensmpl.py").read()
i0 = s.index("onE = v.obj(250, 220,")
i1 = s.index("v.c(mA, gSum, 0, 0); v.c(mB, gSum, 0, 1)") + len("v.c(mA, gSum, 0, 0); v.c(mB, gSum, 0, 1)")
VOICE = r'''# (apply_smplloop.py) $f1 pitch rate  $f2 START  $f3 END  $f4 sr  $f5 loop  $f6 stretch  $f7 loop start  $f8 loop end
# out: 0 START  1 E (loop end - START)  2 ls (loop start - START)  3 B (loop length)  4 time rate  5 one-shot hold  6 grain offset
LS_ = "max($f2 \\, min($f7 \\, $f8-64))"
LE_ = "min($f8 \\, $f3)"
onE = v.obj(250, 220,
            f"expr $f2 \\; if($f5 \\, max(64 \\, {LE_}-$f2) \\, 1e+09) \\; if($f5 \\, {LS_}-$f2 \\, 0) \\; "
            f"if($f5 \\, max(64 \\, {LE_}-{LS_}) \\, 1e+09) \\; if($f6 \\, 1 \\, $f1) \\; "
            "if($f5 \\, 1e+09 \\, max(1 \\, max(64 \\, $f3-$f2)/$f4*1000/if($f6 \\, 1 \\, $f1)-15))+3 \\; "
            "if($f6 \\, ($f1-1)*2205 \\, 0)")
v.c(v.obj(700, 130, "r smp-stretch"), onE, 0, 5)
v.c(v.obj(400, 130, "r smp-s0"), onE, 0, 1)
v.c(v.obj(500, 130, "r smp-s1"), onE, 0, 2)
v.c(srt, onE, 0, 3)
v.c(v.obj(600, 130, "r smp-loop"), onE, 0, 4)
v.c(v.obj(800, 130, "r smp-l0"), onE, 0, 6)
v.c(v.obj(900, 130, "r smp-l1"), onE, 0, 7)
onT = v.obj(20, 160, "t b")
v.c(mos, onT, 1); v.c(onT, fRate); v.c(fRate, onE)
# envelope now: fade out 1.5 ms, fade in after 3 ms, one-shot fade at the end
env = v.msg(400, 300, "0 1.5 \\, 1 3 3 \\, 0 15 \\$1")
v.c(onE, env, 5)
venv = v.obj(400, 360, "vline~")
v.c(env, venv)
# the new playhead 1.5 ms later (when the voice is silent)
pk = v.obj(250, 260, "pack f f f f f f")
for o_, i_ in ((6, 5), (4, 4), (3, 3), (2, 2), (1, 1), (0, 0)):
    v.c(onE, pk, o_, i_)
held = v.obj(250, 290, "list")
v.c(pk, held, 0, 1)
dl = v.obj(150, 260, "delay 1.5")
v.c(onT, dl)
v.c(dl, held)
apU = v.obj(250, 320, "unpack f f f f f f")
v.c(held, apU)
# counter -> index inside START..END (wrapping into the loop from E on)
cSig = v.obj(150, 360, "sig~ 1")
cRp = v.obj(150, 390, "rpole~ 1")
v.c(cSig, cRp)
idxE = v.obj(150, 430, "expr~ if($v1<$f2 \\, $v1 \\, $f3+fmod($v1-$f2 \\, $f4))")
v.c(cRp, idxE)
v.c(apU, idxE, 1, 1); v.c(apU, idxE, 2, 2); v.c(apU, idxE, 3, 3)
v.c(apU, cSig, 4, 0)
rd = v.obj(20, 460, "tabread4~ smpl")
rdB = v.obj(300, 490, "tabread4~ smpl")
z = v.msg(250, 360, "0")
cZ = v.msg(330, 360, "set 0")
apT = v.obj(250, 340, "t b f")
v.c(apU, apT, 0); v.c(apT, rd, 1, 1); v.c(apT, rdB, 1, 1)
v.c(apT, z, 0); v.c(apT, cZ, 0); v.c(cZ, cRp)
# fold the counter back by one loop once it is a loop past E (keeps float precision on long notes)
fB = v.obj(700, 520, "bang~")
fS = v.obj(700, 550, "snapshot~")
fE = v.obj(700, 580, "expr if($f1>$f2+$f3 \\, $f1-$f3 \\, -1)")
fM = v.obj(700, 610, "moses 0")
v.c(cRp, fS); v.c(fB, fS); v.c(fS, fE)
v.c(apU, fE, 1, 1); v.c(apU, fE, 3, 2)
fSet = v.msg(700, 640, "set \\$1")
v.c(fE, fM); v.c(fM, fSet, 1); v.c(fSet, cRp)
# grains (apply_smplstretch.py): idx = position + grain phase x offset, two heads half a grain apart
gph = v.obj(450, 400, "phasor~ 20.0000")
v.c(z, gph, 0, 1)                                                # grains restart with the note
gD = v.obj(450, 430, "*~ 0"); v.c(apU, gD, 5, 1); v.c(gph, gD)
gB0 = v.obj(560, 430, "+~ 0.5"); gBw = v.obj(560, 460, "wrap~"); gDB = v.obj(560, 490, "*~ 0")
v.c(gph, gB0); v.c(gB0, gBw); v.c(gBw, gDB); v.c(apU, gDB, 5, 1)
iA = v.obj(150, 460, "+~"); iB = v.obj(300, 460, "+~")
v.c(idxE, iA, 0, 0); v.c(gD, iA, 0, 1); v.c(idxE, iB, 0, 0); v.c(gDB, iB, 0, 1)
v.c(iA, rd); v.c(iB, rdB)
gc = v.obj(650, 430, "cos~"); v.c(gph, gc)
wA = v.obj(650, 460, "*~ -0.5"); wA1 = v.obj(650, 490, "+~ 0.5")       # 0.5 - 0.5 cos
wB = v.obj(750, 460, "*~ 0.5"); wB1 = v.obj(750, 490, "+~ 0.5")        # 0.5 + 0.5 cos (half a grain later)
v.c(gc, wA); v.c(wA, wA1); v.c(gc, wB); v.c(wB, wB1)
mA = v.obj(20, 480, "*~"); mB = v.obj(300, 520, "*~"); gSum = v.obj(20, 490, "+~")
v.c(rd, mA, 0, 0); v.c(wA1, mA, 0, 1); v.c(rdB, mB, 0, 0); v.c(wB1, mB, 0, 1)
v.c(mA, gSum, 0, 0); v.c(mB, gSum, 0, 1)
# playhead for the SMPL page: on [s smp-ph-ask] a sounding voice sends its position (sample index)
phT = v.obj(900, 520, "t b b")
v.c(v.obj(900, 490, "r smp-ph-ask"), phT)
phEnv = v.obj(1000, 550, "snapshot~")
phPos = v.obj(900, 550, "snapshot~")
phS0 = v.obj(1100, 550, "f")
v.c(venv, phEnv); v.c(idxE, phPos); v.c(apT, phS0, 1, 1)
phE = v.obj(900, 590, "expr if($f2>0.01 \\, $f1+$f3 \\, -1)")
v.c(phT, phEnv, 1); v.c(phEnv, phE, 0, 1); v.c(phT, phS0, 1); v.c(phS0, phE, 0, 2)
v.c(phT, phPos, 0); v.c(phPos, phE, 0, 0)
phM = v.obj(900, 620, "moses 0")
v.c(phE, phM); v.c(phM, v.obj(900, 650, "s smp-ph"), 1)'''
s = s[:i0] + VOICE + s[i1:]
a = "v.c(onE, holdF, 3, 1)"
assert s.count(a) == 1
s = s.replace(a, "v.c(onE, holdF, 5, 1)")
# searcher: any source object (default: START / END)
a = 'def searcher(x, raw_outlet, send):'
assert s.count(a) == 1
s = s.replace(a, 'def searcher(x, raw_outlet, send, src=None):')
a = '    r.c(rawE, inT, raw_outlet)'
assert s.count(a) == 1
s = s.replace(a, '    r.c(rawE if src is None else src, inT, raw_outlet)')
open("gensmpl.py", "w").write(s)

# ------------------------------------------------------------------ smpl.pd: loop points, page
PAGE = r'''
# ---------------- loop points (apply_smplloop.py): AUX + knobs 2 / 3, relative to START..END
for i_, nm_ in enumerate(("smpla", "smplb", "smps0", "smps1", "smpl0", "smpl1", "smplpf", "smpdlen")):
    r.obj(3600 + i_ * 70, 10, f"v {nm_}")
lpK = r.obj(3600, 60, "route 2 3")
r.c(r.obj(3600, 30, "r smp-lpk"), lpK); r.c(r.obj(3700, 30, "r smp-aux-set"), lpK)
lpDef = r.msg(3800, 60, "2 0 \\, 3 1")
r.c(r.obj(3800, 30, "loadbang"), lpDef); r.c(lpDef, lpK)
lpChg = r.obj(3600, 160, "t b b")                       # 1) raw points now  0) zero-crossing snap 80 ms later
for k_, nm_ in enumerate(("smpla", "smplb")):
    t_ = r.obj(3600 + k_ * 120, 90, "t b f")
    r.c(lpK, t_, k_); r.c(t_, r.obj(3600 + k_ * 120, 120, f"v {nm_}"), 1); r.c(t_, lpChg, 0)
for k_, (src_, nm_) in enumerate((("smp-s0", "smps0"), ("smp-s1", "smps1"))):
    t_ = r.obj(3850 + k_ * 120, 90, "t b f")
    r.c(r.obj(3850 + k_ * 120, 60, f"r {src_}"), t_); r.c(t_, r.obj(3850 + k_ * 120, 120, f"v {nm_}"), 1); r.c(t_, lpChg, 0)
LO_ = "int(smps0+min(smpla \\, smplb)*(smps1-smps0))"
HI_ = f"max({LO_}+64 \\, int(smps0+max(smpla \\, smplb)*(smps1-smps0)))"
lpI = r.obj(3600, 190, f"expr {LO_} \; {HI_}")
r.c(lpChg, lpI, 1)
r.c(lpI, r.obj(3600, 220, "s smp-l0"), 0); r.c(lpI, r.obj(3700, 220, "s smp-l1"), 1)
r.c(lpChg, r.msg(3800, 190, "\; smp-phd bang"), 1)      # redraw the page
lpD = r.obj(3600, 250, "delay 80")
r.c(lpChg, lpD, 0)
lpS = r.obj(3600, 280, f"expr {LO_} \; {HI_}")
r.c(lpD, lpS)
searcher(3600, 0, "smp-l0", lpS)
searcher(4100, 1, "smp-l1", lpS)
r.c(r.obj(4600, 30, "r smp-l0"), r.obj(4600, 60, "v smpl0"))
r.c(r.obj(4700, 30, "r smp-l1"), r.obj(4700, 60, "v smpl1"))
r.c(r.obj(4800, 30, "r smp-loop"), r.obj(4800, 60, "v smplpf"))
r.c(r.obj(4900, 30, "r smp-dlen"), r.obj(4900, 60, "v smpdlen"))
# ---------------- page: playheads (inverted columns) and loop ticks, drawn with the START / END markers
phB = r.obj(3000, 400, "t b b b")                       # 2) none yet  1) ask the voices  0) any -> next frame
r.c(dT, phB, 1)
phAny = r.obj(3100, 460, "f 0")
ph0 = r.msg(3100, 430, "0")
r.c(phB, ph0, 2); r.c(ph0, phAny, 0, 1)
r.c(phB, r.msg(3000, 430, "\; smp-ph-ask bang"), 1)
# next frame while a voice sounds, and for 6 frames after any note (a frame right after the note-on comes
# before the voice has faded in: without this margin the frames would stop there)
r.obj(3100, 400, "v smpgrace")
phT2 = r.obj(3000, 475, "t f b")
phNext = r.obj(3000, 490, "expr $f1 || smpgrace>0")
phAnyS = r.obj(3000, 505, "sel 1")
phDec = r.obj(3150, 505, "expr max(0 \\, smpgrace-1)")
r.c(phB, phAny, 0); r.c(phAny, phT2); r.c(phT2, phNext, 0); r.c(phNext, phAnyS)
r.c(phT2, phDec, 1); r.c(phDec, r.obj(3150, 535, "v smpgrace"))
r.c(phAnyS, r.msg(3000, 520, "\\; smp-phd bang"))
smGr = r.msg(3300, 370, "6")                                   # a note starts the playhead frames
r.c(r.obj(3300, 340, "r smpl-notes"), smGr); r.c(smGr, r.obj(3360, 370, "v smpgrace"))
r.c(smGr, r.msg(3300, 400, "\\; smp-phd bang"))
phIn = r.obj(3200, 400, "t f b")
r.c(r.obj(3200, 370, "r smp-ph"), phIn)
ph1 = r.msg(3300, 430, "1")
r.c(phIn, ph1, 1); r.c(ph1, phAny, 0, 1)
phX = r.obj(3200, 460, "expr 1+int(min(1 \\, $f1/max(1 \\, smpdlen))*125)")
r.c(phIn, phX, 0)
phXg = r.obj(3200, 475, "- 1")                         # black 3-px gutter, white line inside (shorter than START / END)
phP = r.obj(3200, 490, "pack f f")
r.c(phX, phXg); r.c(phXg, phP, 0, 1); r.c(phX, phP, 0, 0)
r.c(phP, r.msg(3200, 520, "\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\$2 12 3 29 0 \\; oscOut sendtyped /oled/gLine iiiiii 3 \\$1 14 \\$1 38 1"))
lmE = r.obj(3400, 400, "expr smplpf")
lmS = r.obj(3400, 430, "sel 1")
r.c(dT, lmE, 1); r.c(lmE, lmS)
lmT = r.obj(3400, 460, "t b b")
r.c(lmS, lmT)
for k_, nm_ in enumerate(("smpl0", "smpl1")):
    e_ = r.obj(3400 + k_ * 120, 490, f"expr 1+int(min(1 \\, {nm_}/max(1 \\, smpdlen))*125)")
    r.c(lmT, e_, k_)
    r.c(e_, r.msg(3400 + k_ * 120, 520, "\; oscOut sendtyped /oled/gLine iiiiii 3 \\$1 10 \\$1 13 1 "
                                         "\; oscOut sendtyped /oled/gLine iiiiii 3 \\$1 39 \\$1 42 1"))
# ---------------- AUX held: VOL / L-ST / L-END instead of STA / END / REL / MODE
axF = r.obj(2500, 130, "f 0")
r.c(r.obj(2560, 100, "r aux"), axF, 0, 1)
axS = r.obj(2500, 145, "sel 0 1")
r.c(axF, axS); r.c(axS, vB, 0)
vAx = r.obj(3000, 160, "t b b b b")
r.c(axS, vAx, 1)
r.c(vAx, r.msg(3000, 190, "\; oscOut sendtyped /oled/gPrintln iiiiis 3 1 45 8 1 VOL \; oscOut sendtyped /oled/gPrintln iiiiis 3 33 45 8 1 L-ST "
                          "\; oscOut sendtyped /oled/gPrintln iiiiis 3 65 45 8 1 L-END"), 3)
vVol = r.obj(3100, 220, "f 1")
r.c(r.obj(3100, 190, "r synth-vol"), vVol, 0, 1)
vVolE = r.obj(3100, 250, "expr int($f1*80+0.5)")
r.c(vAx, vVol, 2); r.c(vVol, vVolE)
r.c(vVolE, r.msg(3100, 280, "\; oscOut sendtyped /oled/gPrintln iiiiif 3 1 55 8 1 \\$1"))
for k_, (nm_, x_) in enumerate((("smpla", 33), ("smplb", 65))):
    e_ = r.obj(3250 + k_ * 120, 250, f"expr int({nm_}*100+0.5)")
    r.c(vAx, e_, 1 - k_)
    r.c(e_, r.msg(3250 + k_ * 120, 280, f"\; oscOut sendtyped /oled/gPrintln iiiiif 3 {x_} 55 8 1 \\$1"))
'''
s = open("gensmpl.py").read()
a = "r.c(dT, vB, 0)"
assert s.count(a) == 1
s = s.replace(a, "r.c(dT, axF, 0)                                     # AUX -> loop labels (apply_smplloop.py)")
a = 'r.save("smpl.pd")'
assert s.count(a) == 1
# axF is created in PAGE: move the dT -> axF connection after it
s = s.replace("r.c(dT, axF, 0)                                     # AUX -> loop labels (apply_smplloop.py)", "")
s = s.replace(a, PAGE + 'r.c(dT, axF, 0)                                     # AUX -> loop labels (apply_smplloop.py)\n' + a)
open("gensmpl.py", "w").write(s)

# ------------------------------------------------------------------ synth.pd: AUX knobs and page for SMPL, redraws
edit("gensynth.py", [
    ('for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live", "syn-lfo-page", "lfo-cfg", "syn-lfo-p"):',
     'for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live", "syn-lfo-page", "lfo-cfg", "syn-lfo-p", "smp-phd"):'),
    ('s.c(volIn, adKsp, 1)                                   # [route 1] reject = "k v" with k = 2..4',
     's.c(volIn, adKsp, 1)                                   # [route 1] reject = "k v" with k = 2..4\n'
     'smKsp = s.obj(1400, 600, "spigot")                     # AUX knobs 2..4 -> SMPL loop points (apply_smplloop.py)\n'
     'smIs4 = s.obj(1400, 570, "== 4")\n'
     's.c(s.obj(1400, 540, "r synth-engine"), smIs4); s.c(smIs4, smKsp, 0, 1)\n'
     's.c(volIn, smKsp, 1); s.c(smKsp, s.obj(1400, 630, "s smp-lpk"))'),
    ('auxEngS = s.obj(500, 510, "sel 1")', 'auxEngS = s.obj(500, 510, "sel 1 4")'),
    ('s.c(auxEngS, auxNo, 1)', 's.c(auxEngS, s.obj(450, 540, "s syn-extra"), 1)    # SMPL + AUX: its own page (apply_smplloop.py)\ns.c(auxEngS, auxNo, 2)'),
    ('volT = s.obj(700, 590, "t f f f")',
     'volT = s.obj(700, 590, "t f f f")\n'
     's.c(volT, s.msg(900, 620, "\\\\; pkval 52 \\\\$1 \\\\; pkval 168 \\\\$1"), 0)   # volume knob pickup in ctx 13 and 42 (apply_smplloop.py)'),
])

# ------------------------------------------------------------------ gen.py / genproj.py: knob context 42
SMDEF = "0.8 0 1 0"
edit("gen.py", [
    ('if($f1==0 && $f5==1 \\\\, 13 \\\\,', 'if($f1==0 && $f5==1 \\\\, if($f3==4 \\\\, 42 \\\\, 13) \\\\,'),
    ('m.obj(560, 530, "table pkval 168")', 'm.obj(560, 530, "table pkval 172")'),
    ('m.obj(680, 530, "table pkpick 168")', 'm.obj(680, 530, "table pkpick 172")'),
    (' 0 0.55 0 0.5 1 0 0 0 \\\\; pkphys', f' 0 0.55 0 0.5 1 0 0 0 {SMDEF} \\\\; pkphys'),
])
s = open("genproj.py").read()
a = '(40, "arp-set"), (41, "arp-aux-set")]'
assert s.count(a) == 1
s = s.replace(a, '(40, "arp-set"), (41, "arp-aux-set"), (42, "smp-aux-set")]')
a = "# projects saved before the arpeggiator:"
assert s.count(a) == 1
SUM = "+".join(f"abs(pkval[{i}]-pkval[168])" for i in range(169, 172))
s = s.replace(a, f'''# projects saved before the SMPL loop points: slots 168..171 all equal (Pd repeats the last value) -> defaults
fixE12 = p.obj(-200, 790, "expr {SUM}==0")
fixS12 = p.obj(-200, 820, "sel 1")
p.c(fixT, fixE12, 1); p.c(fixE12, fixS12); p.c(fixS12, p.msg(-200, 850, "\\\\; pkval 168 {SMDEF}"))
''' + a)
open("genproj.py", "w").write(s)
print("smpl loop points applied")

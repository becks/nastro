#!/usr/bin/env python3
"""Synth LFO, OP-1 style: one LFO per engine, saved with it. On SYNTH, AUX + D5 opens the LFO page of the
current engine (again = back to the parameters; leaving SYNTH closes it). Knobs: TYPE (off sine tri squ ramp
rand drift trem env), RATE (0.05..10 Hz), AMT, DEST (the engine's 4 parameters, PITCH, VOL).
- P1..P4: the parameter moves around its knob value (value = knob + AMT/2 x lfo, clipped); the bar moves, the
  modulated label is shown inverted. Updated every 30 ms (control rate).
- VOL: tremolo on the synth engines' bus. PITCH: vibrato on the same bus (modulated 12 ms delay, so it works for
  every engine). trem = vibrato (20 cents) + tremolo together, DEST ignored. env = level of the audio input.
- Engines now throw~ synth-eng; synth-lfo.pd processes it and throws synth-bus (drums / monitor stay untouched).
- Knob contexts 29..39 (engine id + 29) hold the LFO settings: pkval 116 -> 160, saved with the project."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-lfo")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


NAMES_T = ["off", "sine", "tri", "squ", "ramp", "rand", "drft", "trem", "env"]

# ------------------------------------------------------------------ engines
edit("gensynth.py", [
    ('    th = e.obj(20, 250, "throw~ synth-bus")', '    th = e.obj(20, 250, "throw~ synth-eng")            # -> synth-lfo.pd -> synth-bus'),
    ('''    redT = e.obj(950, 100, "t b b b b")
    e.c(redSp, redT)
''', r'''    redT = e.obj(950, 100, "t b b b b")
    e.c(redSp, redT)
    # LFO (apply_lfo.py): offsets for the 4 parameters, "eng param offset" from synth-lfo.pd
    lfoE = e.obj(1100, 20, f"route {eid}")
    lfoRt = e.obj(1100, 50, "route 0 1 2 3")
    e.c(e.obj(1100, 0, "r syn-lfo-mod"), lfoE); e.c(lfoE, lfoRt)
    # LFO settings of this engine (raw 0..1: TYPE RATE AMT DEST), published while active
    lk = e.obj(20, 420, f"r {name}-lfo-knob")
    lkR = e.obj(20, 450, "route 1 2 3 4")
    lkD = e.msg(120, 420, "1 0 \\, 2 0.3 \\, 3 0.5 \\, 4 0")
    e.c(lk, lkR); e.c(lb, lkD); e.c(lkD, lkR)
    lkB = e.obj(20, 510, "t b b b b")
    lkP = e.obj(20, 570, "pack f f f f")
    for j in range(4):
        st = e.obj(20 + j * 70, 480, "t b f")
        fv = e.obj(20 + j * 70, 540, "f")
        e.c(lkR, st, j); e.c(st, fv, 1, 1); e.c(st, lkB, 0)
        e.c(lkB, fv, j); e.c(fv, lkP, 0, j)
    lkS = e.obj(20, 600, "spigot")
    e.c(eT, lkS, 1, 1); e.c(lkP, lkS)
    lkL = e.obj(20, 630, f"list prepend {eid}")
    e.c(lkS, lkL); e.c(lkL, e.obj(20, 660, "s lfo-cfg"))
    e.c(act, lkB, 0)                                               # becoming active: publish them
'''),
    ('''        e.c(kT, raw, 2, 1); e.c(kT, wE, 1); e.c(wE, rowP, 0, 1)
        e.c(kT, mE, 0); e.c(mE, mT); e.c(mT, snd, 1); e.c(mT, dE, 0); e.c(dE, rowP, 0, 0)''',
     r'''        e.c(kT, raw, 2, 1)
        # LFO (apply_lfo.py): value = clip(knob + offset); sound and bar follow it, the knob stays the centre
        base = e.obj(x + 100, 110, "f")
        smE = e.obj(x, 155, "expr max(0 \\, min(1 \\, $f1+$f2))")
        oT = e.obj(x + 100, 80, "t b f")
        e.c(kT, base, 1, 1); e.c(kT, smE, 0)
        e.c(lfoRt, oT, i); e.c(oT, smE, 1, 1); e.c(oT, base, 0); e.c(base, smE, 0, 0)
        smT = e.obj(x, 185, "t f f")
        e.c(smE, smT); e.c(smT, wE, 1); e.c(wE, rowP, 0, 1)
        e.c(smT, mE, 0); e.c(mE, mT); e.c(mT, snd, 1); e.c(mT, dE, 0); e.c(dE, rowP, 0, 0)'''),
])

# ------------------------------------------------------------------ synth.pd: page, knob routing, screen
edit("gensynth.py", [
    ('''        s.c(r, axLp); s.c(axLp, axRt); s.c(axRt, lp, 0)''',
     r'''        s.c(r, axLp); s.c(axLp, axRt)
        # LFO page open (apply_lfo.py): knobs go to the engine's LFO settings
        pgLp = s.obj(120, y + 30, "list prepend 0"); pgRt = s.obj(120, y + 45, "route 0 1")
        s.c(s.obj(240, y, "r syn-lfo-page"), pgLp, 0, 1)
        s.c(axRt, pgLp, 0); s.c(pgLp, pgRt); s.c(pgRt, lp, 0)
        lfLp = s.obj(1400, y + 30, "list prepend 0")
        lfRt = s.obj(1400, y + 60, "route " + " ".join(str(k_) for k_ in range(len(ENGINES))))
        s.c(pgRt, lfLp, 1); s.c(lfLp, lfRt); s.c(engT, lfLp, 2, 1)
        for k_, (nm_, *_r) in enumerate(ENGINES):
            s.c(lfRt, s.obj(1400 + k_ * 110, y + 90, f"s {nm_}-lfo-knob"), k_)'''),
    ('for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live"):',
     'for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live", "syn-lfo-page", "lfo-cfg", "syn-lfo-p"):'),
    ('mtrI = s.obj(400, 140, "expr if($f1==4 \\\\, 150 \\\\, 50)")',
     r'''mtrI = s.obj(400, 140, "expr if($f1==4 \\, 150 \\, if($f2 \\, 100 \\, 50))")   # LFO moving a row: 10 frames/s
mtrP = s.obj(450, 80, "expr $f1>=0"); mtrPT = s.obj(450, 110, "t b f")
s.c(s.obj(450, 50, "r syn-lfo-p"), mtrP); s.c(mtrP, mtrPT); s.c(mtrPT, mtrI, 1, 1); s.c(mtrPT, mtrI, 0, 0)'''),
    ('s.c(dT, auxD, 2); s.c(auxD, auxDS); s.c(auxDS, engF3, 1)',
     r'''s.c(dT, auxD, 2); s.c(auxD, auxDS)
# LFO page (apply_lfo.py): synth-lfo.pd draws it inside this frame
lpD = s.obj(2000, 450, "f 0")
s.c(s.obj(2000, 420, "r syn-lfo-page"), lpD, 0, 1)
lpDS = s.obj(2000, 480, "sel 1")
s.c(auxDS, lpD, 1); s.c(lpD, lpDS)
s.c(lpDS, s.obj(2000, 510, "s syn-lfo-draw"), 0)
lpNo = s.obj(2100, 510, "t b")
s.c(lpDS, lpNo, 1); s.c(lpNo, engF3)'''),
    ('    s.c(rowsT, n, 3 - k); s.c(n, tg); s.c(tg, lp); s.c(lp, la); s.c(la, m)',
     r'''    s.c(rowsT, n, 3 - k); s.c(n, tg); s.c(tg, lp); s.c(lp, la)
    laT = s.obj(800 + k * 120, 585, "t l l")
    s.c(la, laT); s.c(laT, m, 1)
    mkSp = s.obj(2200 + k * 120, 600, "spigot")                    # label inverted while the LFO moves it
    mkEq = s.obj(2200 + k * 120, 570, f"== {k}")
    s.c(s.obj(2200 + k * 120, 540, "r syn-lfo-p"), mkEq); s.c(mkEq, mkSp, 0, 1); s.c(laT, mkSp, 0)
    s.c(mkSp, s.msg(2200 + k * 120, 630, osc5("gFillArea", "iiiiii", "0 \\$5 33 10 1") + " " +
                    osc5("gPrintln", "iiiiis", "1 \\$1 8 0 \\$2")))'''),
])

# AUX + D5 toggles the page (SYNTH only); leaving SYNTH closes it
s = open("gensynth.py").read()
PAGE = r'''
# ---- LFO page toggle (apply_lfo.py): AUX + D5 on SYNTH; leaving SYNTH closes it
lpKs = s.obj(2000, 40, "sel 74")
lpM = s.obj(2000, 70, "f")
s.c(s.obj(2000, 10, "r aux-key"), lpKs); s.c(s.obj(2100, 40, "r mode"), lpM, 0, 1)
lpM0 = s.obj(2000, 100, "sel 0")
lpF = s.obj(2000, 130, "f 0"); lpNot = s.obj(2050, 160, "== 0")
lpOut = s.obj(2000, 190, "s syn-lfo-page")
s.c(lpKs, lpM); s.c(lpM, lpM0); s.c(lpM0, lpF); s.c(lpF, lpNot); s.c(lpNot, lpF, 0, 1); s.c(lpNot, lpOut)
lpMs = s.obj(2200, 100, "sel 0"); lpZ = s.msg(2250, 130, "0")
s.c(s.obj(2200, 70, "r mode"), lpMs); s.c(lpMs, lpZ, 1); s.c(lpZ, lpF, 0, 1); s.c(lpZ, lpOut)
'''
LFO = r'''

# ---------------------------------------------------------------- synth-lfo-osc.pd (apply_lfo.py)
o = Patch(1000, 600)
o.text(20, 5, "synth-lfo-osc: LFO waveforms - each weighted by lfo-w1..8 (one is 1) - DSP only while TYPE is not off")
o.c(o.obj(20, 40, "r lfo-dsp"), o.obj(20, 70, "switch~"))
ph = o.obj(200, 70, "phasor~ 0.3")
o.c(o.obj(200, 40, "r lfo-rate"), ph)
ox = o.obj(200, 500, "outlet~")


def wgt(k, src, x):
    g_ = o.obj(x, 400, "*~ 0")
    o.c(o.obj(x + 50, 370, f"r lfo-w{k}"), g_, 0, 1); o.c(src, g_); o.c(g_, ox)


cs_ = o.obj(200, 110, "cos~"); o.c(ph, cs_); wgt(1, cs_, 200)                       # sine (and trem)
t1 = o.obj(300, 110, "-~ 0.5"); t2 = o.obj(300, 140, "abs~"); t3 = o.obj(300, 170, "*~ -4"); t4 = o.obj(300, 200, "+~ 1")
o.c(ph, t1); o.c(t1, t2); o.c(t2, t3); o.c(t3, t4); wgt(2, t4, 300)                 # triangle
q1 = o.obj(400, 110, "*~ -1e+06"); q2 = o.obj(400, 140, "+~ 500000"); q3 = o.obj(400, 170, "clip~ -1 1")
o.c(ph, q1); o.c(q1, q2); o.c(q2, q3); wgt(3, q3, 400)                              # square
r1 = o.obj(500, 110, "*~ 2"); r2 = o.obj(500, 140, "-~ 1")
o.c(ph, r1); o.c(r1, r2); wgt(4, r2, 500)                                           # ramp
nz = o.obj(600, 70, "noise~"); sh = o.obj(600, 110, "samphold~")
o.c(nz, sh); o.c(ph, sh, 0, 1); wgt(5, sh, 600)                                     # random (new value each cycle)
d1 = o.obj(700, 140, "lop~ 0.3"); d2 = o.obj(700, 170, "lop~ 0.3"); d3 = o.obj(700, 200, "*~ 2.5")
d4 = o.obj(700, 230, "clip~ -1 1")
rr_ = o.obj(800, 110, "r lfo-rate")
o.c(sh, d1); o.c(d1, d2); o.c(d2, d3); o.c(d3, d4); o.c(rr_, d1, 0, 1); o.c(rr_, d2, 0, 1)
wgt(6, d4, 700)                                                                    # drift (smooth random)
iL = o.obj(850, 40, "r~ inL"); iR = o.obj(950, 40, "r~ inR"); iS = o.obj(850, 70, "+~")
o.c(iL, iS, 0, 0); o.c(iR, iS, 0, 1)
ev = o.obj(850, 100, "env~ 2048 1024")
evE = o.obj(850, 130, "expr max(0 \\, min(1 \\, ($f1-40)/45))*2-1")
evM = o.msg(850, 160, "\\$1 50"); evL = o.obj(850, 190, "line~")
o.c(iS, ev); o.c(ev, evE); o.c(evE, evM); o.c(evM, evL); wgt(8, evL, 850)          # env: input level
o.save("synth-lfo-osc.pd")

# ---------------------------------------------------------------- synth-lfo.pd (apply_lfo.py)
L = Patch(1800, 1000)
L.text(20, 5, "synth-lfo: the active engine LFO - P1..P4 as syn-lfo-mod offsets every 30 ms - PITCH / VOL / trem on the engines bus")
for nm_ in ("lfoE", "lfoT", "lfoTr", "lfoR", "lfoRr", "lfoA", "lfoD", "lfoDr"):
    L.obj(1500, 20 + 25 * ("lfoE lfoT lfoTr lfoR lfoRr lfoA lfoD lfoDr".split().index(nm_)), f"v {nm_}")
up = L.obj(20, 50, "unpack f f f f f")
L.c(L.obj(20, 20, "r lfo-cfg"), up)
dT_ = L.obj(400, 80, "t f f"); dE_ = L.obj(400, 110, "expr int(min($f1 \\, 0.999)*6)")
L.c(up, dT_, 4); L.c(dT_, L.obj(500, 110, "v lfoDr"), 1); L.c(dT_, dE_, 0); L.c(dE_, L.obj(400, 140, "v lfoD"))
L.c(up, L.obj(300, 110, "v lfoA"), 3)
rT_ = L.obj(200, 80, "t f f"); rE_ = L.obj(200, 110, "expr 0.05*pow(200 \\, $f1)")
L.c(up, rT_, 2); L.c(rT_, L.obj(260, 140, "v lfoRr"), 1); L.c(rT_, rE_, 0); L.c(rE_, L.obj(200, 140, "v lfoR"))
tT_ = L.obj(100, 80, "t f f"); tE_ = L.obj(100, 110, "expr int(min($f1 \\, 0.999)*9)")
L.c(up, tT_, 1); L.c(tT_, L.obj(160, 170, "v lfoTr"), 1); L.c(tT_, tE_, 0); L.c(tE_, L.obj(100, 140, "v lfoT"))
eB_ = L.obj(20, 80, "t b f")
L.c(up, eB_, 0); L.c(eB_, L.obj(60, 110, "v lfoE"), 1)
ap = L.obj(20, 200, "t b b b b")
L.c(eB_, ap, 0)
# 1) the modulated parameter changed (engine, dest, type): give the old one back its knob value
keyE = L.obj(600, 230, "expr lfoE*10+if(lfoT>0 && lfoT!=7 && lfoD<4 \\, lfoD \\, 9)")
keyC = L.obj(600, 260, "change -1"); keyT = L.obj(600, 290, "t f b"); oldF = L.obj(600, 320, "f -1")
L.c(ap, keyE, 3); L.c(keyE, keyC); L.c(keyC, keyT); L.c(keyT, oldF, 1); L.c(keyT, oldF, 0, 1)
oT_ = L.obj(600, 350, "t f f"); oM = L.obj(700, 380, "% 10"); oMT = L.obj(700, 410, "t f f"); oLt = L.obj(800, 440, "< 4")
oD = L.obj(600, 380, "/ 10"); oI = L.obj(600, 410, "int"); oP = L.obj(600, 470, "pack f f"); oSp = L.obj(600, 500, "spigot")
L.c(oldF, oT_); L.c(oT_, oM, 1); L.c(oM, oMT); L.c(oMT, oLt, 1); L.c(oLt, oSp, 0, 1); L.c(oMT, oP, 0, 1)
L.c(oT_, oD, 0); L.c(oD, oI); L.c(oI, oP); L.c(oP, oSp)
L.c(oSp, L.msg(600, 530, "\\; syn-lfo-mod \\$1 \\$2 0"))
# 2) DSP and the 30 ms clock on while TYPE is not off
dspE = L.obj(800, 230, "expr lfoT>0"); dspC = L.obj(800, 260, "change -1"); dspT = L.obj(800, 290, "t f f")
mt_ = L.obj(800, 600, "metro 30")
L.c(ap, dspE, 2); L.c(dspE, dspC); L.c(dspC, dspT); L.c(dspT, L.obj(900, 320, "s lfo-dsp"), 1); L.c(dspT, mt_, 0)
# 3) rate, waveform weights, bus depths
pT = L.obj(1000, 230, "t b b b b b b b b b b b b")
L.c(ap, pT, 1)
rtE = L.obj(1000, 260, "expr lfoR")
L.c(pT, rtE, 11); L.c(rtE, L.obj(1000, 290, "s lfo-rate"))
for k_ in (1, 2, 3, 4, 5, 6, 8):                     # trem (7) uses the sine weight
    wE_ = L.obj(1000 + k_ * 70, 320, f"expr lfoT=={k_}" + (" || lfoT==7" if k_ == 1 else ""))
    L.c(pT, wE_, 11 - k_); L.c(wE_, L.obj(1000 + k_ * 70, 350, f"s lfo-w{k_}"))
hdE = L.obj(1000, 400, "expr if(lfoT==7 \\, lfoA*0.25 \\, if(lfoT>0 && lfoD==5 \\, lfoA*0.5 \\, 0))")
hdM = L.msg(1000, 430, "\\$1 30"); hdL = L.obj(1000, 460, "line~")
L.c(pT, hdE, 2); L.c(hdE, hdM); L.c(hdM, hdL)
vaE = L.obj(1200, 400, "expr (lfoT==7 || (lfoT>0 && lfoD==4))*min(10 \\, 1000*lfoA*if(lfoT==7 \\, 0.0116 \\, 0.0293)/(6.2832*lfoR))")
vaM = L.msg(1200, 430, "\\$1 50"); vaL = L.obj(1200, 460, "line~")
L.c(pT, vaE, 1); L.c(vaE, vaM); L.c(vaM, vaL)
wtE = L.obj(1450, 400, "expr lfoT==7 || (lfoT>0 && lfoD==4)")
wtM = L.msg(1450, 430, "\\$1 50"); wtL = L.obj(1450, 460, "line~")
L.c(pT, wtE, 0); L.c(wtE, wtM); L.c(wtM, wtL)
# 4) which row the LFO moves (-1 = none): screen marker, 30 ms offsets on/off
pE = L.obj(20, 600, "expr if(lfoT>0 && lfoT!=7 && lfoD<4 \\, lfoD \\, -1)")
pC = L.obj(20, 630, "change -2")
pOn = L.obj(150, 660, ">= 0")
L.c(ap, pE, 0); L.c(pE, pC); L.c(pC, L.obj(20, 660, "s syn-lfo-p")); L.c(pC, pOn)
# LFO signal
osc = L.obj(400, 700, "synth-lfo-osc")
snap = L.obj(800, 640, "snapshot~")
L.c(osc, snap); L.c(mt_, snap)
pSp = L.obj(800, 670, "spigot")
L.c(pOn, pSp, 0, 1); L.c(snap, pSp)
offE = L.obj(800, 700, "expr lfoA*0.5*$f1")
offT = L.obj(800, 730, "t b b f")
offP = L.obj(800, 790, "pack f f f")
L.c(pSp, offE); L.c(offE, offT); L.c(offT, offP, 2, 2)
eD = L.obj(880, 760, "expr lfoD"); eE = L.obj(800, 760, "expr lfoE")
L.c(offT, eD, 1); L.c(eD, offP, 0, 1); L.c(offT, eE, 0); L.c(eE, offP, 0, 0)
L.c(offP, L.obj(800, 820, "s syn-lfo-mod"))
# the engines' bus: vibrato (modulated delay) cross-faded with the dry sound, then tremolo
cat = L.obj(20, 750, "catch~ synth-eng")
dw = L.obj(200, 780, "delwrite~ synth-vib 40")
xs = L.obj(400, 760, "lop~ 40")
vm = L.obj(400, 790, "*~"); vo = L.obj(400, 820, "+~ 12"); vd = L.obj(400, 850, "vd~ synth-vib")
L.c(cat, dw); L.c(osc, xs); L.c(xs, vm, 0, 0); L.c(vaL, vm, 0, 1); L.c(vm, vo); L.c(vo, vd)
wet = L.obj(400, 880, "*~"); L.c(vd, wet, 0, 0); L.c(wtL, wet, 0, 1)
dI = L.obj(250, 850, "*~ -1"); dI1 = L.obj(250, 870, "+~ 1"); dry = L.obj(20, 880, "*~")
L.c(wtL, dI); L.c(dI, dI1); L.c(cat, dry, 0, 0); L.c(dI1, dry, 0, 1)
g1 = L.obj(600, 760, "-~ 1"); g2 = L.obj(600, 790, "*~"); g3 = L.obj(600, 820, "+~ 1")
L.c(osc, g1); L.c(g1, g2, 0, 0); L.c(hdL, g2, 0, 1); L.c(g2, g3)
mix = L.obj(20, 910, "*~")
L.c(dry, mix, 0, 0); L.c(wet, mix, 0, 0); L.c(g3, mix, 0, 1)
L.c(mix, L.obj(20, 940, "throw~ synth-bus"))
# LFO page, drawn inside synth.pd's frame on [s syn-lfo-draw]
drT = L.obj(1100, 520, "t b b b b b")
L.c(L.obj(1100, 490, "r syn-lfo-draw"), drT)
L.c(drT, L.msg(1100, 550, osc5("gFillArea", "iiiiii", "0 0 35 10 0") + " " + osc5("gPrintln", "iiiiis", "1 1 8 1 LFO")), 4)


def lrow(k, label, outl, raw, x):
    yt, yb, yf = 14 + 12 * k, 13 + 12 * k, 15 + 12 * k
    bT = L.obj(x, 580, "t b b")
    L.c(drT, bT, outl)
    bE = L.obj(x + 60, 610, f"expr int({raw}*59)")
    L.c(bT, bE, 1)
    L.c(bE, L.msg(x + 60, 640, osc5("gPrintln", "iiiiis", f"1 {yt} 8 1 {label}") + " " +
                  osc5("gBox", "iiiiii", f"64 {yb} 63 9 1") + " " + osc5("gFillArea", "iiiiii", f"66 {yf} \\$1 5 1")))
    return bT, yt


bT, yt = lrow(0, "TYPE", 3, "lfoTr", 1100)
tyE = L.obj(1100, 670, "expr lfoT"); tyS = L.obj(1100, 700, "sel " + " ".join(str(i_) for i_ in range(9)))
L.c(bT, tyE, 0); L.c(tyE, tyS)
for i_, nm_ in enumerate(NAMES_T):
    L.c(tyS, L.msg(1100 + i_ * 60, 730 + (i_ % 2) * 20, osc5("gPrintln", "iiiiis", f"34 {yt} 8 1 {nm_}")), i_)
bT, yt = lrow(1, "RATE", 2, "lfoRr", 1300)
raE = L.obj(1300, 670, "expr int(lfoR*100+0.5)/100")
L.c(bT, raE, 0); L.c(raE, L.msg(1300, 700, osc5("gPrintln", "iiiiif", f"34 {yt} 8 1 \\$1")))
bT, yt = lrow(2, "AMT", 1, "lfoA", 1500)
amE = L.obj(1500, 670, "expr int(lfoA*100+0.5)")
L.c(bT, amE, 0); L.c(amE, L.msg(1500, 700, osc5("gPrintln", "iiiiif", f"34 {yt} 8 1 \\$1")))
bT, yt = lrow(3, "DEST", 0, "lfoDr", 1700)
deE = L.obj(1700, 670, "expr lfoD"); deS = L.obj(1700, 700, "sel 4 5")
L.c(bT, deE, 0); L.c(deE, deS)
L.c(deS, L.msg(1700, 730, osc5("gPrintln", "iiiiis", f"34 {yt} 8 1 PTCH")), 0)
L.c(deS, L.msg(1800, 730, osc5("gPrintln", "iiiiis", f"34 {yt} 8 1 VOL")), 1)
deG = L.obj(1900, 730, "text get syn-rows")                   # P1..P4: the engine's parameter name
deSp = L.obj(1900, 760, "list split 1")
L.c(deS, deG, 2); L.c(deG, deSp)
L.c(deSp, L.msg(1900, 790, osc5("gPrintln", "iiiiis", f"34 {yt} 8 1 \\$1")), 0)
L.save("synth-lfo.pd")
'''
s = s.replace('s.save("synth.pd")', PAGE + 's.save("synth.pd")' + LFO.replace("NAMES_T", repr(NAMES_T)))
open("gensynth.py", "w").write(s)

# ------------------------------------------------------------------ gen.py: knob contexts 29..39, instance
s = open("gen.py").read()
i0 = s.index('ctxE = m.obj(560, 660, "expr ')
i1 = s.index('")\n', i0)
line = s[i0:i1]
new = line.replace('"expr ', '"expr if($f1==0 && $f5==0 && $f6==1 \\\\, 29+$f3 \\\\, ', 1) + ")"
s = s[:i0] + new + s[i1:]
DEF = " ".join(["0 0.3 0.5 0"] * 11)
pairs = [
    ('m.c(reng, engTb); m.c(engTb, ctxE, 1, 2); m.c(engTb, ctxE, 0, 0)',
     '''m.c(reng, engTb); m.c(engTb, ctxE, 1, 2); m.c(engTb, ctxE, 0, 0)
lfoPg = m.obj(1100, 630, "r syn-lfo-page")                # SYNTH LFO page: contexts 29 + engine (apply_lfo.py)
lfoTb = m.obj(1100, 660, "t b f")
m.c(lfoPg, lfoTb); m.c(lfoTb, ctxE, 1, 5); m.c(lfoTb, ctxE, 0, 0)'''),
    ('m.obj(560, 530, "table pkval 116")', 'm.obj(560, 530, "table pkval 160")'),
    ('m.obj(680, 530, "table pkpick 116")', 'm.obj(680, 530, "table pkpick 160")'),
    (' 1 1 1 1 1 1 1 1 \\\\; pkphys', f' 1 1 1 1 1 1 1 1 {DEF} \\\\; pkphys'),
    ('m.obj(1620, 680, "mirror")', 'm.obj(1620, 680, "mirror")\nm.obj(1700, 680, "synth-lfo")'),
]
for a, b in pairs:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open("gen.py", "w").write(s)

# ------------------------------------------------------------------ genproj.py: load the LFO contexts
s = open("genproj.py").read()
a = '(27, "dsend-set"), (28, "rsend-set")]'
assert s.count(a) == 1
LCTX = ", ".join(f'({29 + e_}, "{n_}-lfo-knob")' for e_, n_ in enumerate(
    ["fm", "sub", "pluk", "pad", "smpl", "air", "bell", "wave", "strg", "organ", "drone"]))
s = s.replace(a, f'(27, "dsend-set"), (28, "rsend-set"), {LCTX}]')
a = 'fixE9 = p.obj(100, 790,'
assert s.count(a) == 1
SUMA = "+".join(f"abs(pkval[{i}]-pkval[115])" for i in range(116, 138))
SUMB = "+".join(f"abs(pkval[{i}]-pkval[115])" for i in range(138, 160))
s = s.replace(a, f'''# projects saved before the LFO have 116 values: Pd fills the rest of the table with the last one, so all the
# LFO slots equal pkval[115] -> defaults (apply_lfo.py)
fixA10 = p.obj(0, 760, "expr abs(pkval[116]-pkval[115])+abs(pkval[117]-pkval[115])+abs(pkval[118]-pkval[115])+abs(pkval[119]-pkval[115])+abs(pkval[120]-pkval[115])+abs(pkval[121]-pkval[115])+abs(pkval[122]-pkval[115])+abs(pkval[123]-pkval[115])+abs(pkval[124]-pkval[115])+abs(pkval[125]-pkval[115])+abs(pkval[126]-pkval[115])+abs(pkval[127]-pkval[115])+abs(pkval[128]-pkval[115])+abs(pkval[129]-pkval[115])+abs(pkval[130]-pkval[115])+abs(pkval[131]-pkval[115])+abs(pkval[132]-pkval[115])+abs(pkval[133]-pkval[115])+abs(pkval[134]-pkval[115])+abs(pkval[135]-pkval[115])+abs(pkval[136]-pkval[115])+abs(pkval[137]-pkval[115])")
fixB10 = p.obj(0, 775, "expr abs(pkval[138]-pkval[115])+abs(pkval[139]-pkval[115])+abs(pkval[140]-pkval[115])+abs(pkval[141]-pkval[115])+abs(pkval[142]-pkval[115])+abs(pkval[143]-pkval[115])+abs(pkval[144]-pkval[115])+abs(pkval[145]-pkval[115])+abs(pkval[146]-pkval[115])+abs(pkval[147]-pkval[115])+abs(pkval[148]-pkval[115])+abs(pkval[149]-pkval[115])+abs(pkval[150]-pkval[115])+abs(pkval[151]-pkval[115])+abs(pkval[152]-pkval[115])+abs(pkval[153]-pkval[115])+abs(pkval[154]-pkval[115])+abs(pkval[155]-pkval[115])+abs(pkval[156]-pkval[115])+abs(pkval[157]-pkval[115])+abs(pkval[158]-pkval[115])+abs(pkval[159]-pkval[115])")
fixE10 = p.obj(0, 790, "expr $f1+$f2==0")
fixT10 = p.obj(0, 745, "t b b")
fixS10 = p.obj(0, 820, "sel 1")
p.c(fixT, fixT10, 1); p.c(fixT10, fixB10, 1); p.c(fixB10, fixE10, 0, 1); p.c(fixT10, fixA10, 0); p.c(fixA10, fixE10)
p.c(fixE10, fixS10); p.c(fixS10, p.msg(0, 850, "\\\\; pkval 116 {DEF}"))
''' + a)
open("genproj.py", "w").write(s)
print("lfo applied")

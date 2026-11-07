#!/usr/bin/env python3
"""Four more synth engines: 7 WAVE (wavefolder), 8 STRING (plucked string with pick position and body),
9 ORGAN (4 drawbars, key click, gentle leslie), 10 DRONE (two drifting saws, breathing filter, long envelope).
Engine cycle AUX+C in SYNTH: FM SUB PLUK PAD SMPL AIR GLASS WAVE STRING ORGAN DRONE.
Knob contexts 23..26 (pkval / pkpick 92 -> 108); old projects get the defaults."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-moresynth")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


DEFS = {"wave": (0.3, 0.0, 0.5, 0.3), "strg": (0.3, 0.5, 0.25, 0.4),
        "organ": (0.75, 1.0, 0.5, 0.25), "drone": (0.4, 0.4, 0.4, 0.5)}

ENG = r'''    ("wave", 7, "wave-voice", 0.35, [
        ("FOLD", "expr 0.05+pow($f1 \\, 2)*1.45", "wv-fold", DW[0], "expr int($f1*100)"),
        ("SYM", "expr 0.25-$f1*0.25", "wv-sym", DW[1], "expr int((0.25-$f1)*400)"),
        ("ENV", "expr $f1*3", "wv-env", DW[2], "expr int($f1*33)"),
        ("REL", "expr int(10+pow($f1 \\, 2)*3990)", "wv-rel", DW[3], "t f"),
    ]),
    ("strg", 8, "strg-voice", 0.45, [
        ("DAMP", "expr 6*pow(10 \\, 1-$f1)", "st-damp", DS[0], "expr int(100-log10($f1/6)*100)"),
        ("BODY", "t f", "st-body", DS[1], "expr int($f1*100)"),
        ("PICK", "expr 0.04+$f1*0.46", "st-pick", DS[2], "expr int($f1*100)"),
        ("REL", "t f", "st-rel", DS[3], "expr int($f1*100)"),
    ]),
    ("organ", 9, "organ-voice", 0.22, [
        ("16'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d1", DO[0], "expr int(sqrt($f1)*8+0.5)"),
        ("8'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d2", DO[1], "expr int(sqrt($f1)*8+0.5)"),
        ("4'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d3", DO[2], "expr int(sqrt($f1)*8+0.5)"),
        ("2.7'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d4", DO[3], "expr int(sqrt($f1)*8+0.5)"),
    ]),
    ("drone", 10, "drone-voice", 1.6, [
        ("DET", "expr $f1*30", "dn-det", DD[0], "expr int($f1)"),
        ("DRIFT", "t f", "dn-drift", DD[1], "expr int($f1*100)"),
        ("FILT", "expr int(150*pow(40 \\, $f1))", "dn-filt", DD[2], "t f"),
        ("REL", "expr int(500+pow($f1 \\, 2)*14500)", "dn-rel", DD[3], "expr int($f1/100)/10.0"),
    ]),
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS", "WAVE", "STRING", "ORGAN", "DRONE"]'''
for key, tag in (("wave", "DW"), ("strg", "DS"), ("organ", "DO"), ("drone", "DD")):
    for i, v in enumerate(DEFS[key]):
        ENG = ENG.replace(f"{tag}[{i}]", str(v))

VOICES = r'''


def note_env(v, inl, x=20):
    """note-on / note-off split shared by the new voices: returns (tll, mtof, moses)"""
    tll = v.obj(x, 70, "t l l")
    upn = v.obj(x + 180, 100, "unpack f f"); mt = v.obj(x + 180, 130, "mtof")
    upv = v.obj(x, 100, "unpack f f"); mos = v.obj(x + 40, 130, "moses 1")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt); v.c(tll, upv, 0); v.c(upv, mos, 1)
    return tll, mt, mos


def wave_voice():
    """sine -> wavefolder cos(2pi(a*sin + sym)); the fold amount rises at the attack (ENV), DC blocked"""
    v = Patch(900, 700)
    v.text(20, 5, "wave-voice: wavefolder. fold = FOLD * (1 + ENV * attack envelope) - SYM adds even harmonics")
    inl = v.obj(20, 40, "inlet")
    voice_switch(v, inl, rel="wv-rel")
    tll, mt, mos = note_env(v, inl)
    fq = v.obj(200, 160, "sig~"); v.c(mt, fq)
    osc = v.obj(200, 190, "osc~"); v.c(fq, osc)
    # envelopes: amp (velocity, 5 ms attack, REL release) and fold (jump up, decay to 25 % in 400 ms)
    frel = v.obj(550, 100, "f 360")
    v.c(v.obj(550, 70, "r wv-rel"), frel, 0, 1)
    onT = v.obj(110, 160, "t f b")
    vE = v.obj(110, 190, "/ 127")
    am = v.msg(110, 220, "\\$1 5"); rm = v.msg(20, 220, "0 \\$1")
    v.c(mos, onT, 1); v.c(onT, vE, 0); v.c(vE, am)
    offT = v.obj(20, 160, "t b"); v.c(mos, offT, 0); v.c(offT, frel); v.c(frel, rm)
    aenv = v.obj(20, 250, "line~"); v.c(am, aenv); v.c(rm, aenv)
    fm = v.msg(300, 220, "1 2 \\, 0.25 400 2")
    v.c(onT, fm, 1)
    fenv = v.obj(300, 250, "vline~"); v.c(fm, fenv)
    fe = v.obj(300, 280, "*~ 1.5"); fe1 = v.obj(300, 310, "+~ 1")
    v.c(fenv, fe); v.c(v.obj(400, 250, "r wv-env"), fe, 0, 1); v.c(fe, fe1)
    fa = v.obj(300, 340, "*~ 0.48")
    rf = v.obj(450, 310, "r wv-fold")
    v.c(fe1, fa, 0, 0); v.c(rf, fa, 0, 1)
    shp = v.obj(200, 370, "*~"); sym = v.obj(200, 400, "+~ 0.25"); cs = v.obj(200, 430, "cos~")
    v.c(osc, shp, 0, 0); v.c(fa, shp, 0, 1); v.c(shp, sym); v.c(v.obj(330, 370, "r wv-sym"), sym, 0, 1)
    v.c(sym, cs)
    hp = v.obj(200, 460, "hip~ 10"); v.c(cs, hp)
    # small folds come out quiet (amplitude ~ sin(2 pi a)): make up for it
    gE = v.obj(450, 400, "expr 1/max(0.15 \\, sin(6.2832*min($f1 \\, 0.25)))")
    v.c(rf, gE)
    gm = v.obj(200, 490, "*~ 1"); v.c(hp, gm); v.c(gE, gm, 0, 1)
    vca = v.obj(200, 520, "*~"); v.c(gm, vca, 0, 0); v.c(aenv, vca, 0, 1)
    v.c(vca, v.obj(200, 560, "outlet~"))
    v.save("wave-voice.pd")


def strg_voice():
    """Karplus-Strong string: pick-position comb on the excitation, damping lowpass in the loop, body resonances"""
    v = Patch(1000, 800)
    v.text(20, 5, "strg-voice: plucked string. PICK = comb on the excitation - DAMP = loop lowpass - BODY = 3 resonances")
    inl = v.obj(20, 40, "inlet")
    voice_switch(v, inl, fixed=9000, block=16)
    tll, mt, mos = note_env(v, inl)
    perE = v.obj(250, 160, "expr 1000/max($f1 \\, 20)")          # period, ms
    v.c(mt, perE)
    dsig = v.obj(250, 190, "sig~"); v.c(perE, dsig)
    dampE = v.obj(400, 160, "expr min(18000 \\, max($f1 \\, 20)*$f2)")
    v.c(mt, dampE)
    rdT = v.obj(560, 130, "t b f")
    v.c(v.obj(560, 100, "r st-damp"), rdT); v.c(rdT, dampE, 1, 1); v.c(rdT, dampE, 0, 0)
    # excitation: 1 period of noise, louder for short (high) notes
    on = v.obj(110, 160, "t b b")
    v.c(mos, on, 1)
    fex = v.obj(130, 220, "f")
    v.c(perE, fex, 0, 1); v.c(on, fex, 1)
    exP = v.msg(130, 250, "1 \\, 0 \\$1"); v.c(fex, exP)
    exv = v.obj(130, 280, "vline~"); v.c(exP, exv)
    nz = v.obj(20, 280, "noise~"); exm = v.obj(20, 310, "*~")
    v.c(nz, exm, 0, 0); v.c(exv, exm, 0, 1)
    agE = v.obj(330, 250, "expr min(1 \\, sqrt($f1/220))"); v.c(mt, agE)
    # pick position: excitation minus itself delayed by PICK x period
    pkE = v.obj(450, 220, "expr $f1*$f2")
    rpT = v.obj(600, 190, "t b f")
    v.c(v.obj(600, 160, "r st-pick"), rpT); v.c(rpT, pkE, 1, 1); v.c(rpT, pkE, 0, 0)
    v.c(perE, pkE, 0, 0)
    pks = v.obj(450, 250, "sig~"); v.c(pkE, pks)
    exw = v.obj(20, 340, "delwrite~ \\$1-stex 60"); exr = v.obj(450, 340, "vd~ \\$1-stex")
    v.c(exm, exw); v.c(pks, exr)
    exd = v.obj(20, 370, "-~"); v.c(exm, exd, 0, 0); v.c(exr, exd, 0, 1)
    exg = v.obj(20, 400, "*~ 1"); v.c(exd, exg); v.c(agE, exg, 0, 1)
    # loop
    add = v.obj(20, 430, "+~")
    dw = v.obj(20, 460, "delwrite~ \\$1-strg 60"); dr = v.obj(250, 430, "vd~ \\$1-strg")
    lp = v.obj(250, 460, "lop~ 5000"); fbm = v.obj(250, 490, "*~")
    v.c(exg, add, 0, 0); v.c(add, dw)
    v.c(dsig, dr); v.c(dr, lp); v.c(dampE, lp, 0, 1); v.c(lp, fbm, 0, 0); v.c(fbm, add, 0, 1)
    # loop gain: 6 s T60 while held; after release T60 shrinks with REL (0 = mute fast, 1 = ring)
    frel = v.obj(650, 250, "f 0.4")
    v.c(v.obj(650, 220, "r st-rel"), frel, 0, 1)
    onE = v.obj(500, 290, "expr pow(10 \\, -3/(6*max($f1 \\, 20)))")       # $f1 = note frequency
    onM = v.msg(500, 320, "\\$1")
    offE = v.obj(620, 320, "expr pow(10 \\, -3/(6*(0.03+0.97*$f1*$f1)*$f2))")
    offM = v.msg(620, 350, "\\$1 30")
    v.c(mt, offE, 0, 1)
    fOn = v.obj(500, 260, "f 440"); v.c(mt, fOn, 0, 1); v.c(on, fOn, 0); v.c(fOn, onE)
    offB = v.obj(650, 280, "t b")                         # bang: the note-off velocity must not overwrite REL
    v.c(mos, offB, 0); v.c(offB, frel); v.c(frel, offE)
    v.c(onE, onM); v.c(offE, offM)
    fbl = v.obj(500, 380, "line~"); v.c(onM, fbl); v.c(offM, fbl); v.c(fbl, fbm, 0, 1)
    # body: 3 fixed resonances mixed in by BODY
    b1 = v.obj(250, 540, "bp~ 110 3"); b2 = v.obj(350, 540, "bp~ 240 3"); b3 = v.obj(450, 540, "bp~ 520 4")
    for b in (b1, b2, b3):
        v.c(dr, b)
    bs = v.obj(250, 570, "+~"); bs2 = v.obj(250, 600, "+~")
    v.c(b1, bs, 0, 0); v.c(b2, bs, 0, 1); v.c(bs, bs2, 0, 0); v.c(b3, bs2, 0, 1)
    rb = v.obj(600, 540, "r st-body")
    bwE = v.obj(600, 570, "expr $f1*2.5 \\; 1-$f1*0.5")
    v.c(rb, bwE)
    bw = v.obj(250, 630, "*~ 1.25"); dry = v.obj(150, 630, "*~ 0.75")
    v.c(bs2, bw); v.c(bwE, bw, 0, 1); v.c(dr, dry); v.c(bwE, dry, 1, 1)
    mix = v.obj(150, 660, "+~"); v.c(dry, mix, 0, 0); v.c(bw, mix, 0, 1)
    v.c(mix, v.obj(150, 700, "outlet~"))
    v.save("strg-voice.pd")


def organ_voice():
    """4 drawbars (16' 8' 4' 2 2/3'), key click, gentle leslie (vibrato + tremolo)"""
    v = Patch(1000, 700)
    v.text(20, 5, "organ-voice: drawbars 16' 8' 4' 2 2/3' - key click - gentle leslie")
    inl = v.obj(20, 40, "inlet")
    voice_switch(v, inl, fixed=100)
    tll, mt, mos = note_env(v, inl)
    fq = v.obj(200, 160, "sig~"); v.c(mt, fq)
    # leslie: slow vibrato (+-0.25 %) and tremolo (15 %), its own speed per voice
    lr = v.obj(700, 100, "random 1000"); lE = v.obj(700, 130, "expr 0.7+$f1/2500")
    v.c(v.obj(700, 70, "loadbang"), lr); v.c(lr, lE)
    lfo = v.obj(700, 160, "osc~ 0.8"); v.c(lE, lfo)
    vib = v.obj(700, 190, "*~ 0.0025"); vib1 = v.obj(700, 220, "+~ 1")
    v.c(lfo, vib); v.c(vib, vib1)
    trm = v.obj(800, 190, "*~ 0.075"); trm1 = v.obj(800, 220, "+~ 0.925")
    v.c(lfo, trm); v.c(trm, trm1)
    fv = v.obj(200, 190, "*~"); v.c(fq, fv, 0, 0); v.c(vib1, fv, 0, 1)
    mix = v.obj(200, 400, "+~")
    prev = None
    for i, (ratio, snd) in enumerate(((0.5, "og-d1"), (1, "og-d2"), (2, "og-d3"), (3, "og-d4"))):
        X = 200 + i * 120
        fr = v.obj(X, 230, f"*~ {ratio}"); o = v.obj(X, 260, "osc~"); g = v.obj(X, 290, "*~ 0")
        v.c(fv, fr); v.c(fr, o); v.c(o, g); v.c(v.obj(X + 50, 260, f"r {snd}"), g, 0, 1)
        if prev is None:
            prev = g
        else:
            s = v.obj(X, 330, "+~"); v.c(prev, s, 0, 0); v.c(g, s, 0, 1); prev = s
    # key click: 4 ms of high-passed noise at the note-on
    on = v.obj(110, 160, "t b b"); v.c(mos, on, 1)
    ck = v.msg(500, 400, "1 \\, 0 4"); v.c(on, ck, 1)
    ckv = v.obj(500, 430, "vline~"); v.c(ck, ckv)
    nz = v.obj(600, 400, "noise~"); ckh = v.obj(600, 430, "hip~ 1500")
    ckm = v.obj(500, 460, "*~"); ckg = v.obj(500, 490, "*~ 0.12")
    v.c(nz, ckh); v.c(ckh, ckm, 0, 0); v.c(ckv, ckm, 0, 1); v.c(ckm, ckg)
    # gate envelope: 4 ms in, 60 ms out (organs ignore velocity)
    am = v.msg(110, 220, "1 4"); rm = v.msg(20, 220, "0 60")
    v.c(on, am, 0)
    v.c(mos, rm, 0)
    env = v.obj(20, 250, "line~"); v.c(am, env); v.c(rm, env)
    tr = v.obj(200, 430, "*~"); v.c(prev, tr, 0, 0); v.c(trm1, tr, 0, 1)
    vca = v.obj(200, 460, "*~"); v.c(tr, vca, 0, 0); v.c(env, vca, 0, 1)
    out = v.obj(200, 520, "+~"); v.c(vca, out, 0, 0); v.c(ckg, out, 0, 1)
    v.c(out, v.obj(200, 560, "outlet~"))
    v.save("organ-voice.pd")


def drone_voice():
    """two saws detuned apart, each drifting slowly; lowpass that breathes; attack = half the release"""
    v = Patch(1000, 700)
    v.text(20, 5, "drone-voice: 2 drifting detuned saws -> breathing lowpass - long envelope (attack = REL / 2)")
    inl = v.obj(20, 40, "inlet")
    voice_switch(v, inl, rel="dn-rel")
    tll, mt, mos = note_env(v, inl)
    fq = v.obj(200, 160, "sig~"); v.c(mt, fq)
    onT = v.obj(110, 160, "t b"); v.c(mos, onT, 1)
    atE = v.obj(110, 190, "expr max(300 \\, $f1/2)")
    fat =v.obj(450, 160, "f 4100"); v.c(v.obj(450, 130, "r dn-rel"), fat, 0, 1)
    v.c(onT, fat); v.c(fat, atE)
    am = v.msg(110, 220, "1 \\$1"); v.c(atE, am)
    offT = v.obj(20, 160, "t b"); v.c(mos, offT, 0)
    rm = v.msg(20, 220, "0 \\$1")
    frl = v.obj(20, 190, "f 4100"); v.c(v.obj(20, 130, "r dn-rel"), frl, 0, 1)
    v.c(offT, frl); v.c(frl, rm)
    env = v.obj(20, 250, "line~"); env2 = v.obj(20, 280, "*~")
    v.c(am, env); v.c(rm, env); v.c(env, env2, 0, 0); v.c(env, env2, 0, 1)      # squared: softer swell
    # drift LFOs, own speeds per voice
    lb = v.obj(700, 70, "loadbang")
    rr = v.obj(700, 100, "t b b b")
    v.c(lb, rr)
    lfos = []
    for j, (lo, span) in enumerate(((0.05, 0.12), (0.07, 0.15), (0.03, 0.08))):
        r = v.obj(700 + j * 100, 130, "random 1000"); e = v.obj(700 + j * 100, 160, f"expr {lo}+$f1*{span}/1000")
        o = v.obj(700 + j * 100, 190, "osc~ 0.1")
        v.c(rr, r, j); v.c(r, e); v.c(e, o)
        lfos.append(o)
    # detune +-DET/2 cents, drift up to +-15 cents (DRIFT)
    dtE = v.obj(400, 130, "expr pow(2 \\, $f1/2400) \\; pow(2 \\, -$f1/2400)")
    v.c(v.obj(400, 100, "r dn-det"), dtE)
    drE = v.obj(550, 190, "expr $f1*0.0087")                 # 15 cents ~ 0.87 %
    v.c(v.obj(550, 160, "r dn-drift"), drE)
    saws = []
    for j in range(2):
        X = 200 + j * 160
        dm = v.obj(X, 230, "*~ 0"); dm1 = v.obj(X, 260, "+~ 1")
        v.c(lfos[j], dm); v.c(drE, dm, 0, 1); v.c(dm, dm1)
        f1 = v.obj(X, 290, "*~ 1"); v.c(fq, f1, 0, 0); v.c(dtE, f1, j, 1)
        f2 = v.obj(X, 320, "*~"); v.c(f1, f2, 0, 0); v.c(dm1, f2, 0, 1)
        ph = v.obj(X, 350, "phasor~"); v.c(f2, ph)
        saws.append(ph)
    sm = v.obj(200, 390, "+~"); sm1 = v.obj(200, 420, "-~ 1")
    v.c(saws[0], sm, 0, 0); v.c(saws[1], sm, 0, 1); v.c(sm, sm1)
    # breathing filter: cutoff * (1 + 0.4 * slow LFO * DRIFT-ish), resonant lowpass
    cf = v.obj(500, 390, "sig~ 900")
    v.c(v.obj(500, 360, "r dn-filt"), cf)
    br = v.obj(650, 390, "*~ 0.4"); br1 = v.obj(650, 420, "+~ 1")
    v.c(lfos[2], br); v.c(br, br1)
    cfm = v.obj(500, 450, "*~"); v.c(cf, cfm, 0, 0); v.c(br1, cfm, 0, 1)
    vf = v.obj(200, 480, "vcf~ 1.5")
    v.c(sm1, vf, 0, 0); v.c(cfm, vf, 0, 1)
    lp = v.obj(200, 510, "lop~ 6000"); v.c(vf, lp, 1)
    g = v.obj(200, 540, "*~ 0.5"); v.c(lp, g)
    vca = v.obj(200, 570, "*~"); v.c(g, vca, 0, 0); v.c(env2, vca, 0, 1)
    v.c(vca, v.obj(200, 610, "outlet~"))
    v.save("drone-voice.pd")


wave_voice(); strg_voice(); organ_voice(); drone_voice()'''


edit("gensynth.py", [
    ('''    ], 6),
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS"]''', '''    ], 6),
''' + ENG),
    ('air_voice(); bell_voice()', 'air_voice(); bell_voice()' + VOICES),
    ('(FM SUB PLUK PAD SMPL AIR GLASS)', '(FM SUB PLUK PAD SMPL AIR GLASS WAVE STRING ORGAN DRONE)'),
    ('"36 0 34 10 1"', '"36 0 40 10 1"'),          # engine name box wide enough for STRING
])

ALLDEF = " ".join(str(v) for k in ("wave", "strg", "organ", "drone") for v in DEFS[k])
edit("gen.py", [
    ('m.obj(960, 720, "synth-bell")', 'm.obj(960, 720, "synth-bell")\nm.obj(720, 760, "synth-wave")\nm.obj(800, 760, "synth-strg")\n'
                                     'm.obj(880, 760, "synth-organ")\nm.obj(960, 760, "synth-drone")'),
    ('m.obj(560, 530, "table pkval 92")', 'm.obj(560, 530, "table pkval 108")'),
    ('m.obj(680, 530, "table pkpick 92")', 'm.obj(680, 530, "table pkpick 108")'),
    ('if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3)', 'if($f3>=7 \\\\, 16+$f3 \\\\, if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3))'),
    ('0 0.5 0 0 \\\\; pkphys', f'0 0.5 0 0 {ALLDEF} \\\\; pkphys'),
])

edit("genproj.py", [
    ('(22, "comp-set")]', '(22, "comp-set"), (23, "wave-knob"), (24, "strg-knob"), (25, "organ-knob"), (26, "drone-knob")]'),
    ('p.c(fixT, fixE7, 1)', '''fixE8 = p.obj(200, 790, "expr ''' + "+".join(f"pkval[{i}]" for i in range(92, 108)) + '''==0")
fixS8 = p.obj(200, 820, "sel 1")
p.c(fixT, fixE8, 1); p.c(fixE8, fixS8); p.c(fixS8, p.msg(200, 850, "\\\\; pkval 92 ''' + ALLDEF + '''"))
p.c(fixT, fixE7, 1)'''),
])
print("more synths applied")

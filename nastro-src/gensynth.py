# exec'd from gen.py (last): synth engines + SYNTH dispatcher/screen
# engines: 0 FM, 1 SUB, 2 PLUK, 3 PAD. Each engine: 4 voices, 4 knob params,
# publishes its rows ("row label value barwidth") to [s syn-row] while active,
# and switches its DSP off 4 s after it stops being the active engine.

def osc5(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


ENGINES = [
    # name, id, voice, gain, params: (label, map expr, send, default knob, display expr)
    ("fm", 0, "fm-voice", 0.3, [
        ("RATIO", "expr int($f1*15+1)*0.5", "fm-ratio", 0.1, "t f"),
        ("INDEX", "expr int(pow($f1 \\, 2)*1000)/100", "fm-index", 0.5, "t f"),
        ("ATK", "expr int(1+pow($f1 \\, 3)*1999)", "fm-attack", 0.0, "t f"),
        ("REL", "expr int(10+pow($f1 \\, 2)*3990)", "fm-release", 0.3, "t f"),
    ]),
    ("sub", 1, "sub-voice", 0.9, [
        ("CUT", "expr int(60*pow(2 \\, $f1*7.5))", "sub-cut", 0.45, "t f"),
        ("RES", "expr 0.7+pow($f1 \\, 2)*11", "sub-res", 0.3, "expr int($f1*10)/10"),
        ("ENV", "expr $f1*5", "sub-env", 0.5, "expr int($f1*20)"),
        ("DET", "expr pow(2 \\, $f1*30/1200)", "sub-det", 0.3, "expr int(log($f1)/log(2)*1200+0.5)"),
    ]),
    ("pluk", 2, "pluk-voice", 0.5, [
        ("DECAY", "expr 0.1*pow(2 \\, $f1*6.3)", "pk-dec", 0.6, "expr int($f1*10)/10"),
        ("BRITE", "expr 4*pow(2 \\, $f1*4)", "pk-brite", 0.6, "expr int(log($f1/4)/log(2)*25+0.5)"),
        ("PICK", "expr pow(2 \\, $f1*5)", "pk-pick", 0.6, "expr int(log($f1)/log(2)*20+0.5)"),
        ("REL", "t f", "pk-rel", 0.4, "expr int($f1*100)"),
    ]),
    ("pad", 3, "pad-voice", 0.3, [
        ("ATK", "expr int(10+pow($f1 \\, 2)*2990)", "pd-atk", 0.5, "t f"),
        ("REL", "expr int(50+pow($f1 \\, 2)*4950)", "pd-rel", 0.6, "t f"),
        ("TONE", "expr int(200*pow(2 \\, $f1*5.3))", "pd-tone", 0.5, "t f"),
        ("SPRD", "expr $f1*25", "pd-spread", 0.5, "expr int($f1)"),
    ]),
    ("smpl", 4, "smpl-voice", 0.8, [
        ("START", "t f", "smp-start", 0.0, "expr int($f1*100)"),
        ("END", "t f", "smp-end", 1.0, "expr int($f1*100)"),
        ("REL", "expr int(5+pow($f1 \\, 2)*2995)", "smp-rel", 0.3, "t f"),
        ("MODE", "expr int(min($f1 \\, 0.999)*4)", "smp-mode", 0.0, "t f"),
    ]),
    ("air", 5, "air-voice", 1.8, [
        ("ATK", "expr int(10+pow($f1 \\, 2)*3990)", "air-atk", 0.5, "t f"),
        ("REL", "expr int(100+pow($f1 \\, 2)*7900)", "air-rel", 0.5, "t f"),
        ("Q", "expr 2*pow(30 \\, $f1)", "air-q", 0.5, "expr int($f1)"),
        ("MOVE", "t f", "air-mot", 0.4, "expr int($f1*100)"),
    ]),
    ("bell", 6, "bell-voice", 0.3, [
        ("DECAY", "expr int(300+pow($f1 \\, 2)*14700)", "bell-dec", 0.4, "expr int($f1/100)/10.0"),
        ("BRITE", "expr 0.2+$f1*0.8", "bell-brite", 0.5, "expr int($f1*100)"),
        ("INHAR", "t f", "bell-str", 0.7, "expr int($f1*100)"),
        ("BEAT", "expr $f1*2.5", "bell-beat", 0.3, "expr int($f1*10)/10.0"),
    ], 6),
    ("wave", 7, "wave-voice", 0.35, [
        ("FOLD", "expr 0.05+pow($f1 \\, 2)*1.45", "wv-fold", 0.3, "expr int($f1*100)"),
        ("SYM", "expr 0.25-$f1*0.25", "wv-sym", 0.0, "expr int((0.25-$f1)*400)"),
        ("ENV", "expr $f1*3", "wv-env", 0.5, "expr int($f1*33)"),
        ("REL", "expr int(10+pow($f1 \\, 2)*3990)", "wv-rel", 0.3, "t f"),
    ]),
    ("strg", 8, "strg-voice", 0.45, [
        ("DAMP", "expr 6*pow(10 \\, 1-$f1)", "st-damp", 0.3, "expr int(100-log10($f1/6)*100)"),
        ("BODY", "t f", "st-body", 0.5, "expr int($f1*100)"),
        ("PICK", "expr 0.04+$f1*0.46", "st-pick", 0.25, "expr int($f1*100)"),
        ("REL", "t f", "st-rel", 0.4, "expr int($f1*100)"),
    ]),
    ("organ", 9, "organ-voice", 0.22, [
        ("16'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d1", 0.75, "expr int(sqrt($f1)*8+0.5)"),
        ("8'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d2", 1.0, "expr int(sqrt($f1)*8+0.5)"),
        ("4'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d3", 0.5, "expr int(sqrt($f1)*8+0.5)"),
        ("2.7'", "expr pow(int($f1*8+0.5)/8 \\, 2)", "og-d4", 0.25, "expr int(sqrt($f1)*8+0.5)"),
    ]),
    ("drone", 10, "drone-voice", 1.6, [
        ("DET", "expr $f1*30", "dn-det", 0.4, "expr int($f1)"),
        ("DRIFT", "t f", "dn-drift", 0.4, "expr int($f1*100)"),
        ("FILT", "expr int(150*pow(40 \\, $f1))", "dn-filt", 0.4, "t f"),
        ("REL", "expr int(500+pow($f1 \\, 2)*14500)", "dn-rel", 0.5, "expr int($f1/100)/10.0"),
    ]),
    ("piano", 11, "piano-voice", 0.25, [                                          # apply_piano.py
        ("FELT", "t f", "piano-felt", 0.7, "expr int($f1*100)"),
        ("DECAY", "expr int(1500+pow($f1 \\, 2)*18500)", "piano-dec", 0.5, "expr int($f1/100)/10.0"),
        ("LOFI", "t f", "piano-lofi", 0.4, "expr int($f1*100)"),
        ("NOISE", "t f", "piano-noise", 0.5, "expr int($f1*100)"),
    ], 6),
    ("mallet", 12, "mallet-voice", 0.2, [                                       # apply_mallet.py
        ("TYPE", "expr int(min($f1 \\, 0.999)*10)", "mlt-type", 0.05, "expr $f1+1"),
        ("HARD", "t f", "mlt-hard", 0.5, "expr int($f1*100)"),
        ("DECAY", "expr 0.25*pow(16 \\, $f1)", "mlt-dec", 0.5, "expr int($f1*100)/100"),
        ("REL", "t f", "mlt-rel", 1.0, "expr int($f1*100)"),
    ], 6),
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS", "WAVE", "STRING", "ORGAN", "DRONE", "PIANO", "MALLET"]


# ---------------------------------------------------------------- voices
def sub_voice():
    v = Patch(800, 600)
    v.text(20, 5, "sub-voice: 2 detuned saws -> resonant lowpass (vcf~) with filter envelope")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
    voice_switch(v, inl, rel="sub-dr")
    upn = v.obj(200, 100, "unpack f f"); mt = v.obj(200, 130, "mtof"); fq = v.obj(200, 160, "sig~")
    upv = v.obj(20, 100, "unpack f f"); mos = v.obj(60, 130, "moses 1")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt); v.c(mt, fq); v.c(tll, upv, 0); v.c(upv, mos, 1)
    # amp env: ADSR (attack to 1, decay to sustain, release = decay time)  (apply_subadsr.py)
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
    v.c(fP, fM); v.c(fM, fenv)
    # oscillators
    rdet = v.obj(400, 130, "r sub-det")
    f2 = v.obj(330, 190, "*~ 1")
    v.c(fq, f2); v.c(rdet, f2, 0, 1)
    p1 = v.obj(200, 220, "phasor~"); p2 = v.obj(330, 220, "phasor~")
    v.c(fq, p1); v.c(f2, p2)
    s = v.obj(200, 250, "+~"); s1 = v.obj(200, 280, "-~ 1")
    v.c(p1, s, 0, 0); v.c(p2, s, 0, 1); v.c(s, s1)
    # cutoff = base + env * base*(2^amt - 1)
    rcut = v.obj(500, 130, "r sub-cut"); renv = v.obj(600, 130, "r sub-env")
    kE = v.obj(500, 190, "expr $f1*(pow(2 \\, $f2)-1)")
    tcut = v.obj(500, 160, "t f f")
    v.c(rcut, tcut); v.c(tcut, kE, 0, 0)
    renvT = v.obj(600, 160, "t b f")
    v.c(renv, renvT); v.c(renvT, kE, 1, 1); v.c(renvT, kE, 0, 0)
    fk = v.obj(160, 310, "*~ 0"); fb = v.obj(160, 340, "+~ 1000")
    v.c(fenv, fk); v.c(kE, fk, 0, 1); v.c(fk, fb); v.c(tcut, fb, 1, 1)
    fcl = v.obj(160, 370, "clip~ 20 15000")
    v.c(fb, fcl)
    rres = v.obj(400, 340, "r sub-res")
    vcf = v.obj(200, 400, "vcf~ 1")
    v.c(s1, vcf, 0, 0); v.c(fcl, vcf, 0, 1); v.c(rres, vcf, 0, 2)
    g = v.obj(200, 440, "*~ 0.5")
    vca = v.obj(200, 470, "*~")
    v.c(vcf, g, 1); v.c(g, vca, 0, 0); v.c(aenv, vca, 0, 1)
    out = v.obj(200, 510, "outlet~")
    v.c(vca, out)
    v.save("sub-voice.pd")


PLUKC = float(__import__("os").environ.get("PLUKC", "0"))
PLUKK = float(__import__("os").environ.get("PLUKK", "0"))


def pluk_voice():
    v = Patch(800, 600)
    v.text(20, 5, "pluk-voice: Karplus-Strong string. switch~ 16 so the loop can be as short as 16 samples")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
    voice_switch(v, inl, fixed=9000, block=16)
    upn = v.obj(250, 100, "unpack f f"); mt = v.obj(250, 130, "mtof")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt)
    # loop lowpass follows the note (cutoff = f * BRITE factor); its phase delay is
    # subtracted from the delay line so the string stays in tune
    perE = v.obj(250, 160, ("expr min(18000 \\, max($f1 \\, 20)*$f2) \; 1000/max($f1 \\, 20)-PLUKC*atan(max($f1 \\, 20)/min(18000 \\, max($f1 \\, 20)*$f2))*1000/(6.2832*max($f1 \\, 20))+PLUKK*1000/44100").replace("PLUKC", str(PLUKC)).replace("PLUKK", str(PLUKK)))
    perT = v.obj(250, 190, "t f f")
    dsig = v.obj(250, 220, "sig~")
    rbr = v.obj(560, 130, "r pk-brite")
    rbrT = v.obj(560, 160, "t b f")
    v.c(mt, perE); v.c(perE, perT, 1); v.c(perT, dsig, 0)
    v.c(rbr, rbrT); v.c(rbrT, perE, 1, 1); v.c(rbrT, perE, 0, 0)
    upv = v.obj(20, 100, "unpack f f"); mos = v.obj(60, 130, "moses 1")
    v.c(tll, upv, 0); v.c(upv, mos, 1)
    # excitation: noise burst of 2 periods, coloured by the pick lowpass
    exE = v.obj(130, 190, "expr $f1*2")
    exP = v.msg(130, 250, "1 \\, 0 \\$1")
    v.c(perT, exE, 1)
    on = v.obj(110, 160, "t b b")
    fex = v.obj(130, 220, "f")
    v.c(mos, on, 1); v.c(exE, fex, 0, 1); v.c(on, fex, 1); v.c(fex, exP)
    exv = v.obj(130, 280, "vline~")
    nz = v.obj(20, 280, "noise~")
    exm = v.obj(20, 310, "*~")
    v.c(exP, exv); v.c(nz, exm, 0, 0); v.c(exv, exm, 0, 1)
    # pick tone follows the note; excitation gets louder for high (short) notes
    rpick = v.obj(120, 340 - 60, "r pk-pick")
    rpickT = v.obj(120, 310, "t b f")
    pkE = v.obj(330, 280, "expr min(18000 \\, $f1*$f2)")
    exl = v.obj(20, 340, "lop~ 3000")
    v.c(mt, pkE); v.c(rpick, rpickT); v.c(rpickT, pkE, 1, 1); v.c(rpickT, pkE, 0, 0); v.c(pkE, exl, 0, 1)
    agE = v.obj(330, 250, "expr min(1 \\, sqrt($f1/220))")
    exg = v.obj(20, 360, "*~ 1")
    v.c(mt, agE); v.c(agE, exg, 0, 1)
    v.c(exm, exl); v.c(exl, exg)
    # loop
    add = v.obj(20, 380, "+~")
    dw = v.obj(20, 410, "delwrite~ \\$1-pluk 60")
    dr = v.obj(250, 380, "vd~ \\$1-pluk")
    lp = v.obj(250, 410, "lop~ 5000")
    fbm = v.obj(250, 440, "*~")
    v.c(exg, add, 0, 0); v.c(add, dw)
    v.c(dsig, dr); v.c(dr, lp); v.c(perE, lp, 0, 1); v.c(lp, fbm, 0, 0); v.c(fbm, add, 0, 1)
    # feedback: decay while held, shorter after release (pk-rel: 0 = mute fast, 1 = ring)
    # loop gain from the decay time (T60, seconds) and the note frequency, so every
    # note rings for the same time; after release the T60 shrinks by pk-rel
    rdec = v.obj(450, 100, "r pk-dec"); rrel = v.obj(550, 100, "r pk-rel")
    fdOn = v.obj(450, 190, "f 1"); fdOff = v.obj(520, 250, "f 1"); frel = v.obj(600, 220, "f 0.4")
    v.c(rdec, fdOn, 0, 1); v.c(rdec, fdOff, 0, 1); v.c(rrel, frel, 0, 1)
    onE = v.obj(450, 250, "expr pow(10 \\, -3/(max($f1 \\, 0.01)*$f2))")
    onMsg = v.msg(450, 280, "\\$1")
    offE = v.obj(520, 280, "expr pow(10 \\, -3/(max($f1 \\, 0.01)*(0.05+0.95*$f2*$f2)*$f3))")
    offMsg = v.msg(520, 310, "\\$1 30")
    fbl = v.obj(450, 340, "line~")
    v.c(mt, onE, 0, 1); v.c(mt, offE, 0, 2)
    v.c(on, fdOn, 0); v.c(fdOn, onE); v.c(onE, onMsg); v.c(onMsg, fbl)
    offT = v.obj(520, 190, "t b b")
    v.c(mos, offT, 0); v.c(offT, frel, 1); v.c(frel, offE, 0, 1); v.c(offT, fdOff, 0); v.c(fdOff, offE, 0, 0)
    v.c(offE, offMsg); v.c(offMsg, fbl); v.c(fbl, fbm, 0, 1)
    out = v.obj(250, 480, "outlet~")
    v.c(dr, out)
    v.save("pluk-voice.pd")


def pad_voice():
    v = Patch(800, 600)
    v.text(20, 5, "pad-voice: 3 detuned saws -> 2-pole lowpass - slow envelope")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
    voice_switch(v, inl, rel="pd-rel")
    upn = v.obj(200, 100, "unpack f f"); mt = v.obj(200, 130, "mtof"); fq = v.obj(200, 160, "sig~")
    upv = v.obj(20, 100, "unpack f f"); mos = v.obj(60, 130, "moses 1")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt); v.c(mt, fq); v.c(tll, upv, 0); v.c(upv, mos, 1)
    ratk = v.obj(450, 70, "r pd-atk"); rrel = v.obj(550, 70, "r pd-rel")
    fatk = v.obj(450, 100, "f 500"); frel = v.obj(550, 100, "f 1500")
    v.c(ratk, fatk, 0, 1); v.c(rrel, frel, 0, 1)
    onT = v.obj(110, 160, "t b")
    am = v.msg(110, 220, "1 \\$1"); rm = v.msg(20, 220, "0 \\$1")
    v.c(mos, onT, 1); v.c(onT, fatk); v.c(fatk, am)
    offT = v.obj(20, 160, "t b")
    v.c(mos, offT, 0); v.c(offT, frel); v.c(frel, rm)
    env = v.obj(20, 250, "line~")
    v.c(am, env); v.c(rm, env)
    rsp = v.obj(400, 130, "r pd-spread")
    spE = v.obj(400, 160, "expr pow(2 \\, $f1/1200) \\; 1/pow(2 \\, $f1/1200)")
    f2 = v.obj(330, 190, "*~ 1"); f3 = v.obj(430, 190, "*~ 1")
    v.c(rsp, spE); v.c(spE, f2, 0, 1); v.c(spE, f3, 1, 1); v.c(fq, f2); v.c(fq, f3)
    p1 = v.obj(200, 230, "phasor~"); p2 = v.obj(330, 230, "phasor~"); p3 = v.obj(430, 230, "phasor~")
    v.c(fq, p1); v.c(f2, p2); v.c(f3, p3)
    s = v.obj(200, 270, "+~"); s2 = v.obj(200, 300, "+~"); s3 = v.obj(200, 330, "-~ 1.5")
    v.c(p1, s, 0, 0); v.c(p2, s, 0, 1); v.c(s, s2, 0, 0); v.c(p3, s2, 0, 1); v.c(s2, s3)
    rt = v.obj(400, 330, "r pd-tone")
    l1 = v.obj(200, 360, "lop~ 2000"); l2 = v.obj(200, 390, "lop~ 2000")
    v.c(s3, l1); v.c(l1, l2); v.c(rt, l1, 0, 1); v.c(rt, l2, 0, 1)
    g = v.obj(200, 420, "*~ 0.5"); vca = v.obj(200, 450, "*~")
    v.c(l2, g); v.c(g, vca, 0, 0); v.c(env, vca, 0, 1)
    out = v.obj(200, 490, "outlet~")
    v.c(vca, out)
    v.save("pad-voice.pd")


sub_voice(); pluk_voice(); pad_voice()

def air_voice():
    """noise -> 2 band-pass filters at the note and its octave (Q: breath .. whistle), slow random motion"""
    v = Patch(900, 700)
    v.text(20, 5, "air-voice: noise through 2 resonant band-passes (note + octave) - slow LFO on pitch and level")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
    voice_switch(v, inl, rel="air-rel")
    upn = v.obj(200, 100, "unpack f f"); mt = v.obj(200, 130, "mtof"); fq = v.obj(200, 160, "sig~")
    upv = v.obj(20, 100, "unpack f f"); mos = v.obj(60, 130, "moses 1")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt); v.c(mt, fq); v.c(tll, upv, 0); v.c(upv, mos, 1)
    fatk = v.obj(450, 100, "f 1000"); frel = v.obj(550, 100, "f 3000")
    v.c(v.obj(450, 70, "r air-atk"), fatk, 0, 1); v.c(v.obj(550, 70, "r air-rel"), frel, 0, 1)
    onT = v.obj(110, 160, "t b"); offT = v.obj(20, 160, "t b")
    am = v.msg(110, 220, "1 \\$1"); rm = v.msg(20, 220, "0 \\$1")
    v.c(mos, onT, 1); v.c(onT, fatk); v.c(fatk, am)
    v.c(mos, offT, 0); v.c(offT, frel); v.c(frel, rm)
    env = v.obj(20, 250, "line~"); env2 = v.obj(20, 280, "*~")
    v.c(am, env); v.c(rm, env); v.c(env, env2, 0, 0); v.c(env, env2, 0, 1)      # squared: softer swell
    # slow LFO, its own speed per voice
    lr = v.obj(650, 160, "random 1000"); lE = v.obj(650, 190, "expr 0.07+$f1/4000")
    v.c(v.obj(650, 130, "loadbang"), lr); v.c(lr, lE)
    lfo = v.obj(650, 220, "osc~ 0.1")
    v.c(lE, lfo)
    mot = v.obj(750, 160, "r air-mot")
    pdep = v.obj(750, 190, "* 0.03"); adep = v.obj(850, 190, "* 0.4")
    v.c(mot, pdep); v.c(mot, adep)
    pm = v.obj(650, 260, "*~ 0"); pm1 = v.obj(650, 290, "+~ 1")
    v.c(lfo, pm); v.c(pdep, pm, 0, 1); v.c(pm, pm1)
    am2 = v.obj(800, 260, "*~ 0"); am21 = v.obj(800, 290, "+~ 1")
    v.c(lfo, am2); v.c(adep, am2, 0, 1); v.c(am2, am21)
    cf = v.obj(200, 320, "*~"); cf2 = v.obj(330, 320, "*~ 2")
    v.c(fq, cf, 0, 0); v.c(pm1, cf, 0, 1); v.c(cf, cf2)
    nz = v.obj(450, 320, "noise~")
    bp1 = v.obj(200, 360, "vcf~ 10"); bp2 = v.obj(330, 360, "vcf~ 10")
    v.c(nz, bp1, 0, 0); v.c(cf, bp1, 0, 1); v.c(nz, bp2, 0, 0); v.c(cf2, bp2, 0, 1)
    rq = v.obj(450, 360, "r air-q")
    v.c(rq, bp1, 0, 2); v.c(rq, bp2, 0, 2)
    # a narrow band lets less noise through: make up for it (about sqrt(Q))
    gE = v.obj(550, 390, "expr sqrt($f1)*0.5")
    v.c(rq, gE)
    oct_ = v.obj(330, 400, "*~ 0.35"); mix = v.obj(200, 430, "+~")
    v.c(bp1, mix, 0, 0); v.c(bp2, oct_); v.c(oct_, mix, 0, 1)
    gm = v.obj(200, 460, "*~ 1")
    v.c(mix, gm); v.c(gE, gm, 0, 1)
    lv = v.obj(200, 490, "*~"); vca = v.obj(200, 520, "*~")
    v.c(gm, lv, 0, 0); v.c(am21, lv, 0, 1); v.c(lv, vca, 0, 0); v.c(env2, vca, 0, 1)
    v.c(vca, v.obj(200, 560, "outlet~"))
    v.save("air-voice.pd")


BELL_H = [1, 2, 3, 4]                  # harmonic partials
BELL_B = [1, 2.76, 5.40, 8.93]         # bell-like partials
BELL_A = [1, 0.6, 0.35, 0.2]


def bell_voice():
    """4 partials (harmonic .. bell), each with its own decay; 2 slightly detuned twins for slow beating"""
    v = Patch(1400, 800)
    v.text(20, 5, "bell-voice: 4 partials with their own decays (higher = shorter) - harmonic <-> inharmonic - beating twins")
    inl = v.obj(20, 40, "inlet")
    voice_switch(v, inl, rel="bell-dec", onset_only=True)
    up = v.obj(20, 70, "unpack f f")                  # note, velocity (velocity comes out first)
    v.c(inl, up)
    gate = v.obj(20, 130, "spigot")
    on_ = v.obj(120, 100, "> 0")
    v.c(up, on_, 1); v.c(on_, gate, 0, 1); v.c(up, gate, 0)
    # $f1 frequency (from [mtof])  $f2 velocity  $f3 decay ms  $f4 brightness  $f5 inharmonic 0..1  $f6 beat Hz
    outs = []
    for i in range(4):
        r = f"((1-$f5)*{BELL_H[i]}+$f5*{BELL_B[i]})"
        outs += [f"$f1*{r}", f"sqrt($f2/127*{BELL_A[i]}*pow($f4 \\, {i}))", f"$f3/(1+1.4*{i})"]
    outs += ["$f1+$f6", f"$f1*((1-$f5)*{BELL_H[1]}+$f5*{BELL_B[1]})+$f6*1.3"]
    ex = v.obj(20, 170, "expr " + " \\; ".join(outs))
    mt = v.obj(20, 150, "mtof")                       # Pd 0.49 expr has no mtof(): convert first
    v.c(gate, mt); v.c(mt, ex)
    v.c(up, ex, 1, 1)
    for k, (nm, dv) in enumerate((("bell-dec", 2700), ("bell-brite", 0.6), ("bell-str", 0.7), ("bell-beat", 0.75))):
        dm = v.msg(400 + k * 120, 100, f"{dv}")                    # default, then every knob change
        v.c(v.obj(400 + k * 120, 40, "loadbang"), dm); v.c(dm, ex, 0, 2 + k)
        v.c(v.obj(400 + k * 120, 70, f"r {nm}"), ex, 0, 2 + k)
    mix = v.obj(20, 600, "*~ 1")
    envs = []
    for i in range(4):
        X = 20 + i * 300
        osc = v.obj(X, 260, "osc~")
        v.c(ex, osc, i * 3)
        pk = v.obj(X + 100, 260, "pack f f")
        v.c(ex, pk, i * 3 + 2, 1); v.c(ex, pk, i * 3 + 1, 0)       # decay (cold) arrives before the level
        # from the current level up to the new one in 3 ms (no click when a voice is stolen), then decay
        vm = v.msg(X + 100, 290, "\\$1 3 \\, 0 \\$2 3")
        vl = v.obj(X + 100, 320, "vline~"); e2 = v.obj(X + 100, 350, "*~")
        v.c(pk, vm); v.c(vm, vl); v.c(vl, e2, 0, 0); v.c(vl, e2, 0, 1)
        g = v.obj(X, 380, "*~")
        v.c(osc, g, 0, 0); v.c(e2, g, 0, 1)
        v.c(g, mix)
        envs.append(e2)
    for j, (o, envi) in enumerate(((12, 0), (13, 1))):
        X = 20 + j * 300
        tw = v.obj(X, 440, "osc~"); tg = v.obj(X, 470, "*~"); th = v.obj(X, 500, "*~ 0.5")
        v.c(ex, tw, o); v.c(tw, tg, 0, 0); v.c(envs[envi], tg, 0, 1); v.c(tg, th); v.c(th, mix)
    v.c(mix, v.obj(20, 640, "outlet~"))
    v.save("bell-voice.pd")


air_voice(); bell_voice()


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


wave_voice(); strg_voice(); organ_voice(); drone_voice()


# ---------------------------------------------------------------- piano-voice.pd / piano-post.pd (apply_piano.py)
# modes of the felt piano (from the minichord-kalimba "piano felt"): ratio, amplitude, decay factor, detune Hz
PIANO_MODES = ((1.0, 0.6, 1.0, 0), (1.0, 0.5, 1.0, 0.4), (2.002, 0.3, 0.6, 0), (2.002, 0.15, 0.6, 0.7),
               (3.007, 0.12, 0.4, 0), (4.013, 0.05, 0.3, 0), (5.02, 0.02, 0.2, 0))
PIANO_LEVEL, PIANO_CLICK = 0.58, 0.03


def piano_voice():
    """modal synthesis: each mode is a two-pole resonator ([biquad~] fb1 = 2 r cos w, fb2 = -r^2, ff1 = gain),
    struck by a half-sine pulse (the hammer); a longer pulse (more felt) reaches the high modes less, the
    fundamental is brought back to full level. A short noise click at the contact."""
    v = Patch(1600, 900)
    v.text(20, 5, "piano-voice: modal felt piano - 7 resonators struck by a half-sine hammer pulse - click - damper and pedal")
    inl = v.obj(20, 40, "inlet")
    tl = v.obj(20, 55, "t l l")                           # 1) store note and velocity  0) then note-on / off
    upS = v.obj(120, 85, "unpack f f")
    up = v.obj(20, 70, "unpack f f")
    v.c(inl, tl); v.c(tl, upS, 1); v.c(tl, up, 0)
    mos = v.obj(20, 130, "moses 1")
    noteF = v.obj(120, 130, "f")
    v.c(upS, noteF, 0, 1); v.c(up, mos, 1)
    velF = v.obj(300, 190, "f 100")
    v.c(upS, velF, 1, 1)
    # ---- DSP on at the note, off when damped or died away
    sw = v.obj(1300, 300, "switch~")
    z0 = v.msg(1400, 270, "0")
    v.c(v.obj(1400, 240, "loadbang"), z0); v.c(z0, sw)
    offD = v.obj(1300, 270, "delay")
    v.c(offD, z0)
    srt = v.obj(1500, 100, "samplerate~")
    v.c(v.obj(1500, 70, "loadbang"), srt)
    # ---- note-on: 4) DSP on  3) not released  2) mode coefficients  1) hammer pulse + click  0) timer, thump
    # a stolen voice may still ring: fade it out in 1.5 ms, then (2 ms later) clear the resonators and strike
    dcT = v.obj(20, 145, "t b b")
    v.c(mos, dcT, 1)
    outV = v.obj(100, 820, "vline~")
    dcF = v.msg(100, 790, "0 1.5")
    v.c(dcT, dcF, 1); v.c(dcF, outV)
    dcD = v.obj(20, 152, "delay 2")
    v.c(dcT, dcD, 0)
    onT = v.obj(20, 160, "t b b b b b")
    v.c(dcD, onT)
    dcUp = v.msg(180, 790, "1")
    v.c(onT, dcUp, 0); v.c(dcUp, outV)                    # level back up once the strike is under way
    on1 = v.msg(1300, 210, "1")
    v.c(onT, on1, 4); v.c(on1, sw)
    rel0 = v.msg(1000, 100, "0")
    pRel = v.obj(1000, 190, "f 0")
    v.c(onT, rel0, 3); v.c(rel0, pRel, 0, 1)
    # parameters: $f1 frequency  $f2 decay s (at 220 Hz)  $f3 sample rate  $f4 damped (0 / 1)
    feltF = v.obj(500, 190, "f 0.7"); decF = v.obj(600, 190, "f 7000")
    v.c(v.obj(500, 160, "r piano-felt"), feltF, 0, 1); v.c(v.obj(600, 160, "r piano-dec"), decF, 0, 1)
    mt = v.obj(120, 220, "mtof")
    prm = v.obj(120, 260, "pack f f f f")
    dS = v.obj(600, 220, "/ 1000")
    v.c(srt, prm, 0, 2)
    pT = v.obj(120, 190, "t b b b")                      # 2) decay  1) not damped  0) frequency (hot)
    v.c(onT, pT, 2)
    v.c(pT, decF, 2); v.c(decF, dS); v.c(dS, prm, 0, 1)
    d0 = v.msg(200, 220, "0")
    v.c(pT, d0, 1); v.c(d0, prm, 0, 3)
    v.c(pT, noteF, 0); v.c(noteF, mt); v.c(mt, prm, 0, 0)
    mix = v.obj(20, 760, "*~ 1")
    # hammer: half-sine pulse = cos~ of (ramp / 2 - 1/4), ramp 0 -> 1 over the pulse length, times its scale
    hE = v.obj(500, 300, "expr min(0.008-0.0077*(1-$f2) \\, 1/$f1)*1000")      # pulse length in ms
    hP = v.obj(500, 330, "t f f")
    hX = v.obj(650, 360, "expr 2*$f2*$f1/1000")                                   # x = 2 f T ($f1 T ms, $f2 f)
    hL = v.obj(650, 390, "expr if(abs(1-$f1*$f1)<0.001 \\, 0.7854 \\, abs(cos(3.14159*$f1/2)/(1-$f1*$f1)))")
    hS = v.obj(650, 420, "expr $f2/127*3.14159/(2*max(2 \\, $f3*$f4/1000))/max($f1 \\, 0.3)")
    hT = v.obj(500, 270, "t b b b")                       # 2) felt  1) velocity (+ contact click)  0) frequency
    v.c(onT, hT, 1)
    fq = v.obj(400, 240, "f")
    v.c(mt, fq, 0, 1)
    v.c(hT, feltF, 2); v.c(feltF, hE, 0, 1)
    v.c(hT, velF, 1); v.c(velF, hS, 0, 1)
    v.c(srt, hS, 0, 2)
    fqT = v.obj(400, 270, "t f f")                        # 1) f into x (cold)  0) pulse length (hot)
    v.c(hT, fq, 0); v.c(fq, fqT); v.c(fqT, hX, 1, 1); v.c(fqT, hE, 0)
    v.c(hE, hP); v.c(hP, hS, 1, 3); v.c(hP, hX, 0, 0)    # 1) T into the scale (cold)  0) T -> x -> level -> scale
    v.c(hX, hL); v.c(hL, hS)
    # each strike 0..6 ms late at random: nobody hits six keys on the same sample, and a chord's peaks spread
    pDel = v.obj(600, 450, "random 7")
    pPk = v.obj(500, 455, "pack f f")
    pRamp = v.msg(500, 470, "0 \\, 1 \\$1 \\$2")
    pV = v.obj(500, 500, "vline~"); pH = v.obj(500, 530, "*~ 0.5"); pH2 = v.obj(500, 560, "-~ 0.25")
    pC = v.obj(500, 590, "cos~"); pG = v.obj(500, 620, "*~ 0")
    pPT = v.obj(500, 440, "t f b")                        # 1) random delay (cold)  0) pulse length (hot)
    v.c(hP, pPT, 1); v.c(pPT, pDel, 1); v.c(pDel, pPk, 0, 1); v.c(pPT, pPk, 0, 0); v.c(pPk, pRamp)
    v.c(pRamp, pV); v.c(pV, pH); v.c(pH, pH2); v.c(pH2, pC); v.c(pC, pG)
    v.c(hS, pG, 0, 1)
    # resonators
    for k_, (ratio, amp, dfac, det) in enumerate(PIANO_MODES):
        X = 20 + k_ * 130
        FR = f"($f1*{ratio}+{det})"
        W = f"(6.28319*{FR}/$f3)"
        T60 = f"if($f4 \\, 0.15 \\, $f2*{dfac}*min(3 \\, max(0.3 \\, sqrt(220/$f1))))"
        R = f"exp(-6.9078/({T60}*$f3))"
        ce = v.obj(X, 300 + (k_ % 2) * 20,
                   f"expr 2*{R}*cos({W}) \; -{R}*{R} \; if({FR}<0.45*$f3 \\, {PIANO_LEVEL}*{amp}*sin({W}) \\, 0)")
        cp = v.obj(X, 350, "pack f f f")
        v.c(prm, ce)
        v.c(ce, cp, 2, 2); v.c(ce, cp, 1, 1); v.c(ce, cp, 0, 0)
        cm = v.msg(X, 380, "\\$1 \\$2 \\$3 0 0")
        bq = v.obj(X, 650, "biquad~")
        v.c(cp, cm); v.c(cm, bq); v.c(pG, bq); v.c(bq, mix)
        clr = v.msg(X, 620, "set 0 0")                     # resonator state cleared before a new note
        v.c(onT, clr, 4); v.c(clr, bq)
    # contact click (NOISE-independent, part of the tone): noise, about 3 ms
    nz = v.obj(1100, 470, "noise~")
    cE = v.obj(1100, 420, f"expr $f1/127*{PIANO_CLICK}*(0.3+1-$f2)")
    v.c(velF, cE); v.c(feltF, cE, 0, 1)
    cM = v.msg(1100, 445, "\\$1 \\, 0 8")
    cV = v.obj(1100, 500, "vline~"); cG = v.obj(1100, 530, "*~")
    v.c(cE, cM); v.c(cM, cV); v.c(nz, cG, 0, 0); v.c(cV, cG, 0, 1); v.c(cG, mix)
    # hammer thump (NOISE): a low sine for ~35 ms
    noiseF = v.obj(1400, 380, "f 0.5")
    v.c(v.obj(1400, 350, "r piano-noise"), noiseF, 0, 1)
    thO = v.obj(1400, 470, "osc~ 95"); thEnv = v.obj(1450, 500, "vline~"); thG = v.obj(1400, 530, "*~")
    thE = v.obj(1450, 440, "expr $f1*$f2/127*0.08")
    thM = v.msg(1450, 470, "\\$1 2 \\, 0 35 2")
    v.c(onT, noiseF, 0); v.c(noiseF, thE)
    v.c(velF, thE, 0, 1)
    v.c(thE, thM); v.c(thM, thEnv); v.c(thO, thG, 0, 0); v.c(thEnv, thG, 0, 1); v.c(thG, mix)
    # switch-off timer: the longest mode's T60 (+ margin)
    offE = v.obj(1300, 240, "expr $f2*1000*min(3 \\, max(0.3 \\, sqrt(220/$f1)))+400")
    v.c(prm, offE); v.c(offE, offD, 0, 1)
    v.c(onT, offD, 0)
    # ---- damping: the resonators' decay to 0.15 s (gains unchanged), DSP off 450 ms later, a key-release click
    dmp = v.obj(700, 700, "t b b b")
    d1 = v.msg(700, 730, "1")
    d1T = v.obj(700, 745, "t b f")                        # 1) damped = 1  0) re-send the parameters
    v.c(dmp, d1, 2); v.c(d1, d1T); v.c(d1T, prm, 1, 3); v.c(d1T, prm, 0, 0)
    dOff = v.msg(800, 730, "450")
    v.c(dmp, dOff, 1); v.c(dOff, offD, 0, 0)
    clE = v.obj(900, 730, "expr $f1*0.02")
    clM = v.msg(900, 760, "\\$1 1 \\, 0 20 1")
    clEnv = v.obj(900, 790, "vline~"); clLp = v.obj(1000, 790, "lop~ 1500"); clG = v.obj(900, 820, "*~")
    v.c(dmp, noiseF, 0); v.c(noiseF, clE); v.c(clE, clM); v.c(clM, clEnv)
    v.c(nz, clLp); v.c(clLp, clG, 0, 0); v.c(clEnv, clG, 0, 1); v.c(clG, mix)
    # note-off: pedal down -> remember (released), else damp
    offT = v.obj(20, 700, "t b")
    v.c(mos, offT, 0)
    ofE = v.obj(20, 730, "f 0")
    v.c(v.obj(120, 700, "r piano-pedal"), ofE, 0, 1)
    v.c(offT, ofE)
    ofS = v.obj(20, 760, "sel 0 1")
    v.c(ofE, ofS); v.c(ofS, dmp, 0)
    rel1 = v.msg(100, 790, "1")
    v.c(ofS, rel1, 1); v.c(rel1, pRel, 0, 1)
    # pedal lifted: damp the notes released meanwhile
    pT2 = v.obj(1000, 130, "t f f")
    v.c(v.obj(1000, 40, "r piano-pedal"), pT2)
    pUp = v.obj(1000, 160, "sel 0")
    v.c(pT2, pUp, 0)
    v.c(pUp, pRel)
    pRelS = v.obj(1000, 220, "sel 1")
    v.c(pRel, pRelS); v.c(pRelS, rel0); v.c(pRelS, dmp)
    outG = v.obj(20, 840, "*~")
    v.c(mix, outG, 0, 0); v.c(outV, outG, 0, 1); v.c(outG, v.obj(20, 860, "outlet~"))
    v.save("piano-voice.pd")


def piano_post():
    p_ = Patch(1600, 900)
    p_.text(20, 5, "piano-post: sympathetic resonance (pedal) - pedal noises - lo-fi: high cut / wow / hiss")
    inl = p_.obj(20, 40, "inlet~")
    outl = p_.obj(20, 860, "outlet~")
    pedF = p_.obj(600, 70, "f 0")
    noiseF = p_.obj(700, 70, "f 0.5")
    p_.c(p_.obj(700, 40, "r piano-noise"), noiseF, 0, 1)
    pedR = p_.obj(600, 40, "r piano-pedal")
    # sympathetic resonance: 4 combs (A1 E2 A2 E3), fed by the piano, heard only while the pedal is down
    symG = p_.obj(300, 330, "*~")
    symM = p_.msg(400, 270, "\\$1 300")
    symL = p_.obj(400, 300, "line~")
    symE = p_.obj(400, 240, "* 0.18")
    p_.c(pedR, symE); p_.c(symE, symM); p_.c(symM, symL); p_.c(symL, symG, 0, 1)
    for k_, hz in enumerate((55.0, 82.41, 110.0, 164.81)):
        X = 300 + k_ * 150
        nm_ = f"psym{k_}"
        dw = p_.obj(X, 130, f"delwrite~ {nm_} 40")
        dr = p_.obj(X, 160, f"delread~ {nm_} {1000 / hz:.3f}")
        lp = p_.obj(X, 190, "lop~ 2500")
        fb = p_.obj(X, 220, "*~ 0.93")
        inG = p_.obj(X, 100, "*~ 0.25")
        p_.c(inl, inG); p_.c(inG, dw); p_.c(dr, lp); p_.c(lp, fb); p_.c(fb, dw); p_.c(lp, symG)
    # pedal noises: down = thump + rustle, up = lighter thump + shorter rustle (NOISE)
    pT = p_.obj(600, 100, "t f f")
    p_.c(pedR, pT); p_.c(pT, pedF, 1, 1)
    pC = p_.obj(600, 130, "change")
    pS = p_.obj(600, 160, "sel 1 0")
    p_.c(pT, pC, 0); p_.c(pC, pS)
    nzP = p_.obj(800, 300, "noise~")
    bp = p_.obj(800, 330, "bp~ 1100 2")
    ruEnv = p_.obj(900, 330, "vline~"); ruG = p_.obj(800, 360, "*~")
    thO = p_.obj(1000, 300, "osc~ 70"); thEnv = p_.obj(1100, 330, "vline~"); thG = p_.obj(1000, 360, "*~")
    p_.c(nzP, bp); p_.c(bp, ruG, 0, 0); p_.c(ruEnv, ruG, 0, 1)
    p_.c(thO, thG, 0, 0); p_.c(thEnv, thG, 0, 1)
    for k_, (thLvl, thMs, ruLvl, ruMs) in enumerate(((0.10, 80, 0.06, 180), (0.06, 50, 0.04, 110))):
        X = 800 + k_ * 300
        t_ = p_.obj(X, 190, "t b b")
        p_.c(pS, t_, k_)
        eT = p_.obj(X, 220, f"expr $f1*{thLvl}")
        eR = p_.obj(X + 100, 220, f"expr $f1*{ruLvl}")
        nF_ = p_.obj(X + 200, 190, "f 0.5")
        p_.c(p_.obj(X + 200, 160, "r piano-noise"), nF_, 0, 1)
        p_.c(t_, nF_, 1); p_.c(nF_, eT); p_.c(nF_, eR)
        mT = p_.msg(X, 250, f"\\$1 3 \\, 0 {thMs} 3")
        mR = p_.msg(X + 100, 250, f"\\$1 15 \\, 0 {ruMs} 15")
        p_.c(eT, mT); p_.c(mT, thEnv); p_.c(eR, mR); p_.c(mR, ruEnv)
    # everything into the lo-fi stage
    sum_ = p_.obj(20, 400, "+~")
    p_.c(inl, sum_); p_.c(symG, sum_); p_.c(ruG, sum_); p_.c(thG, sum_)
    # body of the instrument: a resonance at 110 Hz, Q 1.5, in parallel (as in the minichord felt piano)
    bdy = p_.obj(150, 370, "bp~ 110 1.5"); bdyG = p_.obj(150, 385, "*~ 0.4")
    p_.c(inl, bdy); p_.c(bdy, bdyG); p_.c(bdyG, sum_)
    lofiF = p_.obj(300, 430, "r piano-lofi")
    # (no saturation: on a piano it sounded like clipping) high cut 16 kHz -> 2.9 kHz
    lpE = p_.obj(300, 520, "expr 16000*pow(0.18 \\, $f1)")
    lp1 = p_.obj(20, 540, "lop~ 16000"); lp2 = p_.obj(20, 570, "lop~ 16000")
    p_.c(lofiF, lpE); p_.c(lpE, lp1, 0, 1); p_.c(lpE, lp2, 0, 1)
    p_.c(sum_, lp1); p_.c(lp1, lp2)
    # wow: a 4 ms delay modulated by two slow sines, depth up to +-1.2 ms
    wW = p_.obj(20, 600, "delwrite~ pwow 30")
    p_.c(lp2, wW)
    w1 = p_.obj(200, 600, "osc~ 0.55"); w2 = p_.obj(300, 600, "osc~ 0.13")
    wS = p_.obj(200, 630, "+~"); wD = p_.obj(200, 660, "*~ 0"); wO = p_.obj(200, 690, "+~ 4")
    wDE = p_.obj(400, 630, "expr $f1*0.6")
    p_.c(lofiF, wDE); p_.c(wDE, wD, 0, 1)
    p_.c(w1, wS, 0, 0); p_.c(w2, wS, 0, 1); p_.c(wS, wD); p_.c(wD, wO)
    wR = p_.obj(20, 720, "vd~ pwow")
    p_.c(wO, wR)
    # hiss that follows the playing: input level (env~) -> 0..1, slow release, times LOFI
    ev = p_.obj(600, 600, "env~ 1024 512")
    evE = p_.obj(600, 630, "expr if($f1>30 \\, 1 \\, 0)*$f2*0.006")
    p_.c(inl, ev); p_.c(ev, evE); p_.c(lofiF, evE, 0, 1)
    evM = p_.msg(600, 660, "\\$1 800"); evL = p_.obj(600, 690, "line~")
    p_.c(evE, evM); p_.c(evM, evL)
    hs = p_.obj(800, 690, "noise~"); hsH = p_.obj(800, 720, "hip~ 1500"); hsG = p_.obj(800, 750, "*~")
    p_.c(hs, hsH); p_.c(hsH, hsG, 0, 0); p_.c(evL, hsG, 0, 1)
    out_ = p_.obj(20, 800, "+~")
    # soft limiter: below 0.8 untouched, above it rounded towards 1 (a struck chord's attack peaks)
    lim = p_.obj(20, 830, "expr~ if(abs($v1)<0.8 \\, $v1 \\, (($v1>0)*2-1)*(0.8+(abs($v1)-0.8)/(1+5*(abs($v1)-0.8))))")
    p_.c(wR, out_); p_.c(hsG, out_); p_.c(out_, lim); p_.c(lim, outl)
    lb = p_.obj(1300, 40, "loadbang")
    lbM = p_.msg(1300, 70, "0.4")
    p_.c(lb, lbM); p_.c(lbM, lpE); p_.c(lbM, wDE)
    p_.save("piano-post.pd")


piano_voice(); piano_post()

MLT_TYPES = [
    "\\; mltr 0 1.0 1.0 6.27 6.27 17.55 1.0 1.0 \\; mlta 0 0.8 0.3 0.45 0.15 0.2 0 0 \\; mltd 0 1.0 1.0 0.35 0.35 0.12 1.0 1.0 \\; mltt 0 0 2.0 0 9.0 0 0 0 \\; mlt-base 1.8 \\; mlt-click 0.15 \\; mlt-level 0.636 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 420 4 0.6 1600 3 0.3",
    "\\; mltr 0 1.0 6.27 17.55 1.0 1.0 1.0 1.0 \\; mlta 0 1.0 0.3 0.1 0 0 0 0 \\; mltd 0 1.0 0.25 0.08 1.0 1.0 1.0 1.0 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 2.5 \\; mlt-click 0.12 \\; mlt-level 0.815 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 230 5 0.5 820 3 0.25",
    "\\; mltr 0 1.0 6.27 17.55 1.0 1.0 1.0 1.0 \\; mlta 0 1.0 0.3 0.1 0 0 0 0 \\; mltd 0 1.0 0.25 0.08 1.0 1.0 1.0 1.0 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 2.5 \\; mlt-click 0.12 \\; mlt-level 0.786 \\; mlt-buzz 2.0 \\; mlt-trem 0 0 \\; mlt-body 230 5 0.5 820 3 0.25",
    "\\; mltr 0 1.0 1.0 2.0 2.0 3.0 3.0 1.0 \\; mlta 0 0.7 0.5 0.45 0.3 0.25 0.15 0 \\; mltd 0 1.0 1.0 0.75 0.75 0.5 0.5 1.0 \\; mltt 0 0 0.7 0 1.1 0 1.6 0 \\; mlt-base 5.0 \\; mlt-click 0.02 \\; mlt-level 0.858 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 1.0 2.0 2.0 3.0 4.0 1.0 1.0 \\; mlta 0 1.0 0.6 0.2 0.35 0.2 0 0 \\; mltd 0 1.0 0.6 0.6 0.4 0.3 1.0 1.0 \\; mltt 0 0 0 1.5 0 0 0 0 \\; mlt-base 1.6 \\; mlt-click 0.05 \\; mlt-level 0.972 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 1.0 3.93 9.2 1.0 1.0 1.0 1.0 \\; mlta 0 1.0 0.35 0.12 0 0 0 0 \\; mltd 0 1.0 0.25 0.1 1.0 1.0 1.0 1.0 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 1.2 \\; mlt-click 0.05 \\; mlt-level 1.154 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 1.0 4.0 10.0 1.0 1.0 1.0 1.0 \\; mlta 0 1.0 0.25 0.06 0 0 0 0 \\; mltd 0 1.0 0.3 0.1 1.0 1.0 1.0 1.0 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 4.0 \\; mlt-click 0.03 \\; mlt-level 1.599 \\; mlt-buzz 0 \\; mlt-trem 5.5 0.45 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 1.0 2.76 5.4 8.93 1.0 1.0 1.0 \\; mlta 0 1.0 0.4 0.2 0.1 0 0 0 \\; mltd 0 1.0 0.5 0.3 0.2 1.0 1.0 1.0 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 3.0 \\; mlt-click 0.08 \\; mlt-level 1.082 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 0.5 1.0 1.2 1.5 2.0 2.5 3.0 \\; mlta 0 0.5 0.6 0.45 0.25 0.5 0.2 0.15 \\; mltd 0 1.6 1.0 0.8 0.6 0.5 0.35 0.3 \\; mltt 0 0 0 0 0 0 0 0 \\; mlt-base 6.0 \\; mlt-click 0.02 \\; mlt-level 0.69 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
    "\\; mltr 0 1.0 1.0 2.71 4.95 1.0 1.0 1.0 \\; mlta 0 0.7 0.5 0.3 0.12 0 0 0 \\; mltd 0 1.0 1.0 0.4 0.2 1.0 1.0 1.0 \\; mltt 0 0 5.0 0 0 0 0 0 \\; mlt-base 3.5 \\; mlt-click 0.06 \\; mlt-level 0.954 \\; mlt-buzz 0 \\; mlt-trem 0 0 \\; mlt-body 1000 1 0 1000 1 0",
]
MLT_NAMES = ["toy", "kalim", "kbuzz", "hpan", "steel", "marim", "vibes", "glock", "bells", "gamel"]


# ---------------------------------------------------------------- mallet-voice.pd / mallet-post.pd (apply_mallet.py)
MLT_NM = 7


def mallet_voice():
    v = Patch(1600, 900)
    v.text(20, 5, "mallet-voice: modal struck instruments - up to 7 resonators from the tables mltr / mlta / mltd / mltt - half-sine strike - click")
    inl = v.obj(20, 40, "inlet")
    tl = v.obj(20, 55, "t l l")                           # 1) store note and velocity  0) then note-on / off
    upS = v.obj(120, 85, "unpack f f")
    up = v.obj(20, 70, "unpack f f")
    v.c(inl, tl); v.c(tl, upS, 1); v.c(tl, up, 0)
    mos = v.obj(20, 130, "moses 1")
    noteF = v.obj(120, 130, "f")
    v.c(upS, noteF, 0, 1); v.c(up, mos, 1)
    velF = v.obj(300, 190, "f 100")
    v.c(upS, velF, 1, 1)
    for nm_ in ("mltbase", "mltclick", "mltlevel"):
        v.obj(1450 + ("mltbase", "mltclick", "mltlevel").index(nm_) * 60, 10, f"v {nm_}")
    # ---- DSP on at the note, off when damped or died away
    sw = v.obj(1300, 300, "switch~")
    z0 = v.msg(1400, 270, "0")
    v.c(v.obj(1400, 240, "loadbang"), z0); v.c(z0, sw)
    offD = v.obj(1300, 270, "delay")
    v.c(offD, z0)
    srt = v.obj(1500, 100, "samplerate~")
    v.c(v.obj(1500, 70, "loadbang"), srt)
    # ---- note-on: 3) DSP on  2) mode coefficients  1) strike + click  0) switch-off timer
    # a stolen voice may still ring: fade it out in 1.5 ms, then (2 ms later) clear the resonators and strike
    dcT = v.obj(20, 145, "t b b")
    v.c(mos, dcT, 1)
    outV = v.obj(100, 820, "vline~")
    dcF = v.msg(100, 790, "0 1.5")
    v.c(dcT, dcF, 1); v.c(dcF, outV)
    dcD = v.obj(20, 152, "delay 2")
    v.c(dcT, dcD, 0)
    onT = v.obj(20, 160, "t b b b b")
    v.c(dcD, onT)
    dcUp = v.msg(180, 790, "1")
    v.c(onT, dcUp, 0); v.c(dcUp, outV)                    # level back up once the strike is under way
    on1 = v.msg(1300, 210, "1")
    v.c(onT, on1, 3); v.c(on1, sw)
    # parameters: $f1 frequency  $f2 decay scale  $f3 sample rate  $f4 damping T60 (0 = none)
    hardF = v.obj(500, 190, "f 0.5"); decF = v.obj(600, 190, "f 1")
    v.c(v.obj(500, 160, "r mlt-hard"), hardF, 0, 1); v.c(v.obj(600, 160, "r mlt-dec"), decF, 0, 1)
    mt = v.obj(120, 220, "mtof")
    prm = v.obj(120, 260, "pack f f f f")
    v.c(srt, prm, 0, 2)
    pT = v.obj(120, 190, "t b b b")                      # 2) decay scale  1) not damped  0) frequency (hot)
    v.c(onT, pT, 2)
    v.c(pT, decF, 2); v.c(decF, prm, 0, 1)
    d0 = v.msg(200, 220, "0")
    v.c(pT, d0, 1); v.c(d0, prm, 0, 3)
    v.c(pT, noteF, 0); v.c(noteF, mt); v.c(mt, prm, 0, 0)
    mix = v.obj(20, 760, "*~ 1")
    # strike: half-sine pulse = cos~ of (ramp / 2 - 1/4), length from the hardness, fundamental compensated
    hE = v.obj(500, 300, "expr min(0.008-0.0077*$f2 \\, 1/$f1)*1000")
    hP = v.obj(500, 330, "t f f")
    hX = v.obj(650, 360, "expr 2*$f2*$f1/1000")
    hL = v.obj(650, 390, "expr if(abs(1-$f1*$f1)<0.001 \\, 0.7854 \\, abs(cos(3.14159*$f1/2)/(1-$f1*$f1)))")
    hS = v.obj(650, 420, "expr $f2/127*3.14159/(2*max(2 \\, $f3*$f4/1000))/max($f1 \\, 0.3)")
    hT = v.obj(500, 270, "t b b b")                       # 2) hardness  1) velocity (+ click)  0) frequency
    v.c(onT, hT, 1)
    fq = v.obj(400, 240, "f")
    v.c(mt, fq, 0, 1)
    v.c(hT, hardF, 2); v.c(hardF, hE, 0, 1)
    v.c(hT, velF, 1); v.c(velF, hS, 0, 1)
    v.c(srt, hS, 0, 2)
    fqT = v.obj(400, 270, "t f f")
    v.c(hT, fq, 0); v.c(fq, fqT); v.c(fqT, hX, 1, 1); v.c(fqT, hE, 0)
    v.c(hE, hP); v.c(hP, hS, 1, 3); v.c(hP, hX, 0, 0)
    v.c(hX, hL); v.c(hL, hS)
    pRamp = v.msg(500, 470, "0 \\, 1 \\$1")
    pV = v.obj(500, 500, "vline~"); pH = v.obj(500, 530, "*~ 0.5"); pH2 = v.obj(500, 560, "-~ 0.25")
    pC = v.obj(500, 590, "cos~"); pG = v.obj(500, 620, "*~ 0")
    v.c(hP, pRamp, 1); v.c(pRamp, pV); v.c(pV, pH); v.c(pH, pH2); v.c(pH2, pC); v.c(pC, pG)
    v.c(hS, pG, 0, 1)
    # resonators: ratio / level / decay / detune of mode k from the type tables
    for k_ in range(MLT_NM):
        X = 20 + k_ * 130
        FR = f"($f1*mltr[{k_}]+mltt[{k_}])"
        W = f"(6.28319*{FR}/$f3)"
        T60N = f"max(0.001 \\, mltbase*$f2*mltd[{k_}]*min(3 \\, max(0.3 \\, sqrt(220/$f1))))"
        T60 = f"if($f4>0 \\, min($f4 \\, {T60N}) \\, {T60N})"
        R = f"exp(-6.9078/({T60}*$f3))"
        ce = v.obj(X, 300 + (k_ % 2) * 20,
                   f"expr 2*{R}*cos({W}) \\; -{R}*{R} \\; if({FR}<0.45*$f3 \\, mltlevel*mlta[{k_}]*sin({W}) \\, 0)")
        cp = v.obj(X, 350, "pack f f f")
        v.c(prm, ce)
        v.c(ce, cp, 2, 2); v.c(ce, cp, 1, 1); v.c(ce, cp, 0, 0)
        cm = v.msg(X, 380, "\\$1 \\$2 \\$3 0 0")
        bq = v.obj(X, 650, "biquad~")
        v.c(cp, cm); v.c(cm, bq); v.c(pG, bq); v.c(bq, mix)
        clr = v.msg(X, 620, "set 0 0")                     # resonator state cleared before a new note
        v.c(onT, clr, 3); v.c(clr, bq)
    # contact click: high-passed noise, about 3 ms (as the minichord)
    nz = v.obj(1100, 470, "noise~")
    cHp = v.obj(1100, 500, "hip~ 2100")
    cE = v.obj(1100, 420, "expr $f1/127*mltclick*(0.3+$f2)")
    v.c(velF, cE); v.c(hardF, cE, 0, 1)
    cM = v.msg(1100, 445, "\\$1 \\, 0 8")
    cV = v.obj(1200, 500, "vline~"); cG = v.obj(1100, 530, "*~")
    v.c(cE, cM); v.c(cM, cV); v.c(nz, cHp); v.c(cHp, cG, 0, 0); v.c(cV, cG, 0, 1); v.c(cG, mix)
    # switch-off timer: the longest ring (a bell's hum mode decays 1.6 x the base)
    offE = v.obj(1300, 240, "expr mltbase*$f2*1600*min(3 \\, max(0.3 \\, sqrt(220/$f1)))+400")
    v.c(prm, offE); v.c(offE, offD, 0, 1)
    v.c(onT, offD, 0)
    # ---- note-off: REL at the top rings on; lower values damp (T60 0.08 .. 6 s), DSP off after that
    relF = v.obj(20, 700, "f 1")
    v.c(v.obj(120, 680, "r mlt-rel"), relF, 0, 1)
    offT = v.obj(20, 690, "t b")
    v.c(mos, offT, 0); v.c(offT, relF)
    rlE = v.obj(20, 730, "expr if($f1<0.99 \\, 0.08+6*$f1*$f1 \\, -1)")
    rlM = v.obj(20, 760, "moses 0")
    v.c(relF, rlE); v.c(rlE, rlM)
    rlT = v.obj(100, 790, "t f f")                        # 1) the damping T60 in, parameters re-sent  0) DSP off later
    v.c(rlM, rlT, 1)
    rlP = v.obj(200, 820, "t b f")
    v.c(rlT, rlP, 1); v.c(rlP, prm, 1, 3); v.c(rlP, prm, 0, 0)
    rlMs = v.obj(100, 820, "expr $f1*1000+400")
    v.c(rlT, rlMs, 0); v.c(rlMs, offD)                    # a float into [delay]'s left inlet: set and start
    outG = v.obj(20, 840, "*~")
    v.c(mix, outG, 0, 0); v.c(outV, outG, 0, 1); v.c(outG, v.obj(20, 860, "outlet~"))
    v.save("mallet-voice.pd")


def mallet_post():
    p_ = Patch(1600, 900)
    p_.text(20, 5, "mallet-post: instrument types (tables) - body resonances - buzz - tremolo - soft limiter - TYPE name on the SYNTH page")
    p_.obj(20, 30, f"table mltr {MLT_NM}"); p_.obj(140, 30, f"table mlta {MLT_NM}")
    p_.obj(260, 30, f"table mltd {MLT_NM}"); p_.obj(380, 30, f"table mltt {MLT_NM}")
    inl = p_.obj(20, 60, "inlet~")
    outl = p_.obj(20, 860, "outlet~")
    for k_, (rcv, var) in enumerate((("mlt-base", "mltbase"), ("mlt-click", "mltclick"), ("mlt-level", "mltlevel"))):
        p_.c(p_.obj(600 + k_ * 100, 30, f"r {rcv}"), p_.obj(600 + k_ * 100, 60, f"v {var}"))
    # type -> tables and values
    tyR = p_.obj(1000, 30, "r mlt-type")
    tyS = p_.obj(1000, 60, "sel " + " ".join(str(i_) for i_ in range(len(MLT_TYPES))))
    p_.c(tyR, tyS)
    for i_, msg_ in enumerate(MLT_TYPES):
        p_.c(tyS, p_.msg(1000 + (i_ % 5) * 120, 90 + (i_ // 5) * 30, msg_), i_)
    p_.c(p_.obj(1100, 30, "loadbang"), p_.msg(1100, 60, "\\; mlt-type 0"))
    # body: dry + g1 bp1(dry) + g2 bp2(dry)
    bU = p_.obj(300, 120, "unpack f f f f f f")
    p_.c(p_.obj(300, 90, "r mlt-body"), bU)
    sum_ = p_.obj(20, 300, "+~")
    p_.c(inl, sum_)
    for b_ in range(2):
        X = 300 + b_ * 250
        bp = p_.obj(X, 200, "bp~ 1000 1"); bg = p_.obj(X, 230, "*~ 0")
        p_.c(bU, bp, 3 * b_, 1); p_.c(bU, bp, 3 * b_ + 1, 2); p_.c(bU, bg, 3 * b_ + 2, 1)
        p_.c(inl, bp); p_.c(bp, bg); p_.c(bg, sum_)
    # buzz: the part above 0.2, times (0.6 + 0.4 noise), high-passed, times the amount
    bzE = p_.obj(800, 330, "expr~ ($v1-min(0.2 \\, max(-0.2 \\, $v1)))*(0.6+0.4*$v2)")
    bzN = p_.obj(950, 300, "noise~")
    bzH = p_.obj(800, 360, "hip~ 700"); bzG = p_.obj(800, 390, "*~ 0")
    p_.c(inl, bzE, 0, 0); p_.c(bzN, bzE, 0, 1); p_.c(bzE, bzH); p_.c(bzH, bzG); p_.c(bzG, sum_)
    p_.c(p_.obj(900, 360, "r mlt-buzz"), bzG, 0, 1)
    # tremolo: 1 - depth (0.5 + 0.5 sin)
    trU = p_.obj(500, 420, "unpack f f")
    p_.c(p_.obj(500, 390, "r mlt-trem"), trU)
    trO = p_.obj(500, 450, "osc~ 0"); trA = p_.obj(500, 480, "*~ 0.5"); trB = p_.obj(500, 510, "+~ 0.5")
    trD = p_.obj(500, 540, "*~ 0"); trN = p_.obj(500, 570, "*~ -1"); trC = p_.obj(500, 600, "+~ 1")
    p_.c(trU, trO, 0); p_.c(trU, trD, 1, 1)
    p_.c(trO, trA); p_.c(trA, trB); p_.c(trB, trD); p_.c(trD, trN); p_.c(trN, trC)
    trM = p_.obj(20, 620, "*~")
    p_.c(sum_, trM, 0, 0); p_.c(trC, trM, 0, 1)
    lim = p_.obj(20, 800, "expr~ if(abs($v1)<0.8 \\, $v1 \\, (($v1>0)*2-1)*(0.8+(abs($v1)-0.8)/(1+5*(abs($v1)-0.8))))")
    p_.c(trM, lim); p_.c(lim, outl)
    # the TYPE row shows the name: on [s mlt-draw] (synth.pd, after the rows) print it over the number
    dwF = p_.obj(1000, 400, "f 0")
    p_.c(p_.obj(1000, 370, "r mlt-type"), dwF, 0, 1)
    dwG = p_.obj(1000, 430, "expr if($f2==12 && $f3==0 && $f4==0 \\, $f1 \\, -1)")
    dwT = p_.obj(1000, 385, "t b b b b")
    p_.c(p_.obj(1000, 355, "r mlt-draw"), dwT)
    for k_, (rcv, x_) in enumerate((("synth-engine", 1100), ("aux", 1200), ("syn-lfo-page", 1300))):
        f_ = p_.obj(x_, 400, "f 0")
        p_.c(p_.obj(x_, 370, f"r {rcv}"), f_, 0, 1); p_.c(dwT, f_, 3 - k_); p_.c(f_, dwG, 0, k_ + 1)
    p_.c(dwT, dwF, 0); p_.c(dwF, dwG)
    dwS = p_.obj(1000, 460, "sel " + " ".join(str(i_) for i_ in range(len(MLT_NAMES))))
    p_.c(dwG, dwS)
    for i_, nm_ in enumerate(MLT_NAMES):
        p_.c(dwS, p_.msg(1000 + (i_ % 5) * 110, 490 + (i_ // 5) * 30,
                         "\\; oscOut sendtyped /oled/gFillArea iiiiii 3 34 13 29 10 0 "
                         f"\\; oscOut sendtyped /oled/gPrintln iiiiis 3 34 14 8 1 {nm_}"), i_)
    p_.save("mallet-post.pd")


mallet_voice(); mallet_post()


# ---------------------------------------------------------------- engines
def engine(name, eid, voice, gain, params, voices=4):
    e = Patch(1200, 700)
    e.text(20, 5, f"synth-{name}: engine {eid} ({NAMES[eid]}). knobs: " + " / ".join(p[0] for p in params))
    rn = e.obj(20, 40, f"r {name}-notes"); rp = e.obj(160, 40, "r synth-panic")
    poly = e.obj(20, 80, f"poly {voices} 1"); pk = e.obj(20, 110, "pack f f f")
    cl = e.obj(20, 140, f"clone -s 1 {voice} {voices}")
    g = e.obj(20, 180, f"*~ {gain}"); cp = e.obj(20, 210, "clip~ -1 1")
    th = e.obj(20, 250, "throw~ synth-eng")            # -> synth-lfo.pd -> synth-bus
    e.c(rn, poly); e.c(rp, poly)
    e.c(poly, pk, 0, 0); e.c(poly, pk, 1, 1); e.c(poly, pk, 2, 2)
    vR = e.obj(160, 150, "r synth-vol"); vM = e.msg(160, 180, "\\$1 20"); vL = e.obj(160, 210, "line~")
    vG = e.obj(20, 195, "*~")
    e.c(vR, vM); e.c(vM, vL)
    e.c(pk, cl); e.c(cl, g); e.c(g, vG, 0, 0); e.c(vL, vG, 0, 1)
    if name in ("piano", "mallet"):                       # their own output stage before the clip (apply_piano.py, apply_mallet.py)
        post = e.obj(20, 205, f"{name}-post")
        e.c(vG, post); e.c(post, cp)
    else:
        e.c(vG, cp)
    e.c(cp, th)
    # active engine / DSP switch
    reng = e.obj(300, 40, "r synth-engine")
    eq = e.obj(300, 70, f"== {eid}")
    eT = e.obj(300, 100, "t f f")
    act = e.obj(450, 130, "sel 1 0")
    on1 = e.msg(450, 160, "1"); stp = e.msg(400, 160, "stop")
    dly = e.obj(520, 160, "delay 4000"); off0 = e.msg(520, 190, "0")
    sw = e.obj(450, 220, "switch~")
    e.c(reng, eq); e.c(eq, eT); e.c(eT, act, 0)
    e.c(act, stp, 0); e.c(stp, dly); e.c(act, on1, 0); e.c(on1, sw)
    e.c(act, dly, 1); e.c(dly, off0); e.c(off0, sw)
    # knobs
    rk = e.obj(600, 40, f"r {name}-knob")
    lb = e.obj(800, 40, "loadbang")
    dflt = e.msg(800, 70, " \\, ".join(f"{i+1} {p[3]}" for i, p in enumerate(params)))
    rt = e.obj(600, 100, "route 1 2 3 4")
    e.c(rk, rt); e.c(lb, dflt); e.c(dflt, rt)
    rred = e.obj(950, 40, "r synth-redisplay")
    redSp = e.obj(950, 70, "spigot")
    e.c(eT, redSp, 1, 1); e.c(rred, redSp)
    redT = e.obj(950, 100, "t b b b b")
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
    for i, (label, mapE, send, dval, dispE) in enumerate(params):
        x = 600 + i * 150
        kT = e.obj(x, 140, "t f f f")
        raw = e.obj(x + 80, 170, "f")
        wE = e.obj(x + 60, 200, "expr int($f1*59)")
        mE = e.obj(x, 170, mapE)
        mT = e.obj(x, 200, "t f f")
        snd = e.obj(x + 40, 230, f"s {send}")
        dE = e.obj(x, 260, dispE)
        rowP = e.obj(x, 290, "pack f f")
        sp = e.obj(x, 320, "spigot")
        row = e.msg(x, 350, f"\\; syn-row {i} {label} \\$1 \\$2")
        e.c(rt, kT, i)
        e.c(kT, raw, 2, 1)
        # LFO (apply_lfo.py): value = clip(knob + offset); sound and bar follow it, the knob stays the centre
        base = e.obj(x + 100, 110, "f")
        smE = e.obj(x, 155, "expr max(0 \\, min(1 \\, $f1+$f2))")
        oT = e.obj(x + 100, 80, "t b f")
        e.c(kT, base, 1, 1); e.c(kT, smE, 0)
        e.c(lfoRt, oT, i); e.c(oT, smE, 1, 1); e.c(oT, base, 0); e.c(base, smE, 0, 0)
        smT = e.obj(x, 185, "t f f")
        e.c(smE, smT); e.c(smT, wE, 1); e.c(wE, rowP, 0, 1)
        e.c(smT, mE, 0); e.c(mE, mT); e.c(mT, snd, 1); e.c(mT, dE, 0); e.c(dE, rowP, 0, 0)
        e.c(rowP, sp); e.c(eT, sp, 1, 1); e.c(sp, row)
        e.c(redT, raw, 3 - i); e.c(raw, kT)
    e.save(f"synth-{name}.pd")


for args in ENGINES:
    engine(*args)

# ---------------------------------------------------------------- synth.pd (dispatcher + screen)
s = Patch(1300, 900)
s.text(20, 5, "synth: SYNTH mode. AUX+C again while in SYNTH = next engine (FM SUB PLUK PAD SMPL AIR GLASS WAVE STRING ORGAN DRONE)")
s.obj(700, 5, "text define syn-rows")
lb = s.obj(20, 40, "loadbang")
lbT = s.obj(20, 70, "t b b b")
s.c(lb, lbT)
riT = s.obj(500, 40, "t b b")
riClr = s.msg(600, 70, "\\; syn-rows clear")
rowsInit = s.msg(500, 70, "list - 0 0 \\, list - 0 0 \\, list - 0 0 \\, list - 0 0")
riIns = s.obj(500, 100 - 0, "text insert syn-rows 1e+06")
s.c(lbT, riT, 2); s.c(riT, riClr, 1); s.c(riT, rowsInit, 0); s.c(rowsInit, riIns)
# engine selection
rmode = s.obj(20, 110, "r mode")
mT = s.obj(20, 140, "t f f")
again = s.obj(20, 170, "expr $f1==0 && $f2==0")
s.c(rmode, mT); s.c(mT, again, 1); s.c(mT, again, 0, 1)
prevInit = s.msg(150, 140, "-1")
s.c(lbT, prevInit, 1); s.c(prevInit, again, 0, 1)
ag = s.obj(20, 200, "sel 1")
engF = s.obj(20, 230, "f")
inc = s.obj(20, 260, "+ 1")
md4 = s.obj(20, 290, f"% {len(ENGINES)}")
s.c(again, ag); s.c(ag, engF); s.c(engF, inc); s.c(inc, md4)
engT = s.obj(20, 320, "t f f f b")
s.c(md4, engT)
e0 = s.msg(100, 290, "0")
engSet = s.obj(200, 290 + 20, "t f")
s.c(s.obj(260, 260, "r synth-engine-set"), engSet)
s.c(lbT, e0, 0); s.c(e0, engT)
panic = s.msg(200, 350, "\\; synth-panic stop")
s.c(engT, panic, 3)
s.c(engSet, engT)
s.c(engT, engF, 2, 1)
seng = s.obj(20, 380, "s synth-engine")
s.c(engT, seng, 1)
redisp = s.msg(120, 410, "\\; synth-redisplay bang")
s.c(engT, redisp, 0)
# synth volume (knob 1 with AUX held): 0..1, 0.8 = unity gain
volIn = s.obj(700, 560, "route 1")
s.c(s.obj(700, 530, "r synth-vol-set"), volIn)
volT = s.obj(700, 590, "t f f f")
s.c(volT, s.msg(900, 620, "\\; pkval 52 \\$1 \\; pkval 168 \\$1"), 0)   # volume knob pickup in ctx 13 and 42 (apply_smplloop.py)
s.c(volIn, volT)
volDiv = s.obj(800, 620, "/ 0.8")
volSend = s.obj(800, 650, "s synth-vol")
fVol = s.obj(700, 620, "f 0.8")
s.c(volT, volDiv, 2); s.c(volDiv, volSend); s.c(volT, fVol, 1, 1)
volDef = s.msg(900, 590, "1 0.8")
s.c(s.obj(900, 560, "loadbang"), volDef); s.c(volDef, volIn)
# notes / knobs to the active engine
for i, (src, suffix) in enumerate((("synth-notes", "notes"), ("synth-knob", "knob"))):
    y = 460 + i * 120
    r = s.obj(20, y, f"r {src}")
    lp = s.obj(20, y + 30, "list prepend 0")
    rt = s.obj(20, y + 60, "route " + " ".join(str(k) for k in range(len(ENGINES))))
    if suffix == "knob":
        axLp = s.obj(120, y, "list prepend 0")
        axRt = s.obj(120, y + 15, "route 0 1")
        s.c(s.obj(240, y - 30, "r aux"), axLp, 0, 1)
        s.c(r, axLp); s.c(axLp, axRt)
        # LFO page open (apply_lfo.py): knobs go to the engine's LFO settings
        pgLp = s.obj(120, y + 30, "list prepend 0"); pgRt = s.obj(120, y + 45, "route 0 1")
        s.c(s.obj(240, y, "r syn-lfo-page"), pgLp, 0, 1)
        s.c(axRt, pgLp, 0); s.c(pgLp, pgRt); s.c(pgRt, lp, 0)
        lfLp = s.obj(1400, y + 30, "list prepend 0")
        lfRt = s.obj(1400, y + 60, "route " + " ".join(str(k_) for k_ in range(len(ENGINES))))
        s.c(pgRt, lfLp, 1); s.c(lfLp, lfRt); s.c(engT, lfLp, 2, 1)
        for k_, (nm_, *_r) in enumerate(ENGINES):
            s.c(lfRt, s.obj(1400 + k_ * 110, y + 90, f"s {nm_}-lfo-knob"), k_)
        s.c(axRt, volIn, 1)
    else:
        s.c(r, lp)
    s.c(lp, rt)
    s.c(engT, lp, 2, 1)
    for k, (nm, *_rest) in enumerate(ENGINES):
        s.c(rt, s.obj(20 + k * 110, y + 90, f"s {nm}-{suffix}"), k)
# rows from the active engine
rrow = s.obj(500, 110, "r syn-row")
rrt = s.obj(500, 140, "route 0 1 2 3")
s.c(rrow, rrt)
dirty = s.msg(800, 110, "1")
for k in range(4):
    ts = s.obj(500 + k * 120, 200, f"text set syn-rows {k}")
    tl = s.obj(500 + k * 120, 170, "list")
    s.c(rrt, tl, k); s.c(tl, ts); s.c(rrt, dirty, k)
# screen: redraw on change (max 20 fps), plus a slow refresh
fD = s.obj(800, 200, "f 1")
s.c(dirty, fD, 0, 1)
for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live", "syn-lfo-page", "lfo-cfg", "syn-lfo-p", "smp-phd"):
    r = s.obj(900 + 0, 140 + 0, f"r {name}")
    s.c(r, dirty)
eq0 = s.obj(300, 140, "== 0")
mtr = s.obj(300, 170, "metro 50")
mtrI = s.obj(400, 140, "expr if($f1==4 \\, 150 \\, if($f2 \\, 100 \\, 50))")   # LFO moving a row: 10 frames/s
mtrP = s.obj(450, 80, "expr $f1>=0"); mtrPT = s.obj(450, 110, "t b f")
s.c(s.obj(450, 50, "r syn-lfo-p"), mtrP); s.c(mtrP, mtrPT); s.c(mtrPT, mtrI, 1, 1); s.c(mtrPT, mtrI, 0, 0)      # SMPL page: at most ~7 frames/s (apply_smplfast.py)
s.c(s.obj(400, 110, "r synth-engine"), mtrI); s.c(mtrI, mtr, 0, 1)
s.c(mT, eq0, 0); s.c(eq0, mtr); s.c(mT, dirty, 1)
slow = s.obj(380, 200, "metro 500")
s.c(eq0, slow)
s.c(mtr, fD)
dS = s.obj(800, 230, "sel 1")
dT = s.obj(800, 260, "t b b b b b b b")
z = s.msg(950, 230, "0")
s.c(fD, dS); s.c(dS, dT); s.c(dT, z, 6); s.c(z, fD, 0, 1)
head = s.msg(800, 300, osc5("gShowInfoBar", "ii", "0") + " " + osc5("gClear", "ii", "1") + " " +
             osc5("gPrintln", "iiiiis", "1 1 8 1 SYNTH") + " " + osc5("gFillArea", "iiiiii", "36 0 40 10 1"))
s.c(dT, head, 5)
engF2 = s.obj(800, 340, "f")
s.c(engT, engF2, 2, 1); s.c(dT, engF2, 4)
nmS = s.obj(800, 370, "sel " + " ".join(str(k) for k in range(len(NAMES))))
s.c(engF2, nmS)
for k, nm in enumerate(NAMES):
    m = s.msg(800 + k * 110, 400, osc5("gPrintln", "iiiiis", f"38 1 8 0 {nm}"))
    s.c(nmS, m, k)
octF = s.obj(1100, 340, "f")
s.c(s.obj(1100, 310, "r nst-oct"), octF, 0, 1); s.c(dT, octF, 3)
octM = s.msg(1100, 370, osc5("gPrintln", "iiiiisf", "92 1 8 1 oct \\$1"))
# REC badge while sampling
fRec = s.obj(1250, 340, "f")
s.c(s.obj(1250, 310, "r smp-recording"), fRec, 0, 1)
s.c(s.obj(1350, 310, "r smp-recording"), dirty)
recS = s.obj(1250, 370, "sel 1 0")
recM = s.msg(1250, 400, osc5("gFillArea", "iiiiii", "67 0 21 10 1") + " " + osc5("gPrintln", "iiiiis", "69 1 8 0 REC"))
s.c(dT, fRec, 1); s.c(fRec, recS); s.c(recS, recM, 0)
s.c(dT, s.msg(1250, 430, "\\; mlt-draw bang"), 1)              # MALLET: TYPE name over the number (apply_mallet.py)
# IN badge when the input monitor is on (and not sampling)
fMon = s.obj(1400, 340, "f")
s.c(s.obj(1400, 310, "r smp-monitor"), fMon, 0, 1)
s.c(s.obj(1500, 310, "r smp-monitor"), dirty)
monS = s.obj(1400, 370, "sel 1")
monM = s.msg(1400, 400, osc5("gFillArea", "iiiiii", "67 0 15 10 1") + " " + osc5("gPrintln", "iiiiis", "69 1 8 0 IN"))
fArm = s.obj(1550, 340, "f")
s.c(s.obj(1550, 310, "r smp-armed"), fArm, 0, 1)
s.c(s.obj(1650, 310, "r smp-armed"), dirty)
armS = s.obj(1550, 370, "sel 1 0")
s.c(recS, fArm, 1); s.c(fArm, armS)
s.c(armS, s.msg(1550, 400, osc5("gFillArea", "iiiiii", "67 0 21 10 1") + " " + osc5("gPrintln", "iiiiis", "69 1 8 0 ARM")), 0)
s.c(armS, fMon, 1); s.c(fMon, monS); s.c(monS, monM)
s.c(octF, octM)
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
smKsp = s.obj(1400, 600, "spigot")                     # AUX knobs 2..4 -> SMPL loop points (apply_smplloop.py)
smIs4 = s.obj(1400, 570, "== 4")
s.c(s.obj(1400, 540, "r synth-engine"), smIs4); s.c(smIs4, smKsp, 0, 1)
s.c(volIn, smKsp, 1); s.c(smKsp, s.obj(1400, 630, "s smp-lpk"))
s.c(adKsp, s.obj(1500, 630, "s sub-adsr"))
# project load: ctx 13 knobs 2..4 always reach the ADSR (the engine may not be set yet)
adSet = s.obj(1600, 600, "route 1")
s.c(s.obj(1600, 570, "r synth-vol-set"), adSet)
s.c(adSet, s.obj(1600, 630, "s sub-adsr"), 1)

# 4 parameter rows: label, value, bar
rowsT = s.obj(800, 450, "t b b b b")
engF3 = s.obj(700, 420, "f")
s.c(engT, engF3, 2, 1)
auxD = s.obj(600, 420, "f")
s.c(s.obj(600, 390, "r aux"), auxD, 0, 1)
s.c(s.obj(520, 390, "r aux"), dirty)
s.c(s.obj(520, 360, "r synth-vol"), dirty)
auxDS = s.obj(600, 450, "sel 1 0")
s.c(dT, auxD, 2); s.c(auxD, auxDS)
# LFO page (apply_lfo.py): synth-lfo.pd draws it inside this frame
lpD = s.obj(2000, 450, "f 0")
s.c(s.obj(2000, 420, "r syn-lfo-page"), lpD, 0, 1)
lpDS = s.obj(2000, 480, "sel 1")
s.c(auxDS, lpD, 1); s.c(lpD, lpDS)
s.c(lpDS, s.obj(2000, 510, "s syn-lfo-draw"), 0)
lpNo = s.obj(2100, 510, "t b")
s.c(lpDS, lpNo, 1); s.c(lpNo, engF3)
volE = s.obj(600, 480, "expr int($f1*100+0.5) \\; int($f1*124)")
volP = s.obj(600, 510, "pack f f")
auxEng = s.obj(500, 480, "f")
s.c(engT, auxEng, 2, 1)
auxEngS = s.obj(500, 510, "sel 1 4")
s.c(auxDS, auxEng, 0); s.c(auxEng, auxEngS)
auxNo = s.obj(560, 525, "t b")                         # [sel] reject passes the number: make it a bang
s.c(auxEngS, s.obj(450, 540, "s syn-extra"), 1)    # SMPL + AUX: its own page (apply_smplloop.py)
s.c(auxEngS, auxNo, 2); s.c(auxNo, fVol); s.c(fVol, volE); s.c(volE, volP, 1, 1); s.c(volE, volP, 0, 0)
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
                  osc5("gFillArea", "iiiiii", f"66 {yf} \\$2 5 1")))
s.c(volP, s.msg(600, 540, osc5("gPrintln", "iiiiiss", "1 14 8 1 VOLUME SYNTH") + " " +
                osc5("gPrintln", "iiiiif", "4 24 24 1 \\$1") + " " + osc5("gBox", "iiiiii", "0 52 128 9 1") + " " +
                osc5("gFillArea", "iiiiii", "2 54 \\$2 5 1")))
engS4 = s.obj(700, 450, "sel 4")
s.c(engF3, engS4)
s.c(engS4, s.obj(700, 480, "s syn-extra"), 0)   # smpl.pd draws its page here, inside this frame
s.c(engS4, rowsT, 1)
for k in range(4):
    yt, yb, yf = 14 + 12 * k, 13 + 12 * k, 15 + 12 * k
    n = s.msg(800 + k * 120, 480, f"{k}")
    tg = s.obj(800 + k * 120, 510, "text get syn-rows")
    lp = s.obj(800 + k * 120, 540, f"list prepend {yt}")
    la = s.obj(800 + k * 120, 570, f"list append {yb} {yf}")
    m = s.msg(800 + k * 120, 600 + k * 40,
              osc5("gPrintln", "iiiiis", "1 \\$1 8 1 \\$2") + " " +
              osc5("gPrintln", "iiiiif", "34 \\$1 8 1 \\$3") + " " +
              osc5("gBox", "iiiiii", "64 \\$5 63 9 1") + " " +
              osc5("gFillArea", "iiiiii", "66 \\$6 \\$4 5 1"))
    s.c(rowsT, n, 3 - k); s.c(n, tg); s.c(tg, lp); s.c(lp, la)
    laT = s.obj(800 + k * 120, 585, "t l l")
    s.c(la, laT); s.c(laT, m, 1)
    mkSp = s.obj(2200 + k * 120, 600, "spigot")                    # label inverted while the LFO moves it
    mkEq = s.obj(2200 + k * 120, 570, f"== {k}")
    s.c(s.obj(2200 + k * 120, 540, "r syn-lfo-p"), mkEq); s.c(mkEq, mkSp, 0, 1); s.c(laT, mkSp, 0)
    s.c(mkSp, s.msg(2200 + k * 120, 630, osc5("gFillArea", "iiiiii", "0 \\$5 33 10 1") + " " +
                    osc5("gPrintln", "iiiiis", "1 \\$1 8 0 \\$2")))
flip = s.msg(800, 780, "\\; oscOut sendtyped /oled/gFlip i 3")
s.c(dT, flip, 0)

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
s.save("synth.pd")

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
for i_, nm_ in enumerate(['off', 'sine', 'tri', 'squ', 'ramp', 'rand', 'drft', 'trem', 'env']):
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


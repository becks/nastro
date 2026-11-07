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
        ("LOOP", "expr $f1>0.5", "smp-loop", 0.0, "t f"),
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
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS"]


# ---------------------------------------------------------------- voices
def sub_voice():
    v = Patch(800, 600)
    v.text(20, 5, "sub-voice: 2 detuned saws -> resonant lowpass (vcf~) with filter envelope")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
    voice_switch(v, inl, fixed=2000)
    upn = v.obj(200, 100, "unpack f f"); mt = v.obj(200, 130, "mtof"); fq = v.obj(200, 160, "sig~")
    upv = v.obj(20, 100, "unpack f f"); mos = v.obj(60, 130, "moses 1")
    v.c(inl, tll); v.c(tll, upn, 1); v.c(upn, mt); v.c(mt, fq); v.c(tll, upv, 0); v.c(upv, mos, 1)
    # amp env
    on = v.obj(110, 160, "t b b")
    atk = v.msg(110, 190, "1 5"); rel = v.msg(20, 190, "0 250")
    aenv = v.obj(20, 220, "line~")
    v.c(mos, on, 1); v.c(on, atk, 1); v.c(atk, aenv); v.c(mos, rel, 0); v.c(rel, aenv)
    # filter env: jump to 1, decay over 400 ms
    fe = v.msg(160, 220, "1 \\, 0 400")
    fenv = v.obj(160, 250, "vline~")
    v.c(on, fe, 0); v.c(fe, fenv)
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


# ---------------------------------------------------------------- engines
def engine(name, eid, voice, gain, params, voices=4):
    e = Patch(1200, 700)
    e.text(20, 5, f"synth-{name}: engine {eid} ({NAMES[eid]}). knobs: " + " / ".join(p[0] for p in params))
    rn = e.obj(20, 40, f"r {name}-notes"); rp = e.obj(160, 40, "r synth-panic")
    poly = e.obj(20, 80, f"poly {voices} 1"); pk = e.obj(20, 110, "pack f f f")
    cl = e.obj(20, 140, f"clone -s 1 {voice} {voices}")
    g = e.obj(20, 180, f"*~ {gain}"); cp = e.obj(20, 210, "clip~ -1 1")
    th = e.obj(20, 250, "throw~ synth-bus")
    e.c(rn, poly); e.c(rp, poly)
    e.c(poly, pk, 0, 0); e.c(poly, pk, 1, 1); e.c(poly, pk, 2, 2)
    vR = e.obj(160, 150, "r synth-vol"); vM = e.msg(160, 180, "\\$1 20"); vL = e.obj(160, 210, "line~")
    vG = e.obj(20, 195, "*~")
    e.c(vR, vM); e.c(vM, vL)
    e.c(pk, cl); e.c(cl, g); e.c(g, vG, 0, 0); e.c(vL, vG, 0, 1); e.c(vG, cp); e.c(cp, th)
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
        e.c(kT, raw, 2, 1); e.c(kT, wE, 1); e.c(wE, rowP, 0, 1)
        e.c(kT, mE, 0); e.c(mE, mT); e.c(mT, snd, 1); e.c(mT, dE, 0); e.c(dE, rowP, 0, 0)
        e.c(rowP, sp); e.c(eT, sp, 1, 1); e.c(sp, row)
        e.c(redT, raw, 3 - i); e.c(raw, kT)
    e.save(f"synth-{name}.pd")


for args in ENGINES:
    engine(*args)

# ---------------------------------------------------------------- synth.pd (dispatcher + screen)
s = Patch(1300, 900)
s.text(20, 5, "synth: SYNTH mode. AUX+C again while in SYNTH = next engine (FM SUB PLUK PAD SMPL AIR GLASS)")
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
        s.c(r, axLp); s.c(axLp, axRt); s.c(axRt, lp, 0)
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
for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live"):
    r = s.obj(900 + 0, 140 + 0, f"r {name}")
    s.c(r, dirty)
eq0 = s.obj(300, 140, "== 0")
mtr = s.obj(300, 170, "metro 50")
s.c(mT, eq0, 0); s.c(eq0, mtr); s.c(mT, dirty, 1)
slow = s.obj(380, 200, "metro 500")
s.c(eq0, slow)
s.c(mtr, fD)
dS = s.obj(800, 230, "sel 1")
dT = s.obj(800, 260, "t b b b b b b b")
z = s.msg(950, 230, "0")
s.c(fD, dS); s.c(dS, dT); s.c(dT, z, 6); s.c(z, fD, 0, 1)
head = s.msg(800, 300, osc5("gShowInfoBar", "ii", "0") + " " + osc5("gClear", "ii", "1") + " " +
             osc5("gPrintln", "iiiiis", "1 1 8 1 SYNTH") + " " + osc5("gFillArea", "iiiiii", "36 0 34 10 1"))
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
# 4 parameter rows: label, value, bar
rowsT = s.obj(800, 450, "t b b b b")
engF3 = s.obj(700, 420, "f")
s.c(engT, engF3, 2, 1)
auxD = s.obj(600, 420, "f")
s.c(s.obj(600, 390, "r aux"), auxD, 0, 1)
s.c(s.obj(520, 390, "r aux"), dirty)
s.c(s.obj(520, 360, "r synth-vol"), dirty)
auxDS = s.obj(600, 450, "sel 1 0")
s.c(dT, auxD, 2); s.c(auxD, auxDS); s.c(auxDS, engF3, 1)
volE = s.obj(600, 480, "expr int($f1*100+0.5) \\; int($f1*124)")
volP = s.obj(600, 510, "pack f f")
s.c(auxDS, fVol, 0); s.c(fVol, volE); s.c(volE, volP, 1, 1); s.c(volE, volP, 0, 0)
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
    s.c(rowsT, n, 3 - k); s.c(n, tg); s.c(tg, lp); s.c(lp, la); s.c(la, m)
flip = s.msg(800, 780, "\\; oscOut sendtyped /oled/gFlip i 3")
s.c(dT, flip, 0)
s.save("synth.pd")

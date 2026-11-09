#!/usr/bin/env python3
"""PIANO, the 12th synth engine: a lo-fi felt piano with an audible sustain pedal. No samples.
Voice (6 voices, piano-voice.pd): modal synthesis, ported from the felt piano of the minichord-kalimba firmware:
7 two-pole resonators ([biquad~]) - two strings per note a fraction of a hertz apart, partials 2..5 slightly
stretched, each with its own decay (shorter for higher notes) - struck by a half-sine hammer pulse: more FELT =
a longer pulse, which reaches the high modes less (the fundamental is brought back to full level), plus a short
contact click. NOISE scales the hammer thump and the key-release click. Damping (released without the pedal, or
the pedal lifted) shortens the resonators' decay to 0.15 s; the voice's DSP goes off when it is damped or silent.
Engine output (piano-post.pd): body resonance (110 Hz), sympathetic resonance (4 tuned combs, only while the pedal is down), pedal noises
(down / up: thump + rustle), lo-fi: high cut, wow and a hiss that follows the playing (no saturation: on
the first version it sounded like clipping).
Pedal: the footswitch, while SYNTH is shown with PIANO (elsewhere it still starts tape recording).
Knob contexts: engine 11 would fall on 27 (MIX sends) and its LFO on 40 (ARP): they get 43 and 44 (pkval 180)."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py", "gentape.py"):
    shutil.copy(f, f + ".pre-piano")


def edit(p, pairs):
    with open(p) as f_:
        s = f_.read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    with open(p, "w") as f_:
        f_.write(s)


VOICE = r'''

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
'''

# ------------------------------------------------------------------ gensynth: voice, engine entry, post stage
s = open("gensynth.py").read()
a = "wave_voice(); strg_voice(); organ_voice(); drone_voice()\n"
assert s.count(a) == 1
s = s.replace(a, a + VOICE)
a = '''    ("drone", 10, "drone-voice", 1.6, ['''
assert s.count(a) == 1
i = s.index(a)
j = s.index("]),\n]", i) + len("]),\n")
s = s[:j] + '''    ("piano", 11, "piano-voice", 0.25, [                                          # apply_piano.py
        ("FELT", "t f", "piano-felt", 0.7, "expr int($f1*100)"),
        ("DECAY", "expr int(1500+pow($f1 \\\\, 2)*18500)", "piano-dec", 0.5, "expr int($f1/100)/10.0"),
        ("LOFI", "t f", "piano-lofi", 0.4, "expr int($f1*100)"),
        ("NOISE", "t f", "piano-noise", 0.5, "expr int($f1*100)"),
    ], 6),
''' + s[j:]
a = 'NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS", "WAVE", "STRING", "ORGAN", "DRONE"]'
assert s.count(a) == 1
s = s.replace(a, 'NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "AIR", "GLASS", "WAVE", "STRING", "ORGAN", "DRONE", "PIANO"]')
# engine(): PIANO gets its post stage before the clip (its soft limiter keeps chords off the hard clip)
a = "    e.c(pk, cl); e.c(cl, g); e.c(g, vG, 0, 0); e.c(vL, vG, 0, 1); e.c(vG, cp); e.c(cp, th)"
assert s.count(a) == 1
s = s.replace(a, '''    e.c(pk, cl); e.c(cl, g); e.c(g, vG, 0, 0); e.c(vL, vG, 0, 1)
    if name == "piano":                                   # felt piano: resonance, pedal noises, lo-fi, soft limiter (apply_piano.py)
        post = e.obj(20, 205, "piano-post")
        e.c(vG, post); e.c(post, cp)
    else:
        e.c(vG, cp)
    e.c(cp, th)''')
with open("gensynth.py", "w") as f_:
    f_.write(s)

# ------------------------------------------------------------------ gen.py: instance, knob contexts 43 / 44
PDEF = "0.7 0.5 0.4 0.5 0 0.3 0.5 0"
edit("gen.py", [
    ('m.obj(960, 760, "synth-drone")', 'm.obj(960, 760, "synth-drone")\nm.obj(1040, 760, "synth-piano")'),
    ('if($f1==0 && $f5==0 && $f6==1 \\\\, 29+$f3 \\\\,', 'if($f1==0 && $f5==0 && $f6==1 \\\\, if($f3==11 \\\\, 44 \\\\, 29+$f3) \\\\,'),
    ('if($f1==0 && $f3>0 \\\\, if($f3==4 \\\\, 10 \\\\,', 'if($f1==0 && $f3>0 \\\\, if($f3==11 \\\\, 43 \\\\, if($f3==4 \\\\, 10 \\\\,'),
    ('m.obj(560, 530, "table pkval 172")', 'm.obj(560, 530, "table pkval 180")'),
    ('m.obj(680, 530, "table pkpick 172")', 'm.obj(680, 530, "table pkpick 180")'),
    (' 0.8 0 1 0 \\\\; pkphys', f' 0.8 0 1 0 {PDEF} \\\\; pkphys'),
])
# the inner if() added for engine 11 needs its closing parenthesis: right after the engine branch
s = open("gen.py").read()
a = "if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3)))"
assert s.count(a) == 1
s = s.replace(a, "if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3))))")
with open("gen.py", "w") as f_:
    f_.write(s)

# ------------------------------------------------------------------ genproj: load contexts 43 / 44, older projects
s = open("genproj.py").read()
a = '(42, "smp-aux-set")]'
assert s.count(a) == 1
s = s.replace(a, '(42, "smp-aux-set"), (43, "piano-knob"), (44, "piano-lfo-knob")]')
a = "# projects saved before the SMPL loop points:"
assert s.count(a) == 1
SUM = "+".join(f"abs(pkval[{i}]-pkval[172])" for i in range(173, 180))
s = s.replace(a, f'''# projects saved before PIANO: slots 172..179 all equal (Pd repeats the last value) -> defaults (apply_piano.py)
fixE13 = p.obj(-300, 790, "expr {SUM}==0")
fixS13 = p.obj(-300, 820, "sel 1")
p.c(fixT, fixE13, 1); p.c(fixE13, fixS13); p.c(fixS13, p.msg(-300, 850, "\\\\; pkval 172 {PDEF}"))
''' + a)
with open("genproj.py", "w") as f_:
    f_.write(s)

# ------------------------------------------------------------------ gentape: footswitch = pedal on SYNTH with PIANO
edit("gentape.py", [
    ('t.c(rak, kDf); t.c(kDf, selk); t.c(rfs, fDf); t.c(fDf, fs1)',
     '''t.c(rak, kDf); t.c(kDf, selk); t.c(fDf, fs1)
# footswitch: sustain pedal while SYNTH shows PIANO, tape record everywhere else (apply_piano.py)
t.obj(400, 40, "v nstmode"); t.obj(480, 40, "v nsteng")
t.c(t.obj(400, 10, "r mode"), t.obj(400, 25, "v nstmode")); t.c(t.obj(480, 10, "r synth-engine"), t.obj(480, 25, "v nsteng"))
fsT = t.obj(260, 105, "t f f")
fsPE = t.obj(360, 120, "expr if(nstmode==0 && nsteng==11 \\\\, $f1 \\\\, -1)")
fsPM = t.obj(360, 135, "moses 0")
fsRE = t.obj(260, 120, "expr nstmode!=0 || nsteng!=11")
fsRS = t.obj(260, 135, "spigot")
t.c(rfs, fsT); t.c(fsT, fsPE, 1); t.c(fsPE, fsPM); t.c(fsPM, t.obj(360, 150, "s piano-pedal"), 1)
t.c(fsT, fsRE, 0); t.c(fsRE, fsRS, 0, 1); t.c(fsT, fsRS, 0); t.c(fsRS, fDf)
# leaving SYNTH or PIANO lifts the pedal
pLvE = t.obj(560, 25, "expr $f1!=0 || $f2!=11")
pLvT = t.obj(640, 10, "t b f")
t.c(t.obj(560, -20, "r mode"), pLvE, 0, 0); t.c(t.obj(640, -20, "r synth-engine"), pLvT)
t.c(pLvT, pLvE, 1, 1); t.c(pLvT, pLvE, 0, 0)
pLvS = t.obj(560, 40, "sel 1")
t.c(pLvE, pLvS); t.c(pLvS, t.msg(560, 55, "\\\\; piano-pedal 0"))'''),
])
print("piano applied")

#!/usr/bin/env python3
"""MALLET, the 13th synth engine: the struck instruments of the minichord-kalimba firmware, by modal synthesis.
TYPE: toy piano, kalimba, kalimba with buzz, handpan, steel pan, marimba, vibraphone, glockenspiel, bells,
gamelan (the felt piano is the PIANO engine). HARD = mallet hardness (a shorter half-sine strike reaches the high
modes more), DECAY = 1/4 .. 4 x the instrument's ring, REL = what a released key does: at the top the note rings
on (no dampers, like the real instruments), lower values damp it (T60 0.08 .. 6 s).
Voice (mallet-voice.pd, 6 voices): up to 7 two-pole resonators ([biquad~]) whose ratios, levels, decays and
detunes come from the tables mltr / mlta / mltd / mltt, filled when TYPE changes; contact click = high-passed
noise (as the minichord). Engine output (mallet-post.pd, before the clip): body resonances (up to 2 band-passes),
buzz (the part of the wave above 0.2, with noise, high-passed: loose metal on a kalimba), tremolo (vibraphone
motor), soft limiter above 0.8. The TYPE row shows the instrument's name (drawn over the number).
Knob contexts: engine 12 would fall on 28 (MIX sends) and its LFO on 41 (ARP + AUX): they get 45 and 46
(pkval 188)."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-mallet")


def edit(p, pairs):
    with open(p) as f_:
        s = f_.read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70])
        s = s.replace(a, b)
    with open(p, "w") as f_:
        f_.write(s)


# name, base decay s, click, level, buzz, tremolo rate, depth, body [(f, q, gain)], modes [(ratio, amp, decay, detune)]
# (values from minichord-kalimba src/instruments.h; levels re-balanced for Nastro: every type's single
# note peaks about the same - the minichord evened them out with a tanh at its output)
TYPES = [
    ("toy", 1.8, 0.15, 0.636, 0, 0, 0, [(420, 4, 0.6), (1600, 3, 0.3)],
     [(1.0, 0.8, 1.0, 0), (1.0, 0.3, 1.0, 2.0), (6.27, 0.45, 0.35, 0), (6.27, 0.15, 0.35, 9.0), (17.55, 0.2, 0.12, 0)]),
    ("kalim", 2.5, 0.12, 0.815, 0, 0, 0, [(230, 5, 0.5), (820, 3, 0.25)],
     [(1.0, 1.0, 1.0, 0), (6.27, 0.30, 0.25, 0), (17.55, 0.10, 0.08, 0)]),
    ("kbuzz", 2.5, 0.12, 0.786, 2.0, 0, 0, [(230, 5, 0.5), (820, 3, 0.25)],
     [(1.0, 1.0, 1.0, 0), (6.27, 0.30, 0.25, 0), (17.55, 0.10, 0.08, 0)]),
    ("hpan", 5.0, 0.02, 0.858, 0, 0, 0, [],
     [(1.0, 0.7, 1.0, 0), (1.0, 0.5, 1.0, 0.7), (2.0, 0.45, 0.75, 0), (2.0, 0.3, 0.75, 1.1), (3.0, 0.25, 0.5, 0), (3.0, 0.15, 0.5, 1.6)]),
    ("steel", 1.6, 0.05, 0.972, 0, 0, 0, [],
     [(1.0, 1.0, 1.0, 0), (2.0, 0.6, 0.6, 0), (2.0, 0.2, 0.6, 1.5), (3.0, 0.35, 0.4, 0), (4.0, 0.2, 0.3, 0)]),
    ("marim", 1.2, 0.05, 1.154, 0, 0, 0, [],
     [(1.0, 1.0, 1.0, 0), (3.93, 0.35, 0.25, 0), (9.2, 0.12, 0.1, 0)]),
    ("vibes", 4.0, 0.03, 1.599, 0, 5.5, 0.45, [],
     [(1.0, 1.0, 1.0, 0), (4.0, 0.25, 0.3, 0), (10.0, 0.06, 0.1, 0)]),
    ("glock", 3.0, 0.08, 1.082, 0, 0, 0, [],
     [(1.0, 1.0, 1.0, 0), (2.76, 0.4, 0.5, 0), (5.40, 0.2, 0.3, 0), (8.93, 0.1, 0.2, 0)]),
    ("bells", 6.0, 0.02, 0.69, 0, 0, 0, [],
     [(0.5, 0.5, 1.6, 0), (1.0, 0.6, 1.0, 0), (1.2, 0.45, 0.8, 0), (1.5, 0.25, 0.6, 0), (2.0, 0.5, 0.5, 0), (2.5, 0.2, 0.35, 0), (3.0, 0.15, 0.3, 0)]),
    ("gamel", 3.5, 0.06, 0.954, 0, 0, 0, [],
     [(1.0, 0.7, 1.0, 0), (1.0, 0.5, 1.0, 5.0), (2.71, 0.3, 0.4, 0), (4.95, 0.12, 0.2, 0)]),
]
NM = 7


def type_message(t):
    name, base, click, level, buzz, trate, tdepth, body, modes = t
    modes = modes + [(1.0, 0, 1.0, 0)] * (NM - len(modes))
    body = body + [(1000, 1, 0)] * (2 - len(body))
    cols = list(zip(*modes))
    parts = [f"mltr 0 {' '.join(str(v) for v in cols[0])}", f"mlta 0 {' '.join(str(v) for v in cols[1])}",
             f"mltd 0 {' '.join(str(v) for v in cols[2])}", f"mltt 0 {' '.join(str(v) for v in cols[3])}",
             f"mlt-base {base}", f"mlt-click {click}", f"mlt-level {level}", f"mlt-buzz {buzz}",
             f"mlt-trem {trate} {tdepth}", f"mlt-body {body[0][0]} {body[0][1]} {body[0][2]} {body[1][0]} {body[1][1]} {body[1][2]}"]
    return " ".join("\\\\; " + p_ for p_ in parts)


CODE = r'''

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
'''

s = open("gensynth.py").read()
a = "piano_voice(); piano_post()\n"
assert s.count(a) == 1
types_py = "MLT_TYPES = [\n" + "".join(f'    "{type_message(t)}",\n' for t in TYPES) + "]\n"
names_py = "MLT_NAMES = [" + ", ".join(f'"{t[0]}"' for t in TYPES) + "]\n"
s = s.replace(a, a + "\n" + types_py + names_py + CODE)
a = '''        ("NOISE", "t f", "piano-noise", 0.5, "expr int($f1*100)"),
    ], 6),
'''
assert s.count(a) == 1
s = s.replace(a, a + '''    ("mallet", 12, "mallet-voice", 0.2, [                                       # apply_mallet.py
        ("TYPE", "expr int(min($f1 \\\\, 0.999)*10)", "mlt-type", 0.05, "expr $f1+1"),
        ("HARD", "t f", "mlt-hard", 0.5, "expr int($f1*100)"),
        ("DECAY", "expr 0.25*pow(16 \\\\, $f1)", "mlt-dec", 0.5, "expr int($f1*100)/100"),
        ("REL", "t f", "mlt-rel", 1.0, "expr int($f1*100)"),
    ], 6),
''')
a = '"STRING", "ORGAN", "DRONE", "PIANO"]'
assert s.count(a) == 1
s = s.replace(a, '"STRING", "ORGAN", "DRONE", "PIANO", "MALLET"]')
a = '''    if name == "piano":                                   # felt piano: resonance, pedal noises, lo-fi, soft limiter (apply_piano.py)
        post = e.obj(20, 205, "piano-post")
        e.c(vG, post); e.c(post, cp)'''
assert s.count(a) == 1
s = s.replace(a, '''    if name in ("piano", "mallet"):                       # their own output stage before the clip (apply_piano.py, apply_mallet.py)
        post = e.obj(20, 205, f"{name}-post")
        e.c(vG, post); e.c(post, cp)''')
# synth.pd: after the rows (badges outlet), let mallet-post print the TYPE name
a = "s.c(dT, fRec, 1); s.c(fRec, recS); s.c(recS, recM, 0)"
assert s.count(a) == 1
s = s.replace(a, a + '\ns.c(dT, s.msg(1250, 430, "\\\\; mlt-draw bang"), 1)              # MALLET: TYPE name over the number (apply_mallet.py)')
with open("gensynth.py", "w") as f_:
    f_.write(s)

# ------------------------------------------------------------------ gen.py: instance, knob contexts 45 / 46
MDEF = "0.05 0.5 0.5 1 0 0.3 0.5 0"
edit("gen.py", [
    ('m.obj(1040, 760, "synth-piano")', 'm.obj(1040, 760, "synth-piano")\nm.obj(1120, 760, "synth-mallet")'),
    ('if($f3==11 \\\\, 44 \\\\, 29+$f3)', 'if($f3==11 \\\\, 44 \\\\, if($f3==12 \\\\, 46 \\\\, 29+$f3))'),
    ('if($f3==11 \\\\, 43 \\\\, if($f3==4 \\\\, 10 \\\\,', 'if($f3==11 \\\\, 43 \\\\, if($f3==12 \\\\, 45 \\\\, if($f3==4 \\\\, 10 \\\\,'),
    ("if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3))))", "if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3)))))"),
    ('m.obj(560, 530, "table pkval 180")', 'm.obj(560, 530, "table pkval 188")'),
    ('m.obj(680, 530, "table pkpick 180")', 'm.obj(680, 530, "table pkpick 188")'),
    (' 0.7 0.5 0.4 0.5 0 0.3 0.5 0 \\\\; pkphys', f' 0.7 0.5 0.4 0.5 0 0.3 0.5 0 {MDEF} \\\\; pkphys'),
])

# ------------------------------------------------------------------ genproj: load contexts 45 / 46, older projects
s = open("genproj.py").read()
a = '(43, "piano-knob"), (44, "piano-lfo-knob")]'
assert s.count(a) == 1
s = s.replace(a, '(43, "piano-knob"), (44, "piano-lfo-knob"), (45, "mallet-knob"), (46, "mallet-lfo-knob")]')
a = "# projects saved before PIANO:"
assert s.count(a) == 1
SUM = "+".join(f"abs(pkval[{i}]-pkval[180])" for i in range(181, 188))
s = s.replace(a, f'''# projects saved before MALLET: slots 180..187 all equal (Pd repeats the last value) -> defaults (apply_mallet.py)
fixE14 = p.obj(-400, 790, "expr {SUM}==0")
fixS14 = p.obj(-400, 820, "sel 1")
p.c(fixT, fixE14, 1); p.c(fixE14, fixS14); p.c(fixS14, p.msg(-400, 850, "\\\\; pkval 180 {MDEF}"))
''' + a)
with open("genproj.py", "w") as f_:
    f_.write(s)
print("mallet applied")

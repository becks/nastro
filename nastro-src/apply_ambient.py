#!/usr/bin/env python3
"""Two ambient synth engines: 5 ARIA (noise resonating at the note: breath <-> whistle, slow random motion)
and 6 VETRO (glass / bells: 4 partials with their own decays, harmonic <-> inharmonic, slow beating; 6 voices).
Engine cycle AUX+C in SYNTH goes FM SUB PLUK PAD SMPL ARIA VETRO. Knob contexts 18 / 19 (pkval 80)."""
import shutil

for f in ("gensynth.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-ambient")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


ENG = r'''    ("air", 5, "air-voice", 1.8, [
        ("ATK", "expr int(10+pow($f1 \\, 2)*3990)", "air-atk", 0.5, "t f"),
        ("REL", "expr int(100+pow($f1 \\, 2)*7900)", "air-rel", 0.5, "t f"),
        ("Q", "expr 2*pow(30 \\, $f1)", "air-q", 0.5, "expr int($f1)"),
        ("MOTO", "t f", "air-mot", 0.4, "expr int($f1*100)"),
    ]),
    ("bell", 6, "bell-voice", 0.3, [
        ("DECAY", "expr int(300+pow($f1 \\, 2)*14700)", "bell-dec", 0.4, "expr int($f1/100)/10.0"),
        ("BRITE", "expr 0.2+$f1*0.8", "bell-brite", 0.5, "expr int($f1*100)"),
        ("INARM", "t f", "bell-str", 0.7, "expr int($f1*100)"),
        ("BATT", "expr $f1*2.5", "bell-beat", 0.3, "expr int($f1*10)/10.0"),
    ], 6),
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL", "ARIA", "VETRO"]'''

VOICES = r'''

def air_voice():
    """noise -> 2 band-pass filters at the note and its octave (Q: breath .. whistle), slow random motion"""
    v = Patch(900, 700)
    v.text(20, 5, "air-voice: noise through 2 resonant band-passes (note + octave) - slow LFO on pitch and level")
    inl = v.obj(20, 40, "inlet"); tll = v.obj(20, 70, "t l l")
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


air_voice(); bell_voice()'''

edit("gensynth.py", [
    ('''    ]),
]
NAMES = ["FM", "SUB", "PLUK", "PAD", "SMPL"]''', '''    ]),
''' + ENG),
    ('sub_voice(); pluk_voice(); pad_voice()', 'sub_voice(); pluk_voice(); pad_voice()' + VOICES),
    ('def engine(name, eid, voice, gain, params):', 'def engine(name, eid, voice, gain, params, voices=4):'),
    ('poly = e.obj(20, 80, "poly 4 1")', 'poly = e.obj(20, 80, f"poly {voices} 1")'),
    ('cl = e.obj(20, 140, f"clone -s 1 {voice} 4")', 'cl = e.obj(20, 140, f"clone -s 1 {voice} {voices}")'),
    ('md4 = s.obj(20, 290, "% 5")', 'md4 = s.obj(20, 290, f"% {len(ENGINES)}")'),
    ('nmS = s.obj(800, 370, "sel 0 1 2 3 4")', 'nmS = s.obj(800, 370, "sel " + " ".join(str(k) for k in range(len(NAMES))))'),
    ('AUX+C again while in SYNTH = next engine (FM SUB PLUK PAD)', 'AUX+C again while in SYNTH = next engine (FM SUB PLUK PAD SMPL ARIA VETRO)'),
    ('    rt = s.obj(20, y + 60, "route 0 1 2 3 4")', '    rt = s.obj(20, y + 60, "route " + " ".join(str(k) for k in range(len(ENGINES))))'),
])

DEF = "0.5 0.5 0.5 0.4 0.4 0.5 0.7 0.3"     # ARIA, VETRO knob defaults (pkval 72..79)
edit("gen.py", [
    ('m.obj(880, 680, "synth-pad")', 'm.obj(880, 680, "synth-pad")\nm.obj(880, 720, "synth-air")\nm.obj(960, 720, "synth-bell")'),
    ('m.obj(560, 530, "table pkval 72")', 'm.obj(560, 530, "table pkval 80")'),
    ('m.obj(680, 530, "table pkpick 72")', 'm.obj(680, 530, "table pkpick 80")'),
    ('if($f3==4 \\\\, 10 \\\\, 5+$f3)', 'if($f3==4 \\\\, 10 \\\\, if($f3>=5 \\\\, 13+$f3 \\\\, 5+$f3))'),
    ('0.6 0.45 0.1 1 \\\\; pkphys', f'0.6 0.45 0.1 1 {DEF} \\\\; pkphys'),
])

edit("genproj.py", [
    ('(17, "endl-set")]', '(17, "endl-set"), (18, "air-knob"), (19, "bell-knob")]'),
    ('p.c(fixT, fixE3, 1)', '''fixE4 = p.obj(600, 790, "expr pkval[72]+pkval[73]+pkval[74]+pkval[75]+pkval[76]+pkval[77]+pkval[78]+pkval[79]==0")
fixS4 = p.obj(600, 820, "sel 1")
p.c(fixT, fixE4, 1); p.c(fixE4, fixS4); p.c(fixS4, p.msg(600, 850, "\\\\; pkval 72 ''' + DEF + '''"))
p.c(fixT, fixE3, 1)'''),
])
s = open("gensynth.py").read()
s = s.replace('"36 0 30 10 1"', '"36 0 34 10 1"')      # engine name box wide enough for VETRO
open("gensynth.py", "w").write(s)
print("ambient applied")

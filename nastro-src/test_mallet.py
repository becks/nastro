#!/usr/bin/env python3
"""MALLET engine (apply_mallet.py). Every TYPE plays C4 for 0.6 s: sound, pitch (261.6 Hz; bells may show their hum
an octave below - checked as hum + strike note -, gamelan's pair beats a few Hz apart), peak below 1. REL at the top: the note rings after the
release; REL 0: it is damped. A loud 6-note chord stays below the clip. The SYNTH page prints the TYPE's name."""
import os, shutil, subprocess, struct, math, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
NAMES = ["toy", "kalim", "kbuzz", "hpan", "steel", "marim", "vibes", "glock", "bells", "gamel"]
ev = [(300, ["synth-engine-set 12", "synth-knob 4 1"])]
t = 600
for k in range(10):
    ev += [(t, [f"synth-knob 1 {(k + 0.5) / 10}"]), (t + 100, [f"rec{k} bang", "notes 60 100"]), (t + 400, ["notes 60 0"])]
    t += 1000
ev += [(t, ["synth-knob 1 0.05", "synth-knob 4 1"]), (t + 100, ["recR bang", "notes 60 100"]), (t + 300, ["notes 60 0"])]
t += 4500                                                   # the REL-top note has died away before the next test
ev += [(t, ["synth-knob 4 0"]), (t + 100, ["recD bang", "notes 60 100"]), (t + 300, ["notes 60 0"])]
t += 1200
ev += [(t, ["synth-knob 2 1", "synth-knob 4 1"]), (t + 100, ["recC bang"] + [f"notes {n} 127" for n in (48, 55, 60, 64, 67, 72)])]
t += 1200
ev += [(t, ["dump bang"]), (t + 200, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2


def add(s):
    global n
    L.append(s); n += 1
    return n - 1


cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
caps = [str(k) for k in range(10)] + ["R", "D", "C"]
dumps = []
for nm in caps:
    add(f"#X obj 1100 120 table cap{nm} {int(1.0 * SR)};")
    tw = add(f"#X obj 1100 90 tabwrite~ cap{nm};"); r_ = add(f"#X obj 1100 60 r rec{nm};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {r_} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/{nm}.wav cap{nm}")
sf2 = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf2} 0;"]
ow = add("#X obj 1500 20 r oscOut;"); orr = add("#X obj 1500 50 route sendtyped;"); op = add("#X obj 1500 80 print OSC;")
C += [f"#X connect {ow} 0 {orr} 0;", f"#X connect {orr} 0 {op} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if ("error" in l) and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])


W = {nm: rd_(f"{T}/{nm}.wav") for nm in caps}
shutil.rmtree(T)
rms = lambda x, a, b: math.sqrt(sum(v * v for v in x[int(a * SR):int(b * SR)]) / max(1, int((b - a) * SR)))


def pitch(x, a, b, lo_hz=100, hi_hz=320):
    seg = x[int(a * SR):int(b * SR)]
    lo, hi = int(SR / hi_hz), int(SR / lo_hz)
    c = [sum(seg[i] * seg[i + lg] for i in range(2048)) for lg in range(lo - 1, hi + 2)]
    k = max(range(1, len(c) - 1), key=lambda j: c[j])
    d = (c[k - 1] - c[k + 1]) / (2 * (c[k - 1] - 2 * c[k] + c[k + 1])) if (c[k - 1] - 2 * c[k] + c[k + 1]) else 0
    return SR / (lo - 1 + k + d)


import cmath


def tone(x, f, a, b):
    seg = x[int(a * SR):int(b * SR)]
    return abs(sum(v * cmath.exp(-2j * math.pi * f * i / SR) for i, v in enumerate(seg))) * 2 / len(seg)


ok = True
for k in range(10):
    x = W[str(k)]
    p = pitch(x, 0.05, 0.25, 200, 320)
    if NAMES[k] == "bells":                                 # inharmonic: the hum an octave below and the strike note
        p = 261.6 if tone(x, 130.8, 0.05, 0.3) > 0.05 and tone(x, 261.6, 0.05, 0.3) > 0.02 else 0
    good = rms(x, 0.02, 0.3) > 0.01 and max(map(abs, x)) < 0.99 and abs(p - 261.6) < 6
    ok &= good
    print(f"{NAMES[k]:6s} rms {rms(x, 0.02, 0.3):.3f}  peak {max(map(abs, x)):.3f}  pitch {p:6.1f}  {'OK' if good else 'FAIL'}")
rR, rD, Cc = W["R"], W["D"], W["C"]
ring, damp = rms(rR, 0.5, 0.7) / rms(rR, 0.02, 0.15), rms(rD, 0.5, 0.7) / rms(rD, 0.02, 0.15)
print(f"REL top: after release {ring:.3f} of the attack   REL 0: {damp:.4f}   chord peak {max(map(abs, Cc)):.3f}")
names_drawn = [nm for nm in NAMES if f" 34 14 8 1 {nm}" in out]
print("TYPE names drawn:", names_drawn, " errors:", errs[:4])
ok &= ring > 0.1 and damp < 0.02 and max(map(abs, Cc)) < 0.99 and len(names_drawn) == 10 and not errs
print("ALL OK" if ok else "FAIL")

#!/usr/bin/env python3
"""PIANO engine (apply_piano.py), on SYNTH with PIANO selected.
A one note: sound, pitch 261.6 Hz, level comparable to the FM engine.   B released without pedal: damped.
C footswitch held (= pedal): the released note keeps sounding; lifting it damps the note.
D pedal noise alone (NOISE 100): something is heard.   E on TAPE the footswitch still records (no pedal).
F no Pd errors (the knob-context expression included)."""
import os, shutil, subprocess, struct, math, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
ev = [(300, ["synth-engine-set 0"]), (500, ["recF bang", "notes 60 100"]), (1500, ["notes 60 0"]),
      (2000, ["synth-engine-set 11", "synth-knob 4 1"]),
      (2400, ["recA bang", "notes 60 100"]), (2900, ["notes 60 0"]),
      (3800, ["recC bang", "fs 1"]), (3900, ["notes 60 100"]), (4400, ["notes 60 0"]), (5400, ["fs 0"]),
      (6200, ["recD bang", "fs 1"]), (6700, ["fs 0"]),
      (7200, ["mark E", "mode 2", "fs 1"]), (7300, ["fs 0"]), (7500, ["fs 1"]), (7600, ["fs 0", "mark end"]),
      (7800, ["dump bang"]), (8000, ["pd quit"])]
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


for rcv in ("mark", "tp-rec", "piano-pedal"):
    a = add(f"#X obj 700 {20 + n} r {rcv};"); b = add(f"#X obj 700 {40 + n} print {rcv};"); C.append(f"#X connect {a} 0 {b} 0;")
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
dumps = []
for nm, sec in (("F", 1.2), ("A", 1.4), ("C", 2.2), ("D", 0.8)):
    add(f"#X obj 1100 120 table cap{nm} {int(sec * SR)};")
    tw = add(f"#X obj 1100 90 tabwrite~ cap{nm};"); r_ = add(f"#X obj 1100 60 r rec{nm};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {r_} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/{nm}.wav cap{nm}")
sf2 = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf2} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if ("error" in l or "syntax" in l) and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])


W = {nm: rd_(f"{T}/{nm}.wav") for nm in "FACD"}
shutil.rmtree(T)
rms = lambda x, a, b: math.sqrt(sum(v * v for v in x[int(a * SR):int(b * SR)]) / max(1, int((b - a) * SR)))


def pitch(x, a, b):
    seg = x[int(a * SR):int(b * SR)]
    lo, hi = int(SR / 320), int(SR / 220)
    c = [sum(seg[i] * seg[i + lg] for i in range(2048)) for lg in range(lo - 1, hi + 2)]
    k = max(range(1, len(c) - 1), key=lambda j: c[j])
    d = (c[k - 1] - c[k + 1]) / (2 * (c[k - 1] - 2 * c[k] + c[k + 1])) if (c[k - 1] - 2 * c[k] + c[k + 1]) else 0
    return SR / (lo - 1 + k + d)


A, F, Cc, D = W["A"], W["F"], W["C"], W["D"]
print(f"A: rms 0.05-0.4 s {rms(A, 0.05, 0.4):.3f} (FM {rms(F, 0.05, 0.4):.3f})  peak {max(map(abs, A)):.3f}  pitch {pitch(A, 0.1, 0.3):.1f} Hz")
print(f"B: after release (0.75-0.95 s) {rms(A, 0.75, 0.95):.4f}")
print(f"C: pedal held, note released at 0.6 s: 0.9-1.1 s {rms(Cc, 0.9, 1.1):.4f}  after lifting (1.8-2.0 s) {rms(Cc, 1.8, 2.0):.4f}")
print(f"D: pedal noise alone {max(map(abs, D)):.4f}")
recs = [l.split()[-1] for l in out.splitlines() if l.startswith("tp-rec")]
peds = [l.split()[-1] for l in out.splitlines() if l.startswith("piano-pedal")]
print("tape rec states", recs, " pedal messages", peds, " errors", errs[:4])
ok = {"A": rms(A, 0.05, 0.4) > 0.3 * rms(F, 0.05, 0.4) and max(map(abs, A)) < 0.95 and abs(pitch(A, 0.1, 0.3) - 261.6) < 2,
      "B": rms(A, 0.75, 0.95) < 0.05 * rms(A, 0.05, 0.4),
      "C": rms(Cc, 0.9, 1.1) > 0.1 * rms(A, 0.05, 0.4) and rms(Cc, 1.8, 2.0) < 0.1 * rms(Cc, 0.9, 1.1),
      "D": max(map(abs, D)) > 0.005,
      "E": recs[-2:] == ["1", "0"] and peds.count("1") == 2,
      "F": not errs}
print(ok)
print("ALL OK" if all(ok.values()) else "FAIL")

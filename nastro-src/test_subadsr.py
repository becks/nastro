#!/usr/bin/env python3
"""SUB ADSR test: one note held 2 s then released, with the default envelope and with an ADSR set through
AUX + knobs 2..4 (attack ~750 ms, decay/release ~460 ms, sustain 30 %). Prints the level over time."""
import os, shutil, subprocess, tempfile, math, struct

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
ev = [(600, ["mode 0", "synth-engine-set 1"]),
      (800, ["recA bang", "notes 48 100"]), (2800, ["notes 48 0"]),
      (4000, ["aux 1", "synth-knob 2 0.5", "synth-knob 3 0.3", "synth-knob 4 0.3", "aux 0"]),
      (4200, ["recB bang", "notes 48 100"]), (6200, ["notes 48 0"]),
      (7600, ["dump bang"]), (7800, ["pd quit"])]
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
sf = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
dumps = []
for k in "AB":
    add(f"#X obj 1100 20 table cap{k} {3 * SR};")
    tw = add(f"#X obj 1100 80 tabwrite~ cap{k};"); rr = add(f"#X obj 1100 50 r rec{k};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/{k}.wav cap{k}")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))


for k, nm in (("A", "default"), ("B", "ADSR set")):
    x = rd_(f"{T}/{k}.wav")
    rms = lambda a: math.sqrt(sum(v * v for v in x[int(a * SR):int(a * SR) + 882]) / 882)
    pts = (0.01, 0.1, 0.3, 0.6, 0.9, 1.5, 1.95, 2.1, 2.3, 2.6)
    peak = max(rms(t) for t in pts) or 1
    print(f"{nm:9s} " + "  ".join(f"{t:.2f}s:{rms(t) / peak:4.2f}" for t in pts) + "   (note off at 2.00 s)")
shutil.rmtree(T)

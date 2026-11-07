#!/usr/bin/env python3
"""WAVE / STRING / ORGAN / DRONE test: one C4 (261.6 Hz) per case, 1.5 s held then released; reports peak, level over time
(release tail), and the pitch (autocorrelation) of the held part."""
import os, shutil, subprocess, wave, struct, tempfile, math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
CASES = [("WAVE default", 7, []), ("WAVE fold max sym", 7, ["wave-knob 1 1", "wave-knob 2 1"]),
         ("STRING default", 8, []), ("STRING dark body", 8, ["strg-knob 1 1", "strg-knob 2 1"]),
         ("ORGAN default", 9, []), ("ORGAN 8' only", 9, ["organ-knob 1 0", "organ-knob 3 0", "organ-knob 4 0"]),
         ("DRONE default", 10, []), ("DRONE short rel", 10, ["drone-knob 4 0"])]
ev, t = [], 700
for k, (nm, eng, knobs) in enumerate(CASES):
    ev.append((t, [f"synth-engine-set {eng}"] + knobs))
    ev.append((t + 300, [f"rec{k} bang", "notes 60 100"]))
    ev.append((t + 1800, ["notes 60 0"]))
    t += 4500
ev.append((t, ["dump bang"])); ev.append((t + 200, ["pd quit"]))
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
for k in range(len(CASES)):
    add(f"#X obj {1100 + k * 150} 20 table cap{k} {4 * SR};")
    tw = add(f"#X obj {1100 + k * 150} 80 tabwrite~ cap{k};")
    rr = add(f"#X obj {1100 + k * 150} 50 r rec{k};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/c{k}.wav cap{k}")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
for line in out.splitlines():
    if "error" in line and not any(k in line for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob", "receive~")):
        print(line)


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))


def pitch(x):
    seg = x[:8192]
    best, bl = 0, 0
    for lag in range(40, 600):
        c = sum(seg[i] * seg[i + lag] for i in range(0, 8192 - lag, 2))
        if c > best:
            best, bl = c, lag
    return SR / bl if bl else 0


for k, (nm, *_r) in enumerate(CASES):
    x = rd_(f"{T}/c{k}.wav")
    rms = lambda a, b: math.sqrt(sum(v * v for v in x[int(a * SR):int(b * SR)]) / max(1, int((b - a) * SR)))
    print(f"{nm:22s} peak {max(map(abs, x)):.3f}  rms held {rms(0.8, 1.4):.3f}  after release +0.5s {rms(2.0, 2.2):.4f} "
          f"+2s {rms(3.5, 3.9):.4f}  pitch {pitch(x[int(0.8 * SR):]):.1f} Hz")
shutil.rmtree(T)

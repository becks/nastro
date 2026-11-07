#!/usr/bin/env python3
"""Headless test of the SMPL engine: sample the input, play it pitched, loop, resample the output."""
import os, shutil, subprocess, wave, struct, math, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
events = [
    (100, ["synth-knob 2 0", "synth-knob 4 0.05"]),
    (700, ["dbg SAMPLE-INPUT"] + A(76)), (1200, A(76)),
    (1300, A(60) + A(60) + A(60) + A(60)),                      # FM -> SUB -> PLUK -> PAD -> SMPL
    (1500, ["dbg C4", "notes 60 100"]), (1900, ["notes 60 0"]),
    (2100, ["dbg C5", "notes 72 100"]), (2500, ["notes 72 0"]),
    (2700, ["dbg LOOP", "synth-knob 4 1", "notes 60 100"]), (4700, ["notes 60 0"]),
    (5000, ["dbg RESAMPLE", "synth-knob 4 0"] + A(77)), (5050, ["notes 67 100"]), (5550, ["notes 67 0"]), (5600, A(77)),
    (5800, ["dbg C4-after-resample-held-1.2s", "notes 60 100"]), (7000, ["notes 60 0"]),
    (7500, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "smp-len", "smp-recording", "synth-engine"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
# fake audio input: 330 Hz sine on inL / inR (on the Organelle these come from mother.pd)
L.append("#X obj 600 300 osc~ 330;"); o = n; n += 1
L.append("#X obj 600 330 *~ 0.5;"); g = n; n += 1
L.append("#X obj 600 360 s~ inL;"); sl = n; n += 1
L.append("#X obj 700 360 s~ inR;"); sr = n; n += 1
C += [f"#X connect {o} 0 {g} 0;", f"#X connect {g} 0 {sl} 0;", f"#X connect {g} 0 {sr} 0;"]
L.append("#X obj 600 20 catch~ outL;"); cl = n; n += 1
L.append("#X obj 700 20 catch~ outR;"); n += 1
L.append("#X obj 600 200 writesf~ 1;"); ws = n; n += 1
L.append("#X obj 600 100 delay 1;"); dl = n; n += 1
L.append(f"#X msg 600 130 open {T}/cap.wav " + BS + ", start;"); om = n; n += 1
L.append("#X obj 700 100 delay 7400;"); d2 = n; n += 1
L.append("#X msg 700 130 stop;"); sm = n; n += 1
C += [f"#X connect {cl} 0 {ws} 0;", f"#X connect 0 0 {dl} 0;", f"#X connect {dl} 0 {om} 0;", f"#X connect {om} 0 {ws} 0;",
      f"#X connect 0 0 {d2} 0;", f"#X connect {d2} 0 {sm} 0;", f"#X connect {sm} 0 {ws} 0;"]
open(f"{T}/hs.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hs.pd"],
                     capture_output=True, text=True).stderr
for line in out.splitlines():
    if any(k in line for k in ("no such object", "tape-", "soundfiler read", "seq-", "smpl.wav")):
        continue
    print(line)
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
s = [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]
SR = 44100


def pitch(t0, dur=0.12):
    x = s[int(t0 * SR):int((t0 + dur) * SR)]
    if max(map(abs, x)) < 0.01:
        return 0
    m = sum(x) / len(x); x = [v - m for v in x]
    def ac(l): return sum(x[i] * x[i + l] for i in range(0, len(x) - l, 2))
    best, bl = 0, 0
    for lag in range(int(SR / 2000), int(SR / 80)):
        c = ac(lag)
        if c > best: best, bl = c, lag
    a, b, c = ac(bl - 1), ac(bl), ac(bl + 1)
    off = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) else 0
    return SR / (bl + off)


def peak(a, b):
    return round(max(abs(v) for v in s[int(a * SR):int(b * SR)]), 3)


for name, t0, exp in (("C4 (expect 330)", 1.6, 330), ("C5 (expect 660)", 2.2, 660),
                      ("LOOP at +1.5 s (expect 330)", 4.2, 330), ("C4 after resample (expect 494)", 5.9, 493.9)):
    f = pitch(t0)
    print(f"{name:32s} {f:7.1f} Hz  ({1200 * math.log2(f / exp):+.0f} cents)  peak {peak(t0, t0 + 0.1)}" if f else f"{name}: silent")
print("one-shot, key still held: level 0.7-0.9 s after the start (sample is 0.6 s):", peak(6.5, 6.7))
shutil.rmtree(T)

#!/usr/bin/env python3
"""ENDLESS test: SEQ page 4, enter 60 64 67 rest 72, start + tape play; check note order, transposition,
backward direction, prob 0 (silence) and 1/32 rate (twice as many notes)."""
import os, shutil, subprocess, tempfile
from collections import Counter

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
N = lambda k: [f"notes {k} 100", f"notes {k} 0"]
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
events = [
    (700, ["dbg PAGE", "mode 4", "mode 4", "mode 4", "mode 4"]),
    (800, ["dbg ENTER"] + N(60) + N(64) + N(67) + A(70) + N(72)),
    (900, ["dbg FWD"] + A(72) + ["aux-key 65"]),
    (2900, ["dbg TRANSPOSE+2"] + N(62)),
    (3900, ["dbg BACK", "endl-knob 3 0.3", "endp 5 0"]),
    (4900, ["dbg PROB0", "endl-knob 4 0"]),
    (5900, ["dbg RATE32", "endl-knob 4 1", "endl-knob 3 0", "endl-knob 1 1"]),
    (6900, ["dbg STOP"] + A(72)),
    (7400, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for nm in ("dbg", "seq-notes", "seq-page"):
    L.append(f"#X obj 400 {80 + n * 10} r {nm};"); L.append(f"#X obj 400 {100 + n * 10} print {nm};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
phase, got = "", {}
for line in out.splitlines():
    if line.startswith("dbg:"):
        phase = line[5:]; got[phase] = []
    elif line.startswith("seq-page:"):
        print("  ", line)
    elif line.startswith("seq-notes:") and phase:
        a = line.split()[1:]
        if float(a[1]) > 0:
            got[phase].append(int(float(a[0])))
    elif "error" in line and not any(k in line for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob", "receive~")):
        print("  ", line)
for ph, ns in got.items():
    print(f"{ph:14s} {len(ns):3d} notes: {ns[:14]}")
shutil.rmtree(T)

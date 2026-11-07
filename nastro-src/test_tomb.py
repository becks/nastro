#!/usr/bin/env python3
"""TOMBOLA test: SEQ page 3, throw 3 balls, run 6 s. Reports the notes played (seq-notes), checks that the balls stay
inside the polygon, and measures the wall-clock cost of the physics per tick (batch mode)."""
import os, shutil, subprocess, tempfile, re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
N = lambda k: [f"notes {k} 100", f"notes {k} 0"]
events = [
    (800, ["dbg PAGE", "mode 4", "mode 4", "mode 4"]),
    (900, ["dbg THROW"] + N(60) + N(64) + N(67)),
    (4000, ["dbg SIDES-3", "tomb-knob 4 0"]),
    (5000, ["dbg SPIN-FAST", "tomb-knob 1 1"]),
    (7000, ["dbg ALL-OFF", "aux-key 71"]),
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
for name in ("dbg", "seq-notes", "seq-page"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
# every 100 ms: max distance of an active ball from the centre, and the polygon apothem
objs = ["metro 100", f"expr max(" + ", ".join(f"(tmbnt[{i}]>0)*sqrt(tmbx[{i}]*tmbx[{i}]+tmby[{i}]*tmby[{i}])" for i in range(8)).replace(",", " \\,").replace("max(", "max(max(max(max(max(max(max(", 1) + ")"]
# simpler: print every ball radius separately
L.append(f"#X obj 600 20 metro 100;"); mt = n; n += 1
L.append("#X obj 600 50 expr " + " \\; ".join(f"tmbx[{i}] \\; tmby[{i}] \\; tmbnt[{i}]" for i in range(3)) + " \\; tmbp[0] \\; tmbp[4] \\; tmbp[5];"); ex = n; n += 1
L.append("#X obj 600 80 pack " + " ".join(["f"] * 12) + ";"); pk = n; n += 1
L.append("#X obj 600 110 print R;"); pr = n; n += 1
C += [f"#X connect 0 0 {mt} 0;", f"#X connect {mt} 0 {ex} 0;"] + [f"#X connect {ex} {o} {pk} {o};" for o in range(12)] + [f"#X connect {pk} 0 {pr} 0;"]
# tick cost: realtime around one physics tick is not reachable from here; measure the whole run instead
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
import time
t0 = time.time()
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
el = time.time() - t0
notes, worst, phase = [], 0, ""
W = {}
for line in out.splitlines():
    if line.startswith("dbg:"):
        phase = line[5:]; print(line)
    elif line.startswith("seq-page:"):
        print("  ", line)
    elif line.startswith("seq-notes:"):
        a = line.split()[1:]
        if float(a[1]) > 0:
            notes.append((phase, int(float(a[0])), int(float(a[1]))))
    elif line.startswith("R:"):
        v = [float(x) for x in line.split()[1:]]
        import math
        R, Ns, ap = v[9], int(v[10]), v[11]
        over = -99
        for i in range(3):
            x, y, nt = v[i * 3:i * 3 + 3]
            if nt > 0:
                over = max(over, max(x * math.cos(R + (j + 0.5) * 2 * math.pi / Ns) + y * math.sin(R + (j + 0.5) * 2 * math.pi / Ns) - ap for j in range(Ns)))
        worst = max(worst, over); W[phase] = max(W.get(phase, 0), over)
    elif "error" in line and not any(k in line for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob")):
        print("  ", line)
from collections import Counter
for ph in ("THROW", "SIDES-3", "SPIN-FAST", "ALL-OFF"):
    ns = [x for x in notes if x[0] == ph]
    print(f"{ph:10s}: {len(ns):3d} hits  notes {dict(Counter(x[1] for x in ns))}  vel {min((x[2] for x in ns), default=0)}..{max((x[2] for x in ns), default=0)}")
print("per phase:", {k: round(v, 1) for k, v in W.items()})
print(f"worst ball centre beyond a wall: {worst:.2f} px (0 = touching; ball radius 1.5)")
print(f"whole 7.5 s run took {el:.2f} s of CPU in batch mode")
shutil.rmtree(T)

#!/usr/bin/env python3
"""Measure clicks in SMPL playback: fast retriggers and a loop with arbitrary START/END.
usage: test_click.py <patch dir>"""
import os, sys, shutil, subprocess, wave, struct, math, tempfile

SRC = sys.argv[1]
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
# start after the project has been loaded (the patch loads the last project ~300 ms after opening)
ev = [(700, A(76)), (1200, A(76)), (1300, A(60) + A(60) + A(60) + A(60))]
t = 1500
for i in range(14):                                   # fast retriggers, voices get reused
    ev.append((t, [f"notes {60 + (i % 3) * 4} 100"])); ev.append((t + 90, [f"notes {60 + (i % 3) * 4} 0"])); t += 100
ev.append((3200, ["synth-knob 1 0.1", "synth-knob 2 0.37", "synth-knob 4 1"]))
ev.append((3400, ["notes 60 100"])); ev.append((5400, ["notes 60 0"]))
ev.append((5800, ["pd quit"]))
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]; n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 5} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 5} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]; n += 2
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
L.append("#X obj 700 100 delay 5700;"); d2 = n; n += 1
L.append("#X msg 700 130 stop;"); sm = n; n += 1
C += [f"#X connect {cl} 0 {ws} 0;", f"#X connect 0 0 {dl} 0;", f"#X connect {dl} 0 {om} 0;", f"#X connect {om} 0 {ws} 0;",
      f"#X connect 0 0 {d2} 0;", f"#X connect {d2} 0 {sm} 0;", f"#X connect {sm} 0 {ws} 0;"]
open(f"{T}/hk.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hk.pd"], capture_output=True)
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
s = [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]
SR = 44100


def clicks(a, b):
    x = s[int(a * SR):int(b * SR)]
    d2 = [abs(x[i + 1] - 2 * x[i] + x[i - 1]) for i in range(1, len(x) - 1)]
    # a smooth 330-990 Hz sound at this level stays well under 0.02; count bigger jumps
    return len([v for v in d2 if v > 0.02]), round(max(d2), 3)


print(f"{os.path.basename(os.path.normpath(SRC)):10s} retriggers: clicks/max {clicks(1.5, 3.0)}   "
      f"loop START 10% END 37%: clicks/max {clicks(3.5, 5.3)}")
shutil.rmtree(T)

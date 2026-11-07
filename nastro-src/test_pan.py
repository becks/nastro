#!/usr/bin/env python3
"""Headless pan test: tone on tape track 1, pan hard left / centre / hard right, measure L and R."""
import os, shutil, subprocess, wave, struct, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
events = [
    (100, ["synth-knob 2 0"] + A(62) + A(66)), (200, ["notes 69 100"]), (2200, ["notes 69 0"]), (2300, A(66) + A(67) + A(65)),
    (2600, ["dbg LEFT", "aux 1", "mix-knob 1 0", "aux 0"]),
    (3400, ["dbg CENTRE", "aux 1", "mix-knob 1 0.5", "aux 0"]),
    (4200, ["dbg RIGHT", "aux 1", "mix-knob 1 1", "aux 0"]),
    (5000, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
L.append("#X obj 600 20 catch~ outL;"); cl = n; n += 1
L.append("#X obj 700 20 catch~ outR;"); cr = n; n += 1
L.append("#X obj 600 200 writesf~ 2;"); ws = n; n += 1
L.append("#X obj 600 100 delay 1;"); dl = n; n += 1
L.append(f"#X msg 600 130 open {T}/cap.wav " + BS + ", start;"); om = n; n += 1
L.append("#X obj 700 100 delay 4900;"); d2 = n; n += 1
L.append("#X msg 700 130 stop;"); sm = n; n += 1
C += [f"#X connect {cl} 0 {ws} 0;", f"#X connect {cr} 0 {ws} 1;", f"#X connect 0 0 {dl} 0;", f"#X connect {dl} 0 {om} 0;",
      f"#X connect {om} 0 {ws} 0;", f"#X connect 0 0 {d2} 0;", f"#X connect {d2} 0 {sm} 0;", f"#X connect {sm} 0 {ws} 0;"]
open(f"{T}/hp.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hp.pd"],
                     capture_output=True, text=True).stderr
for line in out.splitlines():
    if any(k in line for k in ("no such object", "tape-", "soundfiler read", "seq-", "smpl.wav")):
        continue
    print(line)
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
s = struct.unpack("<%dh" % (len(d) // 2), d)
Ls, Rs = [v / 32768 for v in s[0::2]], [v / 32768 for v in s[1::2]]
pk = lambda x, a, b: round(max(abs(v) for v in x[int(a * 44100):int(b * 44100)]), 3)
for name, a, b in (("tape, no pan yet", 2.35, 2.55), ("LEFT", 2.8, 3.2), ("CENTRE", 3.6, 4.0), ("RIGHT", 4.4, 4.8)):
    print(f"{name:18s} L {pk(Ls, a, b):6}  R {pk(Rs, a, b):6}")
shutil.rmtree(T)

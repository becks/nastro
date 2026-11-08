#!/usr/bin/env python3
"""LED blink while recording: on TAPE, rec starts at 800 ms and stops at 2000 ms. The LED must alternate
0 / page colour (3 = TAPE) every 250 ms during recording and end steady on 3; freeze while recording blinks white."""
import os, shutil, subprocess, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
ev = [(500, ["mode 2"]), (800, ["mark rec-on", "aux-key 66"]), (2000, ["mark rec-off", "aux-key 66"]),
      (2600, ["mark frz", "aux-key 79"]), (2700, ["aux-key 66"]), (3500, ["aux-key 66"]), (4000, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;",
     "#X obj 600 20 r led;", "#X obj 600 50 print LED;", "#X obj 700 20 r mark;", "#X obj 700 50 print MARK;"]
C = ["#X connect 0 0 1 0;", "#X connect 2 0 3 0;", "#X connect 4 0 5 0;"]
n = 6
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
shutil.rmtree(T)
seq, cur = {"pre": []}, "pre"
for l in out.splitlines():
    if l.startswith("MARK:"):
        cur = l.split()[-1]; seq[cur] = []
    elif l.startswith("LED:"):
        seq[cur].append(l.split()[-1])
print(seq)
r, f = seq.get("rec-on", []), seq.get("frz", [])
ok = (len(r) >= 4 and set(r) == {"0", "3"} and seq.get("rec-off") == ["3"]
      and "0" in f and "7" in f and f[-1] == "7" and "3" not in f[1:])
print("OK" if ok else "FAIL")

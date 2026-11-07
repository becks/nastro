#!/usr/bin/env python3
"""Loop recording seam test: a continuous 220 Hz tone is recorded on track 1 over a 1-bar loop (overdub off =
replace) for several passes. Then the tape is checked for discontinuities inside the loop (2nd difference much
larger than a clean sine's) and for writes past the loop end."""
import os, shutil, subprocess, tempfile, sys, math, wave, struct

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 88320 + 37          # loop length not a multiple of 64
BS = "\\"
ev = [(700, ["mode 2", f"tp-loop-set 2 0 {B}", "tape-knob 3 0", "amp 0.4"]),
      (800, ["aux-key 66"]),                       # rec (starts play)
      (800 + 5 * 2003, ["aux-key 66", "amp 0"]),   # 5 passes
      (800 + 5 * 2003 + 200, ["dump bang"]),
      (800 + 5 * 2003 + 400, ["pd quit"])]
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


o = add("#X obj 600 20 osc~ 220;"); ra = add("#X obj 700 20 r amp;"); mu = add("#X obj 600 50 *~ 0;")
th = add("#X obj 600 80 throw~ synth-bus;")
C += [f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
add("#X obj 800 20 catch~ outL;"); add("#X obj 900 20 catch~ outR;")
sf = add("#X obj 700 600 soundfiler;"); rd = add("#X obj 700 300 r dump;")
md = add(f"#X msg 700 330 write -wave -bytes 4 -nframes {B + 4000} {T}/t1.wav tape1;")
C += [f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)
b = open(f"{T}/t1.wav", "rb").read(); i = b.index(b"data") + 8
x = list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))
amp = max(map(abs, x[:B]))
clean = amp * (2 * math.pi * 220 / SR) ** 2
d2 = [abs(x[k + 1] - 2 * x[k] + x[k - 1]) for k in range(1, B - 1)]
bad = [(k, d2[k - 1]) for k in range(1, B - 1) if d2[k - 1] > 4 * clean]
print(f"tone amplitude on tape {amp:.3f}, clean d2 {clean:.5f}")
print(f"discontinuities inside the loop: {len(bad)}  first: {[(k, round(v, 4)) for k, v in bad[:6]]}")
past = x[B:B + 200]
print(f"written past the loop end (first 200 samples after it): peak {max(map(abs, past)):.3f}")
shutil.rmtree(T)

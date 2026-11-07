#!/usr/bin/env python3
"""Track filter sweep test (zipper / clicks): track 1 holds a 200 Hz sine; the filter knob is turned like the
Organelle sends it (a message every 10 ms, steps of 0.01) from off down to a low low-pass and back, then into the
high-pass. A click shows as a 2nd-difference spike far above what a clean 200 Hz sine gives."""
import os, shutil, subprocess, tempfile, math, wave, struct, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
w = wave.open(f"{T}/a.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(0.4 * math.sin(2 * math.pi * 200 * i / SR) * 32767)) for i in range(6 * SR)))
w.close()
BS = "\\"
path = [0.5 - 0.01 * i for i in range(46)] + [0.05 + 0.01 * i for i in range(46)] + [0.5 + 0.01 * i for i in range(40)]
ev = [(500, ["ld bang"]), (700, ["aux-key 65"]), (1000, ["recA bang"])]
for i, v in enumerate(path):
    ev.append((1100 + i * 10, [f"tfilt-knob 1 {v:.3f}"]))
end = 1100 + len(path) * 10 + 200
ev += [(end, ["dump bang"]), (end + 200, ["pd quit"])]
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


sf = add("#X obj 900 500 soundfiler;"); rl = add("#X obj 900 400 r ld;")
ml = add(f"#X msg 900 430 read {T}/a.wav tape1;")
C += [f"#X connect {rl} 0 {ml} 0;", f"#X connect {ml} 0 {sf} 0;"]
cl = add("#X obj 1100 20 catch~ outL;"); add("#X obj 1200 20 catch~ outR;")
add(f"#X obj 1100 100 table capA {3 * SR};"); tw = add("#X obj 1100 80 tabwrite~ capA;"); rr = add("#X obj 1100 50 r recA;")
rd = add("#X obj 1300 400 r dump;"); md = add(f"#X msg 1300 430 write -wave -bytes 4 {T}/A.wav capA;")
C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)
b = open(f"{T}/A.wav", "rb").read(); i = b.index(b"data") + 8
x = struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])
shutil.rmtree(T)
seg = x[int(0.05 * SR):int((len(path) * 10 + 150) / 1000 * SR)]
amp = max(map(abs, seg))
clean = amp * (2 * math.pi * 200 / SR) ** 2
d2 = [abs(seg[k + 1] - 2 * seg[k] + seg[k - 1]) for k in range(1, len(seg) - 1)]
over = [v / clean for v in d2]
print(f"output peak {amp:.3f}  clean d2 {clean:.5f}  worst d2 {max(d2):.5f} ({max(over):.1f}x clean)  "
      f"samples above 3x clean: {sum(o > 3 for o in over)}")
print("CLEAN" if max(over) < 3 else "ZIPPER")

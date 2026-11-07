#!/usr/bin/env python3
"""Loop wrap click test: a 440 Hz tone on track 1, looped over a length that cuts the wave mid-cycle.
Plays ~3 s of loop and reports the largest 2nd-difference spike in the output (a click shows as a big d2)."""
import os, shutil, subprocess, wave, struct, math, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 30017                      # loop length: not a whole number of cycles
src = [0.5 * math.sin(2 * math.pi * 440 * i / SR) for i in range(B + 4000)]
w = wave.open(f"{T}/src.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in src)); w.close()
BS = "\\"
events = [(600, ["ldsrc bang", f"tp-loop-set 2 0 {B}", "aux-key 65"]), (1000, ["rec1 bang"]), (4200, ["dump bang"]), (4400, ["pd quit"])]
Lp = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    Lp.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    Lp.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
objs = ["soundfiler", "r ldsrc", f"msg read {T}/src.wav tape1", "catch~ outL", "tabwrite~ cap", "r rec1",
        f"table cap {3 * SR}", "r dump", f"msg write -wave -bytes 2 {T}/cap.wav cap", "catch~ outR"]
base = n
for i, o in enumerate(objs):
    kind = "msg" if o.startswith("msg ") else "obj"
    Lp.append(f"#X {kind} 600 {20 + i * 30} {o[4:] if kind == 'msg' else o};")
sf, rl, ml, co, tw, rr, tb, rd, md, cR = range(base, base + len(objs))
C += [f"#X connect {rl} 0 {ml} 0;", f"#X connect {ml} 0 {sf} 0;", f"#X connect {co} 0 {tw} 0;",
      f"#X connect {rr} 0 {tw} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(Lp + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
x = struct.unpack("<%dh" % (len(d) // 2), d)
x = [v / 32768 for v in x]
amp = max(map(abs, x))
d2 = [abs(x[i + 1] - 2 * x[i] + x[i - 1]) for i in range(1, len(x) - 1)]
base_d2 = amp * (2 * math.pi * 440 / SR) ** 2      # d2 of a clean sine at this amplitude
big = sorted(range(len(d2)), key=lambda i: -d2[i])[:3]
print(f"amp {amp:.3f}  clean-sine d2 {base_d2:.5f}  worst d2 {[round(d2[i], 4) for i in big]} at {big}")
print("CLICK" if max(d2) > 4 * base_d2 else "CLEAN")
shutil.rmtree(T)

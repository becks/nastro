#!/usr/bin/env python3
"""Master compressor test: a loud (0.5) and a quiet (0.05) 440 Hz tone into the synth bus, with COMP at 0, 0.5 and
1 (speed 0.5). Prints the settled output peaks and the loud/quiet ratio (compression brings them closer)."""
import os, shutil, subprocess, tempfile, struct, math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
CASES = [0, 0.5, 1]
ev, t = [], 700
for k, a in enumerate(CASES):
    ev += [(t, [f"comp-knob 1 {a}", "amp 0.5"]), (t + 900, [f"recL{k} bang"]),
           (t + 1200, ["amp 0.05"]), (t + 2400, [f"recQ{k} bang"])]
    t += 2700
ev += [(t, ["dump bang"]), (t + 200, ["pd quit"])]
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


o = add("#X obj 600 20 osc~ 440;"); ra = add("#X obj 700 20 r amp;"); mu = add("#X obj 600 50 *~ 0;")
th = add("#X obj 600 80 throw~ synth-bus;")
C += [f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
sf = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
dumps = []
for k in range(len(CASES)):
    for w in "LQ":
        add(f"#X obj 1100 20 table c{w}{k} 4410;")
        tw = add(f"#X obj 1100 80 tabwrite~ c{w}{k};"); rr = add(f"#X obj 1100 50 r rec{w}{k};")
        C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
        dumps.append(f"write -wave -bytes 4 {T}/{w}{k}.wav c{w}{k}")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)


def pk(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    x = struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])
    return max(map(abs, x))


for k, a in enumerate(CASES):
    lo, qu = pk(f"{T}/L{k}.wav"), pk(f"{T}/Q{k}.wav")
    print(f"COMP {a:3}: loud {lo:.3f}  quiet {qu:.3f}  loud/quiet {20 * math.log10(lo / qu):5.1f} dB")
shutil.rmtree(T)

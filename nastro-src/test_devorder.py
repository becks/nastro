#!/usr/bin/env python3
"""Device event-order test. On the Organelle, key presses arrive from the network right after a DSP tick, before
that tick's [bang~] has updated the tape position. Here the keys are sent from a [bang~] in a patch opened AFTER
main.pd (Pd runs the newest canvas first in the DSP chain), so they run before tape.pd's [bang~] (same order as on the device). A tone is recorded over a looped
range for 3 passes, then the tape is checked: silent samples at the loop start and steps inside the loop."""
import os, shutil, subprocess, tempfile, sys, math, struct

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 88320
BS = "\\"
# early patch: [bang~] -> spigot -> key message (keys at "device time")
keys = [(800, "aux-key 66"), (800 + 3 * 2003 + 300, "aux-key 66")]
E = ["#N canvas 0 0 600 400 12;"]
C = []
n = 0
def add(lst, s):
    global n
    lst.append(s); n += 1
    return n - 1
bg = add(E, "#X obj 20 20 bang~;")
for t_ms, key in keys:
    lb = add(E, "#X obj 200 20 loadbang;"); dl = add(E, f"#X obj 200 50 delay {t_ms};")
    one = add(E, "#X msg 200 80 1;"); sp = add(E, "#X obj 20 110 spigot;")
    tt = add(E, "#X obj 20 140 t b b;"); zero = add(E, "#X msg 100 170 0;")
    km = add(E, f"#X msg 20 170 {BS}; {key};")
    C += [f"#X connect {lb} 0 {dl} 0;", f"#X connect {dl} 0 {one} 0;", f"#X connect {one} 0 {sp} 1;",
          f"#X connect {bg} 0 {sp} 0;", f"#X connect {sp} 0 {tt} 0;", f"#X connect {tt} 1 {zero} 0;",
          f"#X connect {zero} 0 {sp} 1;", f"#X connect {tt} 0 {km} 0;"]
open(f"{T}/early.pd", "w").write("\n".join(E + C) + "\n")
# late patch: setup, tone, dump
ev = [(700, ["mode 2", f"tp-loop-set 2 0 {B}", "tape-knob 3 1", "amp 0.4"]),
      (800 + 3 * 2003 + 600, ["dump bang"]), (800 + 3 * 2003 + 800, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
o = add(L, "#X obj 600 20 osc~ 220;"); ra = add(L, "#X obj 700 20 r amp;"); mu = add(L, "#X obj 600 50 *~ 0;")
th = add(L, "#X obj 600 80 throw~ synth-bus;")
C += [f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
add(L, "#X obj 800 20 catch~ outL;"); add(L, "#X obj 900 20 catch~ outR;")
sf = add(L, "#X obj 700 600 soundfiler;"); rd = add(L, "#X obj 700 300 r dump;")
md = add(L, f"#X msg 700 330 write -wave -bytes 4 -nframes {B + 2000} {T}/t1.wav tape1;")
C += [f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd", "-open", f"{T}/early.pd"],
               capture_output=True, text=True)
b = open(f"{T}/t1.wav", "rb").read(); i = b.index(b"data") + 8
x = list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))
shutil.rmtree(T)
z = 0
while abs(x[z]) < 1e-6:
    z += 1
amp = max(map(abs, x[:B]))
clean = amp * (2 * math.pi * 220 / SR) ** 2
d2 = [abs(x[k + 1] - 2 * x[k] + x[k - 1]) for k in range(1, B - 1)]
bad = [k for k in range(1, B - 1) if d2[k - 1] > 4 * clean]
print(f"silent samples at the loop start: {z}   steps inside the loop: {len(bad)} {bad[:4]}   wrap |x[B-1]-x[0]| {abs(x[B-1]-x[0]):.3f}")
print("CLEAN" if z == 0 and not bad else "GAP")

#!/usr/bin/env python3
"""Control-rate cost around the loop wrap: TAPE page shown, 1-bar loop playing (4 tracks with audio), optionally
recording. Every DSP block's wall time is measured (bang~ + realtime, batch mode). Reports the slowest blocks and
whether they line up with the loop restarts. (Mac timings: the Organelle is ~10-20x slower.)"""
import os, shutil, subprocess, tempfile, sys, math, wave, struct

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
REC = "rec" in sys.argv
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 88320
w = wave.open(f"{T}/s.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(0.3 * math.sin(2 * math.pi * 330 * i / SR) * 32767)) for i in range(B * 2)))
w.close()
BS = "\\"
ev = [(500, ["ld bang"]), (700, ["mode 2", f"tp-loop-set 2 0 {B}", "aux-key 65"])]
if REC:
    ev.append((900, ["aux-key 66", "notes 60 100"]))
ev += [(30700, ["pd quit"])]
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


sf = add("#X obj 700 600 soundfiler;"); r_ = add("#X obj 700 300 r ld;")
m_ = add("#X msg 700 330 " + " \\, ".join(f"read {T}/s.wav tape{k}" for k in range(1, 5)) + ";")
C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
# per block: wall time since the previous block (realtime), printed with the logical time when > threshold
b = add("#X obj 900 20 bang~;"); tb = add("#X obj 900 50 t b b;"); rt = add("#X obj 900 80 realtime;")
tm = add("#X obj 1000 80 timer;"); pk = add("#X obj 900 140 pack f f;"); pr = add("#X obj 900 170 print BLK;")
lb = add("#X obj 1000 20 loadbang;")
C += [f"#X connect {b} 0 {tb} 0;", f"#X connect {tb} 0 {rt} 0;", f"#X connect {tb} 1 {rt} 1;",
      f"#X connect {rt} 0 {pk} 0;", f"#X connect {lb} 0 {tm} 0;", f"#X connect {tb} 1 {tm} 1;",
      f"#X connect {tm} 0 {pk} 1;", f"#X connect {pk} 0 {pr} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
blk = []
for line in out.splitlines():
    if line.startswith("BLK:"):
        a = line.split()
        blk.append((float(a[1]), float(a[2])))          # wall ms of the block, logical ms
blk = [x for x in blk if x[1] > 1500]
blk.sort(reverse=True)
period = B / SR * 1000
start = 700
print(f"blocks: {len(blk)}  median {sorted(x[0] for x in blk)[len(blk) // 2]:.3f} ms")
print("slowest blocks (wall ms, logical ms, ms after the last loop restart):")
for wall, t in blk[:15]:
    ph = (t - start) % period
    print(f"   {wall:7.3f}   t={t:9.1f}   +{ph:7.1f}")
near = [x for x in blk if min((x[1] - start) % period, period - (x[1] - start) % period) < 15]
rest = [x for x in blk if x not in near]
avg = lambda v: sum(a for a, _ in v) / max(1, len(v))
print(f"avg block near a restart (±15 ms): {avg(near):.3f} ms   elsewhere: {avg(rest):.3f} ms   "
      f"max near: {max((a for a, _ in near), default=0):.3f}  max elsewhere: {max((a for a, _ in rest), default=0):.3f}")
shutil.rmtree(T)

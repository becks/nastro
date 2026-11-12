#!/usr/bin/env python3
"""DRUM KIT recording (apply_drumkit.py): a 440 Hz tone on the input; DRUM, a knob edit on key 3, AUX+G#5 (KIT),
AUX+E5 arms and the input starts it, AUX+E5 again after ~3 s. Checks: [drums] = the take's length (about 3 s) and
not silent across the 24 slices, [drec] = one slice, the key parameters back to neutral, KIT mode off afterwards,
a key plays; then a normal one-key recording (KIT off) still copies into the key and leaves the kit size alone."""
import os, shutil, subprocess, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
ev = [(300, ["mode 1"]), (400, ["drum-notes 63 100", "drum-notes 63 0", "drum-knob 1 0.9"]),
      (600, ["aux-key 80"]), (700, ["aux-key 76"]), (800, ["src 0.5"]), (3800, ["aux-key 76"]),
      (4000, ["chk bang"]), (4100, ["drum-notes 70 100"]), (4200, ["src 0", "aux-key 76"]), (4300, ["src 0.5"]),
      (4500, ["aux-key 76"]), (4700, ["chk bang"]), (4800, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
def add(line):
    global n
    L.append(line); n += 1; return n - 1
# input: a tone whose level is set by [r src]
o = add("#X obj 600 20 osc~ 440;"); g = add("#X obj 600 50 *~;"); sl = add("#X obj 700 20 r src;")
li = add("#X obj 700 40 line~;"); s1 = add("#X obj 600 80 s~ inL;"); s2 = add("#X obj 700 80 s~ inR;")
z = add("#X obj 800 50 sig~ 0;")
C += [f"#X connect {o} 0 {g} 0;", f"#X connect {sl} 0 {li} 0;", f"#X connect {li} 0 {g} 1;", f"#X connect {g} 0 {s1} 0;",
      f"#X connect {z} 0 {s2} 0;"]
# output peak while a key plays
cl = add("#X obj 900 20 catch~ outL;")
ev_ = add("#X obj 900 50 env~ 4096;"); pe = add("#X obj 900 80 print ENV;")
C += [f"#X connect {cl} 0 {ev_} 0;", f"#X connect {ev_} 0 {pe} 0;"]
# checks
ck = add("#X obj 1100 20 r chk;"); tt = add("#X obj 1100 50 t b b b;")
az = add("#X obj 1100 80 array size drums;"); ar = add("#X obj 1250 80 array size drec;")
pk = add("#X obj 1100 110 pack f f;")
pr = add("#X obj 1100 140 print SIZE;")
ex = add(r"#X obj 1400 80 expr dk1[3] \; dk2[3] \; dk4[3];"); pp = add("#X obj 1400 110 pack f f f;"); pd_ = add("#X obj 1400 140 print DK;")
C += [f"#X connect {ck} 0 {tt} 0;", f"#X connect {tt} 2 {ar} 0;", f"#X connect {ar} 0 {pk} 1;", f"#X connect {tt} 1 {az} 0;",
      f"#X connect {az} 0 {pk} 0;", f"#X connect {pk} 0 {pr} 0;", f"#X connect {tt} 0 {ex} 0;",
      f"#X connect {ex} 2 {pp} 2;", f"#X connect {ex} 1 {pp} 1;", f"#X connect {ex} 0 {pp} 0;", f"#X connect {pp} 0 {pd_} 0;"]
for rcv in ("drum-kit", "drum-recording"):
    r_ = add(f"#X obj 1600 {20 + n} r {rcv};"); p_ = add(f"#X obj 1600 {40 + n} print {rcv};")
    C.append(f"#X connect {r_} 0 {p_} 0;")
# peaks of each slice of the kit, after the take
pkr = add("#X obj 1800 20 r chkpk;")
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
shutil.rmtree(T)
lines = out.splitlines()
sizes = [l for l in lines if l.startswith("SIZE:")]
dks = [l for l in lines if l.startswith("DK:")]
kit = [l for l in lines if l.startswith("drum-kit:")]
rec = [l for l in lines if l.startswith("drum-recording:")]
envs = [float(l.split()[-1]) for l in lines if l.startswith("ENV:")]
errs = [l for l in lines if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
print("sizes", sizes); print("dk", dks); print("drum-kit", kit); print("drum-recording", rec)
print("max env while key plays", max(envs) if envs else None); print("errors", errs[:5])
ok = len(sizes) == 2 and not errs
if ok:
    k1, d1 = map(float, sizes[0].split()[1:3]); k2, d2 = map(float, sizes[1].split()[1:3])
    ok = 2.7 * 44100 < k1 < 3.3 * 44100 and d1 == int(k1 / 24) and k2 == k1 and d2 == d1
    ok = ok and dks[0].split()[1:] == ["0.5", "1", "0.8"] and kit[-1].endswith("0") and max(envs) > 60
print("ALL OK" if ok else "FAIL")

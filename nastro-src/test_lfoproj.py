#!/usr/bin/env python3
"""LFO settings in projects: on FM, AUX + D5, the real knobs (through pickup) set sine / 2 Hz / 100 % / INDEX;
save P1; + NEW (P2: defaults); load P1 -> the FM LFO comes back (lfo-cfg) and moves INDEX again; load P2 -> off.
Also an old project file with 116 values (no LFO) loads with the LFO defaults."""
import os, shutil, subprocess, tempfile, math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
R2 = round(math.log(40) / math.log(200), 4)
ENC = lambda n, d: [f"enc {d}"] * n
PRESS = ["encbut 1", "encbut 0"]
K = lambda k, a, b: [f"knob{k} {a}", f"knob{k} {b}"]
events = [
    (600, ["dbg SET", "aux-key 74"] + K(1, 0, 0.15) + K(2, 0.3, R2) + K(3, 0.5, 1) + K(4, 0, 0.2)),
    (700, ["dbg SAVE-P1", "aux 1", "notes 69 100", "notes 69 0", "aux 0"]),
    (1000, ["dbg NEW-P2"] + ENC(2, 1) + PRESS),
    (1400, ["dbg SAVE-P2", "aux 1", "notes 69 100", "notes 69 0", "aux 0"]),
    (1800, ["dbg LOAD-P1"] + ENC(1, 1) + PRESS + PRESS),
    (2400, ["dbg LOAD-P2"] + ENC(1, 1) + PRESS),
    (3000, ["dbg OLD-P3", "pkval resize 116", "pkval write p3-pk.txt", "pkval resize 160", "nstproj 3 1"]),
    (3100, ["pm-load 3"]),
    (3700, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect {0} 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "lfo-cfg", "syn-lfo-p"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
open(f"{T}/hj.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hj.pd"],
                     capture_output=True, text=True).stderr
shutil.rmtree(T)
sec, cur = {}, "start"
for l in out.splitlines():
    if l.startswith("dbg:"):
        cur = l.split()[1]
    elif l.startswith(("lfo-cfg:", "syn-lfo-p:")):
        sec.setdefault(cur, []).append(l.split(":", 1)[1].strip())
for k, v in sec.items():
    print(k, v)
last_cfg = lambda k: [x for x in sec.get(k, []) if " " in x][-1:] or [""]
p1 = last_cfg("LOAD-P1")[0].split(); p2 = last_cfg("LOAD-P2")[0].split(); p3 = last_cfg("OLD-P3")[0].split()
ok = (p1 and p1[0] == "0" and abs(float(p1[1]) - 0.15) < 0.01 and abs(float(p1[2]) - R2) < 0.01 and float(p1[3]) == 1
      and abs(float(p1[4]) - 0.2) < 0.01 and "1" in sec.get("LOAD-P1", [])
      and p2 == ["0", "0", "0.3", "0.5", "0"] and p3 == ["0", "0", "0.3", "0.5", "0"])
print("OK" if ok else "FAIL")

#!/usr/bin/env python3
"""Headless projects test: save P1, + NEW (P2) from the menu, change, save, reload P1 / P2 from the menu."""
import os, shutil, subprocess, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
ENC = lambda n, d: [f"enc {d}"] * n
PRESS = ["encbut 1", "encbut 0"]
# menu: 0 back, 1 save, 2 + new, 3.. projects, last system
events = [
    (600, ["dbg STATE-A", "synth-engine-set 2", "nst-oct-set 1", "pkval 12 0.3", "mix-lvl-set 1 0.3",
           "seqn 0 64", "dk1 3 0.9", "tp-loop-set 2 1000 45100"]),
    (700, ["dbg SAVE-P1 (AUX+A)", "aux 1", "notes 69 100", "notes 69 0", "aux 0"]),
    (1000, ["dbg MENU-NEW"] + ENC(2, 1) + PRESS),                 # open, go to '+ NUOVO', press
    (1400, ["dbg STATE-B", "pkval 12 0.9", "mix-lvl-set 1 0.9", "synth-engine-set 3", "seqn 0 72"]),
    (1500, ["dbg SAVE-P2 (AUX+A)", "aux 1", "notes 69 100", "notes 69 0", "aux 0"]),
    (1900, ["dbg LOAD-P1"] + ENC(1, 1) + PRESS),                              # row 3 = PROG 1
    (2300, ["dbg CHECK-P1", "chk bang"]),
    (2400, ["dbg LOAD-P2"] + ENC(1, 1) + PRESS),                              # row 4 = PROG 2
    (2800, ["dbg CHECK-P2", "chk bang"]),
    (3000, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "nst-proj-status", "pm-cur", "tape-lvl1", "synth-engine", "nst-oct", "tp-hi"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
# chk: print table values that live outside messages
L.append("#X obj 600 20 r chk;"); ck = n; n += 1
L.append("#X obj 600 50 expr pkval[12] \\; seqn[0] \\; dk1[3];"); ce = n; n += 1
L.append("#X obj 600 80 pack f f f;"); cp = n; n += 1
L.append("#X obj 600 110 print CHECK(pkval12-seqn0-dk1_3);"); cr = n; n += 1
C += [f"#X connect {ck} 0 {ce} 0;", f"#X connect {ce} 0 {cp} 0;", f"#X connect {ce} 1 {cp} 1;", f"#X connect {ce} 2 {cp} 2;",
      f"#X connect {cp} 0 {cr} 0;"]
open(f"{T}/hj.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hj.pd"],
                     capture_output=True, text=True).stderr
show = False
for line in out.splitlines():
    if line.startswith("dbg:"):
        show = True
    if not show:
        continue
    if any(k in line for k in ("no such object", "receive~", "Find menu")):
        continue
    print(line)
print("files:", sorted(f for f in os.listdir(T) if f.startswith("p") and not f.endswith(".pd") or f.endswith(".txt")))
shutil.rmtree(T)

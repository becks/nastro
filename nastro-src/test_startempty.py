#!/usr/bin/env python3
"""Start-up test: run 1 changes the state and saves (AUX+A -> project 1); run 2 restarts in the same folder and
must start EMPTY (defaults), with project 1 still in the list and loadable."""
import os, shutil, subprocess, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"


def run(events, name):
    L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
    C = ["#X connect 0 0 1 0;"]
    n = 2
    for t_ms, msgs in events:
        L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
        L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
        C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
        n += 2
    for nm in ("dbg", "nst-proj-status", "pm-cur"):
        L.append(f"#X obj 400 {80 + n * 10} r {nm};"); L.append(f"#X obj 400 {100 + n * 10} print {nm};")
        C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
    L.append("#X obj 600 20 r chk;"); L.append("#X obj 600 50 expr pkval[12] \\; seqn[0];")
    L.append("#X obj 600 80 pack f f;"); L.append("#X obj 600 110 print CHK;")
    C += [f"#X connect {n} 0 {n + 1} 0;", f"#X connect {n + 1} 0 {n + 2} 0;", f"#X connect {n + 1} 1 {n + 2} 1;",
          f"#X connect {n + 2} 0 {n + 3} 0;"]
    open(f"{T}/{name}.pd", "w").write("\n".join(L + C) + "\n")
    out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                          "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/{name}.pd"], capture_output=True, text=True).stderr
    return [l for l in out.splitlines() if l.split(":")[0] in ("dbg", "nst-proj-status", "pm-cur", "CHK")]


print("\n".join(run([(700, ["dbg RUN1-SET", "pkval 12 0.3", "seqn 0 64"]),
                     (800, ["dbg SAVE", "aux 1", "notes 69 100", "notes 69 0", "aux 0"]),
                     (1200, ["chk bang"]), (1300, ["pd quit"])], "r1")))
print("---- restart")
print("\n".join(run([(700, ["dbg RUN2-START", "chk bang"]),
                     (800, ["dbg LOAD-P1", "enc 1", "enc 1", "enc 1", "encbut 1", "encbut 0"]),
                     (1300, ["chk bang"]), (1400, ["pd quit"])], "r2")))
shutil.rmtree(T)

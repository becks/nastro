#!/usr/bin/env python3
"""Headless test of TAPE navigation (AUX+C#5 / D#5): bar jumps, loop shift, recording after a shift."""
import os, shutil, subprocess, wave, struct, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
P = lambda tag: [f"dbg {tag}", "tp-ask bang"]
BAR = 88320
events = [
    (100, A(62) + ["synth-knob 2 0", "synth-knob 4 0.05"]),     # TAPE, sine synth
    (200, A(65)),                                                 # play from 0
    (1200, A(75)), (1201, P("fwd1 expect 88320")),
    (1300, A(75)), (1301, P("fwd2 expect 176640")),
    (1400, A(73)), (1401, P("back (start of current bar) expect 176640")),
    (1500, A(67) + A(73)), (1501, P("back-at-0 expect 0")),
    # loop of 1 bar starting at 0: IN now, OUT ~1 bar later (snap to bar)
    (1600, A(67) + A(68)), (3300, A(68)),
    (3400, P("loop")),
    (3500, A(75)), (3501, P("loop->next expect lo 88320 hi 176640")),
    # record a note in the shifted loop (track 1)
    (3600, A(66)), (3700, ["notes 69 100"]), (4000, ["notes 69 0"]), (5700, A(66)),
    (5800, A(73)), (5801, P("loop<-back expect lo 0 hi 88320")),
    (6000, A(69)),
    (6500, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "tp-pos", "tp-lo", "tp-hi"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
open(f"{T}/hn.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hn.pd"],
                     capture_output=True, text=True).stderr
cur = None; got = {}
for line in out.splitlines():
    if line.startswith("dbg:"):
        cur = line[5:]; got[cur] = {}; print(line)
    elif cur and line.split(":")[0] in ("tp-pos", "tp-lo", "tp-hi"):
        k, v = line.split(":")
        if k not in got[cur]:
            got[cur][k] = float(v); print("    first", k, float(v))
    elif "error" in line and "no such object" not in line and "soundfiler" not in line and "seq-" not in line:
        print(line)
w = wave.open(f"{T}/p1-tape-1.wav"); d = w.readframes(w.getnframes())
s = struct.unpack("<%dh" % (len(d) // 2), d)
nz = [i for i, v in enumerate(s) if abs(v) > 300]
print("recorded audio on track 1 from sample", nz[0] if nz else None, "to", nz[-1] if nz else None,
      f"(loop 2 = {BAR}..{2 * BAR})")
shutil.rmtree(T)

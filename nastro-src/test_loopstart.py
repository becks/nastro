#!/usr/bin/env python3
"""Loop from the keys (apply_loopstart.py). Tempo 120, loop snap = bar: AUX + G# at bar 0 and bar 4 -> loop 0..4;
DUPLICATE -> loop 4..8; AUX + G# -> loop off; rewind, forward to bar 8, AUX + G#, forward to bar 12, AUX + G# ->
loop 8..12 (before the fix the start was lost and the loop went 0..12)."""
import os, shutil, subprocess, struct, math, tempfile, wave, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro"); SR = 44100; BS = "\\"
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav": shutil.copy(os.path.join(SRC, f), T)
w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 220 * i / SR))) for i in range(30 * SR))); w.close()
F = ["aux-key 75"]
ev = [(300, ["sfread read t1.wav tape1", "tp-loaded bang", "mode 4", "tempo-knob 3 0.9", "mode 2"]),
      (600, ["mark A-loop0-4", "aux-key 68"]), (700, F * 4), (800, ["aux-key 68"]),
      (1000, ["mark B-dup", "tape-edit 6"]),
      (2000, ["mark C-off", "aux-key 68"]),
      (2200, ["mark D-goto8", "aux-key 67"]), (2300, F * 8), (2400, ["mark E-start", "aux-key 68"]),
      (2500, F * 4), (2600, ["mark F-end", "aux-key 68"]), (2800, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]; C = ["#X connect 0 0 1 0;"]; n = 2
for t, m in ev:
    L.append(f"#X obj 20 {80+n*10} delay {t};"); L.append(f"#X msg 120 {80+n*10} " + " ".join(BS + "; " + x for x in m) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n+1} 0;"]; n += 2
L += ["#X obj 600 400 soundfiler;", "#X obj 600 370 r sfread;"]; C.append(f"#X connect {n+1} 0 {n} 0;"); n += 2
for r in ("mark", "tp-ls", "tp-lo", "tp-hi", "tp-in", "nst-proj-status"):
    L += [f"#X obj 900 {n*20} r {r};", f"#X obj 900 {n*20+20} print {r};"]; C.append(f"#X connect {n} 0 {n+1} 0;"); n += 2
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi", "-stderr", "-r", "44100",
                      "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
shutil.rmtree(T)
sec, cur = {}, "pre"
for l in out.splitlines():
    k = l.split(":")[0]
    if k == "mark":
        cur = l.split()[-1]
    elif k in ("tp-lo", "tp-hi"):
        sec.setdefault(cur, {})[k] = round(float(l.split()[-1]) / 88200)
print(sec)
ok = (sec.get("A-loop0-4") == {"tp-hi": 4, "tp-lo": 0} and sec.get("B-dup") == {"tp-hi": 8, "tp-lo": 4}
      and sec.get("F-end") == {"tp-hi": 12, "tp-lo": 8})
print("ALL OK" if ok else "FAIL")

#!/usr/bin/env python3
"""Reverb freeze test. A 500 Hz burst goes into the reverb (short DEC, T60 ~0.8 s); AUX + G5 freezes right after.
Checks: the tail holds for seconds while frozen (also with REV turned to 0 meanwhile), a 1200 Hz burst sent
while frozen does not enter it, after the
release the tail decays again, the level never grows, the LED goes white (7) and back to the page colour."""
import os, shutil, subprocess, tempfile, sys, math, struct

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
# timeline (ms): 1000 burst A (500 Hz, 100 ms) ; 1250 freeze ; 2500 burst B (1200 Hz) ; 5000 release ; 8000 end
ev = [(600, ["fx-rmix 0.8", "fx-dmix 0", "rvb-knob 1 0.2", "rvb-knob 2 0.6"]),
      (990, ["recA bang"]), (1000, ["frq 500", "amp 0.4"]), (1100, ["amp 0"]),
      (1250, ["aux-key 79"]), (2500, ["frq 1200", "amp 0.4"]), (2600, ["amp 0"]), (2700, ["fx-rmix 0"]),
      (5000, ["aux-key 79"]), (8000, ["dump bang"]), (8200, ["pd quit"])]
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


o = add("#X obj 600 20 osc~ 500;"); fr = add("#X obj 700 20 r frq;"); ra = add("#X obj 800 20 r amp;")
mu = add("#X obj 600 50 *~ 0;"); th = add("#X obj 600 80 throw~ fxr-tape;")       # straight into the reverb send bus
C += [f"#X connect {fr} 0 {o} 0;", f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
add(f"#X obj 1100 100 table capA {8 * SR};"); tw = add("#X obj 1100 80 tabwrite~ capA;"); rr = add("#X obj 1100 50 r recA;")
sf = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
md = add(f"#X msg 900 430 write -wave -bytes 4 {T}/A.wav capA;")
rl = add("#X obj 1300 20 r led;"); pl = add("#X obj 1300 50 print LED;")
C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;",
      f"#X connect {rl} 0 {pl} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
b = open(f"{T}/A.wav", "rb").read(); i = b.index(b"data") + 8
x = struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])
shutil.rmtree(T)
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
leds = [l.split(":")[1].strip() for l in out.splitlines() if l.startswith("LED:")]


def rms(a, b_):                       # seconds from the start of the capture (burst A at 0.01 s)
    seg = x[int(a * SR):int(b_ * SR)]
    return math.sqrt(sum(v * v for v in seg) / max(1, len(seg)))


def tone(f, a, b_):
    seg = x[int(a * SR):int(b_ * SR)]
    c = sum(v * math.cos(2 * math.pi * f * k / SR) for k, v in enumerate(seg))
    s_ = sum(v * math.sin(2 * math.pi * f * k / SR) for k, v in enumerate(seg))
    return 2 * math.hypot(c, s_) / max(1, len(seg))


r_frz0, r_frz1, r_frz2 = rms(0.35, 0.55), rms(2.0, 2.2), rms(3.7, 3.9)
b_in = tone(1200, 1.6, 3.9) / max(1e-9, tone(500, 1.6, 3.9))
r_rel = rms(6.5, 7.0)
peak = max(map(abs, x))
print(f"frozen tail rms: 0.4 s {r_frz0:.4f}   2.1 s {r_frz1:.4f}   3.8 s {r_frz2:.4f}")
print(f"1200 Hz sent while frozen, relative to the frozen 500 Hz: {b_in:.3f}")
print(f"2 s after the release: {r_rel:.5f}   peak {peak:.3f}   LED {leds}   errors {errs[:3]}")
ok = (r_frz2 > 0.5 * r_frz0 and r_frz2 < 1.2 * r_frz0 and b_in < 0.05 and r_rel < 0.05 * r_frz2 and peak < 1.0
      and "7" in leds and leds[-1] != "7" and not errs)
print("OK" if ok else "FAIL")

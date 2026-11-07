#!/usr/bin/env python3
"""Per-track FX sends. Track 1 holds a 100 ms 500 Hz burst, track 2 a 100 ms 1200 Hz burst, both 1 s into the tape
(after the play speed ramp).
Delay measured with the reverb off, reverb with the delay off, over everything after the dry burst.
1) defaults: both tones in the echo and in the tail, and the output (delay + reverb on) equals the build in argv[1]
2) track 1 delay send 0: no 500 Hz in the echo, 1200 Hz still there
3) track 2 reverb send 0: no 1200 Hz in the tail, 500 Hz still there"""
import os, shutil, subprocess, tempfile, sys, math, struct, wave

HERE = os.path.dirname(os.path.abspath(__file__))
NEW = os.path.join(HERE, "..", "Nastro")
OLD = sys.argv[1] if len(sys.argv) > 1 else None
SR, BS = 44100, "\\"


def run(src, setup):
    T = tempfile.mkdtemp()
    for f in os.listdir(src):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(src, f), T)
    for k, fr in ((1, 500), (2, 1200)):
        w = wave.open(f"{T}/t{k}.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(0.3 * 32767 * math.sin(2 * math.pi * fr * i / SR)) if SR <= i < SR + 4410 else 0)
                               for i in range(3 * SR)))
        w.close()
    ev = [(400, ["ld bang"]), (850, setup),
          (900, ["recA bang", "aux-key 65"]), (3300, ["dump bang"]), (3500, ["pd quit"])]
    L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
    C = ["#X connect 0 0 1 0;"]
    n = 2
    for t_ms, msgs in ev:
        L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
        L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
        C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
        n += 2

    def add(s_):
        nonlocal n
        L.append(s_); n += 1
        return n - 1
    sf = add("#X obj 900 500 soundfiler;"); rl = add("#X obj 900 400 r ld;")
    ml = add(f"#X msg 900 430 read {T}/t1.wav tape1 \\, read {T}/t2.wav tape2;")
    C += [f"#X connect {rl} 0 {ml} 0;", f"#X connect {ml} 0 {sf} 0;"]
    cl = add("#X obj 1100 20 catch~ outL;"); add("#X obj 1200 20 catch~ outR;")
    add(f"#X obj 1100 100 table capA {3 * SR};"); tw = add("#X obj 1100 80 tabwrite~ capA;"); rr = add("#X obj 1100 50 r recA;")
    rd = add("#X obj 1300 400 r dump;"); md = add(f"#X msg 1300 430 write -wave -bytes 4 {T}/A.wav capA;")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                          "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
    b = open(f"{T}/A.wav", "rb").read(); i = b.index(b"data") + 8
    x = struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])
    shutil.rmtree(T)
    errs = [l for l in out.splitlines() if "error" in l and not any(
        k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
    return x, errs


def tone(x, f, a, b):
    seg = x[int(a * SR):int(b * SR)]
    c = sum(v * math.cos(2 * math.pi * f * k / SR) for k, v in enumerate(seg))
    s_ = sum(v * math.sin(2 * math.pi * f * k / SR) for k, v in enumerate(seg))
    return 2 * math.hypot(c, s_) / max(1, len(seg))


def onset(x):
    return next(k for k, v in enumerate(x) if abs(v) > 0.05) / SR


bad = 0
DLY = ["fx-fb 0", "fx-dmix 0.7", "fx-rmix 0"]; REV = ["fx-dmix 0", "fx-rmix 0.7"]
cases = [("defaults (delay)", DLY), ("defaults (reverb)", REV), ("track 1 delay send 0", DLY + ["dsend-knob 1 0"]),
         ("track 2 reverb send 0", REV + ["rsend-knob 2 0"])]
res = {}
for nm, setup in cases:
    x, errs = run(NEW, setup)
    t0 = onset(x)
    echo = (tone(x, 500, t0 + 0.15, t0 + 2.0), tone(x, 1200, t0 + 0.15, t0 + 2.0))      # all after the dry burst
    tail = echo
    res[nm] = (x, echo, tail)
    print(f"{nm:24s} after the burst: 500 Hz {echo[0]:.5f}  1200 Hz {echo[1]:.5f}  {errs[:2]}")
    bad += bool(errs)
d_echo, d_tail = res["defaults (delay)"][1], res["defaults (reverb)"][2]
e1, t2 = res["track 1 delay send 0"][1], res["track 2 reverb send 0"][2]
ok1 = min(d_echo) > 0.001 and min(d_tail) > 0.001
ok2 = e1[0] < d_echo[0] * 0.05 and e1[1] > d_echo[1] * 0.9
ok3 = t2[1] < d_tail[1] * 0.05 and t2[0] > d_tail[0] * 0.9
print("defaults: both tones in echo and tail", "OK" if ok1 else "FAIL")
print("delay send 0 removes only track 1 from the echo", "OK" if ok2 else "FAIL")
print("reverb send 0 removes only track 2 from the tail", "OK" if ok3 else "FAIL")
bad += (not ok1) + (not ok2) + (not ok3)
if OLD:
    xo, _ = run(OLD, DLY[:2] + ["fx-rmix 0.7"])
    xn, _ = run(NEW, DLY[:2] + ["fx-rmix 0.7"])
    diff = max(abs(a - b) for a, b in zip(xo, xn))
    print(f"defaults vs previous build: max sample difference {diff:.6f}", "OK" if diff < 1e-4 else "FAIL")
    bad += diff >= 1e-4
print("ALL OK" if not bad else f"{bad} FAILED")

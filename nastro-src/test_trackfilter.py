#!/usr/bin/env python3
"""Track DJ filter test: track 1 holds 200 Hz + 5 kHz, track 2 holds 1 kHz. The level of each tone at the output
is measured (Goertzel) with track 1's filter off, low-pass (knob 0.2) and high-pass (knob 0.8); track 2 must not
change."""
import os, shutil, subprocess, tempfile, math, wave, struct

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, N = 44100, 44100 * 4
for name, tones in (("a", (200, 5000)), ("b", (1000,))):
    w = wave.open(f"{T}/{name}.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(sum(0.2 * math.sin(2 * math.pi * f_ * i / SR) for f_ in tones) * 32767))
                           for i in range(N)))
    w.close()
BS = "\\"
CASES = [("off", 0.5), ("LP 0.2", 0.2), ("HP 0.8", 0.8)]
ev = [(500, ["ld bang"]), (700, ["aux-key 65"])]
t = 900
for k, (nm, v) in enumerate(CASES):
    ev.append((t, [f"tfilt-knob 1 {v}"])); ev.append((t + 200, [f"rec{k} bang"])); t += 700
ev += [(t, ["dump bang"]), (t + 200, ["pd quit"])]
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
m_ = add(f"#X msg 700 330 read {T}/a.wav tape1 \\, read {T}/b.wav tape2;")
C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
rd = add("#X obj 900 400 r dump;")
dumps = []
for k in range(len(CASES)):
    add(f"#X obj {1100 + k * 150} 20 table cap{k} 8192;")
    tw = add(f"#X obj {1100 + k * 150} 80 tabwrite~ cap{k};"); rr = add(f"#X obj {1100 + k * 150} 50 r rec{k};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/c{k}.wav cap{k}")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))


def level(x, f):
    s = sum(v * math.sin(2 * math.pi * f * i / SR) for i, v in enumerate(x))
    c = sum(v * math.cos(2 * math.pi * f * i / SR) for i, v in enumerate(x))
    return 2 * math.hypot(s, c) / len(x)


base = None
for k, (nm, v) in enumerate(CASES):
    x = rd_(f"{T}/c{k}.wav")
    lv = [level(x, f) for f in (200, 5000, 1000)]
    if base is None:
        base = lv
    db = [20 * math.log10(max(a, 1e-9) / max(b, 1e-9)) for a, b in zip(lv, base)]
    print(f"{nm:7s}  200 Hz {db[0]:+6.1f} dB   5 kHz {db[1]:+6.1f} dB   track 2 (1 kHz) {db[2]:+5.1f} dB")
shutil.rmtree(T)

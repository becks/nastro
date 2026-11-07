#!/usr/bin/env python3
"""Punch-in/out test: track 1 holds a 300 Hz tone, the tape plays, and a 500 Hz tone is recorded from 1.0 s to
2.0 s, with overdub (knob 3 = 1) and with replace (knob 3 = 0). Reports steps left on tape at the punch points
(a step shows as a 2nd difference far above a clean tone's)."""
import os, shutil, subprocess, tempfile, sys, math, wave, struct

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
SR, BS = 44100, "\\"


def run(dub):
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(SRC, f), T)
    w = wave.open(f"{T}/old.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 300 * i / SR))) for i in range(4 * SR))); w.close()
    ev = [(500, ["ld bang"]), (700, ["mode 2", f"tape-knob 3 {dub}", "amp 0.3", "aux-key 65"]),
          (1700, ["aux-key 66"]), (2700, ["aux-key 66"]), (3400, ["aux-key 65", "dump bang"]), (3600, ["pd quit"])]
    L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
    C = ["#X connect 0 0 1 0;"]
    n = 2
    for t_ms, msgs in ev:
        L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
        L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
        C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
        n += 2

    def add(s):
        nonlocal n
        L.append(s); n += 1
        return n - 1
    o = add("#X obj 600 20 osc~ 500;"); ra = add("#X obj 700 20 r amp;"); mu = add("#X obj 600 50 *~ 0;")
    th = add("#X obj 600 80 throw~ synth-bus;")
    C += [f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
    add("#X obj 800 20 catch~ outL;"); add("#X obj 900 20 catch~ outR;")
    sf = add("#X obj 700 600 soundfiler;"); rl = add("#X obj 700 250 r ld;")
    ml = add(f"#X msg 700 270 read {T}/old.wav tape1;")
    rd = add("#X obj 700 300 r dump;")
    md = add(f"#X msg 700 330 write -wave -bytes 4 -nframes {3 * SR} {T}/t1.wav tape1;")
    C += [f"#X connect {rl} 0 {ml} 0;", f"#X connect {ml} 0 {sf} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                    "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)
    b = open(f"{T}/t1.wav", "rb").read(); i = b.index(b"data") + 8
    x = list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))
    shutil.rmtree(T)
    amp = max(map(abs, x))
    clean = amp * (2 * math.pi * 500 / SR) ** 2
    d2 = [abs(x[k + 1] - 2 * x[k] + x[k - 1]) for k in range(1, len(x) - 1)]
    bad = [k for k in range(len(d2)) if d2[k] > 3 * clean]
    rec = [k for k in range(len(x)) if abs(x[k]) > 0.3]       # where the new tone landed (overdub peaks > old)
    worst = max(d2)
    mode = "overdub" if dub else "replace"
    print(f"{mode:8s} tape peak {amp:.3f}  clean d2 {clean:.5f}  worst d2 {worst:.5f}  steps {len(bad)} "
          f"{[round(k / SR, 3) for k in bad[:4]]}")
    return len(bad)


bad = run(1) + run(0)
print("CLEAN" if bad == 0 else "STEPS")

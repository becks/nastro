#!/usr/bin/env python3
"""SMPL loop points (apply_smplloop.py). A 1 s sample in four quarters: 300 / 500 / 700 / 900 Hz.
A loop, points 50 / 75 % (AUX + knobs 2 / 3 through synth.pd): after the first pass only 700 Hz, never 300 or 900.
B loop, default points 0 / 100 %: the whole sample again after 1 s (300 Hz back), as before.
C one-shot: silent after the sample.   D s+lp (time-stretch) with 50 / 75 %: 700 Hz from 0.75 s on.
E playheads: while a note plays, [s smp-ph-ask] (the test's and the SMPL page's) gets positions that move forward."""
import os, shutil, subprocess, struct, math, tempfile, sys, wave

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
w = wave.open(f"{T}/s.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
ph, fr = 0.0, (300, 500, 700, 900)
data = []
for i in range(SR):
    ph += 2 * math.pi * fr[i * 4 // SR] / SR
    data.append(struct.pack("<h", int(16000 * math.sin(ph))))
w.writeframes(b"".join(data)); w.close()
LOOPK = ["aux 1", "synth-knob 2 0.5", "synth-knob 3 0.75", "aux 0"]
DEFK = ["aux 1", "synth-knob 2 0", "synth-knob 3 1", "aux 0"]
ev = [(300, ["synth-engine-set 4", "sfread read -resize s.wav smpl", "smp-len 44100"]),
      (500, ["synth-knob 1 0", "synth-knob 2 1", "synth-knob 3 0.2", "synth-knob 4 0.9"] + LOOPK),
      (1000, ["recA bang", "notes 60 100"]), (3000, ["notes 60 0"]),
      (3500, DEFK), (3700, ["recB bang", "notes 60 100"]), (5700, ["notes 60 0"]),
      (6200, ["synth-knob 4 0"]), (6400, ["recC bang", "notes 60 100"]), (8400, ["notes 60 0"]),
      (8900, ["synth-knob 4 0.6"] + LOOPK), (9100, ["recD bang", "notes 60 100"]), (11100, ["notes 60 0"]),
      (11600, ["synth-knob 4 0.9", "notes 60 100"]), (11700, ["smp-ph-ask bang"]), (11900, ["smp-ph-ask bang"]),
      (12100, ["notes 60 0"]), (12400, ["dump bang"]), (12600, ["pd quit"])]
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


sf = add("#X obj 600 400 soundfiler;"); rr = add("#X obj 600 370 r sfread;"); C.append(f"#X connect {rr} 0 {sf} 0;")
for rcv, tag in (("smp-ph", "PH"), ("smp-l0", "L0"), ("smp-l1", "L1")):
    a = add(f"#X obj 700 {20 + n} r {rcv};"); b = add(f"#X obj 700 {40 + n} print {tag};"); C.append(f"#X connect {a} 0 {b} 0;")
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
dumps = []
for nm in "ABCD":
    add(f"#X obj 1100 120 table cap{nm} {int(2.1 * SR)};")
    tw = add(f"#X obj 1100 90 tabwrite~ cap{nm};"); r_ = add(f"#X obj 1100 60 r rec{nm};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {r_} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/{nm}.wav cap{nm}")
sf2 = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf2} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])


def freqs(x):
    """dominant frequency every 100 ms (zero crossings), 0 when silent"""
    res = []
    for t0 in range(0, len(x) - 4410, 4410):
        seg = x[t0:t0 + 4410]
        if max(abs(v) for v in seg) < 0.01:
            res.append(0); continue
        z = sum(1 for j in range(1, len(seg)) if seg[j - 1] < 0 <= seg[j])
        res.append(round(z * 10 / 100) * 100)
    return res


F = {nm: freqs(rd_(f"{T}/{nm}.wav")) for nm in "ABCD"}
shutil.rmtree(T)
for nm in "ABCD":
    print(nm, F[nm])
ph = [float(l.split()[-1]) for l in out.splitlines() if l.startswith("PH:")]
lpts = [l for l in out.splitlines() if l.startswith(("L0:", "L1:"))][-2:]
print("loop points", lpts, " playheads", ph, " errors", errs[:3])
ok = {}
ok["A"] = all(f in (700, 0) for f in F["A"][9:19]) and 300 in F["A"][:3] and 900 not in F["A"][8:19]
ok["B"] = 900 in F["B"][7:10] and 300 in F["B"][10:13]
ok["C"] = all(f == 0 for f in F["C"][11:19])
ok["D"] = all(f in (700, 0) for f in F["D"][9:19]) and 900 not in F["D"][9:19]
ok["E"] = len(ph) >= 4 and max(ph) > min(ph)          # the page asks on every frame while notes sound
print(ok)
print("ALL OK" if all(ok.values()) and not errs else "FAIL")

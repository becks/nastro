#!/usr/bin/env python3
"""Synth LFO. FM engine, LFO page opened with AUX + D5.
1) DEST INDEX, sine 2 Hz, AMT 100 %: fm-index swings around its knob value, back to it when TYPE goes off.
2) DEST VOL: a held note's level swings at 2 Hz.  3) DEST PITCH: a held note's pitch swings at 2 Hz.
4) knob contexts: the LFO page is context 29 + engine, the page closes when leaving SYNTH."""
import os, shutil, subprocess, struct, math, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
R2 = math.log(40) / math.log(200)                      # RATE knob for 2 Hz
ev = [(300, ["synth-knob 2 0.5"]),                     # FM (already on SYNTH), INDEX knob 0.5 -> 2.5
      (500, ["mark page", "aux-key 74"]),
      (600, ["synth-knob 1 0.15", f"synth-knob 2 {R2}", "synth-knob 3 1", "synth-knob 4 0.2"]),
      (1600, ["mark off", "synth-knob 1 0"]),
      (1900, ["mark vol", "synth-knob 4 0.9", "synth-knob 1 0.15", "synth-knob 3 1"]),
      (2000, ["recV bang", "notes 60 100"]), (3600, ["notes 60 0"]),
      (3800, ["mark pitch", "synth-knob 4 0.7"]),
      (4000, ["recP bang", "notes 72 100"]), (5600, ["notes 72 0"]),
      (5800, ["mark tape", "mode 2"]), (6000, ["pd quit"])]
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


for rcv, tag in (("fm-index", "IDX"), ("mark", "MARK"), ("syn-lfo-page", "PAGE"), ("syn-lfo-p", "LFOP")):
    a = add(f"#X obj 600 {20 + n} r {rcv};"); b = add(f"#X obj 600 {40 + n} print {tag};")
    C.append(f"#X connect {a} 0 {b} 0;")
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
sf = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
for nm in ("V", "P"):
    add(f"#X obj 1100 120 table cap{nm} {int(1.6 * SR)};")
    tw = add(f"#X obj 1100 90 tabwrite~ cap{nm};"); rr = add(f"#X obj 1100 60 r rec{nm};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
dm = add(f"#X msg 900 430 write -wave -bytes 4 {T}/V.wav capV \\, write -wave -bytes 4 {T}/P.wav capP;")
lb = add("#X obj 900 370 r pd-quit-dummy;")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
L[-1:] = L[-1:]
# dump right before quitting
ev_dump = add("#X obj 1300 20 delay 5900;"); dmb = add("#X msg 1300 50 " + BS + "; dump bang;")
C += [f"#X connect 0 0 {ev_dump} 0;", f"#X connect {ev_dump} 0 {dmb} 0;"]
ctx = add("#X obj 1500 20 metro 100;"); ce = add("#X obj 1500 50 r mark;")
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if ("error" in l or "couldn't" in l or "bad arguments" in l) and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])


seq, cur = {}, "pre"
for l in out.splitlines():
    if l.startswith("MARK:"):
        cur = l.split()[-1]
    elif l.startswith(("IDX:", "PAGE:", "LFOP:")):
        seq.setdefault(cur, []).append(l)
idx_page = [float(l.split()[-1]) for l in seq.get("page", []) if l.startswith("IDX")]
idx_off = [float(l.split()[-1]) for l in seq.get("off", []) if l.startswith("IDX")]
print(f"INDEX while modulated: {len(idx_page)} values, {min(idx_page, default=0):.2f} .. {max(idx_page, default=0):.2f}"
      f"   after TYPE off: {idx_off[-1:] }")
print("page / row markers:", {k: [l for l in v if not l.startswith('IDX')] for k, v in seq.items()})
ok1 = len(idx_page) > 20 and min(idx_page) < 1.0 and max(idx_page) > 4.5 and idx_off and abs(idx_off[-1] - 2.5) < 0.01

x = rd_(f"{T}/V.wav")[int(0.2 * SR):]
env = [math.sqrt(sum(v * v for v in x[i:i + 441]) / 441) for i in range(0, len(x) - 441, 441)]
# level swing and its period (autocorrelation of the envelope, 10 ms steps)
m = sum(env) / len(env); e0 = [v - m for v in env]
best = max(range(30, 80), key=lambda L_: sum(e0[i] * e0[i + L_] for i in range(len(e0) - L_)))
print(f"VOL: level {min(env):.3f} .. {max(env):.3f}, period {best * 10} ms (expect 500)")
ok2 = min(env) < 0.3 * max(env) and abs(best * 10 - 500) <= 40

y = rd_(f"{T}/P.wav")[int(0.2 * SR):]
win = []
for t0 in range(0, len(y) - 2048, 1102):              # pitch every 25 ms: autocorrelation around 523 Hz
    w = y[t0:t0 + 2048]
    lo, hi = int(SR / 600), int(SR / 450)
    c = [sum(w[i] * w[i + lg] for i in range(1024)) for lg in range(lo - 1, hi + 2)]
    k = max(range(1, len(c) - 1), key=lambda j: c[j])
    d = (c[k - 1] - c[k + 1]) / (2 * (c[k - 1] - 2 * c[k] + c[k + 1])) if (c[k - 1] - 2 * c[k] + c[k + 1]) else 0
    win.append(SR / (lo - 1 + k + d))
print(f"PITCH: {min(win):.1f} .. {max(win):.1f} Hz around {sum(win) / len(win):.1f}")
ok3 = max(win) / min(win) > 1.02 and max(win) / min(win) < 1.08
pg = [l for l in seq.get("tape", []) if l.startswith("PAGE")]
ok4 = pg and pg[-1].endswith("0")
shutil.rmtree(T)
print("errors:", errs[:5])
print("OK" if ok1 and ok2 and ok3 and ok4 and not errs else f"FAIL {ok1} {ok2} {ok3} {ok4}")

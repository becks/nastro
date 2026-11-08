#!/usr/bin/env python3
"""SMPL time-stretch: a 330 Hz input is sampled (~0.5 s), then C3 / C4 / C5 are played (held 2 s, one-shot)
with MODE one and with MODE str. Without stretch a note lasts sample length / rate and sounds at 330 x rate;
with stretch every note lasts the sample length and sounds at 330 x rate within the granular limit (+-20 Hz on a
pure tone with 50 ms grains)."""
import os, shutil, subprocess, struct, math, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
NOTES = (48, 60, 72)
ev = [(100, ["synth-knob 2 0", "synth-knob 4 0", "synth-knob 3 0"]),
      (300, A(60) + A(60) + A(60) + A(60)),                   # FM -> SUB -> PLUK -> PAD -> SMPL
      (700, A(76)), (1200, A(76))]                            # sample the input for ~0.5 s
t, recs = 1600, []
for mode_knob, tag in ((0.0, "one"), (0.3, "str")):
    ev.append((t, [f"synth-knob 4 {mode_knob}"])); t += 200
    for nt in NOTES:
        k = len(recs)
        ev.append((t, [f"rec{k} bang", f"notes {nt} 100"])); ev.append((t + 2000, [f"notes {nt} 0"]))
        recs.append((tag, nt)); t += 2600
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


o = add("#X obj 600 300 osc~ 330;"); g = add("#X obj 600 330 *~ 0.5;")
sl = add("#X obj 600 360 s~ inL;"); sr = add("#X obj 700 360 s~ inR;")
C += [f"#X connect {o} 0 {g} 0;", f"#X connect {g} 0 {sl} 0;", f"#X connect {g} 0 {sr} 0;"]
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
sf = add("#X obj 900 500 soundfiler;"); rd = add("#X obj 900 400 r dump;")
pl = add("#X obj 1300 20 r smp-len;"); pp = add("#X obj 1300 50 print LEN;")
C.append(f"#X connect {pl} 0 {pp} 0;")
dumps = []
for k in range(len(recs)):
    add(f"#X obj {1100 + k * 100} 120 table cap{k} {int(2.4 * SR)};")
    tw = add(f"#X obj {1100 + k * 100} 90 tabwrite~ cap{k};"); rr = add(f"#X obj {1100 + k * 100} 60 r rec{k};")
    C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
    dumps.append(f"write -wave -bytes 4 {T}/c{k}.wav cap{k}")
dm = add("#X msg 900 430 " + " \\, ".join(dumps) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
lens = [l for l in out.splitlines() if l.startswith("LEN:")]
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
slen = float(lens[-1].split()[1]) / SR if lens else 0


def rd_(p):
    b = open(p, "rb").read(); i = b.index(b"data") + 8
    return struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4])


def freq(seg, guess):
    """pitch inside the grains: autocorrelation on short windows (1024 samples, shorter than a 50 ms grain) at
    several offsets, median. A long-window spectrum shows the 20 Hz grain comb instead of the grains' pitch."""
    est = []
    lo, hi = int(SR / (guess * 1.25)), int(SR / (guess * 0.8)) + 1
    for off in range(0, max(1, len(seg) - 1024 - hi), 700):
        w = seg[off:off + 1024 + hi]
        best, bl = -1e9, 0
        for lag in range(lo, hi):
            c = sum(w[i] * w[i + lag] for i in range(1024))
            if c > best:
                best, bl = c, lag
        # parabolic refinement around the best lag
        cm = sum(w[i] * w[i + bl - 1] for i in range(1024)); cp = sum(w[i] * w[i + bl + 1] for i in range(1024))
        d = (cm - cp) / (2 * (cm - 2 * best + cp)) if (cm - 2 * best + cp) else 0
        est.append(SR / (bl + d))
    est.sort()
    return est[len(est) // 2] if est else 0


bad = 0
print(f"sample length {slen:.3f} s   {errs[:3]}")
for k, (tag, nt) in enumerate(recs):
    x = rd_(f"{T}/c{k}.wav")
    env = [math.sqrt(sum(v * v for v in x[i:i + 441]) / 441) for i in range(0, len(x) - 441, 441)]
    top = max(env) or 1
    on = [i for i, e in enumerate(env) if e > top * 0.3]
    dur = (on[-1] - on[0] + 1) / 100 if on else 0
    rate = 2 ** ((nt - 60) / 12)
    seg = x[on[0] * 441 + 1000:on[0] * 441 + 1000 + min(8192, int(dur * SR * 0.8))] if on else []
    f = freq(seg, 330 * rate) if on else 0
    exp_dur = slen if tag == "str" else slen / rate
    # two cross-fading grains read the sound at different phases: with 50 ms grains the pitch of a pure tone can
    # drift by up to 1 / (2 x 25 ms) = 20 Hz (granular pitch shift; on real sounds it is a slight chorus)
    tol = 20 if tag == "str" else 330 * rate * 0.02
    ok = abs(dur - exp_dur) < 0.06 + 0.05 * exp_dur and abs(f - 330 * rate) < tol
    bad += not ok
    print(f"MODE {tag}  note {nt}: lasts {dur:.2f} s (expect {exp_dur:.2f})  pitch {f:6.1f} Hz (expect {330 * rate:6.1f})  {'OK' if ok else 'FAIL'}")
shutil.rmtree(T)
print("ALL OK" if not bad and not errs else f"{bad} FAILED")

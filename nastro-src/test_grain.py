#!/usr/bin/env python3
"""Reverb SIZE / GRAIN / long DECAY, and the conversion of projects saved before them.
A 10 ms noise burst goes into the reverb (track sends only, delay off) for each setting; checks:
1) DECAY at the top reaches tens of seconds (RT60 extrapolated from the -5..-25 dB slope)
2) SIZE: same DECAY gives about the same RT60 at SIZE 0 and 1; the pre-delay grows with SIZE
3) GRAIN: at 1 the tail has much more high-frequency grit than at 0, stays bounded and still dies away
4) a project saved before SIZE / GRAIN (192 values, PRE 0.15 / MOD 0.3) loads as SIZE 0.5 / GRAIN 0;
   a new one (196 values) keeps its SIZE / GRAIN"""
import os, shutil, subprocess, tempfile, math, struct

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
PD = "/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd"
SR, BS = 44100, "\\"


def patch(T, events, extra=lambda add, C: None):
    L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
    C = ["#X connect 0 0 1 0;"]
    n = [2]
    for t_ms, msgs in events:
        L.append(f"#X obj 20 {80 + n[0] * 10} delay {t_ms};")
        L.append(f"#X msg 120 {80 + n[0] * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
        C += [f"#X connect 0 0 {n[0]} 0;", f"#X connect {n[0]} 0 {n[0] + 1} 0;"]
        n[0] += 2

    def add(t):
        L.append(t); n[0] += 1
        return n[0] - 1
    extra(add, C)
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    return subprocess.run([PD, "-nogui", "-batch", "-noaudio", "-nomidi", "-stderr", "-r", str(SR),
                           "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr


def tmp():
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(SRC, f), T)
    return T


def capture(knobs, secs):
    """burst into the reverb with rvb-set knobs, return the left output (secs long, from the burst)"""
    T = tmp()
    ev = [(700, ["fx-dmix 0", "fx-rmix 1"] + [f"rvb-set {k} {v}" for k, v in knobs.items()]),
          (1200, ["burst bang", "rec bang"]), (1300 + int(secs * 1000), ["dump bang"]),
          (1500 + int(secs * 1000), ["pd quit"])]

    def extra(add, C):
        nz = add("#X obj 600 20 noise~;"); env = add("#X obj 700 20 vline~;"); mul = add("#X obj 600 50 *~;")
        rb = add("#X obj 700 -10 r burst;"); bm = add("#X msg 700 5 0.3 \\, 0 0 10;")
        th = add("#X obj 600 80 throw~ fxr-tape;")
        C += [f"#X connect {nz} 0 {mul} 0;", f"#X connect {env} 0 {mul} 1;", f"#X connect {mul} 0 {th} 0;",
              f"#X connect {rb} 0 {bm} 0;", f"#X connect {bm} 0 {env} 0;"]
        cL = add("#X obj 900 20 catch~ outL;")
        add(f"#X obj 1100 20 table cap {int(secs * SR)};")
        tw = add("#X obj 1100 60 tabwrite~ cap;"); rr = add("#X obj 1100 40 r rec;")
        C += [f"#X connect {cL} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
        sf = add("#X obj 900 400 soundfiler;"); rd = add("#X obj 900 300 r dump;")
        dm = add(f"#X msg 900 330 write -wave -bytes 4 {T}/c.wav cap;")
        C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
    out = patch(T, ev, extra)
    b = open(f"{T}/c.wav", "rb").read()
    i = b.index(b"data") + 8
    x = list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))
    errs = [l for l in out.splitlines() if "error" in l and not any(
        k in l for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob", "receive~"))]
    shutil.rmtree(T)
    return x, errs


def env_db(x, w=0.02):
    n = int(w * SR)
    return [10 * math.log10(sum(v * v for v in x[i:i + n]) / n + 1e-20) for i in range(0, len(x) - n, n)]


def rt60(x):
    """extrapolated from the -5..-25 dB part of the decay"""
    e = env_db(x[int(0.025 * SR):])
    pk = max(range(len(e)), key=lambda i: e[i])
    t5 = next((i for i in range(pk, len(e)) if e[i] < e[pk] - 5), None)
    t25 = next((i for i in range(pk, len(e)) if e[i] < e[pk] - 25), None)
    if t5 is None:
        return None
    if t25 is None:                                   # slow decay: slope over what we have
        t25 = len(e) - 1
        return 60 * (t25 - t5) * 0.02 / max(0.1, e[t5] - e[t25])
    return (t25 - t5) * 0.02 * 3


def onset(x):
    tail = x[int(0.012 * SR):]                        # after the dry burst... the reverb only (send-only feed)
    pk = max(map(abs, tail))
    return next(i for i, v in enumerate(tail) if abs(v) > 0.05 * pk) / SR * 1000 + 12


def hf(x, a, b):
    """high-frequency share of the tail: energy of the 2nd difference over energy"""
    s = x[int(a * SR):int(b * SR)]
    d2 = [s[i] - 2 * s[i - 1] + s[i - 2] for i in range(2, len(s))]
    return sum(v * v for v in d2) / (sum(v * v for v in s) + 1e-20)


ok = True
# 1) long DECAY
x, er = capture({1: 1.0, 2: 1.0, 3: 0.5, 4: 0}, 8)    # TONE open: damping shortens the early decay
t = rt60(x)
print(f"DECAY 1.0, TONE 1.0: RT60 ~{t:.0f} s (expect ~30-40)  errors {er[:2]}")
ok &= t is not None and 25 < t < 60 and not er
# 2) SIZE
res = {}
for sz in (0, 1):
    x, er = capture({1: 0.5, 2: 0.6, 3: sz, 4: 0}, 4)
    res[sz] = (rt60(x), onset(x), er)
    print(f"SIZE {sz}: RT60 {res[sz][0]:.2f} s   first reflection {res[sz][1]:.0f} ms   errors {er[:2]}")
ok &= abs(res[0][0] - res[1][0]) < 0.35 * res[1][0] and res[1][1] > res[0][1] + 40 and not res[0][2] and not res[1][2]
# 3) GRAIN
g = {}
for gr in (0, 1):
    x, er = capture({1: 0.6, 2: 0.6, 3: 0.5, 4: gr}, 5)
    g[gr] = (hf(x, 0.3, 1.5), max(map(abs, x)), math.sqrt(sum(v * v for v in x[int(4.5 * SR):]) / (0.4 * SR)),
             math.sqrt(sum(v * v for v in x[int(0.3 * SR):int(0.5 * SR)]) / (0.2 * SR)), er)
    print(f"GRAIN {gr}: HF share {g[gr][0]:.4f}   peak {g[gr][1]:.3f}   rms 0.3 s {g[gr][3]:.4f} -> 4.5 s {g[gr][2]:.5f}"
          f"   errors {er[:2]}")
ok &= g[1][0] > 3 * g[0][0] and g[1][1] < 1 and g[1][2] < 0.1 * g[1][3] and not g[0][4] and not g[1][4]
# 4) conversion of saved projects
T = tmp()
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen.py")).read()
init = src.split("pkval 0 ")[1].split(" " + BS + BS + ";")[0].split()
assert len(init) == 196, len(init)
old = init[:192]; old[66:68] = ["0.15", "0.3"]
new = init[:]; new[66:68] = ["0.8", "0.7"]
open(f"{T}/p5-pk.txt", "w").write("\n".join(old) + "\n")
open(f"{T}/p6-pk.txt", "w").write("\n".join(new) + "\n")


def extra(add, C):
    a = add("#X obj 600 50 r chk;"); e = add("#X obj 600 80 expr pkval[66] \\; pkval[67];")
    p = add("#X obj 600 110 pack f f;"); r = add("#X obj 600 140 print SIZE_GRAIN;")
    C += [f"#X connect {a} 0 {e} 0;", f"#X connect {e} 0 {p} 0;", f"#X connect {e} 1 {p} 1;", f"#X connect {p} 0 {r} 0;"]


out = patch(T, [(800, ["pm-load 5"]), (2000, ["chk bang"]), (2200, ["pm-load 6"]), (3400, ["chk bang"]),
                (3600, ["pd quit"])], extra)
sg = [l.split(":")[1].strip() for l in out.splitlines() if l.startswith("SIZE_GRAIN")]
shutil.rmtree(T)
print(f"old project (PRE 0.15, MOD 0.3) -> SIZE/GRAIN {sg[0]}   new project (0.8, 0.7) -> {sg[1]}")
ok &= sg == ["0.5 0", "0.8 0.7"]
print("OK" if ok else "FAIL")

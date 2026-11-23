#!/usr/bin/env python3
"""Delay with TONE / GRAIN / WOW / SPREAD (DELAY page) and FDBK up to 110 %.
A 10 ms 1 kHz burst goes into the delay (track sends only, reverb off), time 200 ms.
1) defaults: same echoes as the delay before (master.pd from git HEAD), both channels equal (mono)
2) SPREAD 1: ping-pong, 1st echo left, 2nd echo right
3) GRAIN 1: the echoes get much more high-frequency grit
4) WOW 1: the echoes move in time (differ from WOW 0), level about the same
5) FDBK knob at the top: self-oscillation that stays bounded (peak < 1)
6) AUX + D# cycles MIX -> FX -> DELAY -> FILTER -> MASTER -> SEND -> VIS -> MIX; a knob on DELAY is stored (ctx 48)
7) a project saved before (192 values) loads with the DELAY defaults"""
import os, shutil, subprocess, tempfile, math, struct

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "Nastro")
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


def tmp(old_master=False):
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(SRC, f), T)
    if old_master:
        for f in ("master.pd", "mix.pd"):
            open(f"{T}/{f}", "w").write(subprocess.run(["git", "show", f"HEAD:Nastro/{f}"], capture_output=True,
                                                       text=True, cwd=os.path.join(HERE, "..")).stdout)
    return T


def rdwav(p):
    b = open(p, "rb").read()
    i = b.index(b"data") + 8
    return list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))


def capture(setup, secs, old=False, fb=0.5):
    T = tmp(old)
    ev = [(700, ["fx-rmix 0", "fx-dmix 1", "fx-time 200", f"fx-fb {fb}"] + setup),
          (1200, ["burst bang", "rec bang"]), (1300 + int(secs * 1000), ["dump bang"]),
          (1500 + int(secs * 1000), ["pd quit"])]

    def extra(add, C):
        o = add("#X obj 600 20 osc~ 1000;"); env = add("#X obj 700 20 vline~;"); mul = add("#X obj 600 50 *~;")
        rb = add("#X obj 700 -10 r burst;"); bm = add("#X msg 700 5 0.3 \\, 0 0 10;")
        th = add("#X obj 600 80 throw~ fxd-tape;")
        C += [f"#X connect {o} 0 {mul} 0;", f"#X connect {env} 0 {mul} 1;", f"#X connect {mul} 0 {th} 0;",
              f"#X connect {rb} 0 {bm} 0;", f"#X connect {bm} 0 {env} 0;"]
        sf = add("#X obj 900 400 soundfiler;"); rd = add("#X obj 900 300 r dump;")
        dm = []
        for ch in "LR":
            c = add(f"#X obj 900 20 catch~ out{ch};")
            add(f"#X obj 1100 20 table cap{ch} {int(secs * SR)};")
            tw = add(f"#X obj 1100 60 tabwrite~ cap{ch};"); rr = add("#X obj 1100 40 r rec;")
            C += [f"#X connect {c} 0 {tw} 0;", f"#X connect {rr} 0 {tw} 0;"]
            dm.append(f"write -wave -bytes 4 {T}/{ch}.wav cap{ch}")
        m = add("#X msg 900 330 " + " \\, ".join(dm) + ";")
        C += [f"#X connect {rd} 0 {m} 0;", f"#X connect {m} 0 {sf} 0;"]
    out = patch(T, ev, extra)
    l, r = rdwav(f"{T}/L.wav"), rdwav(f"{T}/R.wav")
    errs = [x for x in out.splitlines() if "error" in x and not any(
        k in x for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob", "receive~", "read failed"))]
    shutil.rmtree(T)
    return l, r, errs


def rms(x, a, b):
    s = x[int(a * SR):int(b * SR)]
    return math.sqrt(sum(v * v for v in s) / max(1, len(s)))


def hf(x, a, b):
    s = x[int(a * SR):int(b * SR)]
    d2 = [s[i] - 2 * s[i - 1] + s[i - 2] for i in range(2, len(s))]
    return sum(v * v for v in d2) / (sum(v * v for v in s) + 1e-20)


ok = True
# 1) defaults vs the old delay
l0, r0, e0 = capture([], 1.5, old=True)
l1, r1, e1 = capture([], 1.5)
seg = slice(int(0.1 * SR), int(1.5 * SR))                      # echoes only (the dry burst is not in the delay output)
diff = math.sqrt(sum((a - b) ** 2 for a, b in zip(l0[seg], l1[seg])) / (sum(a * a for a in l0[seg]) + 1e-20))
lr = math.sqrt(sum((a - b) ** 2 for a, b in zip(l1[seg], r1[seg])) / (sum(a * a for a in l1[seg]) + 1e-20))
print(f"defaults: difference from the old delay {100 * diff:.1f} %   L-R difference {100 * lr:.2f} %   "
      f"echo 1 {rms(l1, 0.2, 0.21):.4f} (old {rms(l0, 0.2, 0.21):.4f})   errors {e1[:1]}")
ok &= diff < 0.05 and lr < 0.001 and not e1
# 2) SPREAD 1
l, r, e = capture(["dly-set 4 1"], 1.0)
e1L, e1R, e2L, e2R = rms(l, 0.2, 0.21), rms(r, 0.2, 0.21), rms(l, 0.4, 0.41), rms(r, 0.4, 0.41)
print(f"SPREAD 1: echo 1 L {e1L:.4f} R {e1R:.4f}   echo 2 L {e2L:.4f} R {e2R:.4f}   errors {e[:1]}")
ok &= e1L > 10 * e1R and e2R > 10 * e2L and not e
# 3) GRAIN
lg, _, e = capture(["dly-set 2 1"], 1.0)
h0, h1 = hf(l1, 0.19, 0.23), hf(lg, 0.19, 0.23)
print(f"GRAIN: HF share of echo 1  0 -> {h0:.4f}   1 -> {h1:.4f}   errors {e[:1]}")
ok &= h1 > 3 * h0 and not e
# 4) WOW
lw, _, e = capture(["dly-set 3 1"], 1.5)
dw = math.sqrt(sum((a - b) ** 2 for a, b in zip(l1[seg], lw[seg])) / (sum(a * a for a in l1[seg]) + 1e-20))
print(f"WOW 1: differs from WOW 0 by {100 * dw:.0f} %   level {rms(lw, 0.1, 1.5):.4f} vs {rms(l1, 0.1, 1.5):.4f}   errors {e[:1]}")
ok &= dw > 0.2 and 0.7 < rms(lw, 0.1, 1.5) / rms(l1, 0.1, 1.5) < 1.4 and not e
# 5) FDBK at the top (knob 1 -> 1.1)
ls, _, e = capture([], 6.0, fb=1.1)
print(f"FDBK 110 %: rms 1 s {rms(ls, 1, 1.5):.4f}   5.5 s {rms(ls, 5.5, 6):.4f}   peak {max(map(abs, ls)):.3f}   errors {e[:1]}")
ok &= rms(ls, 5.5, 6) > 0.5 * rms(ls, 1, 1.5) and max(map(abs, ls)) < 1 and not e
# 6) page cycle and DELAY knob storage
T = tmp()
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
ev = [(800, A(63))] + [(1000 + i * 100, A(63)) for i in range(7)]
ev += [(1150, ["knob1 0.545", "knob1 0.7", "knob3 0", "knob3 0.4"])]   # on DELAY (between the 2nd and 3rd page press)
ev = sorted(ev) + [(2000, ["chk bang"]), (2200, ["pd quit"])]


def extra(add, C):
    a = add("#X obj 400 50 r mix-page;"); b = add("#X obj 400 80 print PAGE;"); C.append(f"#X connect {a} 0 {b} 0;")
    a = add("#X obj 500 50 r dly-knob;"); b = add("#X obj 500 80 print DLYKNOB;"); C.append(f"#X connect {a} 0 {b} 0;")
    a = add("#X obj 600 50 r chk;"); e = add("#X obj 600 80 expr pkval[192] \\; pkval[194];")
    p = add("#X obj 600 110 pack f f;"); r = add("#X obj 600 140 print PK;")
    C += [f"#X connect {a} 0 {e} 0;", f"#X connect {e} 0 {p} 0;", f"#X connect {e} 1 {p} 1;", f"#X connect {p} 0 {r} 0;"]


out = patch(T, ev, extra)
shutil.rmtree(T)
pages = [x.split(":")[1].strip() for x in out.splitlines() if x.startswith("PAGE:")]
dk = [x.split(":")[1].strip() for x in out.splitlines() if x.startswith("DLYKNOB:")]
pk = [x.split(":")[1].strip() for x in out.splitlines() if x.startswith("PK:")]
print(f"pages {pages}   DELAY knobs {dk}   stored {pk}")
ok &= pages == ["1", "6", "2", "3", "4", "5", "0"] and "1 0.7" in dk and "3 0.4" in dk and pk == ["0.7 0.4"]
# 7) old project
T = tmp()
src = open(os.path.join(HERE, "gen.py")).read()
init = src.split("pkval 0 ")[1].split(" " + BS + BS + ";")[0].split()
open(f"{T}/p5-pk.txt", "w").write("\n".join(init[:191] + ["0.9"]) + "\n")


def extra2(add, C):
    a = add("#X obj 600 50 r chk;"); e = add("#X obj 600 80 expr pkval[192] \\; pkval[193] \\; pkval[194] \\; pkval[195];")
    p = add("#X obj 600 110 pack f f f f;"); r = add("#X obj 600 140 print DLY;")
    C += [f"#X connect {a} 0 {e} 0;"] + [f"#X connect {e} {i} {p} {i};" for i in range(4)] + [f"#X connect {p} 0 {r} 0;"]


out = patch(T, [(800, ["pm-load 5"]), (2000, ["chk bang"]), (2200, ["pd quit"])], extra2)
shutil.rmtree(T)
d = [x.split(":")[1].strip() for x in out.splitlines() if x.startswith("DLY:")]
print(f"old project -> DELAY slots {d}")
ok &= d == ["0.545 0 0 0"]
print("OK" if ok else "FAIL")

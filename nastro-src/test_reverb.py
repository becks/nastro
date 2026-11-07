#!/usr/bin/env python3
"""Reverb test: 10 ms noise burst into the synth bus with only the reverb send up (delay off).
Measures the decay (RT60 from the -5..-35 dB slope) for two DECAY settings, the left/right correlation of the tail,
the ripple of the tail envelope (metallic ringing shows as big ripple), and the auto switch-off (output silent
after the send goes to 0 and the tail ends)."""
import os, shutil, subprocess, wave, struct, tempfile, math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
events = [
    (700, ["fx-dmix 0", "fx-rmix 1", "rvb-set 1 0.5"]),
    (1000, ["burst bang", "recA bang"]),
    (6000, ["rvb-set 1 0.2"]),
    (6500, ["burst bang", "recB bang"]),
    (9000, ["fx-rmix 0"]),
    (12500, ["burst bang", "recC bang"]),           # send is 0 and reverb switched off: must be silent
    (13500, ["fx-rmix 1"]),
    (13600, ["burst bang", "recD bang"]),           # back on
    (15000, ["dump bang"]),
    (15200, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2


def add(t):
    global n
    L.append(t); n += 1
    return n - 1


nz = add("#X obj 600 20 noise~;"); env = add("#X obj 700 20 vline~;"); mul = add("#X obj 600 50 *~;")
rb = add("#X obj 700 -10 r burst;"); bm = add("#X msg 700 5 0.3 \\, 0 0 10;")
th = add("#X obj 600 80 throw~ fxr-tape;")             # the reverb is fed by the track sends only
C += [f"#X connect {nz} 0 {mul} 0;", f"#X connect {env} 0 {mul} 1;", f"#X connect {mul} 0 {th} 0;",
      f"#X connect {rb} 0 {bm} 0;", f"#X connect {bm} 0 {env} 0;"]
cL = add("#X obj 900 20 catch~ outL;"); cR = add("#X obj 1000 20 catch~ outR;")
sf = add("#X obj 900 400 soundfiler;"); rd = add("#X obj 900 300 r dump;")
dump = []
for k, nm in enumerate("ABCD"):
    dur = 4.5 if nm in "A" else (2.4 if nm == "B" else 0.9)
    for ch, cc in (("L", cL), ("R", cR)):
        add(f"#X obj {1100 + k * 150} {20 + (ch == 'R') * 200} table cap{nm}{ch} {int(dur * SR)};")
        tw = add(f"#X obj {1100 + k * 150} {60 + (ch == 'R') * 200} tabwrite~ cap{nm}{ch};")
        C.append(f"#X connect {cc} 0 {tw} 0;")
        rr = add(f"#X obj {1100 + k * 150} {40 + (ch == 'R') * 200} r rec{nm};")
        C.append(f"#X connect {rr} 0 {tw} 0;")
        dump.append(f"write -wave -bytes 4 {T}/{nm}{ch}.wav cap{nm}{ch}")
dm = add("#X msg 900 330 " + " \\, ".join(dump) + ";")
C += [f"#X connect {rd} 0 {dm} 0;", f"#X connect {dm} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
for line in out.splitlines():
    if "error" in line and not any(k in line for k in ("oscOut", "led:", "can't open", "No such", "enableSub", "screenLine", "fm-knob", "receive~")):
        print(line)


def rd_(p):
    # 32-bit float wav: parse the data chunk by hand (python's wave module refuses float)
    b = open(p, "rb").read()
    i = b.index(b"data") + 8
    return list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))


def rt60(x):
    w = int(0.02 * SR)
    e = [10 * math.log10(sum(v * v for v in x[i:i + w]) / w + 1e-20) for i in range(0, len(x) - w, w)]
    pk = max(range(len(e)), key=lambda i: e[i])
    ref = e[pk]
    t5 = next((i for i in range(pk, len(e)) if e[i] < ref - 5), None)
    t35 = next((i for i in range(pk, len(e)) if e[i] < ref - 35), None)
    if t5 is None or t35 is None:
        return None, e
    return (t35 - t5) * 0.02 * 2, e


for nm, expect in (("A", 2.2), ("B", 0.4 * 30 ** 0.2)):
    l, r = rd_(f"{T}/{nm}L.wav"), rd_(f"{T}/{nm}R.wav")
    l, r = l[int(0.025 * SR):], r[int(0.025 * SR):]          # skip the dry burst
    t, e = rt60(l)
    # correlation of the tail 100..600 ms
    a, b = l[int(0.1 * SR):int(0.6 * SR)], r[int(0.1 * SR):int(0.6 * SR)]
    corr = sum(p * q for p, q in zip(a, b)) / math.sqrt(sum(p * p for p in a) * sum(q * q for q in b) + 1e-20)
    # ripple: deviation of the 20 ms energy from a straight-line fit (dB) over the -5..-30 dB part
    pk = max(range(len(e)), key=lambda i: e[i])
    seg = [(i, v) for i, v in enumerate(e) if i > pk and e[pk] - 30 < v < e[pk] - 5]
    if len(seg) > 3:
        n_ = len(seg); sx = sum(i for i, _ in seg); sy = sum(v for _, v in seg)
        sxx = sum(i * i for i, _ in seg); sxy = sum(i * v for i, v in seg)
        k = (n_ * sxy - sx * sy) / (n_ * sxx - sx * sx); c = (sy - k * sx) / n_
        rip = max(abs(v - (k * i + c)) for i, v in seg)
    else:
        rip = float("nan")
    print(f"DECAY {nm}: RT60 {t if t is None else round(t, 2)} s (expect ~{expect:.1f})  peak {max(map(abs, l)):.3f}  "
          f"L/R corr {corr:+.2f}  envelope ripple {rip:.1f} dB")
c_ = rd_(f"{T}/CL.wav")[int(0.025 * SR):]; d_ = rd_(f"{T}/DL.wav")[int(0.025 * SR):]
print(f"switched off (send 0): peak {max(map(abs, c_)):.5f}   back on: peak {max(map(abs, d_)):.3f}")
shutil.rmtree(T)

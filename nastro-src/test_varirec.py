#!/usr/bin/env python3
"""Tape recording at 0.5x / 2x.
1) no loop: a 440 Hz tone recorded for 1 s at 0.5x and at 2x. On tape (= played back at 1x) it must last 0.5 s /
   2 s and sound at 880 / 220 Hz.
2) loop: a continuous 220 Hz tone recorded over a 1-bar loop for 3.5 passes at 1x (reference), 2x and 0.5x
   (replace). No discontinuities inside the loop (the punch-out fade excluded), nothing written past the end.
3) overdub at 0.5x over a 300 Hz tone already on tape: both tones must be on tape, the old one unchanged in level."""
import os, shutil, subprocess, tempfile, sys, math, struct, wave

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
SR, BS = 44100, "\\"
KNOB = {0.5: 0.62, 1: 0.78, 2: 0.95}          # tape knob 1 positions for the speed steps


def run(ev, frames, prefill=None, extra_print=()):
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(SRC, f), T)
    if prefill:
        w = wave.open(f"{T}/old.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * prefill * i / SR))) for i in range(6 * SR))); w.close()
    end = max(t for t, _ in ev)
    ev = [(400, ["ld bang"])] + ev + [(end + 300, ["dump bang"]), (end + 500, ["pd quit"])]
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
    o = add("#X obj 600 20 osc~ 440;"); fr = add("#X obj 700 20 r frq;"); ra = add("#X obj 800 20 r amp;")
    mu = add("#X obj 600 50 *~ 0;"); th = add("#X obj 600 80 throw~ synth-bus;")
    C += [f"#X connect {fr} 0 {o} 0;", f"#X connect {o} 0 {mu} 0;", f"#X connect {ra} 0 {mu} 1;", f"#X connect {mu} 0 {th} 0;"]
    add("#X obj 800 120 catch~ outL;"); add("#X obj 900 120 catch~ outR;")
    sf = add("#X obj 700 600 soundfiler;"); rl = add("#X obj 700 250 r ld;")
    ml = add(f"#X msg 700 270 read {T}/old.wav tape1;" if prefill else "#X msg 700 270 tape1 const 0;")
    rd = add("#X obj 700 300 r dump;")
    md = add(f"#X msg 700 330 write -wave -bytes 4 -nframes {frames} {T}/t1.wav tape1;")
    C += [f"#X connect {rl} 0 {ml} 0;", f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
    if prefill:
        C.append(f"#X connect {ml} 0 {sf} 0;")
    for nm in extra_print:
        r = add(f"#X obj 1000 20 r {nm};"); pr = add(f"#X obj 1000 50 print {nm};")
        C.append(f"#X connect {r} 0 {pr} 0;")
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                          "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
    b = open(f"{T}/t1.wav", "rb").read(); i = b.index(b"data") + 8
    x = list(struct.unpack("<%df" % ((len(b) - i) // 4), b[i:i + ((len(b) - i) // 4) * 4]))
    shutil.rmtree(T)
    errs = [l for l in out.splitlines() if ("error" in l or "bad" in l) and not any(
        k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
    prints = [l for l in out.splitlines() if any(l.startswith(nm + ":") for nm in extra_print)]
    return x, errs, prints


def freq(seg):
    zc = [k for k in range(1, len(seg)) if seg[k - 1] < 0 <= seg[k]]
    return SR * (len(zc) - 1) / (zc[-1] - zc[0]) if len(zc) > 2 else 0


bad = 0
# 1) length and pitch
for spd, exp_len, exp_f in ((0.5, 0.5, 880), (2, 2.0, 220)):
    ev = [(600, ["mode 2", f"tape-knob 1 {KNOB[spd]}", "tape-knob 3 1", "frq 440", "amp 0.4"]),
          (800, ["aux-key 66"]), (1800, ["aux-key 66", "amp 0"]), (2000, ["aux-key 65"])]
    x, errs, pr = run(ev, 4 * SR, extra_print=("tp-recf",))
    nz = [k for k in range(len(x)) if abs(x[k]) > 0.05]
    ln = (nz[-1] - nz[0]) / SR if nz else 0
    f = freq(x[nz[0] + 2000:nz[-1] - 2000]) if nz else 0
    ok = abs(ln - exp_len) < 0.03 and abs(f - exp_f) < exp_f * 0.01
    bad += not ok
    print(f"rec {spd}x: on tape {ln:.3f} s (expect {exp_len})  {f:.1f} Hz at 1x (expect {exp_f})  factor {pr[:1]}  "
          f"{'OK' if ok else 'FAIL'}  {errs[:3]}")

# 2) loop seam at 2x and 0.5x (replace, continuous 220 Hz)
B = 88320
for spd in (1, 2, 0.5):
    pas = B / SR / spd * 1000                       # ms per loop pass at this speed
    ev = [(600, ["mode 2", f"tp-loop-set 2 0 {B}", f"tape-knob 1 {KNOB[spd]}", "tape-knob 3 0", "frq 220", "amp 0.4"]),
          (800, ["aux-key 66"]), (800 + int(3.5 * pas), ["aux-key 66"]), (800 + int(3.5 * pas) + 50, ["amp 0", "aux-key 65"])]
    x, errs, _ = run(ev, B + 400)
    amp = max(map(abs, x[:B]))
    f_tape = 220 / spd
    clean = amp * (2 * math.pi * f_tape / SR) ** 2
    d2 = [abs(x[k + 1] - 2 * x[k] + x[k - 1]) for k in range(1, B - 1)]
    # the punch-out (rec stopped half way through the loop) fades between two passes of different phase: skip it
    disc = [k for k in range(1, B - 1) if d2[k - 1] > 4 * clean and not 43500 < k < 45500]
    past = max(map(abs, x[B:B + 300]))
    ok = not disc and past < 1e-6 and amp > 0.3
    bad += not ok
    print(f"loop {spd}x: tape amp {amp:.3f}, discontinuities {len(disc)} {disc[:4]}, past the end {past:.4f}  "
          f"{'OK' if ok else 'FAIL'}  {errs[:3]}")

# 3) overdub at 0.5x over a 300 Hz tone
ev = [(600, ["mode 2", f"tape-knob 1 {KNOB[0.5]}", "tape-knob 3 1", "frq 500", "amp 0.3"]),
      (800, ["aux-key 66"]), (1800, ["aux-key 66", "amp 0"]), (2000, ["aux-key 65"])]
x, errs, _ = run(ev, 3 * SR, prefill=300)
seg = x[int(0.1 * SR):int(0.4 * SR)]                 # inside the overdubbed part (0.5 s of tape)
# project onto the old tone (300 Hz) and the new one (500 Hz at 0.5x -> 1000 Hz on tape)
def comp(sig, f):
    c = sum(v * math.cos(2 * math.pi * f * k / SR) for k, v in enumerate(sig)); s_ = sum(v * math.sin(2 * math.pi * f * k / SR) for k, v in enumerate(sig))
    return 2 * math.hypot(c, s_) / len(sig)
old_a, new_a = comp(seg, 300), comp(seg, 1000)
ok = abs(old_a - 9000 / 32768) < 0.02 and abs(new_a - 0.3) < 0.03
bad += not ok
print(f"overdub 0.5x: old 300 Hz amp {old_a:.3f} (expect {9000 / 32768:.3f}), new 1000 Hz amp {new_a:.3f} (expect 0.3)  "
      f"{'OK' if ok else 'FAIL'}  {errs[:3]}")
print("ALL OK" if not bad else f"{bad} FAILED")

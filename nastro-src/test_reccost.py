#!/usr/bin/env python3
"""DSP/control cost while recording (the user's case): track 1 holds audio, the step sequencer plays FM notes,
speed 0.5, record on track 2. Per-block wall time (bang~ + realtime, batch mode) for: play only, record at 0.5x,
record at 1x. (Mac timings: the Organelle is roughly 10-20x slower; compare the cases, not the absolute ms.)"""
import os, shutil, subprocess, tempfile, sys, math, wave, struct

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
SR, BS = 44100, "\\"
KN = {0.5: 0.72, 1: 0.83}


def run(rec, spd):
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav":
            shutil.copy(os.path.join(SRC, f), T)
    w = wave.open(f"{T}/s.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(0.3 * math.sin(2 * math.pi * 220 * i / SR) * 32767)) for i in range(20 * SR)))
    w.close()
    ev = [(400, ["ld bang"]), (600, ["mode 4", "mode 4"])]
    t = 700
    for nt in (60, 64, 67, 72, 67, 64, 62, 65):
        ev.append((t, [f"notes {nt} 100", f"notes {nt} 0"])); t += 30
    ev += [(1100, ["mode 2", f"tape-knob 1 {KN[spd]}", "tape-knob 2 0.3", "aux 1", "aux-key 72", "aux 0"])]   # track 2, start seq + tape
    if rec:
        ev.append((1600, ["aux-key 66"]))
    ev += [(11600, ["pd quit"])]
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
    sf = add("#X obj 700 600 soundfiler;"); r_ = add("#X obj 700 300 r ld;")
    m_ = add(f"#X msg 700 330 read {T}/s.wav tape1;")
    C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
    b = add("#X obj 900 20 bang~;"); tb = add("#X obj 900 50 t b b;"); rt = add("#X obj 900 80 realtime;")
    tm = add("#X obj 1000 80 timer;"); pk = add("#X obj 900 140 pack f f;"); pr = add("#X obj 900 170 print BLK;")
    lb = add("#X obj 1000 20 loadbang;")
    sn = add("#X obj 1100 20 r seq-notes;"); sp = add("#X obj 1100 50 print SEQ;")
    C += [f"#X connect {b} 0 {tb} 0;", f"#X connect {tb} 0 {rt} 0;", f"#X connect {tb} 1 {rt} 1;",
          f"#X connect {rt} 0 {pk} 0;", f"#X connect {lb} 0 {tm} 0;", f"#X connect {tb} 1 {tm} 1;",
          f"#X connect {tm} 0 {pk} 1;", f"#X connect {pk} 0 {pr} 0;", f"#X connect {sn} 0 {sp} 0;"]
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                          "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
    shutil.rmtree(T)
    blk = sorted(float(l.split()[1]) for l in out.splitlines() if l.startswith("BLK:") and float(l.split()[2]) > 2000)
    seq = sum(1 for l in out.splitlines() if l.startswith("SEQ:"))
    return blk, seq


for name, rec, spd in (("play 0.5x, no rec", False, 0.5), ("record at 0.5x", True, 0.5), ("record at 1x", True, 1)):
    best = None
    for _ in range(3):                                   # best of 3 runs: less noise from the Mac
        blk, seq = run(rec, spd)
        stat = (sum(blk) / len(blk), blk[int(len(blk) * 0.99)], blk[-1])
        best = stat if best is None or stat[0] < best[0] else best
    print(f"{name:18s} block avg {best[0]*1000:6.1f} us   p99 {best[1]*1000:6.1f} us   max {best[2]*1000:7.1f} us   (seq notes {seq})")

#!/usr/bin/env python3
"""Headless test of tape editing: copy/paste, reverse, cut, clear, duplicate - compared sample by sample."""
import os, shutil, subprocess, wave, struct, math, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 88320          # one bar at 120 BPM
# test content for loop 1: 440 Hz with a rising envelope (so 'reversed' is recognisable)
src = [0.6 * math.sin(2 * math.pi * 440 * i / SR) * (i / B) for i in range(B)]
w = wave.open(f"{T}/src.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in src)); w.close()
BS = "\\"
L = lambda a, b: f"tp-loop-set 2 {a} {b}"
events = [
    (600, ["dbg LOAD", "ldsrc bang", L(0, B)]),
    (700, ["dbg COPY-L1", "tape-edit 2"]),
    (900, [L(B, 2 * B), "dbg PASTE-L2", "tape-edit 3"]),
    (1100, ["dump1 bang"]),
    (1200, ["dbg REVERSE-L2", "tape-edit 4"]),
    (3600, ["dump2 bang"]),
    (3700, [L(0, B), "dbg CUT-L1", "tape-edit 1"]),
    (3900, [L(2 * B, 3 * B), "dbg PASTE-L3", "tape-edit 3"]),
    (4100, ["dump3 bang"]),
    (4200, ["dbg CLEAR-L3", "tape-edit 5"]),
    (4400, ["dump4 bang"]),
    (4500, [L(B, 2 * B), "dbg DUP-L2 (via the menu)", "mode 2", "enc 1", "enc 1", "enc 1", "enc 1", "enc 1", "enc 1", "encbut 1", "encbut 0"]),
    (4800, ["dump5 bang"]),
    (4900, ["dbg UNDO-DUP", "tape-edit 7"]),
    (5100, ["dump6 bang"]),
    (5200, ["dbg REDO-DUP", "tape-edit 7"]),
    (5400, ["dump7 bang"]),
    (5500, [L(B, 2 * B), "dbg CLEAR-L2", "tape-edit 5"]),
    (5700, ["dbg UNDO-CLEAR", "tape-edit 7"]),
    (5900, ["dump8 bang"]),
    (6000, ["dbg REVERSE-L2", "tape-edit 4"]),
    (8400, ["dbg UNDO-REVERSE", "tape-edit 7"]),
    (8600, ["dump9 bang"]),
    (8700, [L(0, B), "dbg COPY-L1", "tape-edit 2", "dbg UNDO-AFTER-REC-EXPECT-NOTHING"]),
    (8900, ["tp-rec 1", "tp-rec 0", "tape-edit 7"]),
    (9100, ["pd quit"]),
]
Lp = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    Lp.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    Lp.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "nst-proj-status", "tp-lo"):
    Lp.append(f"#X obj 400 {80 + n * 10} r {name};"); Lp.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
sf = n; Lp.append("#X obj 700 600 soundfiler;"); n += 1
r_ = n; Lp.append("#X obj 700 300 r ldsrc;"); n += 1
m_ = n; Lp.append(f"#X msg 700 330 read {T}/src.wav tape1;"); n += 1
C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
for k in range(1, 10):
    r_ = n; Lp.append(f"#X obj 900 {300 + k * 40} r dump{k};"); n += 1
    m_ = n; Lp.append(f"#X msg 900 {320 + k * 40} write -wave -bytes 2 -nframes {4 * B} {T}/d{k}.wav tape1;"); n += 1
    C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
open(f"{T}/he.pd", "w").write("\n".join(Lp + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/he.pd"],
                     capture_output=True, text=True).stderr
show = False
for line in out.splitlines():
    if line.startswith("dbg:"):
        show = True
    if show and not any(k in line for k in ("no such object", "receive~", "Find menu", "tape-saved", "biggest amplitude")):
        print(line)


def rd(k):
    w = wave.open(f"{T}/d{k}.wav"); d = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]


q = lambda x: [round(v * 32767) / 32768 for v in x]
src_q = q(src)
reg = lambda x, i: x[i * B:(i + 1) * B]
dif = lambda a, b: max(abs(p - q_) for p, q_ in zip(a, b))
silent = lambda a: max(map(abs, a)) < 1e-4
d1, d2, d3, d4, d5, d6, d7, d8, d9 = (rd(k) for k in range(1, 10))
print("COPY+PASTE : loop 2 == loop 1 ->", dif(reg(d1, 1), reg(d1, 0)) < 1e-3, " loop 1 kept ->", dif(reg(d1, 0), src_q) < 1e-3)
print("REVERSE    : loop 2 == loop 1 reversed ->", dif(reg(d2, 1), src_q[::-1]) < 2e-3, f"(max diff {dif(reg(d2, 1), src_q[::-1]):.5f})")
print("CUT        : loop 1 silent ->", silent(reg(d3, 0)), " PASTE into loop 3 == original ->", dif(reg(d3, 2), src_q) < 1e-3)
print("CLEAR      : loop 3 silent ->", silent(reg(d4, 2)), " loop 2 untouched ->", dif(reg(d4, 1), reg(d3, 1)) < 1e-6)
print("DUPLICATE  : loop 3 == loop 2 ->", dif(reg(d5, 2), reg(d5, 1)) < 1e-6, " loop 2 untouched ->", dif(reg(d5, 1), reg(d4, 1)) < 1e-6)
print("UNDO DUP   : == before dup ->", dif(d6, d4) < 1e-6, "   REDO: == after dup ->", dif(d7, d5) < 1e-6)
print("UNDO CLEAR : loop 2 back ->", dif(reg(d8, 1), reg(d7, 1)) < 1e-6, " whole tape same ->", dif(d8, d7) < 1e-6)
print("UNDO REV   : whole tape == before reverse ->", dif(d9, d8) < 1e-6)
shutil.rmtree(T)

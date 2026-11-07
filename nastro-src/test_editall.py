#!/usr/bin/env python3
"""All-tracks tape editing test: 4 different tones on tracks 1..4 (loop 1), mode TUTTE (op 8), then
COPY loop 1 -> PASTE on loop 2 (each track gets its own), UNDO (loop 2 silent again on all), DUPLICATE loop 1
(-> loop 2 on all, loop moves once), CLEAR loop 1 on all, UNDO. Sample by sample."""
import os, shutil, subprocess, wave, struct, math, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, B = 44100, 88320
FREQS = [220, 330, 440, 550]
for k, fq in enumerate(FREQS):
    w = wave.open(f"{T}/s{k + 1}.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(0.5 * math.sin(2 * math.pi * fq * i / SR) * 32767)) for i in range(B)))
    w.close()
BS = "\\"
L = lambda a, b: f"tp-loop-set 2 {a} {b}"
events = [
    (600, ["ld bang", L(0, B)]),
    (700, ["dbg MODE-ALL", "tape-edit 8"]),
    (750, ["dbg COPY-ALL", "tape-edit 2"]),
    (1100, [L(B, 2 * B), "dbg PASTE-ALL", "tape-edit 3"]),
    (1600, ["dump1 bang"]),
    (1700, ["dbg UNDO-ALL", "tape-edit 7"]),
    (2300, ["dump2 bang"]),
    (2400, [L(0, B), "dbg DUP-ALL", "tape-edit 6"]),
    (3000, ["dump3 bang"]),
    (3100, [L(0, B), "dbg CLEAR-ALL", "tape-edit 5"]),
    (3600, ["dump4 bang"]),
    (3700, ["dbg UNDO-CLEAR", "tape-edit 7"]),
    (4300, ["dump5 bang"]),
    (4400, ["pd quit"]),
]
Lp = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    Lp.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    Lp.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for nm in ("dbg", "nst-proj-status", "tp-lo", "te-all"):
    Lp.append(f"#X obj 400 {80 + n * 10} r {nm};"); Lp.append(f"#X obj 400 {100 + n * 10} print {nm};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
sf = n; Lp.append("#X obj 700 600 soundfiler;"); n += 1
r_ = n; Lp.append("#X obj 700 300 r ld;"); n += 1
m_ = n; Lp.append("#X msg 700 330 " + " \\, ".join(f"read {T}/s{k}.wav tape{k}" for k in range(1, 5)) + ";"); n += 1
C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
for d in range(1, 6):
    r_ = n; Lp.append(f"#X obj 900 {300 + d * 40} r dump{d};"); n += 1
    m_ = n; Lp.append(f"#X msg 900 {320 + d * 40} " + " \\, ".join(
        f"write -wave -bytes 2 -nframes {3 * B} {T}/d{d}t{k}.wav tape{k}" for k in range(1, 5)) + ";"); n += 1
    C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {sf} 0;"]
open(f"{T}/he.pd", "w").write("\n".join(Lp + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/he.pd"], capture_output=True, text=True).stderr
show = False
for line in out.splitlines():
    if line.startswith("dbg:"):
        show = True
    if show and line.split(":")[0] in ("dbg", "nst-proj-status", "tp-lo", "te-all"):
        print("  ", line)


def rd(d, k):
    w = wave.open(f"{T}/d{d}t{k}.wav"); x = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack("<%dh" % (len(x) // 2), x)]


reg = lambda x, i: x[i * B:(i + 1) * B]
dif = lambda a, b: max(abs(p - q) for p, q in zip(a, b))
silent = lambda a: max(map(abs, a)) < 1e-4
D = {d: {k: rd(d, k) for k in range(1, 5)} for d in range(1, 6)}
print("PASTE-ALL : loop2 == own loop1 on every track ->", [dif(reg(D[1][k], 1), reg(D[1][k], 0)) < 1e-4 for k in range(1, 5)])
print("UNDO      : loop2 silent again on every track ->", [silent(reg(D[2][k], 1)) for k in range(1, 5)])
print("DUP-ALL   : loop2 == own loop1 on every track ->", [dif(reg(D[3][k], 1), reg(D[3][k], 0)) < 1e-4 for k in range(1, 5)])
print("CLEAR-ALL : loop1 silent on every track ->", [silent(reg(D[4][k], 0)) for k in range(1, 5)])
print("UNDO      : loop1 back on every track ->", [dif(reg(D[5][k], 0), reg(D[3][k], 0)) < 1e-4 for k in range(1, 5)])
shutil.rmtree(T)

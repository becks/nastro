#!/usr/bin/env python3
"""Headless test of sampling into a DRUM key, slot isolation, playback pitch, per-project kit, SMPL still works."""
import os, shutil, subprocess, wave, struct, math, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
SL = 22050
events = [
    (500, A(61) + ["notes 65 100", "notes 65 0"]),            # DRUM, select key 6 (slot 5)
    (700, ["dbg REC-DRUM-INPUT"] + A(76)), (1000, A(76)),     # record ~0.3 s, stop early
    (1300, ["dbg PLAY-KEY6", "notes 65 100"]), (1700, ["notes 65 0"]),
    (1900, ["dbg DUMP", "dumpdrums bang"]),
    (2000, ["dbg SAVE-P1", "pm-save 1"]),
    (2400, ["dbg LOAD-P2-EMPTY", "pm-load 2"]), (2600, ["dbg DUMP2", "dumpdrums2 bang"]),
    (2800, ["dbg LOAD-P1", "pm-load 1"]), (3000, ["dbg DUMP3", "dumpdrums3 bang"]),
    (3200, ["dbg SMPL-STILL-WORKS"] + A(60) + A(76)), (3500, A(76)),
    (3800, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "smp-recording", "nst-proj-status"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
for i, nm in enumerate(("dumpdrums", "dumpdrums2", "dumpdrums3")):
    L.append(f"#X obj 700 {300 + i * 60} r {nm};"); r_ = n; n += 1
    L.append(f"#X msg 700 {330 + i * 60} write -wave -bytes 2 {T}/{nm}.wav drums;"); m_ = n; n += 1
    L.append(f"#X obj 900 {330 + i * 60} soundfiler;"); s_ = n; n += 1
    C += [f"#X connect {r_} 0 {m_} 0;", f"#X connect {m_} 0 {s_} 0;"]
L.append("#X obj 600 300 osc~ 440;"); o = n; n += 1
L.append("#X obj 600 330 *~ 0.5;"); g = n; n += 1
L.append("#X obj 600 360 s~ inL;"); sl = n; n += 1
L.append("#X obj 700 360 s~ inR;"); sr = n; n += 1
C += [f"#X connect {o} 0 {g} 0;", f"#X connect {g} 0 {sl} 0;", f"#X connect {g} 0 {sr} 0;"]
L.append("#X obj 600 20 catch~ outL;"); cl = n; n += 1
L.append("#X obj 700 20 catch~ outR;"); n += 1
L.append("#X obj 600 200 writesf~ 1;"); ws = n; n += 1
L.append("#X obj 600 100 delay 1;"); dl = n; n += 1
L.append(f"#X msg 600 130 open {T}/cap.wav " + BS + ", start;"); om = n; n += 1
L.append("#X obj 700 100 delay 3700;"); d2 = n; n += 1
L.append("#X msg 700 130 stop;"); sm = n; n += 1
C += [f"#X connect {cl} 0 {ws} 0;", f"#X connect 0 0 {dl} 0;", f"#X connect {dl} 0 {om} 0;", f"#X connect {om} 0 {ws} 0;",
      f"#X connect 0 0 {d2} 0;", f"#X connect {d2} 0 {sm} 0;", f"#X connect {sm} 0 {ws} 0;"]
L.append("#X obj 400 600 r drum-recording;"); dr = n; n += 1
L.append("#X obj 400 630 t f b;"); dt = n; n += 1
L.append("#X obj 500 660 timer;"); tmo = n; n += 1
L.append("#X obj 400 690 pack f f;"); pp = n; n += 1
L.append("#X obj 400 720 print drum-recording(value-ms);"); pq = n; n += 1
C += [f"#X connect {dr} 0 {dt} 0;", f"#X connect {dt} 1 {tmo} 1;", f"#X connect 0 0 {tmo} 0;", f"#X connect {tmo} 0 {pp} 1;",
      f"#X connect {dt} 0 {pp} 0;", f"#X connect {pp} 0 {pq} 0;"]
open(f"{T}/hd.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hd.pd"],
                     capture_output=True, text=True).stderr
show = False
for line in out.splitlines():
    if line.startswith("dbg:"):
        show = True
    if show and not any(k in line for k in ("no such object", "receive~", "Find menu", "tape-saved", "biggest amplitude",
                                             "p2-", "can't open")):
        print(line)


def readf(path):
    w = wave.open(path); d = w.readframes(w.getnframes())
    if w.getsampwidth() == 4:
        return [v / 2147483648 for v in struct.unpack("<%di" % (len(d) // 4), d)]
    return [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]


orig = readf(f"{T}/drums.wav")
k1 = readf(f"{T}/dumpdrums.wav")
slot = lambda x, i: x[i * SL:(i + 1) * SL]
diff = lambda a, b: max(abs(p - q) for p, q in zip(a, b))
s5 = slot(k1, 5)
nz = [i for i, v in enumerate(s5) if abs(v) > 0.01]
print(f"slot 6 after recording: sound from {nz[0] if nz else None} to {nz[-1] if nz else None} "
      f"({(nz[-1] + 1) / 44100:.2f} s), rest silent: {max(map(abs, s5[nz[-1] + 100:])) if nz else '-'}")
print("slot 5 unchanged:", diff(slot(orig, 4), slot(k1, 4)) < 1e-3, " slot 7 unchanged:", diff(slot(orig, 6), slot(k1, 6)) < 1e-3)
k2 = readf(f"{T}/dumpdrums2.wav"); k3 = readf(f"{T}/dumpdrums3.wav")
print("empty project 2 -> base kit in slot 6:", diff(slot(orig, 5), slot(k2, 5)) < 1e-3)
print("reload project 1 -> recorded sound back:", diff(slot(k1, 5), slot(k3, 5)) < 2e-3)
cap = readf(f"{T}/cap.wav")
x = cap[int(1.35 * 44100):int(1.5 * 44100)]
zc = sum(1 for i in range(1, len(x)) if x[i - 1] < 0 <= x[i]) / 0.15
print(f"playing key 6: ~{zc:.0f} Hz (expect 440), peak {max(map(abs, x)):.3f}")
shutil.rmtree(T)

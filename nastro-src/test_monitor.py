#!/usr/bin/env python3
"""Headless test of the input monitor: off / toggle on / off / auto while sampling / recording the input on tape."""
import os, shutil, subprocess, wave, struct, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
events = [
    (1000, ["dbg MON-ON"] + A(78)), (2000, ["dbg MON-OFF"] + A(78)),
    (3000, ["dbg SAMPLING"] + A(76)), (4000, A(76)),
    (5000, ["dbg TAPE-REC-INPUT"] + A(78) + A(62) + A(66)), (6000, A(66) + A(78)),
    (6200, A(69)), (6500, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "smp-monitor"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
L.append("#X obj 600 300 osc~ 330;"); o = n; n += 1
L.append("#X obj 600 330 *~ 0.5;"); g = n; n += 1
L.append("#X obj 600 360 s~ inL;"); sl = n; n += 1
L.append("#X obj 700 360 s~ inR;"); sr = n; n += 1
C += [f"#X connect {o} 0 {g} 0;", f"#X connect {g} 0 {sl} 0;", f"#X connect {g} 0 {sr} 0;"]
L.append("#X obj 600 20 catch~ outL;"); cl = n; n += 1
L.append("#X obj 700 20 catch~ outR;"); n += 1
L.append("#X obj 600 200 writesf~ 1;"); ws = n; n += 1
L.append("#X obj 600 100 delay 1;"); dl = n; n += 1
L.append(f"#X msg 600 130 open {T}/cap.wav " + BS + ", start;"); om = n; n += 1
L.append("#X obj 700 100 delay 6400;"); d2 = n; n += 1
L.append("#X msg 700 130 stop;"); sm = n; n += 1
C += [f"#X connect {cl} 0 {ws} 0;", f"#X connect 0 0 {dl} 0;", f"#X connect {dl} 0 {om} 0;", f"#X connect {om} 0 {ws} 0;",
      f"#X connect 0 0 {d2} 0;", f"#X connect {d2} 0 {sm} 0;", f"#X connect {sm} 0 {ws} 0;"]
open(f"{T}/hm.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio",
                      "-nomidi", "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/hm.pd"],
                     capture_output=True, text=True).stderr
for line in out.splitlines():
    if any(k in line for k in ("no such object", "tape-", "soundfiler read", "seq-", "smpl.wav")):
        continue
    print(line)
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
s = [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]
pk = lambda a, b: round(max(abs(v) for v in s[int(a * 44100):int(b * 44100)]), 3)
print("output level  before monitor:", pk(0.5, 0.9), " monitor on:", pk(1.3, 1.9), " monitor off:", pk(2.3, 2.9),
      " while sampling input:", pk(3.3, 3.9), " after sampling:", pk(4.3, 4.9))
w = wave.open(f"{T}/tape-1.wav"); d = w.readframes(w.getnframes())
t1 = struct.unpack("<%dh" % (len(d) // 2), d)
nz = [i for i, v in enumerate(t1) if abs(v) > 1000]
print("input recorded on tape track 1:", f"{len(nz)} loud samples, from {nz[0]} to {nz[-1]}" if nz else "nothing")
shutil.rmtree(T)

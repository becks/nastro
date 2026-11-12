#!/usr/bin/env python3
"""Album viewer. Album 1: 2 s, a 440 Hz tone on tape track 1 for the first second only -> album-1.txt has 42 bars
(first half full, second half empty) and length 2.0. Menu: encoder -> ALBUMS > -> album 1 under the cursor -> press:
plays from the file (the tape stays stopped), AUX + D#5 jumps forward, press again stops. A second album (1 s)
appears first in the list."""
import os, shutil, subprocess, struct, math, tempfile, sys, wave

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / SR)) if i < SR else 0)
                       for i in range(3 * SR))); w.close()
PRESS = ["encbut 1", "encbut 0"]
ev = [(400, ["sfread read t1.wav tape1", "tp-loaded bang"]),
      (800, ["aux-key 81"]), (2800, ["aux-key 81"]),                       # album 1: 2 s
      (3200, ["mark menu", "enc 1", "enc 1", "enc 1", "enc 1"]),                    # open the menu, go to ALBUMS
      (3400, ["mark albums"] + PRESS),
      (3700, ["mark play", "recP bang"] + PRESS),                          # album 1 under the cursor: play
      (4400, ["mark skip", "aux-key 75"]),                                 # +5 s: clipped to the end - 1 s
      (4700, ["mark stop"] + PRESS),
      (5000, ["mark rec2", "mode 0", "aux-key 81"]), (6000, ["aux-key 81"]),
      (6300, ["mark menu2", "enc 1", "enc 1", "enc 1", "enc 1"]), (6500, PRESS),
      (6800, ["mark list2", "chkmenu bang"]), (7000, ["pd quit"])]
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


sf = add("#X obj 600 400 soundfiler;"); rr = add("#X obj 600 370 r sfread;"); C.append(f"#X connect {rr} 0 {sf} 0;")
for rcv in ("mark", "tp-play", "alb-play", "pm-ctx", "pm-sel"):
    a = add(f"#X obj 800 {20 + n} r {rcv};"); b = add(f"#X obj 800 {40 + n} print {rcv};"); C.append(f"#X connect {a} 0 {b} 0;")
cl = add("#X obj 900 20 catch~ outL;"); add("#X obj 1000 20 catch~ outR;")
add(f"#X obj 1100 120 table capP {int(1.2 * SR)};")
tw = add("#X obj 1100 90 tabwrite~ capP;"); rp = add("#X obj 1100 60 r recP;")
C += [f"#X connect {cl} 0 {tw} 0;", f"#X connect {rp} 0 {tw} 0;"]
dmp = add("#X obj 1300 20 delay 6900;"); dm = add(f"#X msg 1300 50 write -wave -bytes 4 {T}/P.wav capP;"); sf2 = add("#X obj 1300 80 soundfiler;")
C += [f"#X connect 0 0 {dmp} 0;", f"#X connect {dmp} 0 {dm} 0;", f"#X connect {dm} 0 {sf2} 0;"]
cm = add("#X obj 1500 20 r chkmenu;"); cg = add("#X msg 1500 50 1;"); ct = add("#X obj 1500 80 text get nst-menu;"); cp = add("#X obj 1500 110 print ROW1;")
C += [f"#X connect {cm} 0 {cg} 0;", f"#X connect {cg} 0 {ct} 0;", f"#X connect {ct} 0 {cp} 0;"]
ow = add("#X obj 1700 20 r oscOut;"); orr = add("#X obj 1700 50 route sendtyped;"); op = add("#X obj 1700 80 print OSC;")
C += [f"#X connect {ow} 0 {orr} 0;", f"#X connect {orr} 0 {op} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if ("error" in l or "out of range" in l) and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
sec, cur = {}, "start"
for l in out.splitlines():
    if l.startswith("mark:"):
        cur = l.split()[-1]
    elif l.startswith(("tp-play:", "alb-play:", "pm-ctx:", "ROW1:")):
        sec.setdefault(cur, []).append(l)
    elif l.startswith("OSC:") and ("ALBUM" in l or "gFillArea" in l or "gLine" in l or "BACK" in l or "PLAY" in l):
        sec.setdefault(cur + "-osc", []).append(l[5:])
for k, v in sec.items():
    if not k.endswith("-osc"):
        print(k, v)
txt = open(f"{T}/album-1.txt").read().split() if os.path.exists(f"{T}/album-1.txt") else []
bars = [float(v) for v in txt[:42]]
print("album-1.txt:", len(txt), "values  length", txt[42:43], " bars first half", [round(b, 2) for b in bars[2:6]],
      " second half", [round(b, 2) for b in bars[30:34]])
ok1 = len(txt) == 44 and abs(float(txt[42]) - 2.0) < 0.15 and min(bars[2:18]) > 0.1 and max(bars[25:40]) < 0.01
x = struct.unpack("<%df" % 0, b"") if False else None
b_ = open(f"{T}/P.wav", "rb").read(); i_ = b_.index(b"data") + 8
y = struct.unpack("<%df" % ((len(b_) - i_) // 4), b_[i_:i_ + ((len(b_) - i_) // 4) * 4])
seg = y[int(0.2 * SR):int(0.6 * SR)]
rms = math.sqrt(sum(v * v for v in seg) / len(seg))
zc = sum(1 for j in range(1, len(seg)) if seg[j - 1] < 0 <= seg[j]) / 0.4
print(f"played from the file: rms {rms:.3f}  {zc:.0f} Hz")
ok2 = rms > 0.05 and abs(zc - 440) < 10
pl = [l.split()[-1] for l in sec.get("play", []) + sec.get("skip", []) + sec.get("stop", []) if l.startswith("alb-play")]
tape = [l.split()[-1] for l in sec.get("play", []) if l.startswith("tp-play")]
ok3 = pl[:1] == ["1"] and pl[-1:] == ["0"] and not tape
row = [l for l in sec.get("list2", []) if l.startswith("ROW1")]
ok4 = row and row[0].endswith("9 2")
osc_play = sec.get("play-osc", [])
print("screen while playing:", osc_play[:3], f"... ({len(osc_play)} draw messages)")
print("play states", pl, " tape during play", tape, " row 1 after the second album", row, " errors", errs[:4])
shutil.rmtree(T)
print("ALL OK" if ok1 and ok2 and ok3 and ok4 and not errs else f"FAIL {ok1} {ok2} {ok3} {ok4}")

#!/usr/bin/env python3
"""Mirror diet (apply_mirrorthrottle.py): VIS page shown for 4 s with SCREEN TO MAC on (to 127.0.0.1, port moved to
9124 in the copy). Checks: the OLED still gets ~10 gFrame/s; the network gets at most ~5 gFrame/s of 1024 bytes,
a gWaveform (the scope) with each gFrame, and the other commands (gFlip ...) still arrive."""
import os, shutil, subprocess, tempfile, sys, socket, threading, time, wave, struct, math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
s = open(f"{T}/mirror.pd").read().replace("connect \\$1 9123", "connect \\$1 9124")
assert "9124" in s
open(f"{T}/mirror.pd", "w").write(s)
open(f"{T}/mirror.txt", "w").write("127.0.0.1;\n")
SR, BS = 44100, "\\"
w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / SR))) for i in range(10 * SR))); w.close()
pkts = []
sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sk.bind(("127.0.0.1", 9124)); sk.settimeout(0.5)
stop = False
def rx():
    while not stop:
        try:
            pkts.append(sk.recv(65536).decode("utf-8", "replace"))
        except socket.timeout:
            pass
th = threading.Thread(target=rx); th.start()
ev = [(200, ["nst-mirror-toggle bang"]), (300, ["sfread read t1.wav tape1", "tp-loaded bang"]), (500, ["aux-key 65", "mode 3"])]
ev += [(600 + 50 * k, ["mode 3"]) for k in range(5)]
ev += [(1500, ["mark VIS"]), (5500, ["mark END"]), (5600, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
L += ["#X obj 600 400 soundfiler;", "#X obj 600 370 r sfread;"]; C.append(f"#X connect {n + 1} 0 {n} 0;"); n += 2
L += ["#X obj 800 20 r oscOut;", "#X obj 800 50 print OSC;", "#X obj 900 20 r mark;", "#X obj 900 50 print MARK;"]
C += [f"#X connect {n} 0 {n + 1} 0;", f"#X connect {n + 2} 0 {n + 3} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
t0 = time.time()
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
stop = True; th.join(); shutil.rmtree(T)
# batch mode runs faster than real time: count per VIS section of the Pd log, and the network share of the same frames
cur, osc = "pre", {"VIS": [0, 0, 0]}
for l in out.splitlines():
    if l.startswith("MARK:"):
        cur = l.split()[-1]
    elif l.startswith("OSC:") and cur == "VIS":
        osc["VIS"][0] += "/oled/gFrame" in l
        osc["VIS"][1] += "/oled/gWaveform" in l
        osc["VIS"][2] += "/oled/gFlip" in l
msgs = [m.replace("\\", "").split() for p in pkts for m in p.split(";") if m.strip()]
nF = [m for m in msgs if len(m) > 1 and m[1] == "/oled/gFrame"]
nW = [m for m in msgs if len(m) > 1 and m[1] == "/oled/gWaveform"]
nFl = [m for m in msgs if len(m) > 1 and m[1] == "/oled/gFlip"]
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
print("OLED in VIS (4 s): gFrame", osc["VIS"][0], "gWaveform", osc["VIS"][1], "gFlip", osc["VIS"][2])
print("network (whole run): gFrame", len(nF), "gWaveform", len(nW), "gFlip", len(nFl), "messages", len(msgs))
print("frame sizes", sorted({len(m) for m in nF}))
print("errors", errs[:5])
ok = osc["VIS"][0] >= 35 and 12 <= len(nF) <= 26 and abs(len(nW) - len(nF)) <= 1 and all(len(m) == 132 for m in nW) and len(nFl) > 0 and all(len(m) == 1028 for m in nF) and not errs
print("PASS" if ok else "FAIL")

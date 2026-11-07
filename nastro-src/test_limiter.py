#!/usr/bin/env python3
"""Limiter test: 440 Hz into the synth bus at 0.5 (must pass untouched), then 2.0 (must be held under 1.0,
settling near 0.89), then 0.5 again (gain must come back to 1 within ~0.5 s)."""
import os, shutil, subprocess, wave, struct, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
P = f"""#N canvas 0 0 800 600 12;
#X obj 20 20 loadbang;
#X msg 20 50 {BS}; pd dsp 1;
#X obj 20 90 delay 700;
#X msg 20 120 {BS}; amp 0.5 {BS}; rec bang;
#X obj 200 90 delay 1700;
#X msg 200 120 {BS}; amp 2;
#X obj 400 90 delay 2700;
#X msg 400 120 {BS}; amp 0.5;
#X obj 600 90 delay 3800;
#X msg 600 120 {BS}; dump bang;
#X obj 600 160 delay 3900;
#X msg 600 190 {BS}; pd quit;
#X obj 20 250 osc~ 440;
#X obj 120 250 r amp;
#X obj 20 280 *~ 0;
#X obj 20 310 throw~ synth-bus;
#X obj 300 250 catch~ outL;
#X obj 300 280 tabwrite~ cap;
#X obj 400 250 r rec;
#X obj 300 320 table cap {3 * SR};
#X obj 500 250 r dump;
#X msg 500 280 write -wave -bytes 2 {T}/cap.wav cap;
#X obj 500 320 soundfiler;
#X obj 700 250 catch~ outR;
#X connect 0 0 1 0;
#X connect 0 0 2 0;
#X connect 2 0 3 0;
#X connect 0 0 4 0;
#X connect 4 0 5 0;
#X connect 0 0 6 0;
#X connect 6 0 7 0;
#X connect 0 0 8 0;
#X connect 8 0 9 0;
#X connect 0 0 10 0;
#X connect 10 0 11 0;
#X connect 12 0 14 0;
#X connect 13 0 14 1;
#X connect 14 0 15 0;
#X connect 16 0 17 0;
#X connect 18 0 17 0;
#X connect 20 0 21 0;
#X connect 21 0 22 0;
"""
open(f"{T}/h.pd", "w").write(P)
subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True)
w = wave.open(f"{T}/cap.wav"); d = w.readframes(w.getnframes())
x = [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]
pk = lambda a, b: max(abs(v) for v in x[int(a * SR):int(b * SR)])
print(f"0.5 in : peak {pk(0.2, 0.95):.3f}   (expect ~0.5 untouched)")
print(f"2.0 in : peak first 5 ms {pk(1.0, 1.005):.3f}  overall {pk(1.0, 2.0):.3f}  settled {pk(1.5, 1.95):.3f}  (expect <=1, ~0.89)")
print(f"back to 0.5: after 50 ms {pk(2.05, 2.1):.3f}  after 500 ms {pk(2.5, 2.9):.3f}  (expect -> 0.5)")
shutil.rmtree(T)

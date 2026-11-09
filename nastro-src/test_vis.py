#!/usr/bin/env python3
"""VIS page (genvis.py, apply_vis.py): a tone on tape plays, MIX page 6 (VIS) is shown for 3 s in WAVE, then 3 s in
SPEC. Checks: one /oled/gFrame of 1024 bytes and (WAVE) one /oled/gWaveform of 128 values per frame, about 10
frames a second at the default SPEED, every value a whole number 0..255; mix.pd draws nothing meanwhile; no Pd errors; the picture is
not empty; leaving the page stops the frames."""
import os, shutil, subprocess, struct, math, tempfile, sys, wave

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / SR))) for i in range(10 * SR))); w.close()
ev = [(300, ["sfread read t1.wav tape1", "tp-loaded bang"]), (500, ["aux-key 65", "mode 3"])]
ev += [(600 + 50 * k, ["mode 3"]) for k in range(5)]
ev += [(1000, ["mark WAVE"]), (4000, ["mark SPEC", "vis-knob 1 0.9"]), (7000, ["mark OFF", "mode 2"]), (8000, ["pd quit"])]
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
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
shutil.rmtree(T)
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
sec, cur = {}, "pre"
for l in out.splitlines():
    if l.startswith("MARK:"):
        cur = l.split()[-1]
    elif l.startswith("OSC:"):
        sec.setdefault(cur, []).append(l.split()[1:])
res = {}
for nm in ("WAVE", "SPEC"):
    msgs = sec.get(nm, [])
    frames = [m for m in msgs if m[1] == "/oled/gFrame"]
    waves = [m for m in msgs if m[1] == "/oled/gWaveform"]
    other = [m[1] for m in msgs if m[1] not in ("/oled/gFrame", "/oled/gWaveform", "/oled/gFlip", "/oled/gFillArea", "/oled/gPrintln")]
    sizes = {len(m) - 4 for m in frames}
    vals_ok = all(v.lstrip("-").isdigit() and 0 <= int(v) <= 255 for m in frames[:5] + waves[:5] for v in m[4:])
    lit = max((sum(1 for v in m[4:] if v != "0") for m in frames), default=0)
    print(f"{nm}: {len(frames) / 3:.1f} gFrame/s (sizes {sizes})  {len(waves) / 3:.1f} gWaveform/s  {len(msgs) / 3:.0f} messages/s  "
          f"non-zero bytes up to {lit}  other commands {sorted(set(other))}")
    res[nm] = 8 <= len(frames) / 3 <= 12 and sizes == {1024} and vals_ok and lit > 20 and not other
    if nm == "WAVE":
        res[nm] &= len(waves) == len(frames) and {len(m) - 4 for m in waves} == {128}
off = [m for m in sec.get("OFF", []) if m[1] == "/oled/gFrame"]
res["OFF"] = len(off) <= 1
print(res, " errors:", errs[:4])
print("ALL OK" if all(res.values()) and not errs else "FAIL")

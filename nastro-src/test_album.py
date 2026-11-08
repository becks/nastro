#!/usr/bin/env python3
"""Album: a 440 Hz tone on tape track 1 (0..10 s). AUX + A5 with the tape stopped -> rewind + play + album-1.wav;
AUX + A5 again after ~2 s -> file closed, tape stopped. Second take: AUX + A5, then the tape is stopped with AUX + F
-> album-2.wav closed too. Checks: stereo 24-bit files of the right length with the tone, album.txt = 2, tape state."""
import os, shutil, subprocess, struct, math, tempfile, sys, wave

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR, BS = 44100, "\\"
w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 440 * i / SR))) for i in range(10 * SR))); w.close()
ev = [(400, ["sfread read t1.wav tape1", "tp-loaded bang", "mode 2"]),
      (800, ["mark A1", "aux-key 81"]), (2800, ["mark A1stop", "aux-key 81"]),
      (3300, ["mark A2", "aux-key 81"]), (4300, ["mark A2stop", "aux-key 65"]),
      (4800, ["pd quit"])]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
L.append("#X obj 600 400 soundfiler;"); sf = n; n += 1
L.append("#X obj 600 370 r sfread;"); rr = n; n += 1
C.append(f"#X connect {rr} 0 {sf} 0;")
for rcv in ("mark", "tp-play", "album-rec", "led"):
    L.append(f"#X obj 800 {20 + n} r {rcv};"); L.append(f"#X obj 800 {40 + n} print {rcv};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
ev_ = [l for l in out.splitlines() if l.startswith(("mark:", "tp-play:", "album-rec:"))]
print(" | ".join(ev_))
ok = True
for k, exp in ((1, 2.0), (2, 1.0)):
    p = f"{T}/album-{k}.wav"
    if not os.path.exists(p):
        print(f"album-{k}.wav missing"); ok = False; continue
    b = open(p, "rb").read()
    ch, bits = struct.unpack("<H", b[22:24])[0], struct.unpack("<H", b[34:36])[0]
    i = b.index(b"data") + 8; nfr = (len(b) - i) // (3 * ch)
    def s24(j):
        v = int.from_bytes(b[i + j * 3:i + j * 3 + 3], "little", signed=True); return v / 8388608
    L_ = [s24(2 * j) for j in range(nfr)]
    tail = L_[int(0.3 * SR):]
    rms = math.sqrt(sum(v * v for v in tail) / max(1, len(tail)))
    zc = sum(1 for j in range(1, len(tail)) if tail[j - 1] < 0 <= tail[j]) / (len(tail) / SR)
    dur = nfr / SR
    good = ch == 2 and bits == 24 and abs(dur - exp) < 0.15 and rms > 0.05 and abs(zc - 440) < 10
    ok &= good
    print(f"album-{k}.wav: {ch} ch {bits} bit {dur:.2f} s (expect ~{exp})  rms {rms:.3f}  {zc:.0f} Hz  {'OK' if good else 'FAIL'}")
cnt = open(f"{T}/album.txt").read().split() if os.path.exists(f"{T}/album.txt") else []
plays = [l.split()[-1] for l in ev_ if l.startswith("tp-play")]
print("album.txt:", cnt, " tape play states:", plays, " errors:", errs[:3])
ok &= cnt[:1] == ["2"] and plays[-1:] == ["0"] and not errs
shutil.rmtree(T)
print("ALL OK" if ok else "FAIL")

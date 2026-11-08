#!/usr/bin/env python3
"""Tape editor vs loop guard (apply_guardedit.py). A 512-sample loop plays (the 3-sample guard after its end is
active for 200 of every 512 samples); DUPLICATE is started at 24 times spread over a loop. The copy must equal the
loop: before the fix the guard's restore wrote the old samples over the copy's first 3 samples in about half of
the runs (a click at every restart of the duplicated loop)."""
import os, shutil, subprocess, struct, math, tempfile, wave, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro"); SR = 44100; BS = "\\"; LOOP = 512
def run(start_ms):
    T = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith(".pd") or f == "drums.wav": shutil.copy(os.path.join(SRC, f), T)
    w = wave.open(f"{T}/t1.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 4 * i / 512))) if i < LOOP else b"\0\0" for i in range(6 * SR))); w.close()
    ev = [(300, ["sfread read t1.wav tape1", "tp-loaded bang", "mode 2"]), (600, [f"tp-loop-set 2 0 {LOOP}", "aux-key 65"]),
          (start_ms, ["tape-edit 6"]), (start_ms + 1500, ["chk bang"]), (start_ms + 1600, ["pd quit"])]
    L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]; C = ["#X connect 0 0 1 0;"]; n = 2
    for t, m in ev:
        L.append(f"#X obj 20 {80+n*10} delay {t};"); L.append(f"#X msg 120 {80+n*10} " + " ".join(BS + "; " + x for x in m) + ";")
        C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n+1} 0;"]; n += 2
    L += ["#X obj 600 400 soundfiler;", "#X obj 600 370 r sfread;"]; C.append(f"#X connect {n+1} 0 {n} 0;"); n += 2
    L += ["#X obj 800 20 r chk;", f"#X obj 800 50 expr tape1[{LOOP}]-tape1[0] \\; tape1[{LOOP+1}]-tape1[1] \\; tape1[{LOOP+2}]-tape1[2];",
          "#X obj 800 80 pack f f f;", "#X obj 800 110 print DIFF;"]
    C += [f"#X connect {n} 0 {n+1} 0;", f"#X connect {n+1} 0 {n+2} 0;", f"#X connect {n+1} 1 {n+2} 1;", f"#X connect {n+1} 2 {n+2} 2;", f"#X connect {n+2} 0 {n+3} 0;"]
    open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
    out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi", "-stderr", "-r", "44100",
                          "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
    shutil.rmtree(T)
    d = [l for l in out.splitlines() if l.startswith("DIFF")]
    return [abs(float(v)) for v in d[0].split()[1:]] if d else None
bad = []
for off in range(0, 24):
    r = run(2000 + off * 0.53)          # 24 start times spread over about one loop length
    if r is None or max(r) > 1e-4: bad.append((off, r))
print("corrupted copies:", len(bad), "of 24", bad[:4])
print("ALL OK" if not bad else "FAIL")

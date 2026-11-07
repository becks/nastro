#!/usr/bin/env python3
"""Auto-start sampling test. Fake input: silence, then a 440 Hz burst with a hard attack at a known time.
SMPL: arm, sound arrives -> recording starts by itself; the saved sample must start with a short pre-roll
(< 20 ms of silence) followed by the attack. Also: arm + press again with no sound = cancel (no recording).
DRUM: arm on key 1, the attack fills the slot from its start (pre-roll then tone)."""
import os, shutil, subprocess, wave, struct, tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
SR = 44100
BS = "\\"
A = lambda k: ["aux 1", f"notes {k} 100", f"notes {k} 0", "aux 0"]
events = [
    (700, ["dbg SMPL-ARM"] + A(60) + A(76)),           # SYNTH mode, arm input sampling
    (1200, ["dbg SOUND", "inamp 0.5"]),                 # attack while armed
    (1700, ["dbg STOP"] + A(76)),
    (1800, ["inamp 0", "dumpS bang"]),
    (1900, ["dbg CANCEL-TEST"] + A(76)),                # arm ...
    (2100, A(76)),                                       # ... and cancel with no sound
    (2200, ["dbg DRUM-ARM", "aux 1", "notes 61 100", "notes 61 0", "aux 0", "notes 60 100", "notes 60 0"] + A(76)),
    (2600, ["dbg SOUND", "inamp 0.5"]),
    (3400, ["inamp 0", "dumpD bang"]),
    (3600, ["pd quit"]),
]
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in events:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
for name in ("dbg", "smp-armed", "smp-recording", "smp-len", "drum-armed", "drum-recording"):
    L.append(f"#X obj 400 {80 + n * 10} r {name};"); L.append(f"#X obj 400 {100 + n * 10} print {name};")
    C.append(f"#X connect {n} 0 {n + 1} 0;"); n += 2
objs = ["osc~ 440", "*~", "r inamp", "s~ inL", "s~ inR", "soundfiler", "r dumpS",
        f"msg write -wave -bytes 2 {T}/smpl.wav smpl", "r dumpD", f"msg write -wave -bytes 2 {T}/drums.wav drums"]
b = n
for i, o in enumerate(objs):
    kind = "msg" if o.startswith("msg ") else "obj"
    L.append(f"#X {kind} 700 {20 + i * 30} {o[4:] if kind == 'msg' else o};")
osc, mul, ra, sl, sr_, sf, rs, ms, rd, md = range(b, b + len(objs))
# hard gate: the amplitude jumps instantly (no line~) -> a sharp attack
C += [f"#X connect {osc} 0 {mul} 0;", f"#X connect {ra} 0 {mul} 1;", f"#X connect {mul} 0 {sl} 0;",
      f"#X connect {mul} 0 {sr_} 0;", f"#X connect {rs} 0 {ms} 0;", f"#X connect {ms} 0 {sf} 0;",
      f"#X connect {rd} 0 {md} 0;", f"#X connect {md} 0 {sf} 0;"]
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
show = False
for line in out.splitlines():
    if line.startswith("dbg:"):
        show = True
    if show and line.split(":")[0] in ("dbg", "smp-armed", "smp-recording", "smp-len", "drum-armed", "drum-recording") or ("error" in line and "oscOut" not in line and "led" not in line):
        print("  ", line)


def rd_(p):
    w = wave.open(p); d = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack("<%dh" % (len(d) // 2), d)]


def onset(x, th=0.05):
    return next((i for i, v in enumerate(x) if abs(v) > th), None)


s = rd_(f"{T}/smpl.wav")
o = onset(s)
print(f"SMPL: length {len(s)} samples ({len(s) / SR * 1000:.0f} ms), attack at {o} = {o / SR * 1000:.1f} ms pre-roll" if o is not None else "SMPL: no sound recorded")
dr = rd_(f"{T}/drums.wav")
# slot of key 60 = first slot: find where the new tone sits
o2 = onset(dr)
print(f"DRUM: first sound in the kit at sample {o2} ({o2 / SR * 1000:.1f} ms)" if o2 is not None else "DRUM: nothing")
shutil.rmtree(T)

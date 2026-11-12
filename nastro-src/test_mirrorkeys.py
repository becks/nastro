#!/usr/bin/env python3
"""Virtual Organelle (apply_mirrorkeys.py, inrelay.py, oled-sim.py): with SCREEN TO MAC on, a scripted session of
AUX combinations, knobs, footswitch and encoder is played into Nastro; the UDP packets go through oled-sim.py's own
parser. Checks the captions (combination + function, named from the page it was pressed on) and the control state."""
import os, shutil, subprocess, tempfile, socket, threading, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "Nastro")
spec = importlib.util.spec_from_file_location("oledsim", os.path.join(SRC, "oled-sim.py"))
sim = importlib.util.module_from_spec(spec); spec.loader.exec_module(sim)
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
s = open(f"{T}/mirror.pd").read().replace("connect \\$1 9123", "connect \\$1 9124")
open(f"{T}/mirror.pd", "w").write(s)
open(f"{T}/mirror.txt", "w").write("127.0.0.1;\n")
pkts, stop = [], False
sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); sk.bind(("127.0.0.1", 9124)); sk.settimeout(0.3)
def rx():
    while not stop:
        try:
            pkts.append(sk.recv(65536).decode("utf-8", "replace"))
        except socket.timeout:
            pass
th = threading.Thread(target=rx); th.start()


def press(n):
    return ["notes %d 100" % n, "notes %d 0" % n]


# each step: (time ms, messages, expected caption combo, expected function) - checked in order
STEPS = [
    (600, ["aux 1"] + press(62) + ["aux 0"], "AUX + D", "TAPE page"),
    (800, ["aux 1"] + press(65) + ["aux 0"], "AUX + F", "tape PLAY / STOP"),
    (1000, ["aux 1"] + press(65) + ["aux 0"], "AUX + F", "tape PLAY / STOP"),
    (1200, ["aux 1"] + press(75) + ["aux 0"], "AUX + D#5", "move FORWARD"),
    (1400, ["aux 1"] + press(64) + ["aux 0"], "AUX + E", "SEQ page"),
    (1600, ["aux 1"] + press(64) + ["aux 0"], "AUX + E", "next page: STEP"),
    (1800, ["aux 1"] + press(71) + ["aux 0"], "AUX + B", "STEP: clear pattern"),
    (2000, ["aux 1"] + press(60) + ["aux 0"], "AUX + C", "SYNTH page"),
    (2200, ["aux 1"] + press(60) + ["aux 0"], "AUX + C", "next engine: SUB"),
    (2400, ["aux 1", "knob2 0.3", "aux 0"], "AUX + KNOB 2", "SUB attack"),
    (2600, ["aux 1"] + press(63) + ["aux 0"], "AUX + D#", "MIX page"),
    (2800, ["aux 1", "knob1 0.7", "aux 0"], "AUX + KNOB 1", "PAN track 1"),
    (3000, ["aux 1"] + press(63) + ["aux 0"], "AUX + D#", "next page: FX"),
    (3200, ["fs 1", "fs 0"], "FOOTSWITCH", "REC tape"),
    (3400, ["fs 1", "fs 0"], "FOOTSWITCH", "REC tape"),
]
ev = [(200, ["nst-mirror-toggle bang"])] + [(t, m) for t, m, _, _ in STEPS]
ev += [(3600, ["notes 67 100", "knob3 0.42", "enc 1", "enc 1", "enc 0"]), (3900, ["pd quit"])]
BS = "\\"
L = ["#N canvas 0 0 800 600 12;", "#X obj 20 20 loadbang;", "#X msg 20 50 " + BS + "; pd dsp 1;"]
C = ["#X connect 0 0 1 0;"]
n = 2
for t_ms, msgs in ev:
    L.append(f"#X obj 20 {80 + n * 10} delay {t_ms};")
    L.append(f"#X msg 120 {80 + n * 10} " + " ".join(BS + "; " + m for m in msgs) + ";")
    C += [f"#X connect 0 0 {n} 0;", f"#X connect {n} 0 {n + 1} 0;"]
    n += 2
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
stop = True; th.join(); shutil.rmtree(T)
o = sim.Oled()
caps = []
for p in pkts:
    for msg in p.split(";"):
        words = msg.replace("\\", "").split()
        if not words:
            continue
        before = o.caption
        o.handle(words)
        if o.caption is not before:
            caps.append(o.caption[:2])
want = [(a, b) for _, _, a, b in STEPS]
ok = True
for k, w in enumerate(want):
    got = caps[k] if k < len(caps) else None
    flag = "ok " if got == w else "BAD"
    ok &= got == w
    print(flag, w, "" if got == w else got)
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
st = o.state()
print("ctx", o.ctx); print("final: keys", st["keys"], "knobs", st["knobs"], "enc", st["enc"], "aux", st["aux"], "page", st["page"])
ok &= st["keys"] == [67] and st["knobs"][2] == 42 and st["enc"] == 1 and not st["aux"] and st["page"] == "PROJECTS" and len(caps) == len(want) and not errs
print("errors", errs[:5])
print("PASS" if ok else "FAIL")

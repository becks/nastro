#!/usr/bin/env python3
"""Arpeggiator (SEQ page 5), tempo 120 (beat 500 ms), tape stopped unless said.
A up 1/16: C E G held -> 60 64 67 60 ... every 125 ms, the first at once; keys do not play by themselves.
B down, 2 octaves -> 79 76 72 67 64 60.   C 1/8T -> 167 ms apart.   D release -> silence.
E HOLD: chord released keeps playing; a new chord (D F A) replaces it; AUX+B clears.   F PROB 0 -> silence.
G tape playing: steps on the tape's 16ths."""
import os, shutil, subprocess, tempfile, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Nastro")
T = tempfile.mkdtemp()
for f in os.listdir(SRC):
    if f.endswith(".pd") or f == "drums.wav":
        shutil.copy(os.path.join(SRC, f), T)
BS = "\\"
on = lambda *ns: [f"notes {n} 100" for n in ns]
off = lambda *ns: [f"notes {n} 0" for n in ns]
ev = [(300, ["mode 4"]), (350, ["mode 4"]), (400, ["mode 4"]), (450, ["mode 4"]), (500, ["mode 4"]),
      (1000, ["mark A"] + on(60, 64, 67)), (1990, off(60, 64, 67)),
      (2300, ["mark B", "arp-knob 1 0.3", "arp-knob 3 0.3"] + on(60, 64, 67)), (3290, off(60, 64, 67)),
      (3600, ["mark C", "arp-knob 1 0", "arp-knob 3 0", "arp-knob 2 0.4"] + on(60, 64, 67)), (4600, off(60, 64, 67)),
      (4700, ["mark D"]),
      (5300, ["mark E", "arp-knob 2 0.55", "aux-key 72"] + on(60, 64, 67)), (5500, off(60, 64, 67)),
      (6300, ["mark E2"] + on(62, 65, 69)), (6400, off(62, 65, 69)), (7000, ["mark E3", "aux-key 71"]),
      (7500, ["mark F", "aux-key 72", "arp-set 1 0", "arp-aux-set 1 0"] + on(60, 64)), (8300, off(60, 64)),
      (8400, ["arp-aux-set 1 1"]),
      (8600, ["mark G", "aux-key 65"]), (8800, on(60, 67)), (9800, off(60, 67)), (10000, ["aux-key 65"]),
      (10200, ["pd quit"])]
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


tm = add("#X obj 900 20 timer;"); C.append(f"#X connect 0 0 {tm} 0;")
for rcv, tag in (("seq-notes", "SEQ"), ("synth-notes", "SYN"), ("tick16", "TICK")):
    r_ = add(f"#X obj 900 {60 + n * 5} r {rcv};"); t_ = add(f"#X obj 900 {80 + n * 5} t l b;")
    lp = add(f"#X obj 900 {100 + n * 5} list prepend;"); pr = add(f"#X obj 900 {120 + n * 5} print {tag};")
    C += [f"#X connect {r_} 0 {t_} 0;", f"#X connect {t_} 1 {tm} 1;", f"#X connect {tm} 0 {lp} 1;",
          f"#X connect {t_} 0 {lp} 0;", f"#X connect {lp} 0 {pr} 0;"]
for rcv in ("mark", "seq-page"):
    a = add(f"#X obj 1200 {n * 5} r {rcv};"); b = add(f"#X obj 1200 {n * 5 + 20} print {rcv};"); C.append(f"#X connect {a} 0 {b} 0;")
open(f"{T}/h.pd", "w").write("\n".join(L + C) + "\n")
out = subprocess.run(["/Applications/Pd-0.54-1.app/Contents/Resources/bin/pd", "-nogui", "-batch", "-noaudio", "-nomidi",
                      "-stderr", "-r", "44100", "-open", f"{T}/main.pd", "-open", f"{T}/h.pd"], capture_output=True, text=True).stderr
shutil.rmtree(T)
errs = [l for l in out.splitlines() if "error" in l and not any(
    k in l for k in ("can't open", "No such", "oscOut", "led:", "enableSub", "screenLine", "fm-knob", "receive~ in", "goHome"))]
sec, cur = {}, "pre"
ticks = []
for l in out.splitlines():
    if l.startswith("mark:"):
        cur = l.split()[-1]
    elif l.startswith(("SEQ:", "SYN:")):
        p = l.split()
        if float(p[3]) > 0:                                     # note-ons: time, note
            sec.setdefault(cur, {}).setdefault(p[0][:3], []).append((float(p[1]), int(float(p[2]))))
    elif l.startswith("TICK:"):
        ticks.append(float(l.split()[1]))
pages = [l for l in out.splitlines() if l.startswith("seq-page")]
notes = lambda k: [nn for _, nn in sec.get(k, {}).get("SEQ", [])]
times = lambda k: [t for t, _ in sec.get(k, {}).get("SEQ", [])]
gaps = lambda k: sorted(round(b - a) for a, b in zip(times(k), times(k)[1:]))
res = {}
res["A"] = notes("A")[:6] == [60, 64, 67, 60, 64, 67] and abs(times("A")[0] - 1020) < 2 and gaps("A")[len(gaps("A")) // 2] == 125
res["A-keys"] = len(sec.get("A", {}).get("SYN", [])) == len(notes("A"))      # the instrument only hears the arp
res["B"] = notes("B")[:6] == [79, 76, 72, 67, 64, 60]
res["C"] = abs(gaps("C")[len(gaps("C")) // 2] - 167) <= 1
res["D"] = notes("D") == []
res["E"] = len(notes("E")) >= 6 and set(notes("E")) == {60, 64, 67} and set(notes("E2")) == {62, 65, 69} and notes("E3") == []
res["F"] = notes("F") == []
gt = times("G")
res["G"] = len(gt) >= 4 and all(any(abs(t - tk) < 1 for tk in ticks) for t in gt)
print("pages:", pages[-1:], " A", notes("A")[:7], gaps("A")[:3], " B", notes("B")[:7], " C gaps", gaps("C")[:4])
print("E", notes("E")[:7], "E2", notes("E2")[:4], "E3", notes("E3"), " F", notes("F"), " G", notes("G")[:5])
print({k: v for k, v in res.items()}, " errors:", errs[:4])
print("ALL OK" if all(res.values()) and not errs else "FAIL")

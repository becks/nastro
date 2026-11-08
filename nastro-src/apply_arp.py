#!/usr/bin/env python3
"""Arpeggiator: 5th SEQ page (genarp.py -> arp.pd). Wiring in the other generators:
- gen.py: exec genarp.py, [arp] in main.pd; on the ARP page the keys' note-ons do not play the instrument
  (arpcap), releases always pass; knob contexts 40 (ARP) and 41 (ARP with AUX): pkval / pkpick 168.
- genseq.py: AUX+E cycles 5 pages; knobs of page 4 go to arp-knob; STEP's AUX + C5 (start STEP + tape, from any
  page) is ignored on the ARP page, where AUX + C5 is HOLD.
- genproj.py: contexts 40 / 41 loaded as arp-set / arp-aux-set; projects saved before have 160 values, and Pd
  repeats the last one into slots 160..167 (all equal) -> defaults."""
import shutil

for f in ("gen.py", "genseq.py", "genproj.py"):
    shutil.copy(f, f + ".pre-arp")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


ARPDEF = "0 0.55 0 0.5 1 0 0 0"
edit("gen.py", [
    ('exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genalbum.py")).read())',
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genalbum.py")).read())\n'
     'exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genarp.py")).read())'),
    ('m.obj(1780, 680, "album")', 'm.obj(1780, 680, "album")\nm.obj(1850, 680, "arp")'),
    ('m.c(sp_play, instr); m.c(instr, irt); m.c(irt, upk, 0)',
     'arpG = m.obj(300, 145, "spigot")                   # ARP page: note-ons go to the arpeggiator (apply_arp.py)\n'
     'arpGT = m.obj(300, 140, "t l l")\n'
     'arpGE = m.obj(380, 145, "expr $f2==0 || arpcap==0")\n'
     'm.c(sp_play, arpGT); m.c(arpGT, arpGE, 1); m.c(arpGE, arpG, 0, 1); m.c(arpGT, arpG, 0)\n'
     'm.c(arpG, instr); m.c(instr, irt); m.c(irt, upk, 0)'),
    ('if($f1==4 && $f4==3 \\\\, 17 \\\\, $f1)',
     'if($f1==4 && $f4==3 \\\\, 17 \\\\, if($f1==4 && $f4==4 \\\\, if($f5==1 \\\\, 41 \\\\, 40) \\\\, $f1))'),
    ('m.obj(560, 530, "table pkval 160")', 'm.obj(560, 530, "table pkval 168")'),
    ('m.obj(680, 530, "table pkpick 160")', 'm.obj(680, 530, "table pkpick 168")'),
    (' 0 0.3 0.5 0 \\\\; pkphys', f' 0 0.3 0.5 0 {ARPDEF} \\\\; pkphys'),
])
edit("genseq.py", [
    ('pgN = q.obj(20, 330, "expr ($f1+1)%4")              # TEMPO -> STEP -> TOMBOLA',
     'pgN = q.obj(20, 330, "expr ($f1+1)%5")              # TEMPO -> STEP -> TOMBOLA -> ENDLESS -> ARP (apply_arp.py)'),
    ('rp = q.obj(300, 240, "route 0 1 2 3")', 'rp = q.obj(300, 240, "route 0 1 2 3 4")'),
    ('q.c(rp, q.obj(460, 270, "s endl-knob"), 3)', 'q.c(rp, q.obj(460, 270, "s endl-knob"), 3)\nq.c(rp, q.obj(540, 270, "s arp-knob"), 4)'),    ('q.c(aks, onT, 2)',
     'onArp = q.obj(1360, 255, "spigot 1")              # not on the ARP page: there AUX + C5 is HOLD (apply_arp.py)\n'
     'onArpE = q.obj(1420, 240, "expr arpcap==0")\n'
     'onArpT = q.obj(1360, 240, "t b b")\n'
     'q.c(aks, onArpT, 2); q.c(onArpT, onArpE, 1); q.c(onArpE, onArp, 0, 1); q.c(onArpT, onArp, 0); q.c(onArp, onT)'),
])
s = open("genproj.py").read()
a = '(39, "drone-lfo-knob")]'
assert s.count(a) == 1
s = s.replace(a, '(39, "drone-lfo-knob"), (40, "arp-set"), (41, "arp-aux-set")]')
a = "# projects saved before the LFO have 116 values"
assert s.count(a) == 1
SUM = "+".join(f"abs(pkval[{i}]-pkval[160])" for i in range(161, 168))
s = s.replace(a, f'''# projects saved before the arpeggiator: Pd repeats the file's last value into slots 160..167, so they are all
# equal (whichever fix runs first) -> defaults (apply_arp.py)
fixE11 = p.obj(-100, 790, "expr {SUM}==0")
fixS11 = p.obj(-100, 820, "sel 1")
p.c(fixT, fixE11, 1); p.c(fixE11, fixS11); p.c(fixS11, p.msg(-100, 850, "\\\\; pkval 160 {ARPDEF}"))
''' + a)
open("genproj.py", "w").write(s)
print("arp wired")

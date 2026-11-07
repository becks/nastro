#!/usr/bin/env python3
"""AUX + C5 = sequencer play. Entering notes already enables the sequence, so the old toggle switched it OFF, and
with the tape stopped (the tape is the clock) nothing ran either way. Now: tape stopped -> enable the sequence and
start the tape; tape playing -> toggle the sequence (the tape keeps playing)."""
p = "genseq.py"; s = open(p).read()
a = '''onE = q.obj(1360, 300, "expr seqp[3]==0")
onM = q.msg(1360, 330, "\\\; seqp 3 \\\\$1")
q.c(aks, onE, 2); q.c(onE, onM); q.c(onM, dirty)'''
assert s.count(a) == 1
s = s.replace(a, '''plF = q.obj(1460, 270, "f 0")                       # tape play state
q.c(q.obj(1460, 240, "r tp-play"), plF, 0, 1)
onT = q.obj(1360, 280, "t b b")
q.c(aks, onT, 2)
onE = q.obj(1360, 300, "expr if($f1==0 \\\\, 1 \\\\, seqp[3]==0)")   # 1) enable (play state before starting)
onM = q.msg(1360, 330, "\\\; seqp 3 \\\\$1")
q.c(onT, plF, 1); q.c(plF, onE); q.c(onE, onM); q.c(onM, dirty)
stF = q.obj(1460, 300, "f 0")
q.c(q.obj(1560, 240, "r tp-play"), stF, 0, 1)
stS = q.obj(1460, 330, "sel 0")                      # 2) tape stopped -> start it (AUX+F)
q.c(onT, stF, 0); q.c(stF, stS); q.c(stS, q.msg(1460, 360, "\\\; aux-key 65"))''')
open(p, "w").write(s); print("ok")

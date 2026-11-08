#!/usr/bin/env python3
"""TAPE lanes rebuild in smaller chunks. While recording with the TAPE page shown, the lanes were rebuilt 4x/s
(256 iterations) in 8 chunks of 32: each chunk was a block-long control burst that, added to synth and sequencer
load, made the Organelle drop audio (the recording itself stayed clean). Now 32 chunks of 8, one per scheduler
tick (~46 ms per rebuild: it must finish before the next 100 ms screen frame can restart it, chunks of 4 took
~93 ms and left the lanes empty), still 4 rebuilds/s while recording (each update
scans only the two newest 0.1 s bins: slower updates leave gaps in the lane). Slowest blocks while recording:
130 -> ~64 us (Mac); plain playback is ~40 us."""
p = "gentapemap.py"; s = open(p).read()
pairs = [('nloop = tm.msg(1000, 590, "32")', 'nloop = tm.msg(1000, 590, "8")'),
         ('ccM = tm.obj(1250, 680, "moses 8")', 'ccM = tm.obj(1250, 680, "moses 32")'),
         ("tm.c(ccM, ccD, 0); tm.c(ccD, chT)", 'ccB = tm.obj(1250, 695, "t b")                    # a float into [delay] would set its time (chunk n waited n ms)\ntm.c(ccM, ccB, 0); tm.c(ccB, ccD); tm.c(ccD, chT)'),
         ("# run the 256 iterations in chunks of 32, one chunk per scheduler tick",
          "# run the 256 iterations in chunks of 8, one chunk per scheduler tick (apply_lanechunks.py)")]
for a, b in pairs:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w").write(s)
print("lanes: 32 chunks of 8")

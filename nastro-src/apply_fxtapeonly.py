#!/usr/bin/env python3
"""Only tape tracks 1-4 reach the delay and reverb (through their sends): the live synth, drums and the input
monitor stay dry. DLY / REV on the FX page are the overall amounts of the track sends."""
p = "genmix.py"; s = open(p).read()
pairs = [("ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(cfd, dry, 0, 1)        # delay feed: synth + track delay sends",
          "ms.c(cs, sti); ms.c(cfd, dry, 0, 1)                             # delay feed: track delay sends only"),
         ("ms.c(cs, dryR, 0, 0); ms.c(cfr, dryR, 0, 1)                         # reverb feed: synth + track reverb sends",
          "ms.c(cfr, dryR, 0, 1)                                              # reverb feed: track reverb sends only"),
         ('ms.text(20, 10, "master: synth + tape -> delay + reverb -> out. The tape records the dry synth.")',
          'ms.text(20, 10, "master: tape tracks (sends) -> delay + reverb. Live synth and drums stay dry. The tape records the dry synth.")')]
for a, b in pairs:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(p, "w").write(s)
print("FX: tape tracks only")

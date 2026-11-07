#!/usr/bin/env python3
"""Track DJ filter resonance defaults to the minimum (0, was 0.3): a smooth filter with no peak at the cutoff.
Knob init (pkval 84..87), tape.pd filter default, FILTER page display, and the fallback for old projects."""


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


s = open("gen.py").read()
i = s.index('pkInit = m.msg(560, 820, "'); j = s.index("\n", i)
line = s[i:j]
head, rest = line.split("pkval ", 1)
body, tail = rest.split(" \\\\; pkphys", 1)
vals = body.split()                      # vals[0] = start index 0, pkval[n] = vals[n + 1]
assert vals[85:89] == ["0.3"] * 4, vals[85:89]
vals[85:89] = ["0"] * 4
s = s[:i] + head + "pkval " + " ".join(vals) + " \\\\; pkphys" + tail + s[j:]
open("gen.py", "w").write(s)

edit("gentape.py", [('fDef = t.msg(1900, 920, "1 0.3 \\\\, 2 0.3 \\\\, 3 0.3 \\\\, 4 0.3")',
                     'fDef = t.msg(1900, 920, "1 0 \\\\, 2 0 \\\\, 3 0 \\\\, 4 0")')])
edit("genmix.py", [('b = x_.obj(2800 + k * 50, 550, "f 0.3")', 'b = x_.obj(2800 + k * 50, 550, "f 0")')])
edit("genproj.py", [('"\\\\; pkval 80 0.5 0.5 0.5 0.5 0.3 0.3 0.3 0.3"', '"\\\\; pkval 80 0.5 0.5 0.5 0.5 0 0 0 0"')])
print("resonance default 0")

#!/usr/bin/env python3
"""Static review of the generated Nastro patches (Pd vanilla 0.49 target)."""
import glob, os, re, sys
from collections import defaultdict

D = sys.argv[1]
EXPR_OK = set("abs acos acosh asin asinh atan atan2 atanh avg cbrt ceil copysign cos cosh erf erfc exp expm1 fact finite floor "
              "fmod if imodf isinf isnan ldexp ln log log1p max min modf nearbyint pow random remainder rint round sin sinh "
              "size sqrt sum tan tanh trunc int float".split())
# names provided / consumed by the Organelle (mother.pd) or Pd itself
EXTERNAL_R = {"notes", "aux", "fs", "enc", "encbut", "knob1", "knob2", "knob3", "knob4", "vol"}
EXTERNAL_S = {"oscOut", "led", "enableSubMenu", "goHome", "pd", "screenLine1", "screenLine2", "screenLine3",
              "screenLine4", "screenLine5"}


def parse(path):
    raw = open(path).read()
    stm = [x.strip() for x in re.split(r"(?<!\\);\s*\n", raw) if x.strip()]
    objs, cons = [], []
    for s in stm:
        if s.startswith("#X connect"):
            a = s.split()
            cons.append(tuple(int(v) for v in a[2:6]))
        elif s.startswith("#X") and not s.startswith("#X coords") and not s.startswith("#X restore"):
            objs.append(s)
        elif s.startswith("#N canvas") and objs:
            objs.append(s)      # (no subpatches expected)
    return objs, cons


def words(o):
    return o.split()


sends, recvs = defaultdict(set), defaultdict(set)
issues = defaultdict(list)
stats = {}
for path in sorted(glob.glob(os.path.join(D, "*.pd"))):
    f = os.path.basename(path)
    if f == "mac-sim.pd":
        continue
    objs, cons = parse(path)
    kinds = [words(o)[1] if len(words(o)) > 1 else "" for o in objs]
    cls = []
    for o in objs:
        w = words(o)
        cls.append(w[4] if len(w) > 4 and w[1] == "obj" else w[1])
    nsig = sum(1 for c in cls if c.endswith("~"))
    stats[f] = (len(objs), nsig)
    deg = defaultdict(int)
    for a, ao, b, bi in cons:
        deg[a] += 1; deg[b] += 1
    for i, o in enumerate(objs):
        w = words(o)
        # sends / receives
        if w[1] == "obj" and len(w) > 5 and w[4] in ("r", "receive", "r~", "receive~", "catch~"):
            recvs[w[5].rstrip(";")].add(f)
        if w[1] == "obj" and len(w) > 5 and w[4] in ("s", "send", "s~", "send~", "throw~"):
            sends[w[5].rstrip(";")].add(f)
        if w[1] == "msg":
            for m in re.finditer(r"\\; (\S+)", o):
                sends[m.group(1)].add(f)
        # expr functions
        if w[1] == "obj" and len(w) > 4 and w[4] in ("expr", "expr~", "fexpr~"):
            for fn in re.findall(r"([A-Za-z_]\w*)\s*\(", " ".join(w[5:])):
                if fn not in EXPR_OK:
                    issues["expr function not in Pd 0.49"].append(f"{f}#{i}: {fn}")
        # orphans
        if deg[i] == 0 and w[1] in ("obj", "msg") and not (len(w) > 4 and w[4] in (
                "table", "text", "r", "receive", "r~", "catch~", "switch~", "loadbang", "declare", "clone")):
            if w[1] == "msg" and "\\;" in o:
                continue                          # message boxes that only send
            issues["orphan object (no connections)"].append(f"{f}#{i}: {' '.join(w[4:])[:60] if w[1]=='obj' else o[:60]}")
    for a, ao, b, bi in cons:
        if b >= len(objs) or a >= len(objs):
            issues["connection out of range"].append(f"{f}: {a}->{b}"); continue
        wb, wa = words(objs[b]), words(objs[a])
        cb = wb[4] if len(wb) > 4 and wb[1] == "obj" else wb[1]
        ca = wa[4] if len(wa) > 4 and wa[1] == "obj" else wa[1]
        if cb in ("r", "receive") and len(wb) > 5:
            issues["connection into [r name] (no inlet)"].append(f"{f}: #{a} {ca} -> #{b} r {wb[5]}")
        if cb in ("delay", "del") and bi == 0 and ca not in ("t", "trigger", "sel", "select", "metro", "bang", "b",
                                                              "delay", "del", "loadbang", "bng", "msg", "until", "spigot",
                                                              "moses", "route", "r", "receive", "timer"):
            issues["[delay] left inlet fed by a float source"].append(f"{f}: #{a} {ca} -> #{b} delay")
        if ca in ("t", "trigger") and len(wa) > 5:
            outs = wa[5:]
            if ao < len(outs) and outs[ao].rstrip(";") in ("f", "l", "a") and cb in ("delay", "del") and bi == 0:
                issues["[delay] left inlet fed by a float source"].append(f"{f}: #{a} t({outs[ao]}) -> #{b} delay")

ext_r = EXTERNAL_R
for n in sorted(recvs):
    if n not in sends and n not in ext_r and not n.startswith("$"):
        issues["receive with no sender"].append(f"{n}  (in {', '.join(sorted(recvs[n]))})")
for n in sorted(sends):
    if n not in recvs and n not in EXTERNAL_S and not n.startswith("$") and n not in ("outL", "outR"):
        # tables written by message also count as receivers
        issues["send with no receiver (or a table name)"].append(f"{n}  (from {', '.join(sorted(sends[n]))})")
for k, v in issues.items():
    print(f"\n== {k}: {len(v)}")
    for x in v[:60]:
        print("   ", x)
print("\n== objects / signal objects per patch")
for f, (n, s) in sorted(stats.items(), key=lambda x: -x[1][1]):
    print(f"   {f:18s} {n:5d} objects  {s:4d} signal")

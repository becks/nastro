#!/usr/bin/env python3
"""Fan-out order risks: one outlet feeds a COLD inlet of X and (directly or downstream) a HOT path that reaches X.
Pd fires fan-out connections in an undefined (creation-dependent) order, so X may compute with the old value."""
import glob, os, re, sys
from collections import defaultdict

D = sys.argv[1]
SIGNAL_SAFE = ("~",)


def parse(path):
    raw = open(path).read()
    stm = [x.strip() for x in re.split(r"(?<!\\);\s*\n", raw) if x.strip()]
    objs, cons = [], []
    for s in stm:
        if s.startswith("#X connect"):
            a = s.split(); cons.append(tuple(int(v) for v in a[2:6]))
        elif s.startswith("#X") and not s.startswith("#X coords"):
            objs.append(s)
    return objs, cons


def cls(o):
    w = o.split()
    return (w[4] if len(w) > 4 and w[1] == "obj" else w[1]).rstrip(";")


for path in sorted(glob.glob(os.path.join(D, "*.pd"))):
    f = os.path.basename(path)
    if f == "mac-sim.pd":
        continue
    objs, cons = parse(path)
    out = defaultdict(list)                      # (obj, outlet) -> [(dst, inlet)]
    succ = defaultdict(set)
    for a, ao, b, bi in cons:
        out[(a, ao)].append((b, bi)); succ[a].add(b)

    def reach(start, target, limit=60):
        seen, st = set(), [start]
        while st and len(seen) < 400:
            n = st.pop()
            if n == target:
                return True
            if n in seen:
                continue
            seen.add(n)
            # message boxes with ';' sends and trigger reorder don't stop propagation; keep it simple
            st.extend(succ[n])
        return False

    for (a, ao), dsts in out.items():
        if len(dsts) < 2 or cls(objs[a]).endswith("~"):
            continue
        cold = [(b, bi) for b, bi in dsts if bi > 0 and not cls(objs[b]).endswith("~")]
        hot = [(b, bi) for b, bi in dsts if bi == 0]
        for (x, xi) in cold:
            for (y, _) in hot:
                if y != x and reach(y, x):
                    print(f"{f}: #{a} {cls(objs[a])}[{ao}] -> cold {cls(objs[x])}#{x}[{xi}]  and hot {cls(objs[y])}#{y} which reaches it")

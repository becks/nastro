#!/usr/bin/env python3
"""Run a test file with subprocess.run wrapped, collect every Pd error line that is not expected."""
import subprocess, sys, io, contextlib, re, os

EXPECTED = ("can't open", "No such file", "oscOut: no such object", "led: no such object", "enableSubMenu",
            "screenLine", "fm-knob: no such object", "receive~ inL", "receive~ inR", "goHome")
test = sys.argv[1]
errors = []
real_run = subprocess.run


def run(*a, **k):
    r = real_run(*a, **k)
    out = (r.stderr or "") if isinstance(r.stderr, str) else ""
    for line in out.splitlines():
        if "error" in line.lower() and not any(e in line for e in EXPECTED):
            errors.append(line.strip())
    return r


subprocess.run = run
os.chdir(os.path.dirname(os.path.abspath(test)))
with contextlib.redirect_stdout(io.StringIO()):
    try:
        exec(compile(open(test).read(), test, "exec"), {"__name__": "__main__", "__file__": os.path.abspath(test)})
    except SystemExit:
        pass
from collections import Counter
c = Counter(errors)
print(f"{os.path.basename(test):22s} {'OK' if not c else ''}")
for e, n in c.most_common(8):
    print(f"    {n:3d} x {e[:110]}")

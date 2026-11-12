#!/usr/bin/env python3
"""VIS on the Mac at 5 frames a second (genmirror.py): with the lighter mirror (apply_mirrortext.py) the gFrame
throttle goes from one per 500 ms to one per 200 ms."""
import shutil

shutil.copy("genmirror.py", "genmirror.py.pre-mirrorvis5")
s = open("genmirror.py").read()
a = 'frD = mi.obj(660, 450, "delay 500")'
assert s.count(a) == 1
s = s.replace(a, 'frD = mi.obj(660, 450, "delay 200")                 # 5 frames a second (apply_mirrorvis5.py)')
open("genmirror.py", "w").write(s)
s = open("test_mirrorthrottle.py").read()
a = "0 < len(nF) <= 11"
assert s.count(a) == 1
open("test_mirrorthrottle.py", "w").write(s.replace(a, "12 <= len(nF) <= 26").replace("at most ~2 gFrame/s", "at most ~5 gFrame/s"))
print("mirror vis 5 fps applied")

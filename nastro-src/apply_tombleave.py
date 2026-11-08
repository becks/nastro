#!/usr/bin/env python3
"""TOMBOLA -> another page left half of the screen with the tombola drawn over the new page. Leaving the page,
[change] fanned out to "tmbp 8 0, tomb-count bang" and to the page gates; when the message went first,
tomb-count asked for a redraw while the gates were still open and one last tombola frame (left half: wipe,
polygon, balls, flip) landed on the new page. Now a trigger updates the gates first, then sends the message."""
import shutil
shutil.copy("gentomb.py", "gentomb.py.pre-tombleave")
with open("gentomb.py") as f_:
    s = f_.read()
a = r'''tb.c(actF, tb.msg(250, 170, "\\; tmbp 8 \\$1 \\; tomb-count bang"))
actT = tb.obj(20, 200, "t f f f")
tb.c(actF, actT)'''
assert s.count(a) == 1
s = s.replace(a, r'''actO = tb.obj(20, 185, "t f f")                  # 1) page gates  0) then tmbp 8 / redraw request (apply_tombleave.py)
tb.c(actF, actO)
tb.c(actO, tb.msg(250, 170, "\\; tmbp 8 \\$1 \\; tomb-count bang"), 0)
actT = tb.obj(20, 200, "t f f f")
tb.c(actO, actT, 1)''')
with open("gentomb.py", "w") as f_:
    f_.write(s)
print("tombola leave fixed")

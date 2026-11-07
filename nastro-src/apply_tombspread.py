#!/usr/bin/env python3
"""TOMBOLA load spreading (it crackled on the Organelle): one ball per 3.75 ms scheduler slot instead of all
balls in one 30 ms burst; collision passes skipped when the ball is far from every wall; drawing split in two
slots (wipe/text + polygon at slot 2, balls + flip at slot 5) of every 3rd cycle."""
import shutil

shutil.copy("gentomb.py", "gentomb.py.pre-spread2")
s = open("gentomb.py").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('mtr = tb.obj(1900, 210, f"metro {TICK}")', 'mtr = tb.obj(1900, 210, f"metro {TICK / NB}")          # one ball per slot')
# clock: slot counter instead of "all balls per tick"
rep('''tick = tb.obj(1900, 240, "t b b b")
tb.c(mtr, tick)''', '''slF = tb.obj(1900, 240, "f 0")
slI = tb.obj(1960, 240, "+ 1")
slM = tb.obj(2020, 240, f"mod {NB}")
slT = tb.obj(1900, 260, "t f f f")
tb.c(mtr, slF); tb.c(slF, slT)
tb.c(slT, slI, 2); tb.c(slI, slM); tb.c(slM, slF, 0, 1)
slS = tb.obj(2000, 280, "sel 0 2 5")
tb.c(slT, slS, 1)''')
rep('tb.c(tick, rotE, 2)', 'tb.c(slS, rotE, 0)')
rep('''n8 = tb.msg(1900, 280, str(NB))
lz = tb.msg(1960, 280, "0")
lpT = tb.obj(1900, 270, "t b b")
tb.c(tick, lpT, 1)
lu = tb.obj(1900, 310, "until")
lc = tb.obj(1900, 340, "f")
lc1 = tb.obj(1960, 340, "+ 1")
tb.c(lpT, lz, 1); tb.c(lz, lc, 0, 1); tb.c(lpT, n8, 0); tb.c(n8, lu); tb.c(lu, lc); tb.c(lc, lc1); tb.c(lc1, lc, 0, 1)
bT = tb.obj(1900, 370, "t f f")
tb.c(lc, bT)''', '''bT = tb.obj(1900, 370, "t f f")
tb.c(slT, bT, 0)''')
# collision passes only near a wall (speed <= 7 px/tick, so 9 px of margin is safe)
rep('''def bpass(o, y, text, tables):''', '''nearT = tb.obj(2100, 470, "t f f")
tb.c(ball, nearT, 4)
nearE = tb.obj(2200, 490, "expr " + E(f"tmbx[$f1]*tmbx[$f1]+tmby[$f1]*tmby[$f1]>(tmbp[5]-9)*(tmbp[5]-9)"))
nearSp = tb.obj(2100, 500, "spigot")
tb.c(nearT, nearE, 1); tb.c(nearE, nearSp, 0, 1); tb.c(nearT, nearSp, 0)
wall = tb.obj(2100, 530, "t f f f f")             # B0 Bk B1 B2


def bpass(o, y, text, tables, src=None):''')
rep('''    tb.c(ball, idx, o)''', '''    tb.c(src if src is not None else ball, idx, o)''')
rep('''bpass(4, 580, f"tmbp[0]''', '''tb.c(nearSp, wall)
bpass(3, 580, f"tmbp[0]''')
rep('''("tmbphi",))''', '''("tmbphi",), wall)''')
rep('''bpass(3, 640, f"if(''', '''bpass(2, 640, f"if(''')
rep('''("tmbk",))''', '''("tmbk",), wall)''')
rep('''bpass(2, 700, f"cos(''', '''bpass(1, 700, f"cos(''')
rep('''("tmbnx", "tmbny", "tmbpen"))''', '''("tmbnx", "tmbny", "tmbpen"), wall)''')
rep('''pB2 = bpass(1, 760,''', '''pB2 = bpass(0, 760,''')
rep('''("tmbx", "tmby", "tmbvx", "tmbvy"))
# a real hit''', '''("tmbx", "tmby", "tmbvx", "tmbvy"), wall)
# a real hit''')
# drawing: frame decided at slot 0, parts drawn at slots 2 and 5
rep('''tb.c(tick, frC, 0); tb.c(frC, frI); tb.c(frI, frC, 0, 1)''', '''tb.c(slS, frC, 0); tb.c(frC, frI); tb.c(frI, frC, 0, 1)''')
rep('''frSp = tb.obj(1700, 390, "spigot")
tb.c(actT, frSp, 1, 1)
tb.c(frS, frSp); tb.c(fr0, frSp)
dT = tb.obj(1700, 420, "t b b b b")
tb.c(frSp, dT)''', '''frSp = tb.obj(1700, 390, "spigot")
tb.c(actT, frSp, 1, 1)
tb.c(fr0, frSp)
dA = tb.obj(1600, 420, "t b b")                 # wipe/text, polygon
dB = tb.obj(1800, 420, "t b b")                 # balls, flip
dT = tb.obj(1700, 420, "t b b")                 # one-shot full draw
tb.c(frSp, dT); tb.c(dT, dA, 1); tb.c(dT, dB, 0)
drawF = tb.obj(1500, 360, "f 0")
d1 = tb.msg(1500, 330, "1")
tb.c(frS, d1); tb.c(d1, drawF, 0, 1)
d0 = tb.msg(1500, 470, "0")
tb.c(d0, drawF, 0, 1)
actD = tb.obj(1450, 330, "f 0")
tb.c(actT, actD, 1, 1)
for slot, part in ((1, dA), (2, dB)):
    q = tb.obj(1400 + slot * 100, 390, "t b b")
    tb.c(slS, q, slot)
    g = tb.obj(1400 + slot * 100, 410, "expr $f1 && $f2")
    tb.c(q, actD, 1); tb.c(actD, g, 0, 1)
    tb.c(q, drawF, 0); tb.c(drawF, g, 0, 0)
    gS = tb.obj(1400 + slot * 100, 440, "sel 1")
    tb.c(g, gS); tb.c(gS, part)
    if part is dB:
        tb.c(gS, d0)''')
rep('''tb.c(dT, textDirty, 3); tb.c(textDirty, tdS)''', '''tb.c(dA, textDirty, 1); tb.c(textDirty, tdS)''')
rep('''tb.c(dT, pgTT, 2)''', '''tb.c(dA, pgTT, 0)''')
rep('''tb.c(dT, blT, 1)''', '''tb.c(dB, blT, 1)''')
rep('''tb.c(dT, tb.msg(1700, 850, "\\\\; oscOut sendtyped /oled/gFlip i 3"), 0)''', '''tb.c(dB, tb.msg(1700, 850, "\\\\; oscOut sendtyped /oled/gFlip i 3"), 0)''')
open("gentomb.py", "w").write(s)
print("spread applied")

# exec'd from gen.py: builds tomb.py -> tomb.pd, the TOMBOLA sequencer (3rd page of SEQ, AUX+E cycles the pages)
# A spinning polygon (3..8 sides) with up to 8 balls under gravity. Each key throws a ball carrying that note;
# a ball hitting a wall plays its note (velocity from the impact) on the active instrument, through seq-notes.
# Knobs: 1 rotation (centre = still) 2 gravity 3 bounce 4 sides.  AUX+A# remove last ball, AUX+B remove all,
# AUX+C5 pause. Physics at ~33 ticks/s only while there are balls; the screen redraws ~11 fps, polygon area only.
import math

NB = 8                  # max balls
RC = 25                 # polygon circumradius on screen (px)
CX, CY = 38, 37         # polygon centre on screen
TICK = 30               # ms
RB = 1.5                # ball radius (physics)


def E(s):
    """natural expression text -> Pd expr text (escaped commas / semicolons)"""
    return s.replace(",", " \\, ").replace(";", " \\; ")


def osc7(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


tb = Patch(2400, 1600)
tb.text(20, 5, "tomb: TOMBOLA - spinning polygon with note balls. keys = throw a ball - AUX+A# last ball off - "
               "AUX+B all off - AUX+C5 pause. knobs: 1 spin 2 gravity 3 bounce 4 sides")
for i, nm in enumerate(("tmbx", "tmby", "tmbvx", "tmbvy", "tmbnt", "tmbnx", "tmbny", "tmbpen", "tmbphi", "tmbk")):
    tb.obj(20 + i * 100, 30, f"table {nm} {NB}")
tb.obj(820, 30, "table tmbp 9")        # 0 angle 1 spin (rad/tick) 2 gravity 3 bounce 4 sides 5 apothem 6 run 7 balls 8 page shown
lb = tb.obj(20, 60, "loadbang")
lbT = tb.obj(20, 90, "t b b")
tb.c(lb, lbT)
init = tb.msg(120, 90, f"\\; tmbnt const 0 \\; tmbp 0 0 0.02 0.3 0.72 6 {RC * math.cos(math.pi / 6):.3f} 1 0")
tb.c(lbT, init, 1)
tb.c(tb.obj(300, 60, "r nst-load"), tb.msg(300, 90, "\\; tmbnt const 0 \\; tomb-count bang"))

# ------------------------------------------------ page active (SEQ mode, page 2)
actE = tb.obj(20, 140, "expr $f1==4 && $f2==2")
mT = tb.obj(20, 120, "t f")
tb.c(tb.obj(20, 110, "r mode"), mT); tb.c(mT, actE, 0, 0)
pgT = tb.obj(120, 120, "t b f")
tb.c(tb.obj(120, 110, "r seq-page"), pgT); tb.c(pgT, actE, 1, 1); tb.c(pgT, actE, 0, 0)
actF = tb.obj(20, 170, "change")
tb.c(actE, actF)
# the TOMBOLA plays only while its page is shown (leaving the page pauses it, the balls stay)
actO = tb.obj(20, 185, "t f f")                  # 1) page gates  0) then tmbp 8 / redraw request (apply_tombleave.py)
tb.c(actF, actO)
tb.c(actO, tb.msg(250, 170, "\\; tmbp 8 \\$1 \\; tomb-count bang"), 0)
actT = tb.obj(20, 200, "t f f f")
tb.c(actO, actT, 1)
textDirty = tb.obj(300, 200, "f 1")
one = tb.msg(250, 200, "1")
tb.c(one, textDirty, 0, 1)
entS = tb.obj(150, 230, "sel 1")
tb.c(actT, entS, 0); tb.c(entS, one)

# ------------------------------------------------ knobs (tomb-knob from the router, tomb-set from the project)
rk = tb.obj(500, 60, "r tomb-knob")
krt = tb.obj(500, 90, "route 1 2 3 4")
tb.c(rk, krt); tb.c(tb.obj(600, 60, "r tomb-set"), krt)   # [r name] has no inlet: both feed the route
# 1 spin: centre snaps to 0, max 0.12 rad/tick either way
k1 = tb.obj(500, 120, "expr " + E("if(abs($f1-0.5)<0.04, 0, ($f1-0.5)*0.24)"))
k2 = tb.obj(620, 120, "expr $f1*0.6")
k3 = tb.obj(740, 120, "expr 0.3+$f1*0.7")
k4 = tb.obj(860, 120, "expr 3+int($f1*5.99)")
for i, (k, idx) in enumerate(((k1, 1), (k2, 2), (k3, 3), (k4, 4))):
    tb.c(krt, k, i)
    m = tb.msg(500 + i * 120, 150, f"\\; tmbp {idx} \\$1")
    tb.c(k, m); tb.c(k, one)
apo = tb.obj(860, 180, "expr " + E(f"{RC}*cos(3.14159265/$f1)"))
tb.c(k4, apo); tb.c(apo, tb.msg(860, 210, "\\; tmbp 5 \\$1"))

# ------------------------------------------------ throwing / removing balls
rn = tb.obj(1100, 60, "r notes")
nu = tb.obj(1100, 90, "unpack f f")
tb.c(rn, nu)
nOn = tb.obj(1180, 120, "> 0")
nSp = tb.obj(1100, 150, "spigot")
nSp2 = tb.obj(1100, 180, "spigot")
tb.c(nu, nOn, 1); tb.c(nOn, nSp, 0, 1); tb.c(nu, nSp, 0); tb.c(nSp, nSp2)
tb.c(actT, nSp2, 1, 1)
nxtF = tb.obj(1300, 240, "f 0")            # slot for the next ball (oldest is replaced)
thT = tb.obj(1100, 210, "t b f b")          # randoms first, then the note (cold), then the slot (hot)
nSpA = tb.obj(1100, 195, "spigot 1")                # AUX up only (apply_tombaux.py)
auxUp = tb.obj(1200, 165, "== 0")
tb.c(tb.obj(1200, 140, "r aux"), auxUp); tb.c(auxUp, nSpA, 0, 1)
tb.c(nSp2, nSpA); tb.c(nSpA, thT)
tb.c(thT, nxtF, 0)
rx = tb.obj(1200, 240, "random 801"); ry = tb.obj(1200, 270, "random 801")
tb.c(thT, rx, 2); tb.c(thT, ry, 2)
nxtT = tb.obj(1300, 270, "t f f")
tb.c(nxtF, nxtT)
nxtInc = tb.obj(1380, 300, "expr ($f1+1)%" + str(NB))
tb.c(nxtT, nxtInc, 0); tb.c(nxtInc, nxtF, 0, 1)
# slot note x vx -> tables ; ball starts near the centre, thrown up with a random sideways speed
thE = tb.obj(1100, 330, "expr " + E("$f1; $f2; ($f3-400)/100; -1.5; ($f4-400)/250"))
thP2 = tb.obj(1100, 300, "pack f f f f")
tb.c(nxtT, thP2, 1, 0); tb.c(thT, thP2, 1, 1); tb.c(rx, thP2, 0, 2); tb.c(ry, thP2, 0, 3)
tb.c(thP2, thE)
thM = tb.obj(1100, 360, "pack f f f f f")
for o in range(5):
    tb.c(thE, thM, o, o)
tb.c(thM, tb.msg(1100, 390, "\\; tmbnt \\$1 \\$2 \\; tmbx \\$1 \\$3 \\; tmby \\$1 \\$4 \\; tmbvx \\$1 \\$5 \\; tmbvy \\$1 -1.5 \\; tomb-count bang"))
tb.c(thM, one)
# AUX keys: 70 last ball off, 71 all off, 72 pause
rak = tb.obj(1500, 60, "r aux-key")
akSp = tb.obj(1500, 90, "spigot")
tb.c(rak, akSp); tb.c(actT, akSp, 2, 1)
aks = tb.obj(1500, 120, "sel 70 71 72")
tb.c(akSp, aks)
lastE = tb.obj(1500, 160, "expr ($f1+" + str(NB - 1) + ")%" + str(NB))
lastF = tb.obj(1500, 140, "f")
tb.c(aks, lastF, 0); tb.c(nxtF, lastF, 0, 1); tb.c(lastF, lastE)
lastT = tb.obj(1500, 190, "t f f")
tb.c(lastE, lastT)
tb.c(lastT, nxtF, 0, 1)
tb.c(lastT, tb.msg(1500, 220, "\\; tmbnt \\$1 0 \\; tomb-count bang"), 1)
allM = tb.msg(1600, 160, "\\; tmbnt const 0 \\; tomb-count bang")
tb.c(aks, allM, 1)
tb.c(allM, tb.msg(1700, 190, "0"))
z0 = tb.msg(1650, 190, "0")
tb.c(aks, z0, 1); tb.c(z0, nxtF, 0, 1)
runE = tb.obj(1750, 160, "expr tmbp[6]==0")
tb.c(aks, runE, 2)
runT = tb.obj(1750, 175, "t f b")
tb.c(runE, runT); tb.c(runT, one, 1)
tb.c(runT, tb.msg(1750, 190, "\\; tmbp 6 \\$1 \\; tomb-count bang"), 0)
tb.c(lastT, one)
tb.c(aks, one, 1)

# ------------------------------------------------ the clock: runs while there are balls and not paused
cnt = tb.obj(1900, 60, "r tomb-count")
cntE = tb.obj(1900, 90, "expr " + E("(" + "+".join(f"(tmbnt[{i}]>0)" for i in range(NB)) + ")"))
tb.c(cnt, cntE)
cntT = tb.obj(1900, 120, "t f f")
tb.c(cntE, cntT)
tb.c(cntT, tb.msg(2000, 150, "\\; tmbp 7 \\$1"), 1)
cntOn = tb.obj(1900, 150, "expr $f1>0 && tmbp[6]>0 && tmbp[8]>0")   # balls, not paused, page shown
cntC = tb.obj(1900, 180, "change")
tb.c(cntT, cntOn, 0); tb.c(cntOn, cntC)
mtr = tb.obj(1900, 210, f"metro {TICK / NB}")          # one ball per slot
tb.c(cntC, mtr)
# when the page is entered while stopped, draw once
fr0 = tb.obj(2100, 230, "t b")
tb.c(entS, fr0)
# also redraw once when something changes while the clock is stopped (pause, knobs, balls removed)
tb.c(cnt, fr0)
kSp = tb.obj(2200, 230, "spigot 1")
kNot = tb.obj(2200, 200, "== 0")
tb.c(cntOn, kNot); tb.c(kNot, kSp, 0, 1)
for k in (k1, k2, k3, k4):
    tb.c(k, kSp)
tb.c(kSp, fr0)

slF = tb.obj(1900, 240, "f 0")
slI = tb.obj(1960, 240, "+ 1")
slM = tb.obj(2020, 240, f"mod {NB}")
slT = tb.obj(1900, 260, "t f f f")
tb.c(mtr, slF); tb.c(slF, slT)
tb.c(slT, slI, 2); tb.c(slI, slM); tb.c(slM, slF, 0, 1)
slS = tb.obj(2000, 280, "sel 0 2 5")
tb.c(slT, slS, 1)
# rotation
rotE = tb.obj(2100, 270, "expr " + E("tmbp[0]+tmbp[1]+if(tmbp[0]+tmbp[1]>6.2831853, -6.2831853, if(tmbp[0]+tmbp[1]<0, 6.2831853, 0))"))
tb.c(slS, rotE, 0)
tb.c(rotE, tb.obj(2100, 300, "tabwrite tmbp"))

# per-ball physics
bT = tb.obj(1900, 370, "t f f")
tb.c(slT, bT, 0)
actB = tb.obj(2000, 400, "expr tmbnt[$f1]>0")
bSp = tb.obj(1900, 430, "spigot")
tb.c(bT, actB, 1); tb.c(actB, bSp, 0, 1); tb.c(bT, bSp, 0)
# per ball, in order: slot for the note, A move, B0 sector angle, Bk best of 3 walls, B1 normal+penetration, B2 bounce
ball = tb.obj(1900, 460, "t f f f f f f f")       # 7 outlets: 6 slot, 5..1 passes, 0 unused
tb.c(bSp, ball)


nearT = tb.obj(2100, 470, "t f f")
tb.c(ball, nearT, 4)
nearE = tb.obj(2200, 490, "expr " + E(f"tmbx[$f1]*tmbx[$f1]+tmby[$f1]*tmby[$f1]>(tmbp[5]-9)*(tmbp[5]-9)"))
nearSp = tb.obj(2100, 500, "spigot")
tb.c(nearT, nearE, 1); tb.c(nearE, nearSp, 0, 1); tb.c(nearT, nearSp, 0)
wall = tb.obj(2100, 530, "t f f f f")             # B0 Bk B1 B2


def bpass(o, y, text, tables, src=None):
    """ball index -> set the tabwrite indices, then evaluate the expr and write its outlets to tables"""
    ws = [tb.obj(1900 + j * 90, y + 30, f"tabwrite {nm}") for j, nm in enumerate(tables)]
    idx = tb.obj(2400, y - 20, "t " + " ".join(["f"] * (len(tables) + 1)))
    tb.c(src if src is not None else ball, idx, o)
    for j, w in enumerate(ws):
        tb.c(idx, w, j + 1, 1)
    e = tb.obj(1900, y, "expr " + E(text))
    tb.c(idx, e, 0)
    # expr evaluates each outlet only when it sends it (right to left): writing a table from one outlet would
    # change what the next outlets read. Collect all results first, then write.
    nout = text.count(";") + 1
    pk = tb.obj(1900, y + 10, "pack " + " ".join(["f"] * nout))
    up = tb.obj(1900, y + 20, "unpack " + " ".join(["f"] * nout))
    for j in range(nout):
        tb.c(e, pk, j, j)
    tb.c(pk, up)
    for j, w in enumerate(ws):
        tb.c(up, w, j, 0)
    return up


S = "(6.2831853/tmbp[4])"
# A: x += vx ; vy += g ; y += vy
bpass(5, 520, "tmbx[$f1]+tmbvx[$f1]; tmby[$f1]+tmbvy[$f1]+tmbp[2]; tmbvy[$f1]+tmbp[2]", ("tmbx", "tmby", "tmbvy"))
# B0: centre angle of the wall in the ball's sector
tb.c(nearSp, wall)
bpass(3, 580, f"tmbp[0]+(floor((atan2(tmby[$f1], tmbx[$f1])-tmbp[0])/{S})+0.5)*{S}", ("tmbphi",), wall)
# Bk: near a corner the neighbouring wall can be the one crossed: keep the wall with the largest penetration
D = lambda k: f"(tmbx[$f1]*cos(tmbphi[$f1]+({k})*{S})+tmby[$f1]*sin(tmbphi[$f1]+({k})*{S}))"
bpass(2, 640, f"if({D(-1)}>{D(0)} && {D(-1)}>={D(1)}, -1, if({D(1)}>{D(0)}, 1, 0))", ("tmbk",), wall)
# B1: normal and penetration of that wall
PHI = f"(tmbphi[$f1]+tmbk[$f1]*{S})"
bpass(1, 700, f"cos({PHI}); sin({PHI}); tmbx[$f1]*cos({PHI})+tmby[$f1]*sin({PHI})+{RB}-tmbp[5]", ("tmbnx", "tmbny", "tmbpen"), wall)
# B2: bounce (only when moving into the wall), spin kick from the moving wall, push back inside, clamp speed
VN = "(tmbvx[$f1]*tmbnx[$f1]+tmbvy[$f1]*tmbny[$f1])"
HIT = f"(tmbpen[$f1]>0 && {VN}>0)"
IN = "(tmbpen[$f1]>0)"
vx2 = f"max(-7, min(7, tmbvx[$f1]-{HIT}*(1+tmbp[3])*{VN}*tmbnx[$f1]-{IN}*0.3*tmbp[1]*tmby[$f1]))"
vy2 = f"max(-7, min(7, tmbvy[$f1]-{HIT}*(1+tmbp[3])*{VN}*tmbny[$f1]+{IN}*0.3*tmbp[1]*tmbx[$f1]))"
x2 = f"tmbx[$f1]-{IN}*tmbpen[$f1]*tmbnx[$f1]"
y2 = f"tmby[$f1]-{IN}*tmbpen[$f1]*tmbny[$f1]"
pB2 = bpass(0, 760, f"{x2}; {y2}; {vx2}; {vy2}; {HIT}*{VN}", ("tmbx", "tmby", "tmbvx", "tmbvy"), wall)
# a real hit plays the ball's note: velocity from the impact speed, ~150 ms long
slotH = tb.obj(2300, 820, "f")
tb.c(ball, slotH, 6, 1)                         # rightmost outlet fires first: the hit below reads this ball's slot
hitE = tb.obj(1900, 790, "expr " + E("$f1>tmbp[2]*2+0.2"))
hitS = tb.obj(1900, 820, "sel 1")
strF = tb.obj(2000, 820, "f")
stT = tb.obj(2000, 790, "t f f")
tb.c(pB2, stT, 4); tb.c(stT, strF, 1, 1); tb.c(stT, hitE, 0); tb.c(hitE, hitS)
hitT = tb.obj(1900, 850, "t b b")
tb.c(hitS, hitT)
tb.c(hitT, slotH, 0)                           # strength (cold) first, then the slot (hot)
nvE = tb.obj(1900, 910, "expr " + E("tmbnt[$f1]; min(127, 45+$f2*22)"))
tb.c(slotH, nvE)
tb.c(hitT, strF, 1); tb.c(strF, nvE, 0, 1)
nvP = tb.obj(1900, 940, "pack f f")
tb.c(nvE, nvP, 1, 1); tb.c(nvE, nvP, 0, 0)
nvT = tb.obj(1900, 970, "t l l")
tb.c(nvP, nvT)
tb.c(nvT, tb.obj(1900, 1060, "s seq-notes"), 0)
offU = tb.obj(2000, 1000, "unpack f f")
tb.c(nvT, offU, 1)
offPp = tb.obj(2000, 1030, "pipe 150")
tb.c(offU, offPp, 0)
offP = tb.msg(2000, 1060, "\\$1 0")
tb.c(offPp, offP); tb.c(offP, tb.obj(2000, 1090, "s seq-notes"))

# ------------------------------------------------ screen (page active): every 3rd tick, or once on entry
frC = tb.obj(1700, 300, "f 0")
frI = tb.obj(1760, 300, "+ 1")
tb.c(slS, frC, 0); tb.c(frC, frI); tb.c(frI, frC, 0, 1)
frM = tb.obj(1700, 330, "mod 3")
tb.c(frI, frM)
frS = tb.obj(1700, 360, "sel 0")
tb.c(frM, frS)
frSp = tb.obj(1700, 390, "spigot")
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
        tb.c(gS, d0)
# text part (title + values) only when something changed; otherwise just wipe the polygon area
tdS = tb.obj(1500, 450, "sel 1 0")
tb.c(dA, textDirty, 1); tb.c(textDirty, tdS)
tz = tb.msg(1600, 450, "0")
tb.c(tdS, tz, 0); tb.c(tz, textDirty, 0, 1)
txE = tb.obj(1500, 480, "expr " + E("int(tmbp[1]*100/1.2+0.5*(tmbp[1]>0)-0.5*(tmbp[1]<0)); int(tmbp[2]/0.6*100+0.5); "
                                    "int((tmbp[3]-0.3)/0.7*100+0.5); tmbp[4]; tmbp[7]; tmbp[6]"))
tb.c(tdS, txE, 0)
txP = tb.obj(1500, 510, "pack f f f f f f")
for o in range(6):
    tb.c(txE, txP, o, o)
txT = tb.obj(1400, 525, "t b l")
tb.c(txP, txT)
tb.c(txT, tb.msg(1500, 540,
                 osc7("gShowInfoBar", "ii", "0") + " " + osc7("gClear", "ii", "1") + " " +
                 osc7("gPrintln", "iiiiis", "1 1 8 1 TOMBOLA") + " " +
                 osc7("gPrintln", "iiiiisf", "80 14 8 1 SPIN \\$1") + " " +
                 osc7("gPrintln", "iiiiisf", "80 26 8 1 GRAV \\$2") + " " +
                 osc7("gPrintln", "iiiiisf", "80 38 8 1 BNCE \\$3") + " " +
                 osc7("gPrintln", "iiiiisf", "80 50 8 1 SIDE \\$4") + " " +
                 osc7("gPrintln", "iiiiisf", "68 1 8 1 balls \\$5")), 1)
pauE = tb.obj(1400, 570, "expr tmbp[6]")
tb.c(txT, pauE, 0)
pauS = tb.obj(1500, 570, "sel 0")
tb.c(pauE, pauS)
tb.c(pauS, tb.msg(1500, 600, osc7("gFillArea", "iiiiii", "68 0 60 10 1") + " " + osc7("gPrintln", "iiiiis", "70 1 8 0 PAUSE")))
tb.c(tdS, tb.msg(1650, 480, osc7("gFillArea", "iiiiii", f"0 11 {CX + RC + 4} {64 - 11} 0")), 1)
# polygon edges
pgN = tb.obj(1700, 640, "expr tmbp[4]")
pgZ = tb.msg(1760, 640, "0")
pgTT = tb.obj(1700, 610, "t b b")
tb.c(dA, pgTT, 0)
tb.c(pgTT, pgZ, 1); tb.c(pgTT, pgN, 0)
pgU = tb.obj(1700, 670, "until"); pgC = tb.obj(1700, 700, "f"); pgC1 = tb.obj(1760, 700, "+ 1")
tb.c(pgZ, pgC, 0, 1); tb.c(pgN, pgU); tb.c(pgU, pgC); tb.c(pgC, pgC1); tb.c(pgC1, pgC, 0, 1)
A0 = "(tmbp[0]+$f1*6.2831853/tmbp[4])"
A1 = "(tmbp[0]+($f1+1)*6.2831853/tmbp[4])"
pgE = tb.obj(1700, 730, "expr " + E(f"int({CX}+{RC}*cos({A0})+0.5); int({CY}+{RC}*sin({A0})+0.5); "
                                    f"int({CX}+{RC}*cos({A1})+0.5); int({CY}+{RC}*sin({A1})+0.5)"))
tb.c(pgC, pgE)
pgP = tb.obj(1700, 760, "pack f f f f")
for o in range(4):
    tb.c(pgE, pgP, o, o)
tb.c(pgP, tb.msg(1700, 790, osc7("gLine", "iiiiii", "\\$1 \\$2 \\$3 \\$4 1")))
# balls
blT = tb.obj(1500, 640, "t b b")
tb.c(dB, blT, 1)
bl8 = tb.msg(1500, 670, str(NB)); blZ = tb.msg(1560, 670, "0")
blU = tb.obj(1500, 700, "until"); blC = tb.obj(1500, 730, "f"); blC1 = tb.obj(1560, 730, "+ 1")
tb.c(blT, blZ, 1); tb.c(blZ, blC, 0, 1); tb.c(blT, bl8, 0); tb.c(bl8, blU); tb.c(blU, blC); tb.c(blC, blC1); tb.c(blC1, blC, 0, 1)
blE = tb.obj(1500, 760, "expr " + E(f"tmbnt[$f1]>0; int({CX}+tmbx[$f1]-1+0.5); int({CY}+tmby[$f1]-1+0.5)"))
tb.c(blC, blE)
blP = tb.obj(1500, 790, "pack f f f")
for o in range(3):
    tb.c(blE, blP, o, o)
blR = tb.obj(1500, 820, "route 1")
tb.c(blP, blR)
tb.c(blR, tb.msg(1500, 850, osc7("gFillArea", "iiiiii", "\\$1 \\$2 3 3 1")))
tb.c(dB, tb.msg(1700, 850, "\\; oscOut sendtyped /oled/gFlip i 3"), 0)
tb.save("tomb.pd")

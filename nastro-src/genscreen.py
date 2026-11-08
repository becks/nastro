# exec'd from gen.py: builds tape-screen.pd (OLED graphics for TAPE mode)
# Organelle OS graphics: /oled/g* on screen 3 (patch screen), shown on gFlip.
N = 2646000
CY = 27            # reel centre y
LX, RX = 32, 96    # reel centre x


def osc(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


g = Patch(1400, 900)
g.text(20, 5, "tape-screen: draws the TAPE page on the OLED (20 fps while in TAPE mode)")

# --- enter / leave TAPE mode
rm = g.obj(20, 40, "r mode")
eq2 = g.obj(20, 70, "== 2")
tm = g.obj(20, 100, "t f f")
mt = g.obj(20, 130, "metro 100")
selib = g.obj(120, 130, "sel 1 0")
hideBar = g.msg(120, 160, osc("gShowInfoBar", "ii", "0"))
showBar = g.msg(260, 160, osc("gShowInfoBar", "ii", "1"))
g.c(rm, eq2); g.c(eq2, tm); g.c(tm, selib, 1); g.c(tm, mt, 0)
# info bar is handled in main.pd

# --- stored state
def store(x, name, init=None):
    r = g.obj(x, 220, f"r {name}")
    f = g.obj(x, 250, "f" if init is None else f"f {init}")
    g.c(r, f, 0, 1)
    return f

sr = g.obj(1100, 40, "loadbang")
srt = g.obj(1100, 70, "samplerate~")
fPos = store(20, "tp-pos")
fPlay = store(120, "tp-play")
fRec = store(220, "tp-rec")
fTrk = store(320, "tp-trk", 1)
fSpd = store(420, "tp-spd", 1)
fLs = store(520, "tp-ls")
fLo = store(620, "tp-lo")
fHi = store(720, "tp-hi", N)
fIn = store(820, "tp-in")
g.c(sr, srt)

# --- frame sequence (fires left-to-right in this list)
steps = []
ask = g.obj(20, 330, "s tp-ask"); steps.append(ask)
clr = g.msg(20, 360, osc("gClear", "ii", "1")); steps.append(clr)

# reels: radius follows how much tape is on each side, angle follows position
pT = g.obj(20, 420, "t f f")
radE = g.obj(160, 450, f"expr int(7+7*(1-$f1/{N})) \\; int(7+7*$f1/{N})")
angE = g.obj(20, 450, "expr $f1/$f2*3.77")
g.c(srt, angE, 0, 1)
g.c(fPos, pT); g.c(pT, radE, 1); g.c(pT, angE, 0)
steps.append(fPos)

for side, cx, outl in (("L", LX, 0), ("R", RX, 1)):
    x0 = 160 + outl * 520
    rT = g.obj(x0, 490, "t f f f f f")
    g.c(radE, rT, outl)
    circ = g.msg(x0, 520, osc("gCircle", "iiiii", f"{cx} {CY} \\$1 1"))
    g.c(rT, circ, 4)
    # tape from the bottom of the reel to the head
    py = g.obj(x0 + 120, 520, f"+ {CY}")
    if side == "L":
        tl = g.msg(x0 + 120, 550, osc("gLine", "iiiiii", f"{cx} \\$1 59 45 1"))
    else:
        tl = g.msg(x0 + 120, 550, osc("gLine", "iiiiii", f"68 45 {cx} \\$1 1"))
    g.c(rT, py, 3); g.c(py, tl)
    aE = g.obj(x0, 580, "expr $f1*14/$f2")
    g.c(rT, aE, 2, 1)
    aT = g.obj(x0, 610, "t f f f")
    g.c(aE, aT)
    for k in range(3):
        off = round(k * 2.0944, 4)
        sp = g.obj(x0 + k * 10, 650 + k * 60,
                   f"expr int({cx}+3*cos($f1+{off})) \\; int({CY}+3*sin($f1+{off})) \\; "
                   f"int({cx}+($f2-1)*cos($f1+{off})) \\; int({CY}+($f2-1)*sin($f1+{off}))")
        g.c(rT, sp, 1, 1)  # radius (cold) first
        pk = g.obj(x0 + k * 10, 680 + k * 60, "pack f f f f")
        for o in range(4):
            g.c(sp, pk, o, o)
        ln = g.msg(x0 + 200, 680 + k * 60, osc("gLine", "iiiiii", "\\$1 \\$2 \\$3 \\$4 1"))
        g.c(pk, ln); g.c(aT, sp, 2 - k)
    angT = angE if side == "L" else None
    # angle into this reel (after radius already set)
    g.c(angE, aE, 0, 0)

# static parts: hubs, head, timeline frame
static = g.msg(20, 780, " ".join([
    osc("gCircle", "iiiii", f"{LX} {CY} 3 1"),
    osc("gCircle", "iiiii", f"{RX} {CY} 3 1"),
    osc("gFillArea", "iiiiii", "59 43 10 4 1"),
    osc("gBox", "iiiiii", "0 55 128 9 1"),
]))
steps.append(static)

# top bar: state (REC blinks), track, speed, time
blinkC = g.obj(300, 330, "f")
blinkP = g.obj(340, 330, "+ 1")
blinkM = g.obj(300, 360, "% 10")
blinkL = g.obj(300, 390, "< 6")
g.c(blinkC, blinkP); g.c(blinkP, blinkM); g.c(blinkM, blinkC, 0, 1); g.c(blinkM, blinkL)
stE = g.obj(300, 420, "expr $f1 + 2*$f2 + 4*($f2 && $f3)")
g.c(blinkL, stE, 0, 2)
stT = g.obj(300, 300, "t b b b")
g.c(stT, blinkC, 2); g.c(stT, fRec, 1); g.c(stT, fPlay, 0)
g.c(fRec, stE, 0, 1); g.c(fPlay, stE, 0, 0)
stSel = g.obj(300, 450, "sel 0 1 3 7 2 6")
g.c(stE, stSel)
txt = {
    0: osc("gPrintln", "iiiiis", "1 1 8 1 STOP"),
    1: osc("gPrintln", "iiiiis", "1 1 8 1 PLAY"),
    3: osc("gPrintln", "iiiiis", "1 1 8 1 REC"),
    7: osc("gFillArea", "iiiiii", "0 0 19 10 1") + " " + osc("gPrintln", "iiiiis", "1 1 8 0 REC"),
}
for i, code in enumerate([0, 1, 3, 7]):
    m = g.msg(300 + i * 160, 480, txt[code])
    g.c(stSel, m, i)
    if code == 3:
        g.c(stSel, m, 4)   # rec while stopped (shouldn't happen) -> plain
    if code == 7:
        g.c(stSel, m, 5)
steps.append(stT)

trk = g.msg(300, 520, osc("gPrintln", "iiiiisi", "34 1 8 1 T \\$1"))
g.c(fTrk, trk); steps.append(fTrk)

spdS = g.obj(500, 520, "sel 1")
spdM = g.msg(500, 550, osc("gPrintln", "iiiiisf", "56 1 8 1 x\\$1"))
g.c(fSpd, spdS); g.c(spdS, spdM, 1); steps.append(fSpd)

timeT = g.obj(700, 300, "t b")
fPos2 = g.obj(700, 330, "f")
g.c(g.obj(700, 270, "r tp-pos"), fPos2, 0, 1)
secE = g.obj(700, 360, "expr int($f1/$f2*10)/10")
g.c(srt, secE, 0, 1)
secM = g.msg(700, 390, osc("gPrintln", "iiiiif", "100 1 8 1 \\$1"))
g.c(timeT, fPos2); g.c(fPos2, secE); g.c(secE, secM); steps.append(timeT)

# timeline: loop region, loop-in marker, playhead
lsS = g.obj(900, 300, "sel 1 2")
g.c(fLs, lsS); steps.append(fLs)
inX = g.obj(900, 330, "expr 1+min(124 \\, max(0 \\, int(($f1-$f2)/max(1 \\, $f3-$f2)*125)))")
g.c(g.obj(980, 300, "r tp-vs"), inX, 0, 1); g.c(g.obj(1060, 300, "r tp-ve"), inX, 0, 2)
inM = g.msg(900, 360, osc("gLine", "iiiiii", "\\$1 53 \\$1 63 1"))
g.c(lsS, fIn, 0); g.c(fIn, inX); g.c(inX, inM)
lpT = g.obj(1000, 330, "t b b")
g.c(lsS, lpT, 1)
lpM = g.msg(1000, 450, osc("gPrintln", "iiiiis", "104 47 8 1 LOOP"))
g.c(lpT, lpM, 0)

# timeline: 4 track lanes (computed by tape-map) + playhead on the same view
phT = g.obj(1150, 300, "t b b")
lnT = g.obj(1250, 330, "t b b")
lnZ = g.msg(1350, 360, "0")
lnS = g.obj(1250, 360, "text size nst-lanes")
lnU = g.obj(1250, 390, "until")
lnC = g.obj(1250, 420, "f")
lnC1 = g.obj(1300, 420, "+ 1")
lnG = g.obj(1250, 450, "text get nst-lanes")
lnM = g.msg(1250, 480, osc("gLine", "iiiiii", "\\$1 \\$2 \\$3 \\$2 1"))
g.c(phT, lnT, 1); g.c(lnT, lnZ, 1); g.c(lnZ, lnC, 0, 1); g.c(lnT, lnS, 0)
g.c(lnS, lnU); g.c(lnU, lnC); g.c(lnC, lnC1); g.c(lnC1, lnC, 0, 1); g.c(lnC, lnG); g.c(lnG, lnM)
fPos3 = g.obj(1150, 390, "f")
g.c(g.obj(1150, 360, "r tp-pos"), fPos3, 0, 1)
phX = g.obj(1150, 420, "expr 1+min(124 \\, max(0 \\, int(($f1-$f2)/max(1 \\, $f3-$f2)*125)))")
g.c(g.obj(1150, 330, "r tp-vs"), phX, 0, 1); g.c(g.obj(1200, 330, "r tp-ve"), phX, 0, 2)
phM = g.msg(1150, 450, osc("gInvertArea", "iiiii", "\\$1 54 2 10"))
g.c(phT, fPos3, 0); g.c(fPos3, phX); g.c(phX, phM)
steps.append(phT)

# overdub amount, bottom left above the timeline
fDub = g.obj(1300, 330, "f 1")
g.c(g.obj(1300, 300, "r tp-dub"), fDub, 0, 1)
dubE = g.obj(1300, 360, "expr int($f1*100+0.5)")
g.c(fDub, dubE)
g.c(dubE, g.msg(1300, 390, osc("gPrintln", "iiiiisf", "1 47 8 1 DUB \\$1")))
steps.append(fDub)
# wow amount, bottom row middle (apply_wowscreen.py)
fWow = g.obj(1450, 330, "f 0")
g.c(g.obj(1450, 300, "r tp-wow"), fWow, 0, 1)
wowE = g.obj(1450, 360, "expr int($f1*100+0.5)")
g.c(fWow, wowE)
g.c(wowE, g.msg(1450, 390, osc("gPrintln", "iiiiisf", "52 47 8 1 WOW \\$1")))
steps.append(fWow)
flip = g.msg(1150, 450, "\\; oscOut sendtyped /oled/gFlip i 3")
steps.append(flip)

seq = g.obj(20, 300, "t " + " ".join(["b"] * len(steps)))
dOne = g.msg(1520, 120, "1")
dF = g.obj(1400, 180, "f 1")
g.c(dOne, dF, 0, 1)
dSel = g.obj(1400, 210, "sel 1")
dTT = g.obj(1400, 240, "t b b")
dZero = g.msg(1520, 240, "0")
g.c(dF, dSel); g.c(dSel, dTT); g.c(dTT, dZero, 1); g.c(dZero, dF, 0, 1); g.c(dTT, seq, 0)
g.c(g.obj(1600, 90, "r tp-play"), dOne)
g.c(g.obj(1690, 90, "r tp-rec"), dOne)
g.c(g.obj(1780, 90, "r tp-trk"), dOne)
g.c(g.obj(1870, 90, "r tp-spd"), dOne)
g.c(g.obj(1960, 90, "r tp-ls"), dOne)
g.c(g.obj(2050, 90, "r tp-lo"), dOne)
g.c(g.obj(2140, 90, "r tp-hi"), dOne)
g.c(g.obj(2230, 90, "r tp-in"), dOne)
g.c(g.obj(2320, 90, "r tp-vs"), dOne)
g.c(g.obj(2410, 90, "r tp-ve"), dOne)
g.c(g.obj(2500, 90, "r tp-lanes"), dOne)
g.c(g.obj(2590, 90, "r mode"), dOne)
g.c(g.obj(2680, 90, "r nst-redraw"), dOne)
gT = g.obj(1400, 150, "t b b")
g.c(mt, gT)
g.c(gT, g.obj(1460, 150, "s tp-ask"), 1)
gPos = g.obj(1700, 150, "f")
g.c(g.obj(1700, 120, "r tp-pos"), gPos, 0, 1)
gPT = g.obj(1700, 180, "t b f")
gChg = g.obj(1800, 210, "change")
g.c(gT, gPos, 0); g.c(gPos, gPT); g.c(gPT, gChg, 1); g.c(gChg, dOne); g.c(gPT, dF, 0)
for i, st in enumerate(steps):
    g.c(seq, st, len(steps) - 1 - i)
g.c(g.obj(1600, 90, "r tp-dub"), dOne)
g.c(g.obj(1650, 60, "r tp-wow"), dOne)
g.save("tape-screen.pd")

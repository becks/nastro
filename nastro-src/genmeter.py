# exec'd from gen.py: builds meter.pd - master output meter in the title row of the MIX level page
# (little segment lights). 2 rows (L y=1, R y=5) of 12 segments, -30..0 dBFS, falling one segment per frame,
# plus a LIM light when the limiter is working. 10 fps; only segments that change are drawn.
# Inputs: [r nst-outL] [r nst-outR] (env~ dB, 100 = 0 dBFS), [r nst-lim-gain], [r mt-reset] (screen was cleared).
THR = [-30, -27, -24, -21, -18, -15, -12, -9, -6, -4, -2, -0.5]   # dBFS for segments 1..12
X0, SW, SWL, SH = 34, 7, 6, 3                                        # first x, pitch, lit width, row height
LX = 121                                                             # LIM light x (6 x 7 px)


def E(s):
    return s.replace(",", " \\, ").replace(";", " \\; ")


def oscm(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


mt = Patch(1600, 900)
mt.text(20, 5, "meter: master output lights on the MIX page title row - L and R 12 segments + LIM")
mt.obj(20, 30, "table mtcur 3")                      # shown state: 0 L segments, 1 R segments, 2 LIM light
# running only while the MIX level page is shown
onE = mt.obj(20, 120, "expr $f1==3 && $f2==0")
mT = mt.obj(20, 90, "t f")
mt.c(mt.obj(20, 60, "r mode"), mT); mt.c(mT, onE, 0, 0)
pT = mt.obj(120, 90, "t b f")
mt.c(mt.obj(120, 60, "r mix-page"), pT); mt.c(pT, onE, 1, 1); mt.c(pT, onE, 0, 0)
met = mt.obj(20, 150, "metro 100")
mt.c(onE, met)
tick = mt.obj(20, 180, "t b b b b")                  # 3 L, 2 R, 1 LIM, 0 flip if something was drawn
mt.c(met, tick)
# the MIX page cleared the screen: nothing is lit any more
mt.c(mt.obj(300, 60, "r mt-reset"), mt.msg(300, 90, "\\; mtcur 0 0 0 0"))
# flip once per frame, only if something was drawn
chg = mt.obj(1200, 180, "f 0")
one = mt.msg(1300, 150, "1")
mt.c(one, chg, 0, 1)
chS = mt.obj(1200, 210, "sel 1")
mt.c(tick, chg, 0); mt.c(chg, chS)
zero = mt.msg(1300, 210, "0")
mt.c(chS, zero); mt.c(zero, chg, 0, 1)
mt.c(chS, mt.msg(1200, 240, "\\; oscOut sendtyped /oled/gFlip i 3"))


def lights(src, x, ch, n_expr, falls, y, first_x, pitch, width, height):
    """src outputs a level -> n (how many lit) -> draw the difference from mtcur[ch], store the new state"""
    nE = mt.obj(x, 250, "expr " + E(n_expr))
    mt.c(src, nE)
    TG = f"max($f1, mtcur[{ch}]-1)" if falls else "$f1"
    # outlets fire right to left: 3 new state (stored first), 2 colour, 1 first segment, 0 count (starts the loop)
    dE = mt.obj(x, 280, "expr " + E(f"abs({TG}-mtcur[{ch}]); min({TG}, mtcur[{ch}]); {TG}>mtcur[{ch}]; {TG}"))
    mt.c(nE, dE)
    # expr evaluates each outlet when it sends it: collect all four values before storing the new state
    dP = mt.obj(x, 290, "pack f f f f"); dU = mt.obj(x, 300, "unpack f f f f")
    for o in range(4):
        mt.c(dE, dP, o, o)
    mt.c(dP, dU)
    dE = dU
    wr = mt.obj(x + 200, 310, "tabwrite mtcur")
    idx = mt.msg(x + 200, 280, str(ch))
    mt.c(mt.obj(x + 200, 250, "loadbang"), idx); mt.c(idx, wr, 0, 1)
    mt.c(dE, wr, 3, 0)
    pk = mt.obj(x, 430, "pack f f")
    mt.c(dE, pk, 2, 1)                                    # colour -> cold inlet
    cF = mt.obj(x + 100, 370, "f")
    c1 = mt.obj(x + 150, 370, "+ 1")
    mt.c(dE, cF, 1, 1)                                    # first segment -> counter
    cnt = mt.obj(x, 340, "moses 1")
    mt.c(dE, cnt, 0)
    go = mt.obj(x + 50, 360, "t f b")
    mt.c(cnt, go, 1); mt.c(go, one, 1)                    # something to draw -> flip at the end of the frame
    u = mt.obj(x + 50, 390, "until")
    mt.c(go, u, 0); mt.c(u, cF); mt.c(cF, c1); mt.c(c1, cF, 0, 1)
    xE = mt.obj(x + 100, 400, f"expr {first_x}+$f1*{pitch}")
    mt.c(cF, xE); mt.c(xE, pk, 0, 0)
    mt.c(pk, mt.msg(x, 460, oscm("gFillArea", "iiiiii", f"\\$1 {y} {width} {height} \\$2")))


N = "+".join(f"($f1>={100 + t})" for t in THR)
for ch, (rcv, x, y) in enumerate((("nst-outL", 20, 1), ("nst-outR", 420, 5))):
    lv = mt.obj(x, 220, "f 0")
    mt.c(mt.obj(x + 60, 190, f"r {rcv}"), lv, 0, 1)
    mt.c(tick, lv, 3 - ch)
    lights(lv, x, ch, N, True, y, X0, SW, SWL, SH)
lim = mt.obj(820, 220, "f 0")
limC = mt.obj(880, 190, "< 0.97")
mt.c(mt.obj(880, 160, "r nst-lim-gain"), limC); mt.c(limC, lim, 0, 1)
mt.c(tick, lim, 1)
lights(lim, 820, 2, "$f1", False, 1, LX, 0, 6, 7)
mt.save("meter.pd")

#!/usr/bin/env python3
"""1) live waveform while sampling  2) stereo tape with per-track pan  3) OP-1-style MIX page with dials,
AUX held = PAN (own pickup context 11)."""
import shutil

for f in ("gen.py", "gensmpl.py", "gensynth.py", "genmix.py", "gentape.py"):
    shutil.copy(f, f + ".pre-mixpan")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# ------------------------------------------------------------ 1) live waveform while sampling
edit("gensmpl.py", [
    # drawing reads display copies (smp-dlen / smp-ds0 / smp-ds1), the voices keep the real values
    (r'''r.c(r.obj(2000, 50, "r smp-s0"), fS0, 0, 1); r.c(r.obj(2080, 50, "r smp-s1"), fS1, 0, 1)''',
     r'''r.c(r.obj(2000, 50, "r smp-ds0"), fS0, 0, 1); r.c(r.obj(2080, 50, "r smp-ds1"), fS1, 0, 1)'''),
    (r'''r.c(bC, bE); r.c(fLen2, bE, 0, 1); r.c(r.obj(2150, 230, "r smp-s0"), bE, 0, 2); r.c(r.obj(2240, 230, "r smp-s1"), bE, 0, 3)''',
     r'''r.c(bC, bE); r.c(r.obj(2060, 230, "r smp-dlen"), bE, 0, 1); r.c(r.obj(2150, 230, "r smp-ds0"), bE, 0, 2); r.c(r.obj(2240, 230, "r smp-ds1"), bE, 0, 3)'''),
    (r'''r.c(fLen2, mE, 0, 2)''', r'''r.c(r.obj(2380, 190, "r smp-dlen"), mE, 0, 2)'''),
    (r'''r.c(r.obj(2400, 160, "r smp-s0"), fS0b, 0, 1)''', r'''r.c(r.obj(2400, 160, "r smp-ds0"), fS0b, 0, 1)'''),
    (r'''r.save("smpl.pd")''', r'''
# display copies: follow the real values, except while recording (then the live view drives them)
recOn = r.obj(2600, 400, "r smp-recording")
recNot = r.obj(2600, 430, "== 0")
r.c(recOn, recNot)
for k, (src, dst) in enumerate((("smp-len", "smp-dlen"), ("smp-s0", "smp-ds0"), ("smp-s1", "smp-ds1"))):
    x = 2600 + k * 150
    rr = r.obj(x, 470, f"r {src}")
    keep = r.obj(x + 70, 500, "f")
    sp = r.obj(x, 530, "spigot 1")
    r.c(rr, keep, 0, 1); r.c(rr, sp); r.c(recNot, sp, 0, 1)
    r.c(sp, r.obj(x, 560, f"s {dst}"))
    back = r.obj(x + 70, 470, "sel 1")
    r.c(recNot, back); r.c(back, keep); r.c(keep, sp)      # recording stopped: push the latest value
# live view: every 100 ms while recording, measure the bar being written and redraw
BW = SMAX // NB
liveM = r.obj(2600, 620, "metro 100")
r.c(recOn, liveM)
liveT0 = r.obj(2750, 620, "timer")
recStart = r.obj(2750, 590, "sel 1")
r.c(recOn, recStart); r.c(recStart, liveT0)
r.c(recStart, r.msg(2850, 620, "\\; smplwave const 0"))
r.c(recStart, wPkZ)                                          # reset the peak
liveB = r.obj(2600, 650, "t b b")
r.c(liveM, liveB); r.c(liveB, liveT0, 1, 1)
liveE = r.obj(2600, 690, f"expr min({SMAX} \\, int($f1*$f2/1000)) \\; min({NB - 1} \\, int(min({SMAX - 1} \\, int($f1*$f2/1000))/{BW}))")
r.c(liveT0, liveE); r.c(srt, liveE, 0, 1)
liveP = r.obj(2600, 720, "pack f f")
r.c(liveE, liveP, 1, 0); r.c(liveE, liveP, 0, 1)      # (bar, written)
liveU = r.obj(2600, 750, "unpack f f")
r.c(liveP, liveU)
# bar i over [i*BW, written)
lbI = r.obj(2700, 780, "t f f")
lbE = r.obj(2700, 810, f"expr $f1*{BW} \\; max(1 \\, $f2-$f1*{BW})")
fWr = r.obj(2800, 780, "f")
wrT = r.obj(2800, 750, "t f f")
r.c(liveU, wrT, 1); r.c(wrT, fWr, 1, 1); r.c(wrT, lbE, 0, 1)   # written first (cold)
r.c(liveU, lbI, 0); r.c(lbI, lbE, 1, 0)
r.c(fWr, lbE, 0, 1) if False else None
lmx = r.obj(2700, 870, "array max smpl")
lmn = r.obj(2850, 870, "array min smpl")
r.c(lbE, lmx, 1, 1); r.c(lbE, lmn, 1, 1)
lon = r.obj(2700, 840, "t f f")
r.c(lbE, lon, 0); r.c(lon, lmn, 1, 0); r.c(lon, lmx, 0, 0)
la = r.obj(2700, 900, "expr max($f1 \\, -$f2)")
r.c(lmn, la, 0, 1); r.c(lmx, la, 0, 0)
laT = r.obj(2700, 930, "t f f")
r.c(la, laT)
lTw = r.obj(2700, 960, "tabwrite smplwave")
r.c(lbI, lTw, 0, 1); r.c(laT, lTw, 0); r.c(laT, pkMax, 1)
# then publish the live view and redraw the SYNTH page
liveV = r.msg(2600, 1000, f"\\; smp-dlen {SMAX} \\; smp-ds0 0 \\; smp-ds1 \\$1 \\; smp-live bang")
r.c(liveB, fWr, 0); r.c(fWr, liveV)                  # after the bar is measured
r.save("smpl.pd")'''),
])
# the written-samples value must reach lbE's right inlet before the bar index arrives
s = open("gensmpl.py").read()
s = s.replace("r.c(fWr, lbE, 0, 1) if False else None\n", "")
assert "if False" not in s
open("gensmpl.py", "w").write(s)

edit("gensynth.py", [
    (r'''for name in ("nst-oct", "nst-redraw", "synth-engine"):''',
     r'''for name in ("nst-oct", "nst-redraw", "synth-engine", "smp-live"):'''),
])

# ------------------------------------------------------------ 2) stereo tape with per-track pan
edit("gentape.py", [
    (r'''thL = t.obj(20, 900, "throw~ tape-bus")''',
     r'''thL = t.obj(20, 960, "throw~ tape-busL")
thR = t.obj(200, 960, "throw~ tape-busR")'''),
    (r'''t.c(rl, rlm); t.c(rlm, rll); t.c(rll, lv, 0, 1); t.c(lv, thL)''',
     r'''t.c(rl, rlm); t.c(rlm, rll); t.c(rll, lv, 0, 1)
    # pan (balance law: centre = full level on both sides)
    rpan = t.obj(x + 130, 880, f"r tape-pan{k+1}")
    panE = t.obj(x + 130, 900, "expr min(1 \\, 2*(1-$f1)) \\; min(1 \\, 2*$f1)")
    pmL = t.msg(x + 130, 920, "\\$1 20"); pmR = t.msg(x + 170, 920, "\\$1 20")
    plL = t.obj(x + 130, 940, "line~"); plR = t.obj(x + 170, 940, "line~")
    gLp = t.obj(x, 930, "*~"); gRp = t.obj(x + 60, 930, "*~")
    t.c(rpan, panE); t.c(panE, pmL, 0); t.c(panE, pmR, 1); t.c(pmL, plL); t.c(pmR, plR)
    t.c(lv, gLp, 0, 0); t.c(plL, gLp, 0, 1); t.c(lv, gRp, 0, 0); t.c(plR, gRp, 0, 1)
    t.c(gLp, thL); t.c(gRp, thR)'''),
])
edit("genmix.py", [
    (r'''ct = ms.obj(200, 50, "catch~ tape-bus")''',
     r'''ctL = ms.obj(200, 50, "catch~ tape-busL")
ctR = ms.obj(330, 50, "catch~ tape-busR")
tMono = ms.obj(200, 70, "+~")
tHalf = ms.obj(200, 75, "*~ 0.5")
ms.c(ctL, tMono, 0, 0); ms.c(ctR, tMono, 0, 1); ms.c(tMono, tHalf)'''),
    (r'''ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(ct, dry, 0, 1)''',
     r'''ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(tHalf, dry, 0, 1)      # mono send for the FX'''),
    (r'''ms.c(dry, ol); ms.c(dry, orr)''',
     r'''ms.c(cs, ol); ms.c(cs, orr); ms.c(ctL, ol); ms.c(ctR, orr)        # dry out: synth centre + panned tape'''),
])

# ------------------------------------------------------------ 3) MIX page: dials, AUX = PAN
PAGE = r'''# MIX page: 4 dials with needles (OP-1 style). Holding AUX shows / edits PAN instead of level.
import math
rauxM = x_.obj(1100, 60, "r aux")
x_.c(rauxM, dOne)
mixT = x_.obj(200, 470, "t b b b b b b")
x_.c(psel, mixT, 0)
DX = [16, 48, 80, 112]
CY, RAD, NEE = 26, 12, 10
ticks = []
for cx in DX:
    for ang in (-135, 135):
        a = math.radians(ang)
        x1, y1 = cx + round((RAD + 1) * math.sin(a)), CY - round((RAD + 1) * math.cos(a))
        x2, y2 = cx + round((RAD + 3) * math.sin(a)), CY - round((RAD + 3) * math.cos(a))
        ticks.append(osc2("gLine", "iiiiii", f"{x1} {y1} {x2} {y2} 1"))
mixStatic = x_.msg(200, 500, " ".join(
    [osc2("gCircle", "iiiii", f"{cx} {CY} {RAD} 1") for cx in DX] +
    [osc2("gFilledCircle", "iiiii", f"{cx} {CY} 2 1") for cx in DX] + ticks +
    [osc2("gPrintln", "iiiiii", f"{cx - 2} 43 8 1 {k + 1}") for k, cx in enumerate(DX)]))
x_.c(mixT, mixStatic, 5)
# title: MIX or PAN
auxF = x_.obj(1000, 500, "f")
x_.c(rauxM, auxF, 0, 1)
auxS = x_.obj(1000, 530, "sel 0 1")
x_.c(mixT, auxF, 4); x_.c(auxF, auxS)
x_.c(auxS, x_.msg(1000, 560, osc2("gPrintln", "iiiiis", "1 1 8 1 MIX") + " " + osc2("gPrintln", "iiiiis", "58 1 8 1 aux=PAN")), 0)
x_.c(auxS, x_.msg(1150, 560, osc2("gFillArea", "iiiiii", "0 0 21 10 1") + " " + osc2("gPrintln", "iiiiis", "2 1 8 0 PAN")), 1)
# pans (0..1), routed when AUX is held
panF = []
rpan = x_.obj(200, 680, "route 1 2 3 4")
auxLP = x_.obj(200, 620, "list prepend 0")
auxR = x_.obj(200, 650, "route 0 1")
x_.c(rauxM, auxLP, 0, 1)
x_.c(auxLP, auxR); x_.c(auxR, rpan, 1)
panDef = x_.msg(400, 650, "1 0.5 \\, 2 0.5 \\, 3 0.5 \\, 4 0.5")
x_.c(lb, panDef); x_.c(panDef, rpan)
dials = []
for k, cx in enumerate(DX):
    t_ = x_.obj(200 + k * 160, 710, "t f f")
    x_.c(rpan, t_, k)
    x_.c(t_, x_.obj(260 + k * 160, 740, f"s tape-pan{k+1}"), 1)
    # needle + value: v = pan if AUX else level ; angle -135..+135 deg
    dE = x_.obj(200 + k * 160, 780,
                f"expr int({cx}+{NEE}*sin((-135+270*if($f3 \\, $f2 \\, $f1))*0.017453)) \\; "
                f"int({CY}-{NEE}*cos((-135+270*if($f3 \\, $f2 \\, $f1))*0.017453)) \\; "
                f"if($f3 \\, if($f2<0.48 \\, 1 \\, if($f2>0.52 \\, 3 \\, 2)) \\, 0) \\; "
                f"if($f3 \\, int(abs($f2-0.5)*200+0.5) \\, int($f1*100+0.5))")
    x_.c(t_, dE, 0, 1)                       # pan -> cold
    x_.c(rauxM, dE, 0, 2)                    # aux -> cold
    x_.c(mixT, lvF[k], 3 - k); x_.c(lvF[k], dE)
    dP = x_.obj(200 + k * 160, 810, "pack f f f f")
    for o in range(4):
        x_.c(dE, dP, o, o)
    dT = x_.obj(200 + k * 160, 840, "t l l")
    x_.c(dP, dT)
    x_.c(dT, x_.msg(200 + k * 160, 870, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1")), 1)
    sp = x_.obj(200 + k * 160, 900, "list split 2")
    vr = x_.obj(200 + k * 160, 930, "route 0 1 2 3")
    x_.c(dT, sp, 0); x_.c(sp, vr, 1)
    X = cx - 9
    x_.c(vr, x_.msg(200 + k * 160, 960, osc2("gPrintln", "iiiiif", f"{X} 55 8 1 \\$1")), 0)
    x_.c(vr, x_.msg(200 + k * 160, 990, osc2("gPrintln", "iiiiisf", f"{X} 55 8 1 L \\$1")), 1)
    x_.c(vr, x_.msg(200 + k * 160, 1020, osc2("gPrintln", "iiiiis", f"{cx - 2} 55 8 1 C")), 2)
    x_.c(vr, x_.msg(200 + k * 160, 1050, osc2("gPrintln", "iiiiisf", f"{X} 55 8 1 R \\$1")), 3)
'''
s = open("genmix.py").read()
a = s.index("# MIX page: 4 vertical faders")
b = s.index("# FX page: 4 horizontal bars")
s = s[:a] + PAGE + "\n" + s[b:]
# level knobs only when AUX is up; with AUX held the page-0 knobs go to the pans
old = "x_.c(rpg, rlv, 0); x_.c(rpg, rfx, 1)"
assert s.count(old) == 1
s = s.replace(old, "x_.c(rpg, rfx, 1)")
s = s.replace("auxR = x_.obj(200, 650, \"route 0 1\")", "auxR = x_.obj(200, 650, \"route 0 1\")\nx_.c(rpg, auxLP, 0); x_.c(auxR, rlv, 0)")
open("genmix.py", "w").write(s)

# ------------------------------------------------------------ pickup: context 11 = MIX page with AUX held (pans)
edit("gen.py", [
    (r'''m.obj(560, 530, "table pkval 44")''', r'''m.obj(560, 530, "table pkval 48")'''),
    (r'''m.obj(680, 530, "table pkpick 44")''', r'''m.obj(680, 530, "table pkpick 48")'''),
    (r'''0 1 0.3 0 \\; pkphys''', r'''0 1 0.3 0 0.5 0.5 0.5 0.5 \\; pkphys'''),
    (r'''ctxE = m.obj(560, 660, "expr if($f1==3 && $f2==1 \\, 5 \\, if($f1==0 && $f3>0 \\, if($f3==4 \\, 10 \\, 5+$f3) \\, if($f1==4 && $f4==1 \\, 9 \\, $f1)))")''',
     r'''ctxE = m.obj(560, 660, "expr if($f1==3 && $f2==0 && $f5==1 \\, 11 \\, if($f1==3 && $f2==1 \\, 5 \\, if($f1==0 && $f3>0 \\, if($f3==4 \\, 10 \\, 5+$f3) \\, if($f1==4 && $f4==1 \\, 9 \\, $f1))))")
rauxC = m.obj(1000, 630, "r aux")
auxTb = m.obj(1000, 660, "t b f")
m.c(rauxC, auxTb); m.c(auxTb, ctxE, 1, 4); m.c(auxTb, ctxE, 0, 0)'''),
])
print("mix/pan + live waveform applied")

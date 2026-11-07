# exec'd from gen.py: builds master.pd (mix + delay + reverb) and mix.pd (MIX/FX pages)

def osc2(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


# ---------------------------------------------------------------- master.pd
ms = Patch(1300, 900)
ms.text(20, 10, "master: synth + tape -> delay + reverb -> out. The tape records the dry synth.")
cs = ms.obj(20, 50, "catch~ synth-bus")
ctL = ms.obj(200, 50, "catch~ tape-busL")
ctR = ms.obj(330, 50, "catch~ tape-busR")
tMono = ms.obj(200, 70, "+~")
tHalf = ms.obj(200, 75, "*~ 0.5")
ms.c(ctL, tMono, 0, 0); ms.c(ctR, tMono, 0, 1); ms.c(tMono, tHalf)
sti = ms.obj(20, 90, "s~ tape-in")
dry = ms.obj(200, 90, "+~")
ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(tHalf, dry, 0, 1)      # mono send for the FX
# --- output limiter
ol = ms.obj(20, 820, "*~ 1")                 # sums everything going to the left output
orr = ms.obj(200, 820, "*~ 1")
LIM_T = 0.89                                # about -1 dBFS
REL = 0.0097                                # per 64-sample block: ~150 ms release
lgL = ms.obj(20, 850, "*~"); lgR = ms.obj(200, 850, "*~")
lcL = ms.obj(20, 880, "clip~ -1 1"); lcR = ms.obj(200, 880, "clip~ -1 1")
ms.c(lgL, lcL); ms.c(lgR, lcR)                             # (ol / orr reach lgL / lgR through the compressor)
muL = ms.obj(20, 895, "*~"); muR = ms.obj(200, 895, "*~")
muM = ms.msg(400, 865, "\\$1 40")
muLn = ms.obj(400, 880, "line~")
ms.c(ms.obj(400, 850, "r nst-mute"), muM); ms.c(muM, muLn)
muI = ms.msg(500, 865, "1")
ms.c(ms.obj(500, 850, "loadbang"), muI); ms.c(muI, muLn)
ms.c(lcL, muL); ms.c(lcR, muR); ms.c(muLn, muL, 0, 1); ms.c(muLn, muR, 0, 1)
ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))
enL = ms.obj(20, 940, "env~ 1024 512"); enR = ms.obj(200, 940, "env~ 1024 512")
ms.c(muL, enL); ms.c(muR, enR)
ms.c(enL, ms.obj(20, 970, "s nst-outL")); ms.c(enR, ms.obj(200, 970, "s nst-outR"))
# detector: max(|L|, |R|) -> 64-sample table every block -> peak
laL = ms.obj(1000, 820, "abs~"); laR = ms.obj(1100, 820, "abs~"); lmx = ms.obj(1000, 850, "max~")
ms.c(laL, lmx, 0, 0); ms.c(laR, lmx, 0, 1)                 # (limiter detector fed after the compressor)
ms.obj(1000, 790, "table nst-lim 64")
ms.c(lmx, ms.obj(1000, 880, "tabsend~ nst-lim"))
lbg = ms.obj(1150, 790, "bang~")
lam = ms.obj(1150, 820, "array max nst-lim")
ms.c(lbg, lam)
# gain: g = min(target, g + (1-g)*REL)   target = min(1, T/peak)
lgE = ms.obj(1150, 850, "expr min(1 \\, %s/max($f1 \\, 0.001))" % LIM_T)
lgN = ms.obj(1150, 880, "expr min($f1 \\, $f2+(1-$f2)*%s)" % REL)
lgT = ms.obj(1150, 910, "t f f")
ms.c(lam, lgE); ms.c(lgE, lgN)
ms.c(lgN, lgT); ms.c(lgT, lgN, 1, 1)          # previous gain -> cold inlet
# to the gain line~ only when it changes (3 decimals)
lgQ = ms.obj(1150, 940, "expr int($f1*1000+0.5)/1000.0")
lgC = ms.obj(1150, 970, "change 1")
lgM = ms.msg(1150, 1000, "\\$1 1")
lgLn = ms.obj(1150, 1030, "line~")
ms.c(lgT, lgQ, 0); ms.c(lgQ, lgC); ms.c(lgC, lgM); ms.c(lgM, lgLn)
lgI = ms.msg(1300, 1000, "1")
ms.c(ms.obj(1300, 970, "loadbang"), lgI); ms.c(lgI, lgLn); ms.c(lgI, lgN, 0, 1)
ms.c(lgLn, lgL, 0, 1); ms.c(lgLn, lgR, 0, 1)
ms.c(lgC, ms.obj(1250, 1060, "s nst-lim-gain"))
ms.c(cs, ol); ms.c(cs, orr); ms.c(ctL, ol); ms.c(ctR, orr)        # dry out: synth centre + panned tape


def smooth(x, y, name, init):
    """[r name] -> line~ (20 ms), with a starting value."""
    r = ms.obj(x, y, f"r {name}")
    m = ms.msg(x, y + 30, "\\$1 20")
    l = ms.obj(x, y + 60, "line~")
    lb = ms.obj(x + 90, y, "loadbang")
    i = ms.msg(x + 90, y + 30, f"{init}")
    ms.c(r, m); ms.c(m, l); ms.c(lb, i); ms.c(i, m)
    return l

# --- delay (mono, feedback through a lowpass)
dmix = smooth(400, 40, "fx-dmix", 0)
dfb = smooth(560, 40, "fx-fb", 0.4)
dtm = smooth(720, 40, "fx-time", 373)
dsend = ms.obj(200, 160, "*~")
ms.c(dry, dsend, 0, 0); ms.c(dmix, dsend, 0, 1)
dsum = ms.obj(200, 200, "+~")
dwr = ms.obj(200, 240, "delwrite~ nst-dly 2100")
drd = ms.obj(400, 200, "vd~ nst-dly")
dlp = ms.obj(400, 240, "lop~ 3500")
dfbm = ms.obj(400, 280, "*~")
dclip = ms.obj(400, 320, "clip~ -1.5 1.5")
ms.c(dsend, dsum, 0, 0); ms.c(dsum, dwr)
ms.c(dtm, drd); ms.c(drd, dlp); ms.c(dlp, dfbm, 0, 0); ms.c(dfb, dfbm, 0, 1)
ms.c(dfbm, dclip); ms.c(dclip, dsum, 0, 1)
ms.c(drd, ol); ms.c(drd, orr)

# --- reverb (reverb.pd: diffusers + 8-line FDN, switches itself off when unused)
rmix = smooth(880, 40, "fx-rmix", 0)
rin = ms.obj(600, 400, "+~")
ms.c(dry, rin, 0, 0); ms.c(drd, rin, 0, 1)
rsend = ms.obj(600, 440, "*~")
ms.c(rin, rsend, 0, 0); ms.c(rmix, rsend, 0, 1)
rvb = ms.obj(600, 480, "reverb")
ms.c(rsend, rvb)
gL = ms.obj(600, 790, "*~ 0.5"); gR = ms.obj(760, 790, "*~ 0.5")
ms.c(rvb, gL, 0); ms.c(rvb, gR, 1); ms.c(gL, ol); ms.c(gR, orr)
# --- master compressor (apply_comp.py): feed-forward RMS, before the limiter
cpL = ms.obj(20, 835, "*~"); cpR = ms.obj(200, 835, "*~")
cpLn = ms.obj(400, 800, "line~")
ms.c(cpLn, cpL, 0, 1); ms.c(cpLn, cpR, 0, 1)
cpI = ms.msg(500, 770, "1")
ms.c(ms.obj(500, 740, "loadbang"), cpI); ms.c(cpI, cpLn)
cpSum = ms.obj(1300, 820, "+~")
ms.c(ol, cpSum, 0, 0); ms.c(orr, cpSum, 0, 1)
cpHalf = ms.obj(1300, 850, "*~ 0.5")
cpEnv = ms.obj(1300, 880, "env~ 1024 128")
ms.c(cpSum, cpHalf); ms.c(cpHalf, cpEnv)
cpSp = ms.obj(1300, 910, "spigot")
ms.c(cpEnv, cpSp)
# parameters: comp-knob / comp-set "k v": 1 amount, 2 speed
cpR_ = ms.obj(1500, 820, "route 1 2")
ms.c(ms.obj(1500, 790, "r comp-knob"), cpR_); ms.c(ms.obj(1600, 790, "r comp-set"), cpR_)
cpDef = ms.msg(1700, 790, "1 0 \\, 2 0.5")
ms.c(ms.obj(1700, 760, "loadbang"), cpDef); ms.c(cpDef, cpR_)
# gain expr: $f1 env dB (100 = 0 dBFS)  $f2 amount  $f3 speed  $f4 previous reduction (dB)
#   outlets: 0 reduction dB, 1 ramp ms, 2 linear gain
cpE = ms.obj(1300, 950, "expr max(0 \\, ($f1-100)-(-2-$f2*28))*0.75 \\; "
                        "if(max(0 \\, ($f1-100)-(-2-$f2*28))*0.75>$f4 \\, 5+45*$f3 \\, 50+750*$f3) \\; "
                        "pow(10 \\, ($f2*8-max(0 \\, ($f1-100)-(-2-$f2*28))*0.75)/20)")
ms.c(cpSp, cpE)
cpP = ms.obj(1300, 980, "pack f f f")
ms.c(cpE, cpP, 2, 2); ms.c(cpE, cpP, 1, 1); ms.c(cpE, cpP, 0, 0)
cpU = ms.obj(1300, 1010, "unpack f f f")
ms.c(cpP, cpU)
cpG = ms.obj(1400, 1040, "pack f f")                  # unpack fires gain (outlet 2) before ramp ms (outlet 1)
ms.c(cpU, cpG, 2, 1); ms.c(cpU, cpG, 1, 0)            # gain -> cold, ramp ms -> hot (last)
cpGM = ms.msg(1400, 1070, "\\$2 \\$1")                # line~ wants "target time"
ms.c(cpG, cpGM); ms.c(cpGM, cpLn)
ms.c(cpU, cpE, 0, 3)                                  # reduction -> state (cold inlet), after all outlets ran
ms.c(cpU, ms.obj(1300, 1040, "s comp-gr"), 0)
# amount: store it, open/close the detector, back to unity gain when off
cpAT = ms.obj(1500, 850, "t f f")
ms.c(cpR_, cpAT, 0)
ms.c(cpAT, cpE, 1, 1)
cpOn = ms.obj(1600, 880, "> 0.02")
ms.c(cpAT, cpOn, 0); ms.c(cpOn, cpSp, 0, 1)
cpOff = ms.obj(1600, 910, "sel 0")
cpUnity = ms.msg(1600, 940, "1 50")
cpZ = ms.msg(1700, 940, "\\; comp-gr 0")
ms.c(cpOn, cpOff); ms.c(cpOff, cpUnity); ms.c(cpUnity, cpLn); ms.c(cpOff, cpZ)
ms.c(cpR_, cpE, 1, 2)                                 # speed (cold)
ms.c(ol, cpL); ms.c(orr, cpR)
ms.c(cpL, lgL); ms.c(cpR, lgR)
ms.c(cpL, laL); ms.c(cpR, laR)
# mono copy of the whole output, for resampling (SMPL engine, AUX+F5)
mA = ms.obj(400, 860, "*~ 1"); mB = ms.obj(500, 860, "*~ 0.5"); mS = ms.obj(400, 890, "+~")
ms.c(dry, mA); ms.c(drd, mA); ms.c(gL, mB); ms.c(gR, mB); ms.c(mA, mS, 0, 0); ms.c(mB, mS, 0, 1)
ms.c(mS, ms.obj(400, 920, "s~ nst-master"))
ms.save("master.pd")

# ---------------------------------------------------------------- mix.pd
x_ = Patch(1300, 900)
x_.text(20, 5, "mix: MIX page = tape track levels / FX page = delay time - feedback - delay amount - reverb amount")
x_.text(20, 25, "press AUX+D# again while in MIX to switch page")
# --- page toggle: mode 3 received while already in mode 3
rmd = x_.obj(20, 60, "r mode")
mt = x_.obj(20, 90, "t f f")
again = x_.obj(20, 130, "expr $f1==3 && $f2==3")
ag1 = x_.obj(20, 160, "sel 1")
pgF = x_.obj(20, 190, "f")
pgN = x_.obj(20, 220, "expr ($f1+1)%4")             # MIX -> FX -> FILTER -> MASTER
pgT = x_.obj(20, 250, "t f f")
x_.c(rmd, mt); x_.c(mt, again, 1); x_.c(mt, again, 0, 1)
x_.c(pgT, x_.obj(120, 280, "s mix-page"), 0)
x_.c(again, ag1); x_.c(ag1, pgF); x_.c(pgF, pgN); x_.c(pgN, pgT); x_.c(pgT, pgF, 1, 1)
# --- knobs, routed by page
rk = x_.obj(200, 60, "r mix-knob")
lp = x_.obj(200, 90, "list prepend 0")
x_.c(rk, lp); x_.c(pgT, lp, 0, 1)
rpg = x_.obj(200, 120, "route 0 1 2 3")
x_.c(lp, rpg)
rlv = x_.obj(200, 150, "route 1 2 3 4")
rfx = x_.obj(500, 150, "route 1 2 3 4")
x_.c(x_.obj(380, 120, "r mix-lvl-set"), rlv)
x_.c(x_.obj(620, 120, "r mix-fx-set"), rfx)
fxAux = x_.obj(500, 120, "list prepend 0")
x_.c(x_.obj(560, 90, "r aux"), fxAux, 0, 1)
fxAuxR = x_.obj(500, 135, "route 0 1")
x_.c(rpg, fxAux, 1); x_.c(fxAux, fxAuxR); x_.c(fxAuxR, rfx, 0)
x_.c(fxAuxR, x_.obj(600, 150, "s rvb-knob"), 1)
# FILTER page: knob k -> track k filter, AUX held -> its resonance
fiK = x_.obj(700, 120, "list prepend 0")
x_.c(x_.obj(760, 90, "r aux"), fiK, 0, 1)
fiKR = x_.obj(700, 135, "route 0 1")
x_.c(rpg, fiK, 2); x_.c(fiK, fiKR)
x_.c(fiKR, x_.obj(700, 150, "s tfilt-knob"), 0); x_.c(fiKR, x_.obj(800, 150, "s tres-knob"), 1)
x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)                # MASTER page: knob 1 COMP, knob 2 SPEED
lb = x_.obj(800, 60, "loadbang")
defs = x_.msg(800, 90, "0 1 0.8 \\, 0 2 0.8 \\, 0 3 0.8 \\, 0 4 0.8 \\, 1 1 0.6 \\, 1 2 0.42 \\, 1 3 0 \\, 1 4 0")
x_.c(lb, defs); x_.c(defs, rpg)
lvF, fxF = [], []
for k in range(4):
    t_ = x_.obj(200 + k * 70, 190, "t f f")
    s_ = x_.obj(200 + k * 70, 220, f"s tape-lvl{k+1}")
    f_ = x_.obj(200 + k * 70, 250, "f")
    x_.c(rlv, t_, k); x_.c(t_, s_, 1); x_.c(t_, f_, 0, 1)
    lvF.append(f_)
fxmap = ["expr int(20+980*pow($f1 \\, 2))", "* 0.95", "t f", "t f"]
fxsend = ["t f", "s fx-fb", "s fx-dmix", "s fx-rmix"]
for k in range(4):
    t_ = x_.obj(500 + k * 120, 190, "t f f")
    e_ = x_.obj(500 + k * 120, 220, fxmap[k])
    s_ = x_.obj(500 + k * 120, 250, fxsend[k])
    f_ = x_.obj(500 + k * 120, 280, "f")
    x_.c(rfx, t_, k); x_.c(t_, e_, 1); x_.c(e_, s_); x_.c(t_, f_, 0, 1)
    fxF.append(f_)
    if k == 0:
        kms = s_

# delay time: free (knob 1) or synced to the tempo (TEMPO page, knob 4)
timeE = x_.obj(500, 340, "expr min(2000 \\, if($f2==0 \\, $f1 \\, $f3*if($f2==1 \\, 0.25 \\, if($f2==2 \\, 0.5 \\, if($f2==3 \\, 0.75 \\, if($f2==4 \\, 1 \\, if($f2==5 \\, 1.5 \\, 2)))))))")
x_.c(kms, timeE, 0, 0)
rds = x_.obj(700, 310, "r dly-sync")
rdsT = x_.obj(700, 340, "t b f")
rbm = x_.obj(820, 310, "r tempo-beatms")
rbmT = x_.obj(820, 340, "t b f")
x_.c(rds, rdsT); x_.c(rdsT, timeE, 1, 1); x_.c(rdsT, timeE, 0, 0)
x_.c(rbm, rbmT); x_.c(rbmT, timeE, 1, 2); x_.c(rbmT, timeE, 0, 0)
timeT = x_.obj(500, 370, "t f f")
x_.c(timeE, timeT); x_.c(timeT, x_.obj(500, 400, "s fx-time"), 0)
ftimeF = x_.obj(600, 400, "f")
fsyncF = x_.obj(700, 400, "f")
x_.c(timeT, ftimeF, 1, 1); x_.c(rdsT, fsyncF, 1, 1)
ftB = x_.obj(800, 400, "t b b")
syS = x_.obj(800, 430, "sel 1 2 3 4 5 6")
x_.c(ftB, fsyncF, 1); x_.c(fsyncF, syS)
for i, nm in enumerate(["1/16", "1/8", "1/8.", "1/4", "1/4.", "1/2"]):
    mm = x_.msg(800 + i * 70, 460, osc2("gPrintln", "iiiiis", f"22 1 8 1 {nm}"))
    x_.c(syS, mm, i)
x_.c(ftB, ftimeF, 0)

# --- screen (10 fps while in MIX)
eq3 = x_.obj(20, 300, "== 3")
mtr = x_.obj(20, 330, "metro 100")
x_.c(mt, eq3, 0); x_.c(eq3, mtr)
pgS = x_.obj(20, 400, "f")
x_.c(pgT, pgS, 0, 1)
seq = x_.obj(20, 370, "t b b b")
dOne = x_.msg(1420, 500, "1")
dF = x_.obj(1300, 560, "f 1")
x_.c(dOne, dF, 0, 1)
dSel = x_.obj(1300, 590, "sel 1")
dTT = x_.obj(1300, 620, "t b b")
dZero = x_.msg(1420, 620, "0")
x_.c(dF, dSel); x_.c(dSel, dTT); x_.c(dTT, dZero, 1); x_.c(dZero, dF, 0, 1); x_.c(dTT, seq, 0)
x_.c(x_.obj(1500, 470, "r mix-knob"), dOne)
x_.c(x_.obj(1590, 470, "r mix-page"), dOne)
x_.c(x_.obj(1680, 470, "r mode"), dOne)
x_.c(x_.obj(1770, 470, "r nst-redraw"), dOne)
x_.c(x_.obj(1860, 470, "r dly-sync"), dOne)
x_.c(x_.obj(1950, 470, "r tempo-beatms"), dOne)
x_.c(mtr, dF)
clr = x_.msg(20, 430, osc2("gClear", "ii", "1"))
flip = x_.msg(20, 460, "\\; oscOut sendtyped /oled/gFlip i 3")
x_.c(seq, clr, 2); x_.c(seq, pgS, 1); x_.c(seq, flip, 0)
x_.c(seq, x_.msg(100, 430, "\\; mt-reset bang"), 2)
psel = x_.obj(200, 430, "sel 0 1 2 3")
x_.c(pgS, psel)

# MIX page: 4 dials with needles (OP-1 style). Holding AUX shows / edits PAN instead of level.
import math
rauxM = x_.obj(1100, 60, "r aux")
x_.c(rauxM, dOne)
mixT = x_.obj(200, 470, "t b b b b b b")
mixW = x_.obj(120, 470, "t b b")
x_.c(psel, mixW, 0); x_.c(mixW, mixT, 1)
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
x_.c(auxS, x_.msg(1000, 560, osc2("gPrintln", "iiiiis", "1 1 8 1 MIX")), 0)
x_.c(auxS, x_.msg(1150, 560, osc2("gFillArea", "iiiiii", "0 0 21 10 1") + " " + osc2("gPrintln", "iiiiis", "2 1 8 0 PAN")), 1)
# pans (0..1), routed when AUX is held
panF = []
rpan = x_.obj(200, 680, "route 1 2 3 4")
x_.c(x_.obj(330, 650, "r mix-pan-set"), rpan)
auxLP = x_.obj(200, 620, "list prepend 0")
auxR = x_.obj(200, 650, "route 0 1")
x_.c(rpg, auxLP, 0); x_.c(auxR, rlv, 0)
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
    ndSp = x_.obj(260 + k * 160, 860, "spigot")
    x_.c(rauxM, ndSp, 0, 1)
    x_.c(dT, ndSp, 1); x_.c(ndSp, x_.msg(200 + k * 160, 870, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1")))
    # level setting: a mark on the ring (level view only)
    mkE = x_.obj(330 + k * 160, 780,
                 f"expr int({cx}+13*sin((-135+270*$f1)*0.017453)) \\; int({CY}-13*cos((-135+270*$f1)*0.017453)) \\; "
                 f"int({cx}+16*sin((-135+270*$f1)*0.017453)) \\; int({CY}-16*cos((-135+270*$f1)*0.017453))")
    x_.c(lvF[k], mkE)
    mkP = x_.obj(330 + k * 160, 810, "pack f f f f")
    for o in range(4):
        x_.c(mkE, mkP, o, o)
    mkSp = x_.obj(330 + k * 160, 840, "spigot 1")
    mkNot = x_.obj(400 + k * 160, 810, "== 0")
    x_.c(rauxM, mkNot); x_.c(mkNot, mkSp, 0, 1)
    x_.c(mkP, mkSp); x_.c(mkSp, x_.msg(330 + k * 160, 870, osc2("gLine", "iiiiii", "\\$1 \\$2 \\$3 \\$4 1")))
    sp = x_.obj(200 + k * 160, 900, "list split 2")
    vr = x_.obj(200 + k * 160, 930, "route 0 1 2 3")
    x_.c(dT, sp, 0); x_.c(sp, vr, 1)
    X = cx - 9
    x_.c(vr, x_.msg(200 + k * 160, 960, osc2("gPrintln", "iiiiif", f"{X} 55 8 1 \\$1")), 0)
    x_.c(vr, x_.msg(200 + k * 160, 990, osc2("gPrintln", "iiiiis", f"{cx - 12} 55 8 1 L") + " " + osc2("gPrintln", "iiiiif", f"{cx - 6} 55 8 1 \\$1")), 1)
    x_.c(vr, x_.msg(200 + k * 160, 1020, osc2("gPrintln", "iiiiis", f"{cx - 2} 55 8 1 C")), 2)
    x_.c(vr, x_.msg(200 + k * 160, 1050, osc2("gPrintln", "iiiiis", f"{cx - 12} 55 8 1 R") + " " + osc2("gPrintln", "iiiiif", f"{cx - 6} 55 8 1 \\$1")), 3)

# --- VU meters (level view): 10 fps, only needles that moved are erased and redrawn
vuOnE = x_.obj(1300, 700, "expr $f1==3 && $f2==0 && $f3==0")
x_.c(mt, vuOnE, 0)
vpB = x_.obj(1400, 670, "t b f"); x_.c(pgT, vpB, 0); x_.c(vpB, vuOnE, 1, 1); x_.c(vpB, vuOnE, 0, 0)
vaB = x_.obj(1500, 670, "t b f"); x_.c(rauxM, vaB); x_.c(vaB, vuOnE, 1, 2); x_.c(vaB, vuOnE, 0, 0)
vuM = x_.obj(1300, 730, "metro 100")
x_.c(vuOnE, vuM)
vuTick = x_.obj(1300, 760, "t b b b b b")
x_.c(vuM, vuTick)
flagF = x_.obj(1300, 1100, "f")
flagS = x_.obj(1300, 1130, "sel 1")
flagT = x_.obj(1300, 1160, "t b b")
flag0 = x_.msg(1400, 1160, "0")
flag1 = x_.msg(1400, 1100, "1")
x_.c(vuTick, flagF, 0); x_.c(flagF, flagS); x_.c(flagS, flagT)
x_.c(flagT, flag0, 1); x_.c(flag0, flagF, 0, 1); x_.c(flag1, flagF, 0, 1)
x_.c(flagT, x_.msg(1300, 1190, "\\; oscOut sendtyped /oled/gFlip i 3"), 0)
# after a full redraw in the level view: forget the drawn needles and draw them now
vfSp = x_.obj(120, 500, "spigot 1")
vfNot = x_.obj(60, 500, "== 0")
x_.c(rauxM, vfNot); x_.c(vfNot, vfSp, 0, 1)
x_.c(mixW, vfSp, 0)
vfT = x_.obj(120, 530, "t b b")
x_.c(vfSp, vfT); x_.c(vfT, vuTick, 0)
for k, cx in enumerate(DX):
    x = 1300 + k * 220
    raw = x_.obj(x, 800, "f")
    vuIn = x_.obj(x + 80, 770, f"r tape-vu{k+1}")
    vuN = x_.obj(x + 80, 800, "expr min(1 \\, max(0 \\, ($f1-50)/50))")
    x_.c(vuIn, vuN); x_.c(vuN, raw, 0, 1)
    vE = x_.obj(x, 830,
                f"expr max($f1 \\, $f2-0.12) \\; "
                f"int({cx}+{NEE}*sin((-135+270*max($f1 \\, $f2-0.12))*0.017453))*100+"
                f"int({CY}-{NEE}*cos((-135+270*max($f1 \\, $f2-0.12))*0.017453))")
    x_.c(vuTick, raw, 4 - k); x_.c(raw, vE)
    x_.c(vE, vE, 0, 1)                        # fall-back state (needle ballistics)
    chg = x_.obj(x, 860, "change")
    x_.c(vE, chg, 1)
    setM = x_.msg(x + 80, 860, "set -1")
    x_.c(vfT, setM, 1); x_.c(setM, chg)
    cT = x_.obj(x, 890, "t f f b")
    x_.c(chg, cT)
    prevF = x_.obj(x + 100, 920, f"f {cx * 100 + CY}")
    dec1 = x_.obj(x + 100, 950, "expr int($f1/100) \\; $f1%100")
    pk1 = x_.obj(x + 100, 980, "pack f f")
    x_.c(cT, prevF, 2); x_.c(prevF, dec1); x_.c(dec1, pk1, 1, 1); x_.c(dec1, pk1, 0, 0)
    x_.c(pk1, x_.msg(x + 100, 1010, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 0")))      # erase old needle
    dec2 = x_.obj(x, 950, "expr int($f1/100) \\; $f1%100")
    pk2 = x_.obj(x, 980, "pack f f")
    x_.c(cT, dec2, 1); x_.c(dec2, pk2, 1, 1); x_.c(dec2, pk2, 0, 0)
    x_.c(pk2, x_.msg(x, 1010, osc2("gLine", "iiiiii", f"{cx} {CY} \\$1 \\$2 1") + " " +
                     osc2("gFilledCircle", "iiiii", f"{cx} {CY} 2 1")))                           # draw new
    x_.c(cT, prevF, 0, 1); x_.c(cT, flag1, 0)

# FX page: 4 horizontal bars + delay time in ms
fxT = x_.obj(800, 470, "t b b b b b b")
fxPgAux = x_.obj(900, 440, "f")
x_.c(x_.obj(960, 410, "r aux"), fxPgAux, 0, 1)
fxPgS = x_.obj(900, 455, "sel 0 1")
x_.c(psel, fxPgAux, 1); x_.c(fxPgAux, fxPgS); x_.c(fxPgS, fxT, 0)
# reverb page: title with the decay time, 4 bars
rvT = x_.obj(1600, 470, "t b b b b b b")
x_.c(fxPgS, rvT, 1)
x_.c(rvT, x_.msg(1600, 500, " ".join(
    [osc2("gPrintln", "iiiiis", "1 1 8 1 REVERB")] +
    [osc2("gPrintln", "iiiiis", f"1 {15 + k * 12} 8 1 {nm}") for k, nm in enumerate(("DEC", "TONE", "PRE", "MOD"))] +
    [osc2("gBox", "iiiiii", f"34 {14 + k * 12} 93 9 1") for k in range(4)])), 5)
rvV = []
for k in range(4):
    f_ = x_.obj(1600 + k * 70, 560, "f")
    rvV.append(f_)
rvIn = x_.obj(1600, 530, "route 1 2 3 4")
x_.c(x_.obj(1600, 500, "r rvb-knob"), rvIn); x_.c(x_.obj(1700, 500, "r rvb-set"), rvIn)
rvDef = x_.msg(1800, 500, "1 0.5 \\, 2 0.6 \\, 3 0.15 \\, 4 0.3")
x_.c(x_.obj(1800, 470, "loadbang"), rvDef); x_.c(rvDef, rvIn)
for k in range(4):
    x_.c(rvIn, rvV[k], k, 1)
    e_ = x_.obj(1600 + k * 70, 600, "expr max(0 \\, int($f1*89))")
    x_.c(rvT, rvV[k], 4 - k); x_.c(rvV[k], e_)
    x_.c(e_, x_.msg(1600 + k * 70, 640 + k * 30, osc2("gFillArea", "iiiiii", f"36 {16 + k * 12} \\$1 5 1")))
# decay in seconds in the title (one decimal)
rvSec = x_.obj(1900, 560, "expr int(0.4*pow(30 \\, $f1)*10+0.5)/10.0")
rvTV = x_.obj(1900, 530, "t b")
x_.c(rvT, rvTV, 0)
rvD = x_.obj(1950, 530, "f")
x_.c(rvIn, rvD, 0, 1)
x_.c(rvTV, rvD); x_.c(rvD, rvSec)
x_.c(rvSec, x_.msg(1900, 590, osc2("gPrintln", "iiiiifs", "80 1 8 1 \\$1 s")))
labels = ["TIME", "FDBK", "DLY", "REV"]
fxStatic = x_.msg(800, 500, " ".join(
    [osc2("gPrintln", "iiiiis", "1 1 8 1 FX")] +
    [osc2("gPrintln", "iiiiis", f"1 {15 + k * 12} 8 1 {labels[k]}") for k in range(4)] +
    [osc2("gBox", "iiiiii", f"34 {14 + k * 12} 93 9 1") for k in range(4)]))
x_.c(fxT, fxStatic, 5)
msE = x_.obj(800, 560, "int")
msM = x_.msg(800, 590, osc2("gPrintln", "iiiiifs", "70 1 8 1 \\$1 ms"))
fT0 = x_.obj(800, 530, "t b")
x_.c(fxT, fT0, 4)
# value for the title: re-use knob-1 value stored in fxF[0]
x_.c(fT0, fxF[0])
for k in range(4):
    Y = 16 + k * 12
    e_ = x_.obj(1000 + k * 70, 600, "expr max(0 \\, int($f1*89))")
    m_ = x_.msg(1000 + k * 70, 640 + k * 30, osc2("gFillArea", "iiiiii", f"36 {Y} \\$1 5 1"))
    x_.c(e_, m_)
    if k == 0:
        x_.c(fxF[0], e_); x_.c(fxF[0], ftB)
    else:
        x_.c(fxT, fxF[k], 4 - k); x_.c(fxF[k], e_)
x_.c(msE, msM); x_.c(ftimeF, msE)

# ------------------------------------------------ FILTER page (apply_trackfilter.py): 4 dials, LP <- off -> HP
fltV, resV = [], []
fvR = x_.obj(2600, 520, "route 1 2 3 4"); frR = x_.obj(2800, 520, "route 1 2 3 4")
x_.c(x_.obj(2600, 490, "r tfilt-knob"), fvR); x_.c(x_.obj(2650, 470, "r tfilt-set"), fvR)
x_.c(x_.obj(2800, 490, "r tres-knob"), frR); x_.c(x_.obj(2850, 470, "r tres-set"), frR)
for k in range(4):
    a = x_.obj(2600 + k * 50, 550, "f 0.5"); b = x_.obj(2800 + k * 50, 550, "f 0.3")
    x_.c(fvR, a, k, 1); x_.c(frR, b, k, 1)
    fltV.append(a); resV.append(b)
x_.c(x_.obj(2900, 490, "r tres-knob"), dOne); x_.c(x_.obj(2950, 490, "r tfilt-set"), dOne)
x_.c(x_.obj(3000, 490, "r tfilt-knob"), dOne)
fiT = x_.obj(2600, 600, "t b b b b b")                 # 4 header (AUX state first), 3..0 tracks 1..4
x_.c(psel, fiT, 2)
fiAux = x_.obj(2500, 600, "f")
x_.c(x_.obj(2500, 570, "r aux"), fiAux, 0, 1)
fiHead = x_.obj(2500, 630, "sel 0 1")
x_.c(fiT, fiAux, 4); x_.c(fiAux, fiHead)
x_.c(fiHead, x_.msg(2500, 660, osc2("gPrintln", "iiiiis", "1 1 8 1 FILTER")), 0)
x_.c(fiHead, x_.msg(2650, 660, osc2("gFillArea", "iiiiii", "0 0 21 10 1") + " " + osc2("gPrintln", "iiiiis", "2 1 8 0 RES")), 1)
for k in range(4):
    cx = 16 + 32 * k
    X = 2600 + k * 260
    tb = x_.obj(X, 700, "t b b")
    x_.c(fiT, tb, 3 - k)
    # text expr: $f1 mode (hot) $f2 AUX $f3 resonance knob $f4 frequency
    txE = x_.obj(X, 880, "expr if($f2 \\, 5 \\, if($f1==0 \\, 0 \\, ($f1-1)*2+1)) \\; "
                         "if($f2 \\, int((0.6+$f3*6)*10)/10.0 \\, int($f4))")
    x_.c(fiAux, txE, 0, 1)
    x_.c(tb, resV[k], 1); x_.c(resV[k], txE, 0, 2)
    # dial: needle from -135 (full LP) through 0 (off, up) to +135 (full HP); outlets 0 x 1 y 2 mode 3 frequency
    dE = x_.obj(X, 760, "expr "
                f"int({cx}+9*sin((-135+270*$f1)*0.017453)) \\; int(28-9*cos((-135+270*$f1)*0.017453)) \\; "
                "if($f1<0.47 \\, 1 \\, if($f1>0.53 \\, 2 \\, 0)) \\; "
                "if($f1<0.47 \\, 80*pow(225 \\, $f1/0.47) \\, 20*pow(400 \\, ($f1-0.53)/0.47))")
    x_.c(tb, fltV[k], 0); x_.c(fltV[k], dE)
    x_.c(dE, txE, 3, 3)                                 # frequency (fires first, cold)
    x_.c(dE, txE, 2, 0)                                 # mode (hot)
    dP = x_.obj(X, 790, "pack f f")
    x_.c(dE, dP, 1, 1); x_.c(dE, dP, 0, 0)
    x_.c(dP, x_.msg(X, 820, osc2("gCircle", "iiiii", f"{cx} 28 11 1") + " " +
                    osc2("gLine", "iiiiii", f"{cx} 28 \\$1 \\$2 1")))
    tP = x_.obj(X, 910, "pack f f")
    x_.c(txE, tP, 1, 1); x_.c(txE, tP, 0, 0)
    tR = x_.obj(X, 940, "route 0 1 2 3 4 5")
    x_.c(tP, tR)
    L1 = lambda txt: osc2("gPrintln", "iiiiis", f"{cx - 12} 43 8 1 {k + 1} {txt}")
    V = lambda suf: osc2("gPrintln", "iiiiif" + ("s" if suf else ""), f"{cx - 12} 54 8 1 \\$1" + (f" {suf}" if suf else ""))
    x_.c(tR, x_.msg(X, 970, L1("--")), 0)
    x_.c(tR, x_.msg(X, 1000, L1("LP") + " " + V("")), 1)
    x_.c(tR, x_.msg(X, 1030, L1("LP") + " " + V("k")), 2)
    x_.c(tR, x_.msg(X + 130, 970, L1("HP") + " " + V("")), 3)
    x_.c(tR, x_.msg(X + 130, 1000, L1("HP") + " " + V("k")), 4)
    x_.c(tR, x_.msg(X + 130, 1030, L1("Q") + " " + V("")), 5)

# ------------------------------------------------ MASTER page (apply_comp.py): COMP, SPEED, gain reduction
cvR = x_.obj(3600, 520, "route 1 2")
x_.c(x_.obj(3600, 490, "r comp-knob"), cvR); x_.c(x_.obj(3700, 490, "r comp-set"), cvR)
cvA = x_.obj(3600, 550, "f 0"); cvS = x_.obj(3700, 550, "f 0.5"); cvG = x_.obj(3800, 550, "f 0")
x_.c(cvR, cvA, 0, 1); x_.c(cvR, cvS, 1, 1)
x_.c(x_.obj(3800, 520, "r comp-gr"), cvG, 0, 1)
x_.c(x_.obj(3900, 490, "r comp-knob"), dOne); x_.c(x_.obj(3950, 490, "r comp-set"), dOne)
# live GR while the page is shown: redraw 10x/s
mpOn = x_.obj(3600, 600, "expr $f1==3 && $f2==3")
mpM = x_.obj(3600, 580, "t f")
x_.c(x_.obj(3600, 560, "r mode"), mpM); x_.c(mpM, mpOn, 0, 0)
mpP = x_.obj(3700, 580, "t b f")
x_.c(x_.obj(3700, 560, "r mix-page"), mpP); x_.c(mpP, mpOn, 1, 1); x_.c(mpP, mpOn, 0, 0)
mpMet = x_.obj(3600, 630, "metro 100")
x_.c(mpOn, mpMet); x_.c(mpMet, dOne)
msT = x_.obj(3600, 660, "t b b b b")
x_.c(psel, msT, 3)
x_.c(msT, x_.msg(3600, 690, osc2("gPrintln", "iiiiis", "1 1 8 1 MASTER") + " " +
                 osc2("gPrintln", "iiiiis", "1 15 8 1 COMP") + " " + osc2("gPrintln", "iiiiis", "1 27 8 1 SPEED") + " " +
                 osc2("gPrintln", "iiiiis", "1 39 8 1 GR") + " " +
                 osc2("gBox", "iiiiii", "64 14 63 9 1") + " " + osc2("gBox", "iiiiii", "64 26 63 9 1") + " " +
                 osc2("gBox", "iiiiii", "64 38 63 9 1")), 3)
caE = x_.obj(3600, 720, "expr int($f1*100+0.5) \\; int($f1*59)")
x_.c(msT, cvA, 2); x_.c(cvA, caE)
caP = x_.obj(3600, 750, "pack f f")
x_.c(caE, caP, 1, 1); x_.c(caE, caP, 0, 0)
x_.c(caP, x_.msg(3600, 780, osc2("gPrintln", "iiiiif", "38 15 8 1 \\$1") + " " + osc2("gFillArea", "iiiiii", "66 16 \\$2 5 1")))
csE = x_.obj(3800, 720, "expr int($f1*100+0.5) \\; int($f1*59)")
x_.c(msT, cvS, 1); x_.c(cvS, csE)
csP = x_.obj(3800, 750, "pack f f")
x_.c(csE, csP, 1, 1); x_.c(csE, csP, 0, 0)
x_.c(csP, x_.msg(3800, 780, osc2("gPrintln", "iiiiif", "38 27 8 1 \\$1") + " " + osc2("gFillArea", "iiiiii", "66 28 \\$2 5 1")))
cgE = x_.obj(4000, 720, "expr int($f1*10+0.5)/10.0 \\; int(min(59 \\, $f1*59/20))")
x_.c(msT, cvG, 0); x_.c(cvG, cgE)
cgP = x_.obj(4000, 750, "pack f f")
x_.c(cgE, cgP, 1, 1); x_.c(cgE, cgP, 0, 0)
x_.c(cgP, x_.msg(4000, 780, osc2("gPrintln", "iiiiif", "26 39 8 1 -\\$1") + " " + osc2("gFillArea", "iiiiii", "66 40 \\$2 5 1")))
x_.save("mix.pd")

# exec'd from gen.py: builds arp.pd - ARPEGGIATOR, 5th page of SEQ (AUX+E: TEMPO -> STEP -> TOMBOLA -> ENDLESS -> ARP)
# On the page, held keys are arpeggiated on the active instrument (through seq-notes) instead of being played
# (main.pd blocks their note-ons while arpcap is 1). Releases are always taken, so no note hangs if the page
# changes while a key is down.
# Knobs (ctx 40): 1 MODE up / down / u-d / rand / play (press order)  2 RATE 1/4 1/8 1/8T 1/16 1/16T 1/32
#                 3 OCT 1..4 octaves  4 GATE.   AUX + knob 1 (ctx 41): PROB, chance that a step sounds.
# AUX + C5: HOLD on / off (notes stay after the keys are released; a new chord replaces them).  AUX + B: clear.
# Clock: the tape's 16ths while the tape plays (aligned for recording), an internal 16th metro otherwise
# (first step 20 ms after the first key, so a chord is taken whole). Triplets and 1/32 are subdivided with [delay].
# State: tables arpm (128, 1 = note held), arpo (press order), arps (sorted); [v] arpc count, arpp position,
# arphold, arpdown (keys physically down), arprun, arpcur (last note), arpmode arprate arpoct arpgate arpprob,
# arpbeat (ms per beat), arpcap (page active), arpaux, arptp (tape playing).
# expr names have no '-' (in expr a-b is a minus b); a [v] is written through its own [v name] object.
MAXA = 16
SCa = "\\;"


def Ma(*parts):
    return " ".join(f"{SCa} {p}" for p in parts)


def osca(path, types, args):
    return f"{SCa} oscOut sendtyped /oled/{path} {types} 3 {args}"


ar = Patch(3000, 2000)
ar.text(20, 5, "arp: ARPEGGIATOR (SEQ page 5) - held keys are arpeggiated - AUX+C5 hold - AUX+B clear - "
               "knobs mode rate oct gate - AUX+knob 1 prob")
ar.obj(20, 30, "table arpm 128")
ar.obj(150, 30, f"table arpo {MAXA}")
ar.obj(280, 30, f"table arps {MAXA}")
DEFV = (("arpc", 0), ("arpp", 0), ("arphold", 0), ("arpdown", 0), ("arprun", 0), ("arpcur", -1), ("arpmode", 0),
        ("arprate", 3), ("arpoct", 0), ("arpgate", 0.5), ("arpprob", 1), ("arpbeat", 500), ("arpcap", 0),
        ("arpaux", 0), ("arptp", 0))


def V(name, x, y):
    """a [v name] object: a float writes the variable, a bang outputs it"""
    return ar.obj(x, y, f"v {name}")


def setTo(src, outlet, name, value, x, y):
    """src outlet -> [value( -> [v name]"""
    m_ = ar.msg(x, y, str(value))
    ar.c(src, m_, outlet)
    ar.c(m_, V(name, x, y + 25))


def counter_loop(x, y, src, outlet):
    """src outlet gives N -> the returned [f] counts 0 .. N-1 (reset to 0 first)"""
    t_ = ar.obj(x, y, "t f b")
    z_ = ar.msg(x + 80, y + 25, "0")
    u_ = ar.obj(x, y + 50, "until")
    f_ = ar.obj(x, y + 75, "f")
    p_ = ar.obj(x + 50, y + 75, "+ 1")
    ar.c(src, t_, outlet)
    ar.c(t_, z_, 1); ar.c(z_, f_, 0, 1)
    ar.c(t_, u_, 0); ar.c(u_, f_); ar.c(f_, p_); ar.c(p_, f_, 0, 1)
    return f_


def write_index(x, y, table):
    """returns (hit, rst, wMir): a value into hit is written at index w of table, then w + 1.
    rst sets w to 0; a bang into wMir outputs w (= values written) without changing it"""
    hit = ar.obj(x, y, "t b f")
    pk = ar.obj(x, y + 75, "pack f f")
    w = ar.obj(x + 100, y + 25, "f 0")
    wT = ar.obj(x + 100, y + 50, "t f f")
    w1 = ar.obj(x + 170, y + 50, "+ 1")
    wMir = ar.obj(x + 240, y + 75, "f 0")
    rst = ar.msg(x + 240, y + 25, "0")
    ar.c(hit, pk, 1, 1); ar.c(hit, w, 0)
    ar.c(w, wT); ar.c(wT, w1, 1); ar.c(w1, w, 0, 1); ar.c(w1, wMir, 0, 1); ar.c(wT, pk, 0, 0)
    ar.c(rst, w, 0, 1); ar.c(rst, wMir, 0, 1)
    ar.c(pk, ar.msg(x, y + 100, f"{SCa} {table} \\$1 \\$2"))
    return hit, rst, wMir


# ------------------------------------------------ defaults
lbI = ar.obj(20, 60, "loadbang")
lbIT = ar.obj(20, 90, "t b b")
ar.c(lbI, lbIT)
ar.c(lbIT, ar.msg(120, 90, Ma("arpm const 0", "arpo const 0", "arps const 0")), 1)
for i_, (nm_, val_) in enumerate(DEFV):
    setTo(lbIT, 0, nm_, val_, 300 + i_ * 70, 60)
dirty = ar.msg(2400, 60, "1")

# ------------------------------------------------ context: tempo, aux, tape, page active
ar.c(ar.obj(20, 160, "r tempo-beatms"), V("arpbeat", 20, 190))
ar.c(ar.obj(150, 160, "r aux"), V("arpaux", 150, 190))
pgE = ar.obj(300, 220, "expr $f1==4 && $f2==4")
pgM = ar.obj(300, 190, "t f")
pgP = ar.obj(400, 190, "t b f")
ar.c(ar.obj(300, 160, "r mode"), pgM); ar.c(pgM, pgE, 0, 0)
ar.c(ar.obj(400, 160, "r seq-page"), pgP); ar.c(pgP, pgE, 1, 1); ar.c(pgP, pgE, 0, 0)
pgC = ar.obj(300, 250, "change")
pgT = ar.obj(300, 280, "t f f f")                       # 2 [v arpcap]  1 screen metro  0 redraw on entry
ar.c(pgE, pgC); ar.c(pgC, pgT)
ar.c(pgT, V("arpcap", 450, 310), 2)
pgS = ar.obj(300, 310, "sel 1")
ar.c(pgT, pgS, 0); ar.c(pgS, dirty)

# ------------------------------------------------ rebuild arps (sorted) from arpm: 128 checks
rbT = ar.obj(800, 600, "t b b")
rbN = ar.msg(800, 630, "128")
ar.c(rbT, rbN, 0)
rbI = counter_loop(800, 660, rbN, 0)
rbHit, rbRst, _rbMir = write_index(800, 840, "arps")
ar.c(rbT, rbRst, 1)
rbIT = ar.obj(800, 770, "t f f")
rbE = ar.obj(900, 790, "expr arpm[$f1]")
rbSp = ar.obj(800, 810, "spigot")
ar.c(rbI, rbIT); ar.c(rbIT, rbE, 1); ar.c(rbE, rbSp, 0, 1); ar.c(rbIT, rbSp, 0); ar.c(rbSp, rbHit)

# ------------------------------------------------ compact arpo (keep the notes still held), arpc = how many
cpT = ar.obj(1200, 600, "t b b b")
cpN = ar.obj(1200, 630, "expr arpc")
ar.c(cpT, cpN, 1)
cpI = counter_loop(1200, 660, cpN, 0)
cpHit, cpRst, cpMir = write_index(1200, 860, "arpo")
ar.c(cpT, cpRst, 2)
cpV = ar.obj(1200, 770, "expr arpo[$f1]")
cpVT = ar.obj(1200, 795, "t f f")
cpE = ar.obj(1300, 815, "expr arpm[$f1]")
cpSp = ar.obj(1200, 835, "spigot")
ar.c(cpI, cpV); ar.c(cpV, cpVT); ar.c(cpVT, cpE, 1); ar.c(cpE, cpSp, 0, 1); ar.c(cpVT, cpSp, 0); ar.c(cpSp, cpHit)
ar.c(cpT, cpMir, 0); ar.c(cpMir, V("arpc", 1450, 960))

# ------------------------------------------------ clear / start / stop
clT = ar.obj(1700, 600, "t b b b")                     # tables, count, position (does not stop)
ar.c(clT, ar.msg(1800, 630, Ma("arpm const 0", "arpo const 0", "arps const 0")), 2)
setTo(clT, 1, "arpc", 0, 2000, 630)
setTo(clT, 0, "arpp", 0, 2070, 630)
mt = ar.obj(2300, 900, "metro 125")                     # internal 16ths while the tape is stopped
mtB = ar.obj(2400, 840, "t b")
mtI = ar.obj(2400, 870, "expr arpbeat/4")
ar.c(ar.obj(2400, 810, "r tempo-beatms"), mtB); ar.c(mtB, mtI); ar.c(mtI, mt, 0, 1)
mtC = ar.obj(2300, 930, "f 0")                          # internal 16th counter
mtC1 = ar.obj(2350, 930, "+ 1")
ar.c(mt, mtC); ar.c(mtC, mtC1); ar.c(mtC1, mtC, 0, 1)
mtGo = ar.obj(2200, 840, "t b b b")                     # internal clock: 2 counter 0  1 interval  0 start (first tick now)
mtZ = ar.msg(2250, 870, "0")
ar.c(mtGo, mtZ, 2); ar.c(mtZ, mtC, 0, 1)
ar.c(mtGo, mtB, 1)
mtStart = ar.msg(2200, 900, "1")
mtWait = ar.obj(2200, 870, "delay 20")                  # the first step 20 ms after the first key: a chord is taken whole
ar.c(mtGo, mtWait, 0); ar.c(mtWait, mtStart); ar.c(mtStart, mt)
mtStop = ar.msg(2150, 930, "stop")
ar.c(mtStop, mt)
stT = ar.obj(1700, 700, "t b b b")                     # start: 2 position 0  1 running  0 internal clock if tape stopped
setTo(stT, 2, "arpp", 0, 1800, 730)
setTo(stT, 1, "arprun", 1, 1870, 730)
stTp = ar.obj(1700, 760, "expr arptp==0")
stTpS = ar.obj(1700, 790, "sel 1")
ar.c(stT, stTp, 0); ar.c(stTp, stTpS); ar.c(stTpS, mtGo)
spT = ar.obj(2000, 700, "t b b b")                     # stop: 2 not running  1 metro off  0 redraw
setTo(spT, 2, "arprun", 0, 2100, 730)
ar.c(spT, mtStop, 1)
mtWaitStop = ar.msg(2100, 960, "stop")
ar.c(spT, mtWaitStop, 1); ar.c(mtWaitStop, mtWait)
ar.c(spT, dirty, 0)
stChk = ar.obj(1700, 400, "expr arpc>0 && arprun==0")  # after a note was added
stChkS = ar.obj(1700, 430, "sel 1")
ar.c(stChk, stChkS); ar.c(stChkS, stT)
spChk = ar.obj(2000, 400, "expr arpc==0 && arprun")    # after a note was removed
spChkS = ar.obj(2000, 430, "sel 1")
ar.c(spChk, spChkS); ar.c(spChkS, spT)
csT = ar.obj(2300, 400, "t b b")                       # clear + stop
ar.c(csT, clT, 1); ar.c(csT, spT, 0)
# the tape starts / stops: tape 16ths take over, or the internal clock goes on
tpT = ar.obj(2600, 160, "t f f")
ar.c(ar.obj(2600, 130, "r tp-play"), tpT)
ar.c(tpT, V("arptp", 2700, 190), 1)
tpE = ar.obj(2600, 190, "expr if(arprun \\, $f1 \\, -1)")
tpS = ar.obj(2600, 220, "sel 1 0")
ar.c(tpT, tpE, 0); ar.c(tpE, tpS)
ar.c(tpS, mtStop, 0); ar.c(tpS, mtWaitStop, 0); ar.c(tpS, mtGo, 1)

# ------------------------------------------------ keys: classify (1 = note-on for the arp, 2 = release) then handle
nIn = ar.obj(20, 400, "r notes")
nT = ar.obj(20, 430, "t l l")
clsE = ar.obj(120, 460, "expr if($f2>0 \\, if(arpcap && arpaux==0 \\, 1 \\, 0) \\, 2)")
nLp = ar.obj(20, 490, "list prepend 0")
nRt = ar.obj(20, 520, "route 1 2")
ar.c(nIn, nT); ar.c(nT, clsE, 1); ar.c(clsE, nLp, 0, 1); ar.c(nT, nLp, 0); ar.c(nLp, nRt)
onU = ar.obj(20, 550, "unpack f f")
offU = ar.obj(300, 550, "unpack f f")
ar.c(nRt, onU, 0); ar.c(nRt, offU, 1)
# note-on: 3 hold + no key down = new chord: clear   2 keys down + 1   1 add the note   0 rebuild, start
onT = ar.obj(20, 580, "t b f f b")
ar.c(onU, onT, 0)
hcE = ar.obj(120, 610, "expr arphold && arpdown==0")
hcS = ar.obj(120, 640, "sel 1")
ar.c(onT, hcE, 3); ar.c(hcE, hcS); ar.c(hcS, clT)
dnE = ar.obj(200, 610, "expr arpdown+1+0*$f1")
ar.c(onT, dnE, 2); ar.c(dnE, V("arpdown", 200, 640))
adT = ar.obj(300, 610, "t f f")
adE = ar.obj(400, 640, f"expr arpm[$f1]==0 && arpc<{MAXA}")
adSp = ar.obj(300, 660, "spigot")
ar.c(onT, adT, 1); ar.c(adT, adE, 1); ar.c(adE, adSp, 0, 1); ar.c(adT, adSp, 0)
adW = ar.obj(300, 690, "t b f f")                       # 2 arpm[n] = 1  1 n waits  0 arpo[arpc] = n, arpc + 1
ar.c(adSp, adW)
ar.c(adW, ar.msg(500, 720, f"{SCa} arpm \\$1 1"), 2)
adP = ar.obj(300, 780, "pack f f")
ar.c(adW, adP, 1, 1)
adI = ar.obj(300, 720, "expr arpc")
adIT = ar.obj(300, 750, "t f f")
adInc = ar.obj(400, 750, "+ 1")
ar.c(adW, adI, 0); ar.c(adI, adIT); ar.c(adIT, adInc, 1); ar.c(adInc, V("arpc", 400, 775)); ar.c(adIT, adP, 0, 0)
ar.c(adP, ar.msg(300, 810, f"{SCa} arpo \\$1 \\$2"))
onEnd = ar.obj(20, 850, "t b b b")                      # 2 rebuild  1 start if needed  0 redraw
ar.c(onT, onEnd, 0)
ar.c(onEnd, rbT, 2); ar.c(onEnd, stChk, 1); ar.c(onEnd, dirty, 0)
# release: 1 keys down - 1   0 without HOLD: arpm[n] = 0, compact, rebuild, stop if empty
ofT = ar.obj(300, 580, "t f b")
ar.c(offU, ofT, 0)
dn2 = ar.obj(400, 610, "expr max(0 \\, arpdown-1)")
ar.c(ofT, dn2, 1); ar.c(dn2, V("arpdown", 400, 640))
ofT2 = ar.obj(600, 610, "t f f")
ofE = ar.obj(700, 640, "expr arphold==0")
ofSp = ar.obj(600, 660, "spigot")
ar.c(ofT, ofT2, 0); ar.c(ofT2, ofE, 1); ar.c(ofE, ofSp, 0, 1); ar.c(ofT2, ofSp, 0)
ofW = ar.obj(600, 690, "t b b b b f")                   # 4 arpm[n] = 0  3 compact  2 rebuild  1 stop if empty  0 redraw
ar.c(ofSp, ofW)
ar.c(ofW, ar.msg(700, 720, f"{SCa} arpm \\$1 0"), 4)
ar.c(ofW, cpT, 3); ar.c(ofW, rbT, 2); ar.c(ofW, spChk, 1); ar.c(ofW, dirty, 0)

# ------------------------------------------------ AUX keys on the page: C5 hold, B clear
akSp = ar.obj(20, 1000, "spigot")
akE = ar.obj(120, 980, "expr arpcap")
akT = ar.obj(20, 980, "t f b")
ar.c(ar.obj(20, 950, "r aux-key"), akT); ar.c(akT, akE, 1); ar.c(akE, akSp, 0, 1); ar.c(akT, akSp, 0)
akS = ar.obj(20, 1030, "sel 72 71")
ar.c(akSp, akS)
hoE = ar.obj(20, 1060, "expr arphold==0")
hoT = ar.obj(20, 1090, "t f f b")                       # 2 redraw  1 [v arphold]  0 turned off: clear + stop
ar.c(akS, hoE, 0); ar.c(hoE, hoT)
ar.c(hoT, dirty, 2); ar.c(hoT, V("arphold", 120, 1120), 1)
hoS = ar.obj(20, 1120, "sel 0")
ar.c(hoT, hoS, 0); ar.c(hoS, csT)
ar.c(akS, csT, 1)
# a project load: HOLD off, everything cleared
ldT = ar.obj(300, 1000, "t b b")
ar.c(ar.obj(300, 970, "r nst-load"), ldT)
setTo(ldT, 1, "arphold", 0, 400, 1030)
ar.c(ldT, csT, 0)

# ------------------------------------------------ knobs (arp-knob from the router; arp-set / arp-aux-set from projects)
kLp = ar.obj(800, 1030, "list prepend 0")
kAx = ar.obj(800, 1060, "route 0 1")
ar.c(ar.obj(800, 1000, "r arp-knob"), kLp); ar.c(ar.obj(900, 1000, "r aux"), kLp, 0, 1); ar.c(kLp, kAx)
kR = ar.obj(800, 1100, "route 1 2 3 4")
ar.c(kAx, kR, 0); ar.c(ar.obj(1000, 1070, "r arp-set"), kR)
kP = ar.obj(1300, 1100, "route 1")
ar.c(kAx, kP, 1); ar.c(ar.obj(1300, 1070, "r arp-aux-set"), kP)
KN = (("expr int(min($f1 \\, 0.999)*5)", "arpmode"), ("expr int(min($f1 \\, 0.999)*6)", "arprate"),
      ("expr int(min($f1 \\, 0.999)*4)", "arpoct"), ("expr 0.05+$f1*0.9", "arpgate"))
for i_, (ex_, nm_) in enumerate(KN):
    e_ = ar.obj(800 + i_ * 120, 1130, ex_)
    t_ = ar.obj(800 + i_ * 120, 1160, "t b f")
    ar.c(kR, e_, i_); ar.c(e_, t_); ar.c(t_, V(nm_, 800 + i_ * 120, 1190), 1); ar.c(t_, dirty, 0)
kPt = ar.obj(1300, 1130, "t b f")
ar.c(kP, kPt); ar.c(kPt, V("arpprob", 1300, 1160), 1); ar.c(kPt, dirty, 0)

# ------------------------------------------------ ticks -> steps (1/8T, 1/16T, 1/32: extra steps by [delay])
tkT = ar.obj(20, 1300, "t f f")
tkE = ar.obj(120, 1330, "expr arprun && arptp")
tkSp = ar.obj(20, 1350, "spigot")
ar.c(ar.obj(20, 1270, "r tick16"), tkT); ar.c(tkT, tkE, 1); ar.c(tkE, tkSp, 0, 1); ar.c(tkT, tkSp, 0)
mtT = ar.obj(2300, 960, "t f f")
mtE = ar.obj(2400, 990, "expr arprun && arptp==0")
mtSp = ar.obj(2300, 1010, "spigot")
ar.c(mtC, mtT); ar.c(mtT, mtE, 1); ar.c(mtE, mtSp, 0, 1); ar.c(mtT, mtSp, 0)
tick = ar.obj(20, 1380, "t f")
ar.c(tkSp, tick); ar.c(mtSp, tick)
fireE = ar.obj(20, 1410, "expr if(arprate==0 || arprate==2 \\, $f1%4==0 \\, if(arprate==1 || arprate==4 \\, $f1%2==0 \\, 1))")
fireS = ar.obj(20, 1440, "sel 1")
fireT = ar.obj(20, 1470, "t b b b")                     # 2 second extra step  1 first extra step  0 step now
ar.c(tick, fireE); ar.c(fireE, fireS); ar.c(fireS, fireT)
step = ar.obj(20, 1600, "t b")
ar.c(fireT, step, 0)
for k_, ex_ in enumerate(("if(arprate==2 \\, arpbeat/3 \\, if(arprate==4 \\, arpbeat/6 \\, if(arprate==5 \\, arpbeat/8 \\, -1)))",
                          "if(arprate==2 \\, 2*arpbeat/3 \\, if(arprate==4 \\, arpbeat/3 \\, -1))")):
    x_ = 200 + k_ * 200
    e_ = ar.obj(x_, 1500, f"expr {ex_}")
    m_ = ar.obj(x_, 1530, "moses 0")
    t_ = ar.obj(x_, 1560, "t b f")
    d_ = ar.obj(x_, 1590, "delay")
    ar.c(fireT, e_, 1 + k_); ar.c(e_, m_); ar.c(m_, t_, 1)
    ar.c(t_, d_, 1, 1); ar.c(t_, d_, 0, 0)
    ar.c(d_, step)
# a step: 3 chance  2 the note  1 next position  0 play it (gate time first)
sgE = ar.obj(20, 1630, "expr arprun && arpc>0")
sgS = ar.obj(20, 1660, "sel 1")
sT = ar.obj(20, 1690, "t b b b b")
ar.c(step, sgE); ar.c(sgE, sgS); ar.c(sgS, sT)
pR = ar.obj(400, 1720, "random 100")
pE = ar.obj(400, 1750, "expr $f1<arpprob*100")
okF = ar.obj(400, 1780, "f")
ar.c(sT, pR, 3); ar.c(pR, pE); ar.c(pE, okF, 0, 1)
C, L_ = "arpc", "(arpc*(arpoct+1))"
K_ = f"(2*{L_}-2)"
P_ = "arpp"
qExpr = (f"if(arpmode==0 || arpmode==4 \\, {P_}%{L_} \\, if(arpmode==1 \\, {L_}-1-{P_}%{L_} \\, "
         f"if(arpmode==2 \\, if({L_}<2 \\, 0 \\, if({P_}%{K_}<{L_} \\, {P_}%{K_} \\, {K_}-{P_}%{K_})) \\, $f1%{L_})))")
rI = ar.obj(200, 1720, "random 1000")
qE = ar.obj(200, 1750, f"expr {qExpr}")
nE = ar.obj(200, 1780, f"expr if(arpmode==4 \\, arpo[$f1%{C}] \\, arps[$f1%{C}])+12*int($f1/{C})")
nTT = ar.obj(200, 1810, "t f f")
noteF = ar.obj(200, 1840, "f")
ar.c(sT, rI, 2); ar.c(rI, qE); ar.c(qE, nE); ar.c(nE, nTT)
ar.c(nTT, V("arpcur", 300, 1840), 1); ar.c(nTT, noteF, 0, 1)
adv = ar.obj(600, 1720, "expr arpp+1")
ar.c(sT, adv, 1); ar.c(adv, V("arpp", 600, 1750))
plT = ar.obj(20, 1720, "t b b b")                       # 2 gate time  1 play if the chance said so  0 redraw
ar.c(sT, plT, 0)
gE = ar.obj(20, 1750, "expr arpbeat*if(arprate==0 \\, 1 \\, if(arprate==1 \\, 0.5 \\, if(arprate==2 \\, 1/3 \\, "
                      "if(arprate==3 \\, 0.25 \\, if(arprate==4 \\, 1/6 \\, 0.125)))))*arpgate")
offP = ar.obj(20, 1900, "pipe 100")
ar.c(plT, gE, 2); ar.c(gE, offP, 0, 1)
okS = ar.obj(100, 1780, "sel 1")
ar.c(plT, okF, 1); ar.c(okF, okS); ar.c(okS, noteF)
ntT = ar.obj(100, 1870, "t f f")
sn = ar.obj(100, 1960, "s seq-notes")
ar.c(noteF, ntT)
onM = ar.msg(200, 1900, "\\$1 100")
ar.c(ntT, onM, 1); ar.c(onM, sn)
ar.c(ntT, offP, 0)
ofM = ar.msg(20, 1930, "\\$1 0")
ar.c(offP, ofM); ar.c(ofM, sn)
ar.c(plT, dirty, 0)

# ------------------------------------------------ screen (page active): full redraw when dirty, at most 10 / s
dF = ar.obj(2400, 120, "f 1")
ar.c(dirty, dF, 0, 1)
mtr = ar.obj(2500, 90, "metro 100")
ar.c(pgT, mtr, 1); ar.c(mtr, dF)
dS = ar.obj(2400, 150, "sel 1")
dZ = ar.msg(2550, 150, "0")
full = ar.obj(2400, 180, "t b b b b")                   # 3 header  2 notes  1 bottom row  0 flip
ar.c(dF, dS); ar.c(dS, full); ar.c(dS, dZ); ar.c(dZ, dF, 0, 1)
# 3: header: ARP, chance, HOLD
hdT = ar.obj(2400, 210, "t b b b")
ar.c(full, hdT, 3)
ar.c(hdT, ar.msg(2400, 240, osca("gShowInfoBar", "ii", "0") + " " + osca("gClear", "ii", "1") + " " +
                 osca("gPrintln", "iiiiis", "1 1 8 1 ARP")), 2)
prE = ar.obj(2600, 240, "expr int(arpprob*100+0.5)")
ar.c(hdT, prE, 1); ar.c(prE, ar.msg(2600, 270, osca("gPrintln", "iiiiisf", "40 1 8 1 P \\$1")))
hlE = ar.obj(2800, 240, "expr arphold")
hlS = ar.obj(2800, 270, "sel 1")
ar.c(hdT, hlE, 0); ar.c(hlE, hlS)
ar.c(hlS, ar.msg(2800, 300, osca("gFillArea", "iiiiii", "98 0 30 10 1") + " " + osca("gPrintln", "iiiiis", "100 1 8 0 HOLD")))
# 2: the held notes, sorted (higher = higher on screen); the one playing is a bigger block
noT = ar.obj(2400, 330, "t b b")
ar.c(full, noT, 2)
emE = ar.obj(2600, 360, "expr arpc==0")
emS = ar.obj(2600, 390, "sel 1")
ar.c(noT, emE, 1); ar.c(emE, emS)
ar.c(emS, ar.msg(2600, 420, osca("gPrintln", "iiiiiss", "16 28 8 1 HOLD KEYS")))
noN = ar.obj(2400, 360, "expr arpc")
ar.c(noT, noN, 0)
noI = counter_loop(2400, 390, noN, 0)
CUR = "(arpcur>=arps[$f1] && (arpcur-arps[$f1])%12==0)"
Y = "max(12 \\, min(44 \\, 44-int((arps[$f1]-36)*0.75)))"
noE = [ar.obj(2400 + j_ * 150, 500, f"expr {ex_}") for j_, ex_ in enumerate((
    f"4+$f1*8-{CUR}", f"{Y}-2*{CUR}", f"4+2*{CUR}", f"3+3*{CUR}"))]
noP = ar.obj(2400, 530, "pack f f f f")
noIT = ar.obj(2400, 470, "t f f f f")
ar.c(noI, noIT)
for j_ in range(4):
    ar.c(noIT, noE[j_], j_); ar.c(noE[j_], noP, 0, j_)          # x (pack hot inlet) last
ar.c(noP, ar.msg(2400, 560, osca("gFillArea", "iiiiii", "\\$1 \\$2 \\$3 \\$4 1")))
# 1: bottom row: mode, rate, octaves, gate
btT = ar.obj(2400, 620, "t b b b b")
ar.c(full, btT, 1)
for j_, (ex_, names_, x_) in enumerate((("arpmode", ("up", "down", "u/d", "rand", "play"), 1),
                                         ("arprate", ("1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32"), 28))):
    e_ = ar.obj(2400 + j_ * 300, 650, f"expr {ex_}")
    s_ = ar.obj(2400 + j_ * 300, 680, "sel " + " ".join(str(k_) for k_ in range(len(names_))))
    ar.c(btT, e_, 3 - j_); ar.c(e_, s_)
    for k_, nm_ in enumerate(names_):
        ar.c(s_, ar.msg(2400 + j_ * 300 + k_ * 50, 710 + (k_ % 2) * 20, osca("gPrintln", "iiiiis", f"{x_} 55 8 1 {nm_}")), k_)
ocE = ar.obj(3000, 650, "expr arpoct+1")
ar.c(btT, ocE, 1); ar.c(ocE, ar.msg(3000, 680, osca("gPrintln", "iiiiisf", "62 55 8 1 O \\$1")))
gtE = ar.obj(3100, 650, "expr int(arpgate*100+0.5)")
ar.c(btT, gtE, 0); ar.c(gtE, ar.msg(3100, 680, osca("gPrintln", "iiiiisf", "86 55 8 1 G \\$1")))
ar.c(full, ar.msg(2400, 760, f"{SCa} oscOut sendtyped /oled/gFlip i 3"), 0)
ar.save("arp.pd")

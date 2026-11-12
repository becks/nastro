# exec'd from gen.py: builds reverb.pd - the master reverb (abstraction used by master.pd)
# pre-delay -> 4 series allpass diffusers -> 8-line feedback delay network (Hadamard matrix, per-line damping
# and decay gains, 2 slowly modulated lines) -> stereo out.  Params (AUX + knobs on the FX page, ctx 16):
#   rvb-knob / rvb-set  1 DECAY (T60 0.4..12 s)  2 TONE (damping 1.5..12 kHz)  3 PRE (0..120 ms)  4 MOD (depth)
# DSP is switched off (switch~) when the reverb send is 0 and the tail has died away.
LINES = [31.7, 37.3, 41.1, 47.9, 53.3, 59.9, 67.1, 73.7]   # ms
AP = [(4.77, 0.75), (3.59, 0.75), (12.73, 0.625), (9.31, 0.625)]
MODL = (1, 6)                                             # modulated lines (vd~)
MODHZ = (0.53, 0.37)

rv = Patch(2400, 1400)
rv.text(20, 5, "reverb: pre-delay - 4 allpass diffusers - 8 line FDN (Hadamard) - damping + decay per line - 2 modulated lines")
inl = rv.obj(20, 40, "inlet~")
outL = rv.obj(20, 1300, "outlet~")
outR = rv.obj(200, 1300, "outlet~")
sw = rv.obj(600, 40, "switch~")

# ---------------- params
rk = rv.obj(600, 100, "r rvb-knob")
krt = rv.obj(600, 130, "route 1 2 3 4")
rv.c(rk, krt); rv.c(rv.obj(700, 100, "r rvb-set"), krt)   # [r name] has no inlet: both feed the route
t60E = rv.obj(600, 170, "expr 0.4*pow(30 \\, $f1)")
toneE = rv.obj(750, 170, "expr 1500*pow(8 \\, $f1)")
preE = rv.obj(900, 170, "expr 1+$f1*120")
modE = rv.obj(1050, 170, "expr $f1*1.2")
for i, e in enumerate((t60E, toneE, preE, modE)):
    rv.c(krt, e, i)
t60T = rv.obj(600, 200, "t f f")
rv.c(t60E, t60T)
rv.c(t60T, rv.obj(700, 230, "v rvb-t60"), 1)
# per line gain: 10^(-3 L / T60), times 1/sqrt(8) for the (unnormalised) Hadamard
gE = rv.obj(600, 260, "expr " + " \\; ".join(f"pow(10 \\, -3*{L}/1000/$f1)*0.353553" for L in LINES))
gGate = rv.obj(600, 230, "spigot 1")
rv.c(t60T, gGate, 0); rv.c(gGate, gE)
defs = rv.msg(800, 60, "1 0.5 \\, 2 0.6 \\, 3 0.15 \\, 4 0.3")
rv.c(rv.obj(800, 30, "loadbang"), defs); rv.c(defs, krt)
preM = rv.msg(900, 200, "\\$1 50")
preL = rv.obj(900, 230, "line~")
rv.c(preE, preM); rv.c(preM, preL)

# ---------------- on / off: on as soon as the send is up; off T60 + 0.5 s after it went to 0
rmx = rv.obj(1300, 40, "r fx-rmix")
rmxS = rv.obj(1300, 70, "> 0")
rmxC = rv.obj(1300, 100, "change")
rv.c(rmx, rmxS); rv.c(rmxS, rmxC)
rmxF = rv.obj(1400, 70, "f 0")
rv.c(rmxS, rmxF, 0, 1)
onOff = rv.obj(1300, 130, "sel 1 0")
rv.c(rmxC, onOff)
on1 = rv.msg(1300, 160, "1")
offD = rv.obj(1400, 190, "delay")
offStop = rv.msg(1250, 190, "stop")
rv.c(onOff, on1, 0); rv.c(onOff, offStop, 0); rv.c(offStop, offD)
rv.c(on1, sw)
offB = rv.obj(1400, 160, "t b")
offGate = rv.obj(1400, 145, "spigot 1")                  # REV to 0 while frozen: stay on
rv.c(onOff, offGate, 1); rv.c(offGate, offB)
offT = rv.obj(1400, 175, "v rvb-t60")
offMs = rv.obj(1500, 175, "expr $f1*1000+500")
rv.c(offB, offT); rv.c(offT, offMs); rv.c(offMs, offD)
off0 = rv.msg(1400, 220, "0")
rv.c(offD, off0); rv.c(off0, sw)
lb0 = rv.msg(1450, 10, "0")
rv.c(rv.obj(1500, 10, "loadbang"), lb0); rv.c(lb0, sw)

# ---------------- pre-delay
preW = rv.obj(20, 80, "delwrite~ rvb-pre 130")
inG = rv.obj(20, 60, "*~")                                    # freeze: input closed (apply_freeze.py); signal gain
rv.c(inl, inG); rv.c(inG, preW)
fzIn = rv.obj(1700, 40, "r rvb-freeze")
fzT = rv.obj(1700, 70, "t f f f f")
fzInv = rv.obj(1700, 100, "expr 1-$f1"); fzInM = rv.msg(1700, 130, "\\$1 50"); fzInL = rv.obj(1700, 160, "line~")
rv.c(fzIn, fzT); rv.c(fzT, fzInv, 3); rv.c(fzInv, fzInM); rv.c(fzInM, fzInL); rv.c(fzInL, inG, 0, 1)
lbG1 = rv.msg(1800, 130, "1")
rv.c(rv.obj(1800, 100, "loadbang"), lbG1); rv.c(lbG1, fzInL)
preR = rv.obj(20, 110, "vd~ rvb-pre")
rv.c(preL, preR)
x = preR

# ---------------- allpass diffusers:  w = x + g*d ; y = d - g*w ; d = w delayed
for k, (ms, g) in enumerate(AP):
    X = 20 + k * 200
    d = rv.obj(X, 150, f"delread~ rvb-ap{k} {ms}")
    gd = rv.obj(X, 180, f"*~ {g}")
    w = rv.obj(X, 210, "+~")
    rv.c(d, gd); rv.c(x, w, 0, 0); rv.c(gd, w, 0, 1)
    rv.c(w, rv.obj(X, 240, f"delwrite~ rvb-ap{k} 20"))
    ngw = rv.obj(X + 80, 240, f"*~ {-g}")
    y = rv.obj(X, 270, "+~")
    rv.c(w, ngw); rv.c(d, y, 0, 0); rv.c(ngw, y, 0, 1)
    x = y

# ---------------- FDN
inj = rv.obj(20, 330, "*~ 0.5")
injN = rv.obj(120, 330, "*~ -0.5")
rv.c(x, inj); rv.c(x, injN)
sums, damped, lps = [], [], []
lfo = {}
for j, (li, hz) in enumerate(zip(MODL, MODHZ)):
    o = rv.obj(1600 + j * 200, 300, f"osc~ {hz}")
    dep = rv.obj(1600 + j * 200, 330, "*~ 0.36")
    rv.c(o, dep); rv.c(modE, dep, 0, 1)
    base = rv.obj(1600 + j * 200, 360, f"+~ {LINES[li]}")
    rv.c(dep, base)
    lfo[li] = base
for i, L in enumerate(LINES):
    X = 20 + i * 140
    s_ = rv.obj(X, 400, "+~")                                   # input + feedback
    rv.c(inj if i % 2 == 0 else injN, s_, 0, 0)
    rv.c(s_, rv.obj(X, 430, f"delwrite~ rvb-l{i} 100"))
    if i in lfo:
        d = rv.obj(X, 470, f"vd~ rvb-l{i}")
        rv.c(lfo[i], d)
    else:
        d = rv.obj(X, 470, f"delread~ rvb-l{i} {L}")
    lp = rv.obj(X, 500, "lop~ 5000")
    lps.append(lp)
    gm = rv.obj(X, 530, "*~ 0.3")
    rv.c(gE, gm, i, 1)
    rv.c(d, lp); rv.c(lp, gm)
    sums.append(s_); damped.append(gm)
# Hadamard 8 = 3 butterfly stages
stage = damped
for st, step in enumerate((1, 2, 4)):
    nxt = [None] * 8
    for a in range(8):
        if a & step:
            continue
        b = a + step
        p = rv.obj(20 + a * 140, 600 + st * 80, "+~")
        m = rv.obj(20 + b * 140, 600 + st * 80, "-~")
        rv.c(stage[a], p, 0, 0); rv.c(stage[b], p, 0, 1)
        rv.c(stage[a], m, 0, 0); rv.c(stage[b], m, 0, 1)
        nxt[a], nxt[b] = p, m
    stage = nxt
for i in range(8):
    rv.c(stage[i], sums[i], 0, 1)                               # feedback into each line
# ---------------- outputs: even lines left, odd lines right
oL = rv.obj(20, 1250, "*~ 5"); oR = rv.obj(200, 1250, "*~ 5")      # level matched to the old reverb (same REV knob = same loudness)
for i in range(8):
    rv.c(damped[i], oL if i % 2 == 0 else oR)
rv.c(oL, outL); rv.c(oR, outR)

# ---------------- freeze (apply_freeze.py): gains, damping, on/off
fzSel = rv.obj(1700, 200, "sel 1 0")
rv.c(fzT, fzSel, 0)
gOpen = rv.obj(1850, 200, "== 0")
rv.c(fzT, gOpen, 2); rv.c(gOpen, gGate, 0, 1)                  # DEC gate: closed while frozen
rv.c(gOpen, offGate, 0, 1)                                     # no switch-off while frozen
tGate = rv.obj(750, 200, "spigot 1")
rv.c(gOpen, tGate, 0, 1)
toneF = rv.obj(850, 200, "f 4800")
rv.c(toneE, toneF, 0, 1); rv.c(toneE, tGate)
fzOn = rv.obj(1700, 230, "t b b b")                             # frozen: 2) DSP on  1) lossless gains  0) damping open
rv.c(fzSel, fzOn, 0)
rv.c(fzOn, on1, 2); rv.c(fzOn, offStop, 2)
fzG = rv.msg(1700, 260, "0.3535")
rv.c(fzOn, fzG, 1)
fzTone = rv.msg(1800, 260, "20000")
rv.c(fzOn, fzTone, 0)
fzOff = rv.obj(1900, 230, "t b b b")                            # released: 2) gains from DEC  1) damping from TONE  0) off?
rv.c(fzSel, fzOff, 1)
offT2 = rv.obj(1950, 260, "v rvb-t60")
rv.c(fzOff, offT2, 2); rv.c(offT2, gE)
rv.c(fzOff, toneF, 1)
offChk = rv.obj(2050, 260, "sel 0")
rv.c(fzOff, rmxF, 0); rv.c(rmxF, offChk); rv.c(offChk, offB)
for i in range(8):
    rv.c(fzG, damped[i], 0, 1)
for lp_ in lps:
    rv.c(fzTone, lp_, 0, 1); rv.c(toneF, lp_, 0, 1); rv.c(tGate, lp_, 0, 1)
# AUX + G5 toggles; loading a project releases it
fzK = rv.obj(1700, 320, "r aux-key")
fzKs = rv.obj(1700, 350, "sel 79")
fzState = rv.obj(1700, 380, "f 0")
fzNot = rv.obj(1750, 380, "== 0")
rv.c(fzK, fzKs); rv.c(fzKs, fzState); rv.c(fzState, fzNot); rv.c(fzNot, fzState, 0, 1)
rv.c(fzNot, rv.obj(1700, 410, "s rvb-freeze"))
fzTs = rv.obj(1600, 410, "sel 0 1")                   # message on the screen (apply_toast2.py)
rv.c(fzNot, fzTs)
rv.c(fzTs, rv.msg(1500, 440, "\\; nst-toast REVERB FREEZE OFF"), 0); rv.c(fzTs, rv.msg(1600, 440, "\\; nst-toast REVERB FREEZE ON"), 1)
fzRel = rv.msg(1850, 350, "0")
rv.c(rv.obj(1850, 320, "r nst-load"), fzRel); rv.c(fzRel, fzState, 0, 1); rv.c(fzRel, rv.obj(1850, 380, "s rvb-freeze"))
rv.save("reverb.pd")

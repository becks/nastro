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
rv.c(t60T, gE, 0)
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
onOff = rv.obj(1300, 130, "sel 1 0")
rv.c(rmxC, onOff)
on1 = rv.msg(1300, 160, "1")
offD = rv.obj(1400, 190, "delay")
offStop = rv.msg(1250, 190, "stop")
rv.c(onOff, on1, 0); rv.c(onOff, offStop, 0); rv.c(offStop, offD)
rv.c(on1, sw)
offB = rv.obj(1400, 160, "t b")
rv.c(onOff, offB, 1)
offT = rv.obj(1400, 175, "v rvb-t60")
offMs = rv.obj(1500, 175, "expr $f1*1000+500")
rv.c(offB, offT); rv.c(offT, offMs); rv.c(offMs, offD)
off0 = rv.msg(1400, 220, "0")
rv.c(offD, off0); rv.c(off0, sw)
lb0 = rv.msg(1450, 10, "0")
rv.c(rv.obj(1500, 10, "loadbang"), lb0); rv.c(lb0, sw)

# ---------------- pre-delay
preW = rv.obj(20, 80, "delwrite~ rvb-pre 130")
rv.c(inl, preW)
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
sums, damped = [], []
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
    rv.c(toneE, lp, 0, 1)
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
rv.save("reverb.pd")

#!/usr/bin/env python3
"""Per-track FX sends. Each tape track gets a delay send and a reverb send (0..1, default 1). They scale what the
track feeds into the delay and reverb; DLY and REV on the FX page stay the overall amounts (and the live synth
goes to the FX through them as before). At the defaults the sound is exactly as before.
New MIX page 5, SEND (after MASTER): knob 1..4 = delay send of track 1..4, AUX held = reverb send.
Knob contexts 27 (delay sends) and 28 (reverb sends): pkval / pkpick 108 -> 116; old projects get 1."""
import shutil

for f in ("gentape.py", "genmix.py", "gen.py", "genproj.py"):
    shutil.copy(f, f + ".pre-sends")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# --- tape: per track mono (post filter, post pan) x send -> FX buses
edit("gentape.py", [
    ("    t.c(gLp, thL); t.c(gRp, thR)\n", r'''    t.c(gLp, thL); t.c(gRp, thR)
    # FX sends (apply_sends.py): (L + R) / 2 as the old mono FX feed, x delay / reverb send
    fxM = t.obj(x + 1300, 950, "+~"); fxH = t.obj(x + 1300, 980, "*~ 0.5")
    t.c(gLp, fxM, 0, 0); t.c(gRp, fxM, 0, 1); t.c(fxM, fxH)
    for j, (rt_, bus) in enumerate(((sdR, "fxd-tape"), (srR, "fxr-tape"))):
        sm = t.msg(x + 1300 + j * 100, 1010, "\\$1 20"); sl = t.obj(x + 1300 + j * 100, 1040, "line~")
        si = t.msg(x + 1360 + j * 100, 1010, "1")
        t.c(rt_, sm, k); t.c(sm, sl); t.c(lbS, si); t.c(si, sl)
        sx_ = t.obj(x + 1300 + j * 100, 1070, "*~"); st_ = t.obj(x + 1300 + j * 100, 1100, f"throw~ {bus}")
        t.c(fxH, sx_, 0, 0); t.c(sl, sx_, 0, 1); t.c(sx_, st_)
'''),
    ("tws, dubs = [], []\n", '''tws, dubs = [], []
sdR = t.obj(2600, 900, "route 1 2 3 4"); srR = t.obj(2800, 900, "route 1 2 3 4")      # FX sends (apply_sends.py)
t.c(t.obj(2600, 870, "r dsend-knob"), sdR); t.c(t.obj(2650, 850, "r dsend-set"), sdR)
t.c(t.obj(2800, 870, "r rsend-knob"), srR); t.c(t.obj(2850, 850, "r rsend-set"), srR)
lbS = t.obj(3000, 870, "loadbang")
'''),
])

# --- master: delay <- synth + track delay sends ; reverb <- synth + track reverb sends + delay out
edit("genmix.py", [
    ('''tMono = ms.obj(200, 70, "+~")
tHalf = ms.obj(200, 75, "*~ 0.5")
ms.c(ctL, tMono, 0, 0); ms.c(ctR, tMono, 0, 1); ms.c(tMono, tHalf)
''', '''cfd = ms.obj(200, 70, "catch~ fxd-tape"); cfr = ms.obj(330, 70, "catch~ fxr-tape")      # per-track FX sends
'''),
    ("ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(tHalf, dry, 0, 1)      # mono send for the FX",
     '''ms.c(cs, sti); ms.c(cs, dry, 0, 0); ms.c(cfd, dry, 0, 1)        # delay feed: synth + track delay sends
dryR = ms.obj(330, 90, "+~")
ms.c(cs, dryR, 0, 0); ms.c(cfr, dryR, 0, 1)                         # reverb feed: synth + track reverb sends'''),
    ("ms.c(dry, rin, 0, 0); ms.c(drd, rin, 0, 1)", "ms.c(dryR, rin, 0, 0); ms.c(drd, rin, 0, 1)"),
    # pages: 5
    ('pgN = x_.obj(20, 220, "expr ($f1+1)%4")             # MIX -> FX -> FILTER -> MASTER',
     'pgN = x_.obj(20, 220, "expr ($f1+1)%5")             # MIX -> FX -> FILTER -> MASTER -> SEND'),
    ('rpg = x_.obj(200, 120, "route 0 1 2 3")', 'rpg = x_.obj(200, 120, "route 0 1 2 3 4")'),
    ('psel = x_.obj(200, 430, "sel 0 1 2 3")', 'psel = x_.obj(200, 430, "sel 0 1 2 3 4")'),
    ('x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)                # MASTER page: knob 1 COMP, knob 2 SPEED',
     '''x_.c(rpg, x_.obj(900, 150, "s comp-knob"), 3)                # MASTER page: knob 1 COMP, knob 2 SPEED
seK = x_.obj(1000, 120, "list prepend 0")                       # SEND page: knob k -> delay send, AUX -> reverb send
x_.c(x_.obj(1060, 90, "r aux"), seK, 0, 1)
seKR = x_.obj(1000, 135, "route 0 1")
x_.c(rpg, seK, 4); x_.c(seK, seKR)
x_.c(seKR, x_.obj(1000, 150, "s dsend-knob"), 0); x_.c(seKR, x_.obj(1100, 150, "s rsend-knob"), 1)'''),
    ('x_.save("mix.pd")', r'''# ------------------------------------------------ SEND page (apply_sends.py): 4 bars, delay send (AUX: reverb)
sdV, srV = [], []
svR = x_.obj(4200, 520, "route 1 2 3 4"); swR = x_.obj(4400, 520, "route 1 2 3 4")
x_.c(x_.obj(4200, 490, "r dsend-knob"), svR); x_.c(x_.obj(4250, 470, "r dsend-set"), svR)
x_.c(x_.obj(4400, 490, "r rsend-knob"), swR); x_.c(x_.obj(4450, 470, "r rsend-set"), swR)
for k in range(4):
    a = x_.obj(4200 + k * 50, 550, "f 1"); b = x_.obj(4400 + k * 50, 550, "f 1")
    x_.c(svR, a, k, 1); x_.c(swR, b, k, 1)
    sdV.append(a); srV.append(b)
for nm in ("dsend-knob", "dsend-set", "rsend-knob", "rsend-set"):
    x_.c(x_.obj(4600, 490, f"r {nm}"), dOne)
seT = x_.obj(4200, 600, "t b b b b b")                 # 4 header (AUX state first), 3..0 tracks 1..4
x_.c(psel, seT, 4)
seAux = x_.obj(4100, 600, "f")
x_.c(x_.obj(4100, 570, "r aux"), seAux, 0, 1)
seHead = x_.obj(4100, 630, "sel 0 1")
x_.c(seT, seAux, 4); x_.c(seAux, seHead)
x_.c(seHead, x_.msg(4100, 660, osc2("gPrintln", "iiiiis", "1 1 8 1 SEND DLY")), 0)
x_.c(seHead, x_.msg(4250, 660, osc2("gFillArea", "iiiiii", "0 0 51 10 1") + " " + osc2("gPrintln", "iiiiis", "2 1 8 0 SEND REV")), 1)
for k in range(4):
    cx = 16 + 32 * k
    X = 4200 + k * 200
    tb = x_.obj(X, 700, "t b b")
    x_.c(seT, tb, 3 - k)
    # value shown: AUX ? reverb send : delay send. $f1 delay (hot), $f2 AUX, $f3 reverb
    vE = x_.obj(X, 760, "expr if($f2 \\, $f3 \\, $f1)")
    x_.c(seAux, vE, 0, 1)
    x_.c(tb, srV[k], 1); x_.c(srV[k], vE, 0, 2)
    x_.c(tb, sdV[k], 0); x_.c(sdV[k], vE)
    # bar y 12..38, track number at y 42 and value at y 53 (same spacing as the FILTER page, readable on the OLED)
    hE = x_.obj(X, 790, "expr int($f1*23+0.5) \\; 37-int($f1*23+0.5) \\; int($f1*100+0.5)")
    x_.c(vE, hE)
    hP = x_.obj(X, 820, "pack f f f")
    x_.c(hE, hP, 2, 2); x_.c(hE, hP, 1, 1); x_.c(hE, hP, 0, 0)
    x_.c(hP, x_.msg(X, 850, osc2("gBox", "iiiiii", f"{cx - 5} 12 11 27 1") + " " +
                    osc2("gFillArea", "iiiiii", f"{cx - 3} \\$2 7 \\$1 1") + " " +
                    osc2("gPrintln", "iiiiif", f"{cx - 3} 42 8 1 {k + 1}") + " " +
                    osc2("gPrintln", "iiiiif", f"{cx - 9} 53 8 1 \\$3")))
x_.save("mix.pd")'''),
])

# --- knob contexts 27 (delay sends) / 28 (reverb sends), defaults 1
s = open("gen.py").read()
i = s.index('pkInit = m.msg(560, 820, "'); j = s.index("\n", i)
line = s[i:j]
head, rest = line.split("pkval ", 1)
body, tail = rest.split(r" \\; pkphys", 1)
vals = body.split()                                         # vals[0] = start index, pkval[n] = vals[n + 1]
assert len(vals) == 109, len(vals)
vals += ["1"] * 8
s = s[:i] + head + "pkval " + " ".join(vals) + r" \\; pkphys" + tail + s[j:]
open("gen.py", "w").write(s)
edit("gen.py", [
    ('m.obj(560, 530, "table pkval 108")', 'm.obj(560, 530, "table pkval 116")'),
    ('m.obj(680, 530, "table pkpick 108")', 'm.obj(680, 530, "table pkpick 116")'),
    (r'if($f1==3 && $f2==3 \\, 22 \\, ', r'if($f1==3 && $f2==4 \\, if($f5==1 \\, 28 \\, 27) \\, if($f1==3 && $f2==3 \\, 22 \\, '),
])
s = open("gen.py").read()
i = s.index('ctxE = m.obj(560, 660, "'); j = s.index("\n", i)
ln = s[i:j]
ln = ln[:ln.rindex('")')] + ')' + '")'                     # one more if( opened -> one more closing parenthesis
s = s[:i] + ln + s[j:]
open("gen.py", "w").write(s)

edit("genproj.py", [
    ('(26, "drone-knob")]', '(26, "drone-knob"), (27, "dsend-set"), (28, "rsend-set")]'),
    ("p.c(fixT, fixE8, 1)", '''fixE9 = p.obj(100, 790, "expr ''' + "+".join(f"pkval[{n}]" for n in range(108, 116)) + '''==0")
fixS9 = p.obj(100, 820, "sel 1")
p.c(fixT, fixE9, 1); p.c(fixE9, fixS9); p.c(fixS9, p.msg(100, 850, "\\\\; pkval 108 1 1 1 1 1 1 1 1"))
p.c(fixT, fixE8, 1)'''),
])
print("sends applied")

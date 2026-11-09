#!/usr/bin/env python3
"""Generate the Nastro Organelle patch (main.pd, synth-fm.pd, fm-voice.pd)."""
import os, sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def fix_println_types(text):
    """gPrintln args: 3 (screen) x y size colour, then the text. Rebuild the type string from the arguments:
    the 5 numbers 'i', then per text token 's' for a word, 'f' for a number, and for anything with a $n the type
    given by hand (a $n can be a word or a number) (apply_oledtypes.py)."""
    def isnum(tok):
        try:
            float(tok)
            return True
        except ValueError:
            return tok.lstrip("\\").startswith("$")

    toks = text.split(" ")
    out, i = [], 0
    while i < len(toks):
        out.append(toks[i])
        if toks[i] == "/oled/gPrintln" and i > 0 and toks[i - 1] == "sendtyped" and i + 1 < len(toks):
            j = i + 2
            while j < len(toks) and ";" not in toks[j] and "," not in toks[j]:
                j += 1
            orig, args = toks[i + 1], toks[i + 2:j]   # given types; args up to the next ; or , separator
            # $n placeholders keep the type given by hand (they can be words or numbers); literal text is typed here
            ty = []
            for k, t in enumerate(args):
                if k < 5:
                    ty.append("i")
                elif "$" in t:
                    ty.append(orig[k] if k < len(orig) and orig[k] in "ifs" else "s")
                else:
                    ty.append("f" if isnum(t) else "s")
            out.append("".join(ty))
            out += args
            i = j
            continue
        i += 1
    return " ".join(out)


class Patch:
    def __init__(self, w=1000, h=760):
        self.lines = [f"#N canvas 40 40 {w} {h} 12;"]
        self.n = 0
        self.conns = []

    def _add(self, kind, x, y, text):
        self.lines.append(f"#X {kind} {x} {y} {text};")
        i = self.n
        self.n += 1
        return i

    def obj(self, x, y, t): return self._add("obj", x, y, t)
    def msg(self, x, y, t): return self._add("msg", x, y, fix_println_types(t))
    def text(self, x, y, t): return self._add("text", x, y, t)

    def c(self, a, b, o=0, i=0):
        self.conns.append(f"#X connect {a} {o} {b} {i};")

    def save(self, name):
        with open(os.path.join(OUT, name), "w") as f:
            f.write("\n".join(self.lines + self.conns) + "\n")


def voice_switch(P, inl, rel=None, fixed=1000, onset_only=False, block=None, dur_field=None, x=700, y=420):
    """switch~ for one voice: on at a note-on, off 'hold' ms after the note-off (or after the note-on when
    onset_only). hold = [r rel] value (ms) or 'fixed'; +300 ms margin. dur_field: inputs are lists without a
    note-off (drums): hold = that field of the list."""
    sw = P.obj(x, y + 180, f"switch~ {block}" if block else "switch~")
    z0 = P.msg(x + 100, y + 150, "0")
    P.c(P.obj(x + 100, y + 120, "loadbang"), z0)
    P.c(z0, sw)
    dl = P.obj(x, y + 120, "delay")
    P.c(dl, z0)
    on1 = P.msg(x + 60, y + 90, "1")
    stp = P.msg(x + 120, y + 90, "stop")
    P.c(on1, sw)
    P.c(stp, dl)
    hold = P.obj(x, y + 60, f"f {fixed}")
    add = P.obj(x, y + 90, "+ 300")
    P.c(hold, add)
    if rel:
        P.c(P.obj(x + 200, y, f"r {rel}"), hold, 0, 1)
    if dur_field is not None:
        # one trigger: 3) the list sets the hold time  2) cancel  1) on  0) start the switch-off timer
        trig = P.obj(x + 60, y, "t b b b l")
        P.c(inl, trig)
        up = P.obj(x, y + 30, "unpack " + " ".join(["f"] * 6))
        P.c(trig, up, 3)
        P.c(up, hold, dur_field, 1)
        P.c(trig, stp, 2); P.c(trig, on1, 1); P.c(trig, hold, 0)
    else:
        up = P.obj(x, y, "unpack f f")
        P.c(inl, up)
        mo = P.obj(x, y + 30, "moses 1")
        P.c(up, mo, 1)
        if onset_only:                    # note-on: cancel, on, start the timer (note-offs are ignored)
            onT = P.obj(x + 60, y + 60, "t b b b")
            P.c(mo, onT, 1)
            P.c(onT, stp, 2); P.c(onT, on1, 1); P.c(onT, hold, 0)
        else:                             # note-on: cancel, on ; note-off: start the timer
            onT = P.obj(x + 60, y + 60, "t b b")
            P.c(mo, onT, 1)
            P.c(onT, stp, 1); P.c(onT, on1, 0)
            offB = P.obj(x, y + 45, "t b")
            P.c(mo, offB, 0); P.c(offB, hold)
    P.c(add, dl)
    return sw


# ---------------------------------------------------------------- fm-voice.pd
v = Patch(820, 620)
v.text(20, 10, "fm-voice: one voice of the FM engine. input = note velocity")
inl = v.obj(20, 50, "inlet")
tll = v.obj(20, 80, "t l l")
voice_switch(v, inl, rel="fm-release")
upn = v.obj(160, 110, "unpack f f")
mtof = v.obj(160, 140, "mtof")
freq = v.obj(160, 170, "sig~")
upv = v.obj(20, 110, "unpack f f")
mos = v.obj(60, 140, "moses 1")
# attack branch
div = v.obj(110, 170, "/ 127")
patk = v.obj(110, 200, "pack f f")
ratk = v.obj(400, 40, "r fm-attack")
# release branch
tb = v.obj(20, 170, "t b")
frel = v.obj(20, 200, "f")
rrel = v.obj(560, 40, "r fm-release")
mrel = v.msg(20, 230, "0 \\$1")
envl = v.obj(60, 270, "line~")
env = v.obj(60, 300, "*~")  # squared envelope
# ratio / index smoothing
rrat = v.obj(400, 80, "r fm-ratio")
mrat = v.msg(400, 110, "\\$1 20")
lrat = v.obj(400, 140, "line~")
ridx = v.obj(560, 80, "r fm-index")
midx = v.msg(560, 110, "\\$1 20")
lidx = v.obj(560, 140, "line~")
# operators
modf = v.obj(300, 200, "*~")
mod = v.obj(300, 230, "osc~")
dep1 = v.obj(300, 260, "*~")
dep2 = v.obj(300, 290, "*~")
dep3 = v.obj(300, 320, "*~")
sumf = v.obj(160, 350, "+~")
car = v.obj(160, 380, "osc~")
vca = v.obj(160, 420, "*~")
out = v.obj(160, 460, "outlet~")
v.text(400, 200, "modulator = freq * ratio")
v.text(400, 290, "depth = index * freq * env")

v.c(inl, tll)
v.c(tll, upn, 1)          # note first
v.c(upn, mtof); v.c(mtof, freq)
v.c(tll, upv, 0)          # then velocity -> envelope
v.c(upv, mos, 1)
v.c(mos, tb, 0); v.c(tb, frel); v.c(frel, mrel); v.c(mrel, envl)
v.c(rrel, frel, 0, 1)
v.c(mos, div, 1); v.c(div, patk); v.c(patk, envl)
v.c(ratk, patk, 0, 1)
v.c(envl, env, 0, 0); v.c(envl, env, 0, 1)
v.c(rrat, mrat); v.c(mrat, lrat)
v.c(ridx, midx); v.c(midx, lidx)
v.c(freq, modf, 0, 0); v.c(lrat, modf, 0, 1)
v.c(modf, mod)
v.c(mod, dep1, 0, 0); v.c(lidx, dep1, 0, 1)
v.c(dep1, dep2, 0, 0); v.c(freq, dep2, 0, 1)
v.c(dep2, dep3, 0, 0); v.c(env, dep3, 0, 1)
v.c(freq, sumf, 0, 0); v.c(dep3, sumf, 0, 1)
v.c(sumf, car)
v.c(car, vca, 0, 0); v.c(env, vca, 0, 1)
v.c(vca, out)
v.save("fm-voice.pd")

# ---------------------------------------------------------------- synth-fm.pd
s = Patch(1000, 640)
s.text(20, 10, "synth-fm: 4-voice 2-operator FM engine (mode SYNTH)")
rn = s.obj(20, 50, "r synth-notes")
rp = s.obj(160, 50, "r synth-panic")
poly = s.obj(20, 90, "poly 4 1")
pk = s.obj(20, 120, "pack f f f")
cl = s.obj(20, 150, "clone -s 1 fm-voice 4")
gain = s.obj(20, 190, "*~ 0.3")
clip = s.obj(20, 220, "clip~ -1 1")
tl = s.obj(20, 260, "throw~ synth-bus")
s.c(rn, poly); s.c(rp, poly)
s.c(poly, pk, 0, 0); s.c(poly, pk, 1, 1); s.c(poly, pk, 2, 2)
s.c(pk, cl); s.c(cl, gain); s.c(gain, clip); s.c(clip, tl)

s.text(320, 10, "knobs: 1 ratio / 2 index / 3 attack / 4 release")
rk = s.obj(320, 50, "r synth-knob")
lb = s.obj(520, 20, "loadbang")
defaults = s.msg(520, 50, "1 0.1 \\, 2 0.5 \\, 3 0 \\, 4 0.3")
rt = s.obj(320, 90, "route 1 2 3 4")
exprs = [
    "expr int($f1*15+1)*0.5",
    "expr int(pow($f1 \\, 2)*1000)/100",
    "expr int(1+pow($f1 \\, 3)*1999)",
    "expr int(10+pow($f1 \\, 2)*3990)",
]
sends = ["s fm-ratio", "s fm-index", "s fm-attack", "s fm-release"]
labels = ["screenLine2 Ratio \\$1", "screenLine3 Index \\$1",
          "screenLine4 Attack \\$1 ms", "screenLine5 Release \\$1 ms"]
rm = s.obj(320, 420, "r mode")
sel0 = s.obj(320, 450, "sel 0")
tbbb = s.obj(320, 480, "t b b b b")
s.c(lb, defaults); s.c(defaults, rt); s.c(rk, rt)
s.c(rm, sel0); s.c(sel0, tbbb)
for k in range(4):
    x = 320 + k * 165
    e = s.obj(x, 130, exprs[k])
    t = s.obj(x, 170, "t f f")
    snd = s.obj(x + 50, 200, sends[k])
    f = s.obj(x, 240, "f")
    m = s.msg(x, 280, "\\; " + labels[k])
    s.c(rt, e, k); s.c(e, t); s.c(t, snd, 1); s.c(t, f, 0); s.c(f, m)
    s.c(tbbb, f, 3 - k)
s.save("synth-fm.pd")

# ---------------------------------------------------------------- main.pd
m = Patch(1100, 800)
m.text(20, 5, "NASTRO - tape workstation for Organelle. AUX + key: C=SYNTH C#=DRUM D=TAPE D#=MIX E=SEQ / A#=oct- B=oct+ / F=play F#=rec G=rewind A=save")
# --- aux handling
raux = m.obj(20, 40, "r aux")
tfff = m.obj(20, 70, "t f f f")
eq0 = m.obj(20, 100, "== 0")
sel1 = m.obj(120, 100, "sel 1")
stop = m.msg(120, 130, "stop")
spanic = m.obj(120, 160, "s synth-panic")
# --- notes
rnotes = m.obj(300, 40, "r notes")
tll = m.obj(300, 70, "t l l")
sp_play = m.obj(300, 130, "spigot 1")
sp_sel = m.obj(460, 130, "spigot 0")
m.c(raux, tfff)
m.c(tfff, sp_sel, 2, 1)
m.c(tfff, eq0, 1); m.c(eq0, sp_play, 0, 1)
m.c(tfff, sel1, 0); m.c(sel1, stop); m.c(stop, spanic)
m.c(rnotes, tll); m.c(tll, sp_sel, 1); m.c(tll, sp_play, 0)
# play path: transpose by octave
upk = m.obj(300, 170, "unpack f f")
plus = m.obj(300, 200, "+ 0")
pk = m.obj(300, 230, "pack f f")
snotes = m.obj(300, 260, "s synth-notes")
instr = m.obj(200, 150, "list prepend 0")
irt = m.obj(200, 175, "route 0 1")
arpG = m.obj(300, 145, "spigot")                   # ARP page: note-ons go to the arpeggiator (apply_arp.py)
arpGT = m.obj(300, 140, "t l l")
arpGE = m.obj(380, 145, "expr $f2==0 || arpcap==0")
m.c(sp_play, arpGT); m.c(arpGT, arpGE, 1); m.c(arpGE, arpG, 0, 1); m.c(arpGT, arpG, 0)
m.c(arpG, instr); m.c(instr, irt); m.c(irt, upk, 0)
m.c(irt, m.obj(380, 200, "s drum-notes"), 1)
m.c(m.obj(200, 120, "r seq-notes"), instr)
m.c(upk, pk, 1, 1); m.c(upk, plus, 0); m.c(plus, pk); m.c(pk, snotes)
# select path
upk2 = m.obj(460, 170, "unpack f f")
gt0 = m.obj(560, 200, "> 0")
sp_on = m.obj(460, 230, "spigot")
mos = m.obj(460, 260, "moses 65")
sub = m.obj(460, 290, "- 60")
smode = m.obj(460, 320, "s mode")
sel_oct = m.obj(560, 290, "sel 82 83")
mdn = m.msg(560, 320, "-1")
mup = m.msg(610, 320, "1")
acc = m.obj(560, 350, "+")
clp = m.obj(560, 380, "clip -2 2")
m.c(m.obj(660, 350, "r nst-oct-set"), clp)
toct = m.obj(560, 410, "t f f")
x12 = m.obj(660, 440, "* 12")
m.c(sp_sel, upk2); m.c(upk2, gt0, 1); m.c(gt0, sp_on, 0, 1); m.c(upk2, sp_on, 0)
m.c(sp_on, mos); m.c(mos, sub, 0); m.c(sub, smode); m.c(mos, sel_oct, 1)
auxk = m.obj(660, 320, "s aux-key")
m.c(sel_oct, auxk, 2)
m.c(sel_oct, mdn, 0); m.c(sel_oct, mup, 1); m.c(mdn, acc); m.c(mup, acc)
m.c(acc, clp); m.c(clp, acc, 0, 1); m.c(clp, toct)
m.c(toct, x12, 1); m.c(x12, plus, 0, 1)
m.c(toct, m.obj(620, 470, "s nst-oct"), 0)
# --- display line 1 + led
rmode = m.obj(720, 40, "r mode")
tff = m.obj(720, 70, "t f f")
selm = m.obj(720, 100, "sel 0 1 2 3 4")
names = ["SYNTH", "DRUM", "TAPE", "MIX", "SEQ"]
psf = m.obj(720, 200, "pack s f")
line1 = m.msg(720, 230, "\\; screenLine1 \\$1 oct \\$2")
tbf = m.obj(560, 440, "t b f")
m.c(rmode, tff); m.c(tff, selm, 0)
for k, nm in enumerate(names):
    mm = m.msg(720 + k * 75, 130, f"symbol {nm.replace(' ', '_')}")
    m.c(selm, mm, k); m.c(mm, psf)
todo = m.msg(800, 170, "\\; screenLine2 (todo) \\; screenLine3 - \\; screenLine4 - \\; screenLine5 -")
for k in ():
    m.c(selm, todo, k)
sp1 = m.obj(720, 215, "spigot 1")
ne2 = m.obj(820, 215, "expr 0")
# graphics modes (TAPE, MIX) hide the OS info bar
gfx = m.obj(900, 160, "expr 1")
gfxc = m.obj(900, 185, "change -1")
gsel = m.obj(900, 210, "sel 1 0")
ghide = m.msg(900, 240, "\\; oscOut sendtyped /oled/gShowInfoBar ii 3 0")
gshow = m.msg(900, 270, "\\; oscOut sendtyped /oled/gShowInfoBar ii 3 1")
m.c(tff, gfx, 1); m.c(gfx, gfxc); m.c(gfxc, gsel); m.c(gsel, ghide, 0); m.c(gsel, gshow, 1)
m.c(psf, sp1); m.c(sp1, line1); m.c(tff, ne2, 1); m.c(ne2, sp1, 0, 1)
m.c(toct, tbf, 0); m.c(tbf, psf, 1, 1); m.c(tbf, psf, 0, 0)
ledp = m.obj(900, 70, "expr if($f2 \\, 7 \\, $f1+1)")              # white while the reverb is frozen
ledm = m.msg(900, 100, "\\; led \\$1")
m.c(tff, ledp, 1)
# blink while recording (apply_recblink.py): colour -> [rec && off-phase ? 0 : colour] -> led
ledO = m.obj(1100, 100, "expr if($f2 && $f3 \\, 0 \\, $f1)")
ledCT = m.obj(1100, 70, "t f f"); ledCol = m.obj(1200, 70, "f")
m.c(ledp, ledCT); m.c(ledCT, ledCol, 1, 1); m.c(ledCT, ledO, 0, 0); m.c(ledO, ledm)
recE = m.obj(1300, 40, "expr $f1 || $f2 || $f3 || $f4")
m.c(m.obj(1300, 10, "r tp-rec"), recE, 0, 0)
for k_, nm_ in ((1, "smp-recording"), (2, "drum-recording"), (3, "album-rec")):
    tb_ = m.obj(1400 + k_ * 100, 25, "t b f")
    m.c(m.obj(1400 + k_ * 100, 0, f"r {nm_}"), tb_); m.c(tb_, recE, 1, k_); m.c(tb_, recE, 0, 0)
recC = m.obj(1300, 70, "change"); recT = m.obj(1300, 100, "t f f")
m.c(recE, recC); m.c(recC, recT); m.c(recT, ledO, 1, 1)
recS = m.obj(1300, 130, "sel 0")
m.c(recT, recS, 0)
blM = m.obj(1400, 160, "metro 250")
blStop = m.msg(1300, 160, "stop")
m.c(recS, blStop, 0); m.c(blStop, blM)
m.c(recS, blM, 1)                                                     # non-zero: start (ticks at once)
blPh = m.obj(1400, 190, "f 0"); blNot = m.obj(1460, 190, "== 0")
m.c(blM, blPh); m.c(blPh, blNot); m.c(blNot, blPh, 0, 1)
blT = m.obj(1400, 220, "t b f")
m.c(blNot, blT); m.c(blT, ledO, 1, 2); m.c(blT, ledCol, 0)
bl0 = m.msg(1300, 190, "0")                                           # stopped: phase on, colour back
bl0b = m.obj(1300, 220, "t b f f")                                   # 2) phase  1) off-phase flag  0) colour again
m.c(recS, bl0, 0); m.c(bl0, bl0b); m.c(bl0b, blPh, 2, 1); m.c(bl0b, ledO, 1, 2); m.c(bl0b, ledCol, 0)
m.c(ledCol, ledO, 0, 0)
ledFz = m.obj(1000, 40, "t b f")
m.c(m.obj(1000, 10, "r rvb-freeze"), ledFz); m.c(ledFz, ledp, 1, 1); m.c(ledFz, ledp, 0, 0)
# --- knob router
m.text(20, 500, "knob router: knobs go to the active mode as [knob# value]")
rks = []
for k in range(4):
    r = m.obj(20 + k * 120, 530, f"r knob{k+1}")
    lp = m.obj(20 + k * 120, 560, f"list prepend {k+1}")
    m.c(r, lp); rks.append(lp)
router = m.obj(20, 610, "list prepend 0")
# --- knob pickup: after a mode/page change a knob only takes over its
# parameter once it reaches (or passes) the parameter's current value.
# contexts: 0 synth 1 drum 2 tape 3 mix 4 seq 5 fx ; slot = ctx*4 + knob-1
m.text(560, 500, "pickup: knob controls the parameter only after crossing its current value")
m.obj(560, 530, "table pkval 192")
m.obj(680, 530, "table pkpick 192")
m.obj(800, 530, "table pkphys 4")
pkin = m.obj(20, 590, "t l l l")
for lp in rks:
    m.c(lp, pkin)
accE = m.obj(200, 590, "expr if(pkpick[$f3*4+$f1-1] || abs($f2-pkval[$f3*4+$f1-1])<0.02 || (pkphys[$f1-1]>=0 && (pkphys[$f1-1]-pkval[$f3*4+$f1-1])*($f2-pkval[$f3*4+$f1-1])<=0) \\, 1 \\, 0)")
phE = m.obj(560, 590, "expr $f2 \\; $f1-1")
phW = m.obj(560, 620, "tabwrite pkphys")
gate = m.obj(20, 640, "spigot")
fwd = m.obj(20, 670, "t l l")
stE = m.obj(200, 700, "expr $f2 \\; $f3*4+$f1-1")
stT = m.obj(200, 730, "t f b")
one = m.msg(260, 760, "1")
vW = m.obj(200, 790, "tabwrite pkval")
pW = m.obj(320, 790, "tabwrite pkpick")
m.c(pkin, accE, 2); m.c(accE, gate, 0, 1)
m.c(pkin, phE, 1); m.c(phE, phW, 1, 1); m.c(phE, phW, 0, 0)
m.c(pkin, gate, 0); m.c(gate, fwd)
m.c(fwd, stE, 1); m.c(stE, vW, 1, 1); m.c(stE, pW, 1, 1); m.c(stE, stT, 0)
m.c(stT, one, 1); m.c(one, pW); m.c(stT, vW, 0)
m.c(fwd, router, 0)
# context = mode, or 5 for the FX page of MIX; a change releases all knobs
ctxE = m.obj(560, 660, "expr if($f1==0 && $f5==0 && $f6==1 \\, if($f3==11 \\, 44 \\, if($f3==12 \\, 46 \\, 29+$f3)) \\, if($f1==5 \\, 12 \\, 0) + if($f1==5 \\, 0 \\, if($f1==3 && $f2==0 && $f5==1 \\, 11 \\, if($f1==0 && $f5==1 \\, if($f3==4 \\, 42 \\, 13) \\, if($f1==1 && $f5==1 \\, 14 \\, if($f1==3 && $f2==5 \\, 47 \\, if($f1==3 && $f2==4 \\, if($f5==1 \\, 28 \\, 27) \\, if($f1==3 && $f2==3 \\, 22 \\, if($f1==3 && $f2==2 \\, if($f5==1 \\, 21 \\, 20) \\, if($f1==3 && $f2==1 \\, if($f5==1 \\, 16 \\, 5) \\, if($f1==0 && $f3>0 \\, if($f3==11 \\, 43 \\, if($f3==12 \\, 45 \\, if($f3==4 \\, 10 \\, if($f3>=7 \\, 16+$f3 \\, if($f3>=5 \\, 13+$f3 \\, 5+$f3))))) \\, if($f1==4 && $f4==1 \\, 9 \\, if($f1==4 && $f4==2 \\, 15 \\, if($f1==4 && $f4==3 \\, 17 \\, if($f1==4 && $f4==4 \\, if($f5==1 \\, 41 \\, 40) \\, $f1)))))))))))))))")
rauxC = m.obj(1000, 630, "r aux")
auxTb = m.obj(1000, 660, "t b f")
m.c(rauxC, auxTb); m.c(auxTb, ctxE, 1, 4); m.c(auxTb, ctxE, 0, 0)
rsp = m.obj(900, 630, "r seq-page")
spTb = m.obj(900, 660, "t b f")
m.c(rsp, spTb); m.c(spTb, ctxE, 1, 3); m.c(spTb, ctxE, 0, 0)
reng = m.obj(800, 630, "r synth-engine")
engTb = m.obj(800, 660, "t b f")
m.c(reng, engTb); m.c(engTb, ctxE, 1, 2); m.c(engTb, ctxE, 0, 0)
lfoPg = m.obj(1100, 630, "r syn-lfo-page")                # SYNTH LFO page: contexts 29 + engine (apply_lfo.py)
lfoTb = m.obj(1100, 660, "t b f")
m.c(lfoPg, lfoTb); m.c(lfoTb, ctxE, 1, 5); m.c(lfoTb, ctxE, 0, 0)
rpage = m.obj(700, 630, "r mix-page")
pgTb = m.obj(700, 660, "t b f")
ctxC = m.obj(560, 690, "change -1")
ctxT = m.obj(560, 720, "t f f f")
clr = m.msg(700, 750, "\\; pkpick const 0")
m.c(tff, ctxE, 1, 0)
imo = m.obj(560, 760, "moses 2")
m.c(tff, imo, 1); m.c(imo, instr, 0, 1)
m.c(rpage, pgTb); m.c(pgTb, ctxE, 1, 1); m.c(pgTb, ctxE, 0, 0)
m.c(ctxE, ctxC); m.c(ctxC, ctxT)
m.c(ctxT, accE, 2, 2); m.c(ctxT, stE, 1, 2); m.c(ctxT, clr, 0)
pkInit = m.msg(560, 820, "\\; pkval 0 0.1 0.5 0 0.3 0.5 1 1 0.8 0.75 0 1 0 0.8 0.8 0.8 0.8 0.4286 0 1 0 0.6 0.42 0 0 0.45 0.3 0.5 0.3 0.7 0.6 0.6 0.4 0.5 0.6 0.5 0.5 0 1 0.47 0 0 1 0.3 0 0.5 0.5 0.5 0.5 0 0 0 0 0.8 0.04 0.28 1 0.8 0 0 0 0.583 0.5 0.6 0.6 0.5 0.6 0.15 0.3 0.6 0.45 0.1 1 0.5 0.5 0.5 0.4 0.4 0.5 0.7 0.3 0.5 0.5 0.5 0.5 0 0 0 0 0 0.5 0 0 0.3 0.0 0.5 0.3 0.3 0.5 0.25 0.4 0.75 1.0 0.5 0.25 0.4 0.4 0.4 0.5 1 1 1 1 1 1 1 1 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.3 0.5 0 0 0.55 0 0.5 1 0 0 0 0.8 0 1 0 0.7 0.5 0.4 0.5 0 0.3 0.5 0 0.05 0.5 0.5 1 0 0.3 0.5 0 0 0.6 0.5 0 \\; pkphys 0 -1 -1 -1 -1 \\; pkpick const 0")
m.c(m.obj(560, 790, "loadbang"), pkInit)
m.c(m.obj(700, 790, "r nst-pk-defaults"), pkInit)
m.c(tff, router, 1, 1)
rte = m.obj(20, 640, "route 0 1 2 3 4")
m.c(router, rte)
for k, nm in enumerate(["synth", "drum", "tape", "mix", "seq"]):
    so = m.obj(20 + k * 120, 680, f"s {nm}-knob")
    m.c(rte, so, k)
# --- init + engines
lb = m.obj(900, 500, "loadbang")
tbb = m.obj(900, 530, "t b b")
z1 = m.msg(900, 560, "0")
z2 = m.msg(960, 560, "0")
m.c(lb, tbb); m.c(tbb, z1, 1); m.c(z1, smode); m.c(tbb, z2, 0); m.c(z2, toct)
m.obj(720, 620, "synth-fm")
m.obj(720, 680, "synth-sub")
m.obj(800, 680, "synth-pluk")
m.obj(880, 680, "synth-pad")
m.obj(880, 720, "synth-air")
m.obj(960, 720, "synth-bell")
m.obj(720, 760, "synth-wave")
m.obj(800, 760, "synth-strg")
m.obj(880, 760, "synth-organ")
m.obj(960, 760, "synth-drone")
m.obj(1040, 760, "synth-piano")
m.obj(1120, 760, "synth-mallet")
m.obj(960, 680, "synth")
m.obj(1030, 680, "seq")
m.obj(1080, 680, "synth-smpl")
m.obj(1170, 680, "smpl")
m.obj(1220, 680, "project")
m.obj(1300, 680, "tapeedit")
m.obj(1380, 680, "tomb")
m.obj(1460, 680, "meter")
m.obj(1540, 680, "endl")
m.obj(1620, 680, "mirror")
m.obj(1700, 680, "synth-lfo")
m.obj(1780, 680, "album")
m.obj(1850, 680, "arp")
m.obj(1920, 680, "vis")
m.obj(820, 620, "tape")
m.obj(820, 650, "tape-screen")
m.obj(940, 650, "tape-map")
m.obj(940, 620, "mix")
m.obj(1000, 620, "tempo")
m.obj(1070, 620, "drum")
m.obj(890, 620, "master")
m.text(720, 650, "engines: add drum / mix / seq abstractions here")
m.save("main.pd")
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentape.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genscreen.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmix.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentempo.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gendrum.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentapemap.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gensynth.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genseq.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gensmpl.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genproj.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentapeedit.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gentomb.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genrev.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmeter.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genendl.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genmirror.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genalbum.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genarp.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genvis.py")).read())
print("ok")

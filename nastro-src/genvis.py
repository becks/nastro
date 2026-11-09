# exec'd from gen.py: builds vis.pd, vis-dsp.pd, vis-fft.pd, vis-scope.pd - the VIS page of MIX (6th page,
# AUX+D# cycles MIX -> FX -> FILTER -> MASTER -> SEND -> VIS): a picture of Nastro's output (after the limiter).
# The screen is sent whole with /oled/gFrame (1024 bytes: 8 pages x 128 columns, bit 0 = top pixel of a page)
# and the scope with /oled/gWaveform (128 y values drawn as connected lines): 2-3 messages per frame.
# Views (knob 1): WAVE = the level scrolling to the left (mirrored, filled) and a scope on the right;
#                 SPEC = a spectrogram waterfall, 64 log-spaced rows 40 Hz .. 16 kHz, intensity as a 4x4 dither.
# Knob 2 SPEED (frame interval 200..30 ms, one column per frame), knob 3 GAIN (dB range shown). Knob context 47.
# Everything (DSP and frames) runs only while the page is shown.
import math

VIS_N = 1024                              # FFT size
VIS_HX = 84                               # WAVE: history in columns 0..83, scope in 84..127
VIS_SC = 128 - VIS_HX                     # scope points
VIS_TOP = 148                             # powtodb~ of a full-scale sine through the Hann window and rfft~
BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]


def oscV(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


# ---------------------------------------------------------------- vis-fft.pd: Hann window, FFT, power in dB -> visfft
vf = Patch(800, 500)
vf.text(20, 5, "vis-fft: block 1024 - Hann window - rfft~ - power in dB into the table visfft (bins 0..511)")
vf.obj(20, 30, f"block~ {VIS_N} 1")
vfi = vf.obj(20, 60, "inlet~")
win = vf.obj(150, 60, "tabreceive~ vishann")
wm = vf.obj(20, 90, "*~")
fft = vf.obj(20, 120, "rfft~")
re2 = vf.obj(20, 150, "*~")
im2 = vf.obj(120, 150, "*~")
pw = vf.obj(20, 180, "+~")
db = vf.obj(20, 210, "powtodb~")
tw = vf.obj(20, 240, "tabwrite~ visfft")
bg = vf.obj(200, 210, "bang~")
vf.c(vfi, wm, 0, 0); vf.c(win, wm, 0, 1); vf.c(wm, fft)
vf.c(fft, re2, 0, 0); vf.c(fft, re2, 0, 1); vf.c(fft, im2, 1, 0); vf.c(fft, im2, 1, 1)
vf.c(re2, pw, 0, 0); vf.c(im2, pw, 0, 1); vf.c(pw, db); vf.c(db, tw); vf.c(bg, tw)
vf.save("vis-fft.pd")

# ---------------------------------------------------------------- vis-scope.pd: 1/8 rate, 44 y values -> visy
vs = Patch(800, 400)
vs.text(20, 5, "vis-scope: at 1/8 of the sample rate - y = 32 - 28 x - whole numbers 1..62 - 44 values into visy")
vs.obj(20, 30, "block~ 64 1 0.125")
vsi = vs.obj(20, 60, "inlet~")
g = vs.obj(20, 90, "*~ -28")
off = vs.obj(20, 120, "+~ 32")
cl = vs.obj(20, 150, "clip~ 1 62")
wr = vs.obj(120, 180, "wrap~")
fl = vs.obj(20, 210, "-~")
vtw = vs.obj(20, 240, "tabwrite~ visy")
vsB = vs.obj(150, 210, "r vis-scope-bang")
vs.c(vsi, g); vs.c(g, off); vs.c(off, cl); vs.c(cl, fl, 0, 0); vs.c(cl, wr); vs.c(wr, fl, 0, 1)
vs.c(fl, vtw); vs.c(vsB, vtw)
vs.save("vis-scope.pd")

# ---------------------------------------------------------------- vis-dsp.pd: on only while the page is shown
vd = Patch(800, 500)
vd.text(20, 5, "vis-dsp: the output (after the limiter) in mono - level for WAVE - scope - FFT")
vdOn = vd.obj(20, 30, "r vis-on")
vdSw = vd.obj(20, 60, "switch~")
iL = vd.obj(20, 100, "r~ alb-L")
iR = vd.obj(150, 100, "r~ alb-R")
mo = vd.obj(20, 130, "+~")
mh = vd.obj(20, 160, "*~ 0.5")
ev = vd.obj(300, 190, "env~ 1024 512")
evS = vd.obj(300, 220, "s vis-env")
vfI = vd.obj(20, 220, "vis-fft")
vsI = vd.obj(150, 220, "vis-scope")
vd.c(vdOn, vdSw)
vd.c(iL, mo, 0, 0); vd.c(iR, mo, 0, 1); vd.c(mo, mh)
vd.c(mh, ev); vd.c(ev, evS); vd.c(mh, vfI); vd.c(mh, vsI)
vd.save("vis-dsp.pd")

# ---------------------------------------------------------------- vis.pd
vz = Patch(3000, 1600)
vz.text(20, 5, "vis: VIS page of MIX - one /oled/gFrame per frame (+ /oled/gWaveform for the scope) - knobs view speed gain")
vz.obj(20, 30, "table visbm 1024")
vz.obj(140, 30, f"table visfft {VIS_N // 2}")
vz.obj(280, 30, f"table visy {VIS_SC}")
vz.obj(400, 30, "table visbay 16")
vz.obj(520, 30, f"table vishann {VIS_N}")
for i_, nm_ in enumerate(("visview", "visrange", "visenv", "viscol")):
    vz.obj(700 + i_ * 80, 30, f"v {nm_}")
vz.obj(1200, 30, "vis-dsp")

# ---- tables at load: Bayer thresholds, empty picture, Hann window (one 1024-step loop, once)
lb = vz.obj(20, 70, "loadbang")
lbT = vz.obj(20, 100, "t b b b")
lbM = vz.msg(150, 100, "\\; visbay 0 " + " ".join(f"{(b + 0.5) / 16:.4f}" for b in BAYER) + " \\; visbm const 0")
hN = vz.msg(20, 130, str(VIS_N))
hZ = vz.msg(80, 130, "0")
hU = vz.obj(20, 160, "until")
hC = vz.obj(20, 190, "f")
hC1 = vz.obj(70, 190, "+ 1")
hE = vz.obj(20, 220, f"expr 0.5-0.5*cos(6.28319*$f1/{VIS_N}) \\; $f1")
hW = vz.obj(20, 250, "tabwrite vishann")
vz.c(lb, lbT); vz.c(lbT, lbM, 2)
vz.c(lbT, hZ, 1); vz.c(hZ, hC, 0, 1); vz.c(lbT, hN, 0); vz.c(hN, hU); vz.c(hU, hC); vz.c(hC, hC1); vz.c(hC1, hC, 0, 1)
vz.c(hC, hE); vz.c(hE, hW, 1, 1); vz.c(hE, hW, 0, 0)

# ---- page shown: mode 3 and mix-page 5 -> 2) DSP  1) a clean picture  0) frame clock
acM = vz.obj(300, 70, "t f")
acP = vz.obj(400, 70, "t b f")
acE = vz.obj(300, 100, "expr $f1==3 && $f2==5")
acC = vz.obj(300, 130, "change")
acT = vz.obj(300, 160, "t f f f")
acDsp = vz.obj(400, 190, "s vis-on")
acS = vz.obj(350, 190, "sel 1")
acClr = vz.msg(350, 220, "\\; visbm const 0")
clk = vz.obj(300, 260, "metro 66")
vz.c(vz.obj(300, 40, "r mode"), acM); vz.c(acM, acE, 0, 0)
vz.c(vz.obj(400, 40, "r mix-page"), acP); vz.c(acP, acE, 1, 1); vz.c(acP, acE, 0, 0)
vz.c(acE, acC); vz.c(acC, acT)
vz.c(acT, acDsp, 2); vz.c(acT, acS, 1); vz.c(acS, acClr); vz.c(acT, clk, 0)

# ---- knobs: 1 VIEW (0 WAVE, 1 SPEC)  2 SPEED (frame ms)  3 GAIN (dB range shown)
kR = vz.obj(700, 100, "route 1 2 3")
kD = vz.msg(800, 40, "1 0 \\, 2 0.6 \\, 3 0.5")
kV = vz.obj(700, 130, "expr int(min($f1 \\, 0.999)*2)")
kVT = vz.obj(700, 160, "t b f")                         # 1) the view  0) a clean picture
kVv = vz.obj(760, 190, "v visview")
kVc = vz.msg(700, 190, "\\; visbm const 0")
kS = vz.obj(900, 130, "expr int(200-170*$f1)")
kG = vz.obj(1000, 130, "expr 30+60*$f1")
kGv = vz.obj(1000, 160, "v visrange")
vz.c(vz.obj(700, 70, "r vis-knob"), kR); vz.c(vz.obj(800, 70, "r vis-set"), kR)
vz.c(lb, kD); vz.c(kD, kR)
vz.c(kR, kV, 0); vz.c(kV, kVT); vz.c(kVT, kVv, 1); vz.c(kVT, kVc, 0)
vz.c(kR, kS, 1); vz.c(kS, clk, 0, 1)
vz.c(kR, kG, 2); vz.c(kG, kGv)

# ---- level for WAVE: the loudest env~ value since the last frame
evE = vz.obj(1300, 130, "expr max(visenv \\, $f1)")
evV = vz.obj(1300, 160, "v visenv")
vz.c(vz.obj(1300, 100, "r vis-env"), evE); vz.c(evE, evV)

# ---- a frame: 2) dither column counter  1) the view's picture  0) flip
fr = vz.obj(20, 300, "t b b b")
viewE = vz.obj(20, 330, "expr visview")
viewS = vz.obj(20, 360, "sel 0 1")
flip = vz.msg(20, 1500, "\\; oscOut sendtyped /oled/gFlip i 3")
colC = vz.obj(1500, 300, "f 0")
colC1 = vz.obj(1550, 300, "+ 1")
colM = vz.obj(1500, 330, "% 4")
colV = vz.obj(1500, 360, "v viscol")
vz.c(clk, fr)
vz.c(fr, colC, 2); vz.c(colC, colC1); vz.c(colC1, colC, 0, 1); vz.c(colC1, colM); vz.c(colM, colV)
vz.c(fr, viewE, 1); vz.c(viewE, viewS)
vz.c(fr, flip, 0)


def shift(x, y, trig, outlet, width):
    """scroll columns 1..width-1 of every page one column to the left (8 [array get] -> [array set] copies).
    [array get]: a float in the left inlet is the onset and outputs, the 2nd inlet is the number of points;
    [array set]: the 2nd inlet is the onset (as tapeedit.pd uses them)"""
    t_ = vz.obj(x, y, "t " + " ".join(["b"] * 8))
    vz.c(trig, t_, outlet)
    for p_ in range(8):
        ag = vz.obj(x + p_ * 90, y + 60, "array get visbm")
        as_ = vz.obj(x + p_ * 90, y + 90, "array set visbm")
        on = vz.msg(x + p_ * 90 + 40, y + 30, f"{p_ * 128 + 1}")
        nn = vz.msg(x + p_ * 90 + 60, y + 30, f"{width - 1}")
        os_ = vz.msg(x + p_ * 90 + 40, y + 75, f"{p_ * 128}")
        vz.c(lb, nn); vz.c(lb, os_)
        vz.c(nn, ag, 0, 1); vz.c(os_, as_, 0, 1)
        vz.c(t_, on, p_); vz.c(on, ag, 0, 0); vz.c(ag, as_)


def send_frame(x, y, trig, outlet):
    """the whole bitmap as one /oled/gFrame blob"""
    ag = vz.obj(x, y, "array get visbm")
    lp = vz.obj(x, y + 30, "list prepend sendtyped /oled/gFrame ib 3")
    lt = vz.obj(x, y + 60, "list trim")
    so = vz.obj(x, y + 90, "s oscOut")
    vz.c(trig, ag, outlet); vz.c(ag, lp); vz.c(lp, lt); vz.c(lt, so)


def title(x, y, trig, outlet, text):
    vz.c(trig, vz.msg(x, y, oscV("gFillArea", "iiiiii", "0 0 27 9 0") + " " + oscV("gPrintln", "iiiiis", f"1 1 8 1 {text}")), outlet)


# ---- WAVE: 4) scroll the history  3) new column  2) frame  1) scope  0) title
wvT = vz.obj(200, 400, "t b b b b b")
vz.c(viewS, wvT, 0)
shift(200, 440, wvT, 4, VIS_HX)
# new column at x = HX-1: level (dB, 100 = full scale) -> half height h -> rows 32-h .. 31+h, one byte per page
lvE = vz.obj(1000, 440, "expr int(max(0 \\, min(1 \\, (visenv-100+visrange)/visrange))*31)")
lvT = vz.obj(1000, 470, "t f b")                        # 1) reset the level  0) h to the 8 pages
lvZ = vz.msg(1100, 500, "0")
lvZv = vz.obj(1100, 530, "v visenv")
lvD = vz.obj(1000, 500, "t " + " ".join(["f"] * 8))
vz.c(wvT, lvE, 3); vz.c(lvE, lvT); vz.c(lvT, lvZ, 1); vz.c(lvZ, lvZv); vz.c(lvT, lvD, 0)
for p_ in range(8):
    lo_, hi_ = "(32-$f1)", "(31+$f1)"
    top_, bot_ = 8 * p_, 8 * p_ + 7
    ex_ = (f"expr if(min({hi_} \\, {bot_})>=max({lo_} \\, {top_}) \\, "
           f"pow(2 \\, min({hi_} \\, {bot_})-{top_}+1)-pow(2 \\, max({lo_} \\, {top_})-{top_}) \\, 0)")
    e_ = vz.obj(1000 + p_ * 120, 540, ex_)
    m_ = vz.msg(1000 + p_ * 120, 570, f"\\; visbm {p_ * 128 + VIS_HX - 1} \\$1")
    vz.c(lvD, e_, p_); vz.c(e_, m_)
send_frame(200, 600, wvT, 2)
# scope: the 44 values captured since the last frame, after 84 points on the centre line, as one /oled/gWaveform
scT = vz.obj(500, 600, "t b b")                         # 1) send the last capture  0) capture the next one
scG = vz.obj(500, 630, "array get visy")
scC = vz.obj(500, 660, "list prepend " + " ".join(["32"] * VIS_HX))
scL = vz.obj(500, 690, "list prepend sendtyped /oled/gWaveform ib 3")
scLt = vz.obj(500, 720, "list trim")
scO = vz.obj(500, 750, "s oscOut")
scB = vz.msg(700, 630, "\\; vis-scope-bang bang")
vz.c(wvT, scT, 1); vz.c(scT, scG, 1); vz.c(scG, scC); vz.c(scC, scL); vz.c(scL, scLt); vz.c(scLt, scO)
vz.c(scT, scB, 0)
title(200, 800, wvT, 0, "WAVE")

# ---- SPEC: 3) scroll the whole picture  2) new column (x = 127)  1) frame  0) title
spT = vz.obj(200, 900, "t b b b b")
vz.c(viewS, spT, 1)
shift(200, 940, spT, 3, 128)
# rows 0 (top, 16 kHz) .. 63 (bottom, 40 Hz), log spaced; each row = the loudest of 3 bins across its band
BIN = 44100 / VIS_N


def row_bins(r):
    f_lo = 40 * 400 ** ((63 - r - 0.5) / 63)
    f_hi = 40 * 400 ** ((63 - r + 0.5) / 63)
    a, b = max(1, int(round(f_lo / BIN))), min(VIS_N // 2 - 1, int(round(f_hi / BIN)))
    if b < a:
        b = a
    return a, (a + b) // 2, b


spD = vz.obj(1000, 940, "t " + " ".join(["b"] * 8))
vz.c(spT, spD, 2)
for p_ in range(8):
    terms = []
    for i_ in range(8):
        r_ = 8 * p_ + i_
        a, m, b = row_bins(r_)
        lvl = f"max(max(visfft[{a}] \\, visfft[{m}]) \\, visfft[{b}])"
        thr = f"{VIS_TOP}-visrange*(1-visbay[{(r_ % 4) * 4}+viscol])"
        terms.append(f"({lvl}>{thr})*{2 ** i_}")
    e_ = vz.obj(1000 + p_ * 120, 980, "expr " + "+".join(terms))
    m_ = vz.msg(1000 + p_ * 120, 1010, f"\\; visbm {p_ * 128 + 127} \\$1")
    vz.c(spD, e_, p_); vz.c(e_, m_)
send_frame(200, 1100, spT, 1)
title(200, 1250, spT, 0, "SPEC")
vz.save("vis.pd")

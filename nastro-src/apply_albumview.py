#!/usr/bin/env python3
"""Album viewer. Projects menu (encoder) -> ALBUMS >: turn = choose an album (newest first), press = play / stop,
AUX + C#5 / D#5 = 5 s back / forward while playing. The page shows the album number, its length (or the position
while playing), a 42-bar waveform and the playhead.
- Waveform: while an album records, one peak every 4096 samples goes into albpk; at the stop it is reduced to 42
  bars and saved with the length and the highest bar in album-N.txt (44 numbers), so opening an album reads 44
  numbers, never the WAV. Albums recorded before this have no .txt: length shown as ?, no bars, they still play.
- Play: readsf~ streams the WAV from disk straight to the outputs. It stops on leaving the page, choosing another
  album, or at the end of the file. Redraw 4 times a second while playing.
State lives in [v] variables: albon (page open), albsel (album under the cursor, 0 = BACK), albplay (album
playing, 0 = none; also sent as alb-play), albpos (play position in samples, refreshed by [s alb-pos-upd] before it is read)."""
import shutil

for f in ("genalbum.py", "genproj.py"):
    shutil.copy(f, f + ".pre-albumview")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


VIEW = r'''
# ---------------------------------------------------------------- album viewer (apply_albumview.py)
NBA = 42
SR_ = 44100


def oscA(path, types, args):
    return f"\\; oscOut sendtyped /oled/{path} {types} 3 {args}"


al.obj(700, 110, "table albpk 40000")                 # one peak per 4096 samples: up to ~1 hour
al.obj(700, 140, f"table albw {NBA + 2}")              # 42 bars, [42] length in s, [43] highest bar
for i_, nm_ in enumerate(("albon", "albsel", "albplay", "albpos")):
    al.obj(700 + i_ * 90, 170, f"v {nm_}")

# --- peaks while recording: env~ (dB) -> amplitude -> albpk[n], n counts up from 0 at each start
pkEnv = al.obj(900, 400, "env~ 4096 4096")
al.c(al.obj(900, 370, "r~ alb-L"), pkEnv)
pkSp = al.obj(900, 430, "spigot")
al.c(on1, pkSp, 0, 1); al.c(off0, pkSp, 0, 1)
pkA = al.obj(900, 460, "expr if($f1>0 \\, pow(10 \\, ($f1-100)/20) \\, 0)")
pkT = al.obj(900, 490, "t f b")
pkC = al.obj(1000, 520, "f 0"); pkI = al.obj(1050, 520, "+ 1"); pkCT = al.obj(1000, 550, "t f f")
pkM = al.obj(1000, 580, "moses 40000")
pkW = al.obj(900, 620, "tabwrite albpk")
nTot = al.obj(1100, 550, "f 0")                        # peaks written so far
al.c(pkEnv, pkSp); al.c(pkSp, pkA); al.c(pkA, pkT)
al.c(pkT, pkC, 1); al.c(pkC, pkCT); al.c(pkCT, pkI, 1); al.c(pkI, pkC, 0, 1); al.c(pkI, nTot, 0, 1)
al.c(pkCT, pkM, 0); al.c(pkM, pkW, 0, 1); al.c(pkT, pkW, 0)
pk0 = al.msg(1100, 490, "0")
al.c(stT, pk0, 1); al.c(pk0, pkC, 0, 1); al.c(pk0, nTot, 0, 1)
albK = al.obj(1200, 550, "f")                          # number of the album being recorded
al.c(nT, albK, 0, 1)

# --- at the stop: 3) clear  2) 42 bars + highest bar  1) length  0) write album-N.txt
bnT = al.obj(1300, 600, "t b b b b")
al.c(spT, bnT, 1)
al.c(bnT, al.msg(1300, 630, "\\; albw const 0"), 3)
bnN = al.obj(1400, 640, "t f f f f")
al.c(bnT, nTot, 2); al.c(nTot, bnN)
bnIx = al.obj(1550, 790, f"expr if($f2>={NBA} \\, int($f1*{NBA}/$f2) \\, $f1)")
bnV = al.obj(1400, 820, f"expr if($f2>={NBA} \\, max(albw[int($f1*{NBA}/$f2)] \\, albpk[$f1]) \\, albpk[int($f1*$f2/{NBA})])")
al.c(bnN, bnIx, 3, 1); al.c(bnN, bnV, 2, 1)
bnU = al.obj(1400, 700, "until"); bnJ = al.obj(1400, 730, "f"); bnJ1 = al.obj(1450, 730, "+ 1")
bnZ = al.msg(1480, 670, "0")
bnCnt = al.obj(1400, 670, f"max {NBA}")
al.c(bnN, bnZ, 1); al.c(bnZ, bnJ, 0, 1); al.c(bnN, bnCnt, 0); al.c(bnCnt, bnU)
al.c(bnU, bnJ); al.c(bnJ, bnJ1); al.c(bnJ1, bnJ, 0, 1)
bnJT = al.obj(1400, 760, "t f f f")
bnW = al.obj(1400, 850, "tabwrite albw")
bnMx = al.obj(1600, 850, f"expr max(albw[43] \\, albpk[if($f2>={NBA} \\, $f1 \\, int($f1*$f2/{NBA}))])")
al.c(bnN, bnMx, 3, 1)
al.c(bnJ, bnJT)
al.c(bnJT, bnMx, 2); al.c(bnMx, al.msg(1600, 880, "\\; albw 43 \\$1"))
al.c(bnJT, bnIx, 1); al.c(bnIx, bnW, 0, 1)
al.c(bnJT, bnV, 0); al.c(bnV, bnW, 0, 0)
bnL = al.obj(1700, 640, f"expr $f1*4096/{SR_}")
nTot2 = al.obj(1700, 610, "f")
al.c(pkI, nTot2, 0, 1); al.c(pk0, nTot2, 0, 1)
al.c(bnT, nTot2, 1); al.c(nTot2, bnL); al.c(bnL, al.msg(1700, 670, "\\; albw 42 \\$1"))
mkT = al.obj(1800, 640, "makefilename album-%d.txt")
al.c(bnT, albK, 0); al.c(albK, mkT); al.c(mkT, al.msg(1800, 670, "\\; albw write \\$1"))

# --- menu entries for the ALBUMS context: < BACK, then album N .. 1
amT = al.obj(20, 700, "t b b")
al.c(al.obj(20, 670, "r alb-menu"), amT)
amIns = al.obj(20, 880, "text insert nst-menu 1e+06")
amB = al.msg(120, 730, "list 0 0")
al.c(amT, amB, 1); al.c(amB, amIns)
amN = al.obj(20, 730, "expr albn[0]")
amNT = al.obj(20, 760, "t f f")
amU = al.obj(20, 790, "until"); amC = al.obj(20, 820, "f"); amC1 = al.obj(70, 820, "- 1")
amL = al.obj(20, 850, "list prepend 9")
al.c(amT, amN, 0); al.c(amN, amNT); al.c(amNT, amC, 1, 1); al.c(amNT, amU, 0)
al.c(amU, amC); al.c(amC, amC1); al.c(amC1, amC, 0, 1); al.c(amC, amL); al.c(amL, amIns)

# --- page open = mode 5 and menu context 2
pgE = al.obj(2000, 100, "expr $f1==5 && $f2==2")
pgT1 = al.obj(2000, 70, "t b f"); pgT2 = al.obj(2100, 70, "t b f")
al.c(al.obj(2000, 40, "r mode"), pgT1); al.c(al.obj(2100, 40, "r pm-ctx"), pgT2)
al.c(pgT1, pgE, 1, 0); al.c(pgT2, pgE, 1, 1); al.c(pgT2, pgE, 0, 0)
pgOn = al.obj(2000, 130, "change -1"); pgOT = al.obj(2000, 160, "t f f f")
al.c(pgE, pgOn); al.c(pgOn, pgOT); al.c(pgOT, al.obj(2100, 190, "v albon"), 2)

# --- position: [s alb-pos-upd] -> alb-pos = start point + elapsed time
tmr = al.obj(2900, 640, "timer")
onsF = al.obj(3000, 640, "f 0")
psB = al.obj(3000, 760, "t b b")
psE = al.obj(3000, 820, "expr $f2+$f1*44.1")
al.c(al.obj(3000, 730, "r alb-pos-upd"), psB)
al.c(psB, onsF, 1); al.c(onsF, psE, 0, 1); al.c(psB, tmr, 0, 1); al.c(tmr, psE, 0, 0)
al.c(psE, al.obj(3000, 850, "v albpos"))

# --- stop: 2) readsf~ 0  1) alb-play 0  0) redraw
rd = al.obj(2700, 700, "readsf~ 2")
al.c(rd, al.obj(2700, 740, "throw~ outL"), 0); al.c(rd, al.obj(2800, 740, "throw~ outR"), 1)
plSt = al.obj(2700, 400, "t b b b")
rd0 = al.msg(2700, 430, "0")
al.c(plSt, rd0, 2); al.c(rd0, rd)
al.c(plSt, al.msg(2780, 430, "\\; alb-play 0"), 1)
al.c(al.obj(2900, 400, "r alb-play"), al.obj(2900, 430, "v albplay"))
al.c(plSt, al.msg(2860, 430, "\\; alb-dirty bang"), 0)
al.c(rd, plSt, 2)                                         # end of the file
offS = al.obj(2000, 220, "sel 0")
al.c(pgOT, offS, 0); al.c(offS, plSt)                    # page left

# --- play album k from a start point: [k onset( -> open + start, alb-play k, clock restart
go = al.obj(2700, 520, "t b l l")
al.c(al.obj(2600, 490, "r alb-go"), go)
goU = al.obj(2700, 580, "unpack f f")
goMk = al.obj(2700, 610, "makefilename album-%d.wav")
goP = al.obj(2700, 640, "pack s f")
goO = al.msg(2700, 670, "open \\$1 \\$2 \\, 1")
al.c(go, goU, 2); al.c(goU, goP, 1, 1); al.c(goU, goMk, 0); al.c(goMk, goP); al.c(goP, goO); al.c(goO, rd)
goS = al.obj(3000, 580, "unpack f f")
al.c(go, goS, 1)
al.c(goS, onsF, 1, 1); al.c(goS, al.msg(3100, 610, "\\; alb-play \\$1 \\; alb-dirty bang"), 0)
al.c(go, tmr, 0)                                          # restart the clock

# --- press on album k: playing it -> stop, else play it from the start
prE = al.obj(2700, 280, "expr $f1==albplay")
prK = al.obj(2700, 250, "t f f")
prF = al.obj(2800, 310, "f")
prS = al.obj(2700, 310, "sel 1 0")
al.c(al.obj(2700, 220, "r alb-press"), prK)
al.c(prK, prF, 1, 1); al.c(prK, prE, 0); al.c(prE, prS)
al.c(prS, plSt, 0)
al.c(prS, prF, 1); al.c(prF, al.msg(2800, 340, "\\; alb-go \\$1 0"))

# --- selection: the menu row under the cursor -> alb-sel (0 = BACK); load its waveform; another album stops play
slT = al.obj(2300, 130, "t b f")
al.c(al.obj(2300, 100, "r pm-sel"), slT)
slSp = al.obj(2300, 220, "spigot")
slG = al.obj(2300, 250, "text get nst-menu")
slR = al.obj(2300, 280, "route 0 9")
al.c(pgOT, slSp, 1, 1)
al.c(slT, slSp, 1); al.c(slSp, slG); al.c(slG, slR)
pgB = al.obj(2200, 190, "sel 1")                          # page opened: read the row under the cursor
al.c(pgOT, pgB, 0)
pgSel = al.obj(2200, 220, "f")
al.c(al.obj(2250, 160, "r pm-sel"), pgSel, 0, 1); al.c(pgB, pgSel); al.c(pgSel, slG)
slK = al.obj(2300, 340, "t f f f")
k0 = al.msg(2250, 310, "0")
al.c(slR, k0, 0); al.c(k0, slK); al.c(slR, slK, 1)
chE = al.obj(2500, 370, "expr albplay>0 && $f1!=albplay")
chS = al.obj(2500, 400, "sel 1")
al.c(slK, chE, 2); al.c(chE, chS); al.c(chS, plSt)
al.c(slK, al.obj(2400, 370, "v albsel"), 1)
ldS = al.obj(2300, 400, "moses 1")
ldT = al.obj(2350, 430, "t f b")
ldMk = al.obj(2350, 460, "makefilename album-%d.txt")
al.c(slK, ldS, 0); al.c(ldS, ldT, 1)
al.c(ldT, al.msg(2450, 460, "\\; albw const 0"), 1)
al.c(ldT, ldMk, 0); al.c(ldMk, al.msg(2350, 490, "\\; albw read \\$1 \\; alb-dirty bang"))

# --- AUX + C#5 / D#5 on the page while playing: 5 s back / forward (clipped to the album)
skSp = al.obj(3200, 610, "spigot")
skK = al.obj(3200, 640, "sel 73 75")
al.c(al.obj(3200, 580, "r aux-key"), skSp); al.c(pgOT, skSp, 1, 1); al.c(skSp, skK)
skT = al.obj(3200, 700, "t f b")
for i_, d_ in enumerate(("-5", "5")):
    m_ = al.msg(3200 + i_ * 60, 670, d_)
    al.c(skK, m_, i_); al.c(m_, skT)
al.c(skT, al.msg(3300, 730, "\\; alb-pos-upd bang"), 1)
skE = al.obj(3200, 760, f"expr if(albplay>0 \\, max(0 \\, min(max(0 \\, albw[42]*{SR_}-{SR_}) \\, albpos+$f1*{SR_})) \\, -1)")
skM = al.obj(3200, 790, "moses 0")
skP = al.obj(3200, 850, "pack f f")
skMT = al.obj(3200, 820, "t b f")
skA = al.obj(3300, 850, "expr albplay")
al.c(skT, skE, 0); al.c(skE, skM); al.c(skM, skMT, 1)
al.c(skMT, skP, 1, 1); al.c(skMT, skA, 0); al.c(skA, skP, 0, 0)
al.c(skP, al.obj(3200, 880, "s alb-go"))

# --- redraw 4 times a second while playing on the page
# (the playing album comes straight from [r alb-play]: [v albplay] may not be updated yet)
rdE = al.obj(3400, 370, "expr $f1>0 && $f2")
rdM = al.obj(3400, 400, "metro 250")
rdAp = al.obj(3500, 340, "f 0")
rdPg = al.obj(3600, 310, "t b f")
rdR = al.obj(3400, 280, "r alb-play")
al.c(rdR, rdE, 0, 0); al.c(rdR, rdAp, 0, 1)
al.c(pgOT, rdPg, 0); al.c(rdPg, rdE, 1, 1); al.c(rdPg, rdAp, 0); al.c(rdAp, rdE, 0, 0)
al.c(rdE, rdM); al.c(rdM, al.obj(3400, 430, "s alb-dirty"))

# --- drawing, inside project.pd's frame on [s alb-draw]: 4) position  3) top row  2) waveform  1) playhead  0) PLAY
dwT = al.obj(3600, 40, "t b b b b b")
al.c(al.obj(3600, 10, "r alb-draw"), dwT)
al.c(dwT, al.msg(3700, 40, "\\; alb-pos-upd bang"), 4)
hdE = al.obj(3600, 80, "expr albsel")
hdS = al.obj(3600, 110, "sel 0")
al.c(dwT, hdE, 3); al.c(hdE, hdS)
al.c(hdS, al.msg(3600, 140, oscA("gFillArea", "iiiiii", "0 12 128 10 1") + " " + oscA("gPrintln", "iiiiiss", "4 13 8 0 < BACK")), 0)
hdK = al.obj(3700, 140, "t f f")
al.c(hdS, hdK, 1)
al.c(hdK, al.msg(3700, 170, oscA("gPrintln", "iiiiisf", "1 13 8 1 ALBUM \\$1")), 1)
tmE = al.obj(3800, 170, f"expr if($f1==albplay \\, int(albpos/{SR_}*10)/10 \\, if(albw[42]>0 \\, int(albw[42]*10)/10 \\, -1))")
tmS = al.obj(3800, 200, "moses 0")
al.c(hdK, tmE, 0); al.c(tmE, tmS)
al.c(tmS, al.msg(3800, 230, oscA("gPrintln", "iiiiis", "110 13 8 1 ?")), 0)
al.c(tmS, al.msg(3900, 230, oscA("gPrintln", "iiiiif", "92 13 8 1 \\$1")), 1)
naE = al.obj(4000, 80, "expr albn[0]==0")
naS = al.obj(4000, 110, "sel 1")
al.c(dwT, naE, 3); al.c(naE, naS)
al.c(naS, al.msg(4000, 140, oscA("gPrintln", "iiiiiss", "4 34 8 1 NO ALBUMS")))
# waveform: baseline + bars taller than 0 (x, top, height)
wvE = al.obj(3600, 300, "expr albsel>0 && albw[42]>0")
wvS = al.obj(3600, 330, "sel 1")
wvT = al.obj(3600, 360, "t b b b")
al.c(dwT, wvE, 2); al.c(wvE, wvS); al.c(wvS, wvT)
al.c(wvT, al.msg(3700, 390, oscA("gLine", "iiiiii", "1 39 126 39 1")), 2)
wvZ = al.msg(3700, 420, "0")
wvN = al.msg(3600, 420, f"{NBA}")
wvU = al.obj(3600, 450, "until"); wvC = al.obj(3600, 480, "f"); wvC1 = al.obj(3650, 480, "+ 1")
al.c(wvT, wvZ, 1); al.c(wvZ, wvC, 0, 1); al.c(wvT, wvN, 0); al.c(wvN, wvU)
al.c(wvU, wvC); al.c(wvC, wvC1); al.c(wvC1, wvC, 0, 1)
wvH = al.obj(3600, 510, "expr int(albw[$f1]/max(albw[43] \\, 0.0001)*14)")
wvC2 = al.obj(3700, 510, "t f f")
wvXF = al.obj(3750, 540, "f")
al.c(wvC, wvC2); al.c(wvC2, wvXF, 1, 1); al.c(wvC2, wvH, 0)
wvM = al.obj(3600, 570, "moses 1")
al.c(wvH, wvM)
wvP = al.obj(3600, 630, "pack f f f")
wvY = al.obj(3600, 600, "t b f f")
wvTop = al.obj(3650, 600, "expr 39-$f1"); wvHt = al.obj(3720, 600, "expr 2*$f1+1"); wvX = al.obj(3790, 600, "expr 1+$f1*3")
al.c(wvM, wvY, 1)
al.c(wvY, wvHt, 2); al.c(wvHt, wvP, 0, 2)
al.c(wvY, wvTop, 1); al.c(wvTop, wvP, 0, 1)
al.c(wvY, wvXF, 0); al.c(wvXF, wvX); al.c(wvX, wvP, 0, 0)
al.c(wvP, al.msg(3600, 660, "\\; oscOut sendtyped /oled/gFillArea iiiiii 3 \\$1 \\$2 2 \\$3 1"))
# playhead: the album on the page is the one playing
phE = al.obj(4200, 300, f"expr if(albplay>0 && albplay==albsel && albw[42]>0 \\, 1+int(min(1 \\, albpos/(albw[42]*{SR_}))*125) \\, -1)")
phM = al.obj(4200, 330, "moses 0")
al.c(dwT, phE, 1); al.c(phE, phM)
al.c(phM, al.msg(4200, 360, "\\; oscOut sendtyped /oled/gLine iiiiii 3 \\$1 22 \\$1 56 1"), 1)
# PLAY in the title row while an album plays
plE = al.obj(4400, 300, "expr albplay>0")
plS = al.obj(4400, 330, "sel 1")
al.c(dwT, plE, 0); al.c(plE, plS)
al.c(plS, al.msg(4400, 360, oscA("gFillArea", "iiiiii", "56 0 72 10 0") + " " + oscA("gPrintln", "iiiiis", "58 1 8 1 PLAY")))
'''
edit("genalbum.py", [('al.save("album.pd")\n', VIEW + 'al.save("album.pd")\n')])

# ------------------------------------------------------------------ project.pd: ALBUMS entry, context 2, frame
edit("genproj.py", [
    ('for i, nm in enumerate(("nst-proj-status", "mode", "nst-redraw", "pm-sel", "pm-cur", "pm-rebuilt")):',
     'for i, nm in enumerate(("nst-proj-status", "mode", "nst-redraw", "pm-sel", "pm-cur", "pm-rebuilt", "alb-dirty")):'),
    # the tape-edit list only in context 1 (was: any context but 0)
    ('p.c(p.obj(700, 90, "r pm-ctx"), spE, 0, 1)',
     'spEc = p.obj(700, 105, "== 1")                    # apply_albumview.py: context 2 = albums\n'
     'p.c(p.obj(700, 90, "r pm-ctx"), spEc); p.c(spEc, spE, 0, 1)\n'
     'spA = p.obj(800, 165, "spigot 0")\n'
     'spAc = p.obj(800, 120, "== 2")\n'
     'p.c(p.obj(800, 90, "r pm-ctx"), spAc); p.c(spAc, spA, 0, 1)\n'
     'p.c(rebuild, spA, 3); p.c(spA, p.obj(800, 195, "s alb-menu"))'),
    ('mirL = p.msg(380, 255, "list 7 0")', 'mirL = p.msg(380, 255, "list 8 0 \\\\, list 7 0")'),
    ('p.c(sysT, sysL, 0); p.c(sysL, ins)',
     'sysSp = p.obj(300, 255, "spigot 1")\n'
     'sysNa = p.obj(220, 240, "!= 2")\n'
     'p.c(p.obj(220, 225, "r pm-ctx"), sysNa); p.c(sysNa, sysSp, 0, 1)\n'
     'p.c(sysT, sysSp, 0); p.c(sysSp, sysL); p.c(sysL, ins)'),
    ('actR = p.obj(800, 1030, "route 0 1 2 3 4 5 6 7")', 'actR = p.obj(800, 1030, "route 0 1 2 3 4 5 6 7 8 9")'),
    ('p.c(actR, p.msg(1700, 1120, "\\\\; nst-proj-status symbol \\\\; pm-ctx 0 \\\\; pm-rebuild bang \\\\; pm-reset bang"), 6)',
     'p.c(actR, p.msg(1700, 1120, "\\\\; nst-proj-status symbol \\\\; pm-ctx 0 \\\\; pm-rebuild bang \\\\; pm-reset bang"), 6)\n'
     'p.c(actR, p.msg(1700, 1150, "\\\\; nst-proj-status symbol \\\\; pm-ctx 2 \\\\; pm-rebuild bang \\\\; pm-reset bang"), 8)\n'
     'p.c(actR, p.obj(1700, 1180, "s alb-press"), 9)'),
    ('ttS = p.obj(250, 1510, "sel 0 1")', 'ttS = p.obj(250, 1510, "sel 0 1 2")'),
    ('p.c(ttS, p.msg(250, 1540, oscp("gPrintln", "iiiiis", "1 1 8 1 PROJECTS")), 0)',
     'p.c(ttS, p.msg(250, 1540, oscp("gPrintln", "iiiiis", "1 1 8 1 PROJECTS")), 0)\n'
     'p.c(ttS, p.msg(250, 1570, oscp("gPrintln", "iiiiis", "1 1 8 1 ALBUMS")), 2)'),
    ('p.c(dT, rowsT, 1)',
     'rwF = p.obj(700, 1420, "f 0")                     # context 2: album.pd draws the page instead of the rows\n'
     'p.c(p.obj(760, 1390, "r pm-ctx"), rwF, 0, 1)\n'
     'rwS = p.obj(700, 1435, "sel 2")\n'
     'p.c(dT, rwF, 1); p.c(rwF, rwS); p.c(rwS, p.obj(800, 1435, "s alb-draw"), 0)\n'
     'rwB = p.obj(650, 1440, "t b")\n'
     'p.c(rwS, rwB, 1); p.c(rwB, rowsT)'),
    ('    lblR = p.obj(X0, 1830, "route 0 1 2 3 4 5 6 7")', '    lblR = p.obj(X0, 1830, "route 0 1 2 3 4 5 6 7 8")'),
    ('    p.c(lblR, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$2 PROJECTS >")), 6)',
     '    p.c(lblR, p.msg(X0 + 260, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$2 PROJECTS >")), 6)\n'
     '    p.c(lblR, p.msg(X0 + 360, 1950, oscp("gPrintln", "iiiiiss", f"4 {Y} 8 \\\\$2 ALBUMS >")), 8)'),
])
print("album viewer applied")

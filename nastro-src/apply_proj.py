#!/usr/bin/env python3
"""Projects: modules save / load on [nst-save P] / [nst-load P] with p<P>- file names; restore receivers;
encoder keys in the Mac sim; project.pd in main."""
import shutil

for f in ("gen.py", "gentape.py", "gensmpl.py", "genseq.py", "gendrum.py", "genmix.py", "gensynth.py", "gensim.py"):
    shutil.copy(f, f + ".pre-proj")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


# ---------------- tape: 4 wav per project, loop restore
edit("gentape.py", [
    (r'''# --- save (AUX+A) / load at startup, next to the patch
sf = t.obj(260, 420, "soundfiler")
sv = t.obj(260, 360, "t b b b b")
t.c(selk, sv, 3)
ld = t.obj(420, 360, "t b b b b b")
t.c(ld, t.obj(420, 330, "s tp-loaded"), 0)
t.c(tlb, ld, 0)
for k in range(4):
    w = t.msg(260, 450 + k * 25, f"write -wave -bytes 2 tape-{k+1}.wav tape{k+1}")
    r = t.msg(560, 450 + k * 25, f"read tape-{k+1}.wav tape{k+1}")
    t.c(sv, w, k); t.c(w, sf); t.c(ld, r, k + 1); t.c(r, sf)''',
     r'''# --- save / load with the project (project.pd sends nst-save / nst-load with the project number)
sf = t.obj(260, 420, "soundfiler")
sv = t.obj(260, 360, "t f f f f")
t.c(t.obj(260, 330, "r nst-save"), sv)
ld = t.obj(420, 360, "t b f f f f")
t.c(t.obj(420, 330, "r nst-load"), ld)
t.c(ld, t.obj(420, 390, "s tp-loaded"), 0)
for k in range(4):
    mw = t.obj(260, 450 + k * 50, f"makefilename p%d-tape-{k+1}.wav")
    w = t.msg(260, 475 + k * 50, f"write -wave -bytes 2 \\$1 tape{k+1}")
    lT = t.obj(560, 430 + k * 60, "t f b")
    mr = t.obj(560, 455 + k * 60, f"makefilename p%d-tape-{k+1}.wav")
    r = t.msg(560, 475 + k * 60, f"read \\$1 tape{k+1}")
    t.c(sv, mw, 3 - k); t.c(mw, w); t.c(w, sf)
    t.c(ld, lT, 4 - k); t.c(lT, t.msg(700, 430 + k * 60, f"\\; tape{k+1} const 0"), 1)     # new / missing = empty
    t.c(lT, mr, 0); t.c(mr, r); t.c(r, sf)'''),
    (r'''t.save("tape.pd")''', r'''
# --- restore the loop from a project: "state start end"
tls = t.obj(2000, 700, "r tp-loop-set")
tlsU = t.obj(2000, 730, "unpack f f f")
t.c(tls, tlsU)
tlsS = t.obj(2000, 790, "sel 2")
tlsP = t.obj(2100, 760, "pack f f")
t.c(tlsU, tlsP, 2, 1); t.c(tlsU, tlsP, 1, 0)
tlsK = t.obj(2100, 790, "list")
t.c(tlsP, tlsK, 0, 1)
t.c(tlsU, tlsS, 0)
tlsOn = t.obj(2000, 820, "t b b")
t.c(tlsS, tlsOn, 0)
tlsU2 = t.obj(2100, 850, "unpack f f")
t.c(tlsOn, tlsK, 1); t.c(tlsK, tlsU2); t.c(tlsU2, hiT, 1); t.c(tlsU2, loT, 0)
t.c(tlsOn, m2, 0)
tlsOff = t.obj(2200, 820, "t b b b")
t.c(tlsS, tlsOff, 1)
t.c(tlsOff, mN, 2); t.c(tlsOff, mz, 1); t.c(tlsOff, m0, 0)
t.save("tape.pd")'''),
])

# ---------------- sample
edit("gensmpl.py", [
    (r'''sv = r.msg(20, 520, "write -wave -bytes 2 smpl.wav smpl")
svk = r.obj(20, 460, "r aux-key")
svs = r.obj(20, 490, "sel 69")
r.c(svk, svs); r.c(svs, sv); r.c(sv, sf)
lbl = r.obj(250, 460, "loadbang")
lbT = r.obj(250, 490, "t b b")
dflt = r.msg(350, 520, f"\\; smp-len {SMAX}")
rdM = r.msg(250, 520, "read -resize smpl.wav smpl")
r.c(lbl, lbT); r.c(lbT, dflt, 1); r.c(lbT, rdM, 0); r.c(rdM, sf)''',
     r'''sv = r.msg(20, 520, "write -wave -bytes 2 \\$1 smpl")
svm = r.obj(20, 490, "makefilename p%d-smpl.wav")
r.c(r.obj(20, 460, "r nst-save"), svm); r.c(svm, sv); r.c(sv, sf)
lbT = r.obj(250, 490, "t f b")
r.c(r.obj(250, 460, "r nst-load"), lbT)
dflt = r.msg(350, 520, f"\\; smpl resize {SMAX} \\; smpl const 0 \\; smp-len {SMAX}")
rdm2 = r.obj(250, 520, "makefilename p%d-smpl.wav")
rdM = r.msg(250, 550, "read -resize \\$1 smpl")
r.c(lbT, dflt, 1); r.c(lbT, rdm2, 0); r.c(rdm2, rdM); r.c(rdM, sf)'''),
])

# ---------------- sequencer
edit("genseq.py", [
    (r'''init = q.msg(300, 130, "\\; seqn const 0 \\; seqp 0 16 0.5 0 0 \\; seqn read seq-notes.txt \\; seqp read seq-params.txt")
q.c(lbT, init, 3)''',
     r'''init = q.msg(300, 130, "\\; seqn const 0 \\; seqp 0 16 0.5 0 0")
q.c(lbT, init, 3)
# project save / load
psv = q.obj(500, 100, "t f f")
q.c(q.obj(500, 70, "r nst-save"), psv)
q.c(psv, q.obj(500, 130, "makefilename p%d-seqn.txt"), 1)
q.c(psv, q.obj(650, 130, "makefilename p%d-seqp.txt"), 0)
pld = q.obj(800, 100, "t f f b")
q.c(q.obj(800, 70, "r nst-load"), pld)
q.c(pld, init, 2)'''),
    (r'''saveM = q.msg(1440, 330, "\\; seqn write seq-notes.txt \\; seqp write seq-params.txt")
q.c(aks, saveM, 3)''', r''''''),
    (r'''q.save("seq.pd")''', r'''# wire the project file names (created above) to write / read messages
q.save("seq.pd")'''),
])
s = open("genseq.py").read()
s = s.replace(r'''q.c(psv, q.obj(500, 130, "makefilename p%d-seqn.txt"), 1)
q.c(psv, q.obj(650, 130, "makefilename p%d-seqp.txt"), 0)''', r'''mkn = q.obj(500, 130, "makefilename p%d-seqn.txt"); mkp = q.obj(650, 130, "makefilename p%d-seqp.txt")
q.c(psv, mkn, 1); q.c(psv, mkp, 0)
q.c(mkn, q.msg(500, 160, "\\; seqn write \\$1")); q.c(mkp, q.msg(650, 160, "\\; seqp write \\$1"))''')
s = s.replace(r'''q.c(pld, init, 2)''', r'''q.c(pld, init, 2)
lkn = q.obj(800, 130, "makefilename p%d-seqn.txt"); lkp = q.obj(950, 130, "makefilename p%d-seqp.txt")
q.c(pld, lkn, 1); q.c(pld, lkp, 0)
q.c(lkn, q.msg(800, 160, "\\; seqn read \\$1 \\; seq-cur 0")); q.c(lkp, q.msg(950, 160, "\\; seqp read \\$1"))''')
open("genseq.py", "w").write(s)
edit("genseq.py", [
    (r'''rs = q.obj(450, 270, "route 1 2 3 4")''', r'''rs = q.obj(450, 270, "route 1 2 3 4")
q.c(q.obj(560, 240, "r seq-step-set"), rs)'''),
])

# ---------------- drum: per-key settings
edit("gendrum.py", [
    (r'''init = d.msg(200, 120, "\\; dk1 const 0.5 \\; dk2 const 1 \\; dk3 const 1 \\; dk4 const 0.8")''',
     r'''init = d.msg(200, 120, "\\; dk1 const 0.5 \\; dk2 const 1 \\; dk3 const 1 \\; dk4 const 0.8")
dsv = d.obj(700, 90, "t f f f f")
d.c(d.obj(700, 60, "r nst-save"), dsv)
dld = d.obj(1000, 90, "t f f f f b")
d.c(d.obj(1000, 60, "r nst-load"), dld)
d.c(dld, init, 4)
for k in range(4):
    mk = d.obj(700 + k * 70, 120, f"makefilename p%d-dk{k+1}.txt")
    d.c(dsv, mk, 3 - k); d.c(mk, d.msg(700 + k * 70, 150, f"\\; dk{k+1} write \\$1"))
    lk = d.obj(1000 + k * 70, 120, f"makefilename p%d-dk{k+1}.txt")
    d.c(dld, lk, 3 - k); d.c(lk, d.msg(1000 + k * 70, 150, f"\\; dk{k+1} read \\$1 \\; nst-redraw bang"))'''),
])

# ---------------- mix: direct setters used when a project is loaded
edit("genmix.py", [
    (r'''rfx = x_.obj(500, 150, "route 1 2 3 4")''', r'''rfx = x_.obj(500, 150, "route 1 2 3 4")
x_.c(x_.obj(380, 120, "r mix-lvl-set"), rlv)
x_.c(x_.obj(620, 120, "r mix-fx-set"), rfx)'''),
    (r'''rpan = x_.obj(200, 680, "route 1 2 3 4")''', r'''rpan = x_.obj(200, 680, "route 1 2 3 4")
x_.c(x_.obj(330, 650, "r mix-pan-set"), rpan)'''),
])

# ---------------- synth: engine from a project
edit("gensynth.py", [
    (r'''e0 = s.msg(100, 290, "0")''', r'''e0 = s.msg(100, 290, "0")
s.c(s.obj(200, 260, "r synth-engine-set"), s.obj(200, 290, "t f"))
engSet = s.obj(200, 290 + 20, "t f")
s.c(s.obj(260, 260, "r synth-engine-set"), engSet)'''),
])
s = open("gensynth.py").read()
s = s.replace('''s.c(s.obj(200, 260, "r synth-engine-set"), s.obj(200, 290, "t f"))\n''', "")
s = s.replace('''s.c(engT, panic, 3)''', '''s.c(engT, panic, 3)\ns.c(engSet, engT)''')
open("gensynth.py", "w").write(s)

# ---------------- main: octave setter, menu context, project defaults, project.pd
edit("gen.py", [
    (r'''clp = m.obj(560, 380, "clip -2 2")''', r'''clp = m.obj(560, 380, "clip -2 2")
m.c(m.obj(660, 350, "r nst-oct-set"), clp)'''),
    (r'''m.obj(560, 530, "table pkval 48")''', r'''m.obj(560, 530, "table pkval 52")'''),
    (r'''m.obj(680, 530, "table pkpick 48")''', r'''m.obj(680, 530, "table pkpick 52")'''),
    (r'''0.5 0.5 0.5 0.5 \\; pkphys''', r'''0.5 0.5 0.5 0.5 0 0 0 0 \\; pkphys'''),
    (r'''ctxE = m.obj(560, 660, "expr if($f1==3 && $f2==0 && $f5==1 \\, 11''', r'''ctxE = m.obj(560, 660, "expr if($f1==5 \\, 12 \\, 0) + if($f1==5 \\, 0 \\, if($f1==3 && $f2==0 && $f5==1 \\, 11'''),
    (r'''m.c(m.obj(560, 790, "loadbang"), pkInit)''', r'''m.c(m.obj(560, 790, "loadbang"), pkInit)
m.c(m.obj(700, 790, "r nst-pk-defaults"), pkInit)'''),
    (r'''m.obj(1170, 680, "smpl")''', r'''m.obj(1170, 680, "smpl")
m.obj(1220, 680, "project")'''),
    (r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gensmpl.py")).read())''',
     r'''exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gensmpl.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "genproj.py")).read())'''),
])
# the ctx expression gained an extra "if(" ... ")" pair: close it
g = open("gen.py").read()
a = g.index('ctxE = m.obj(560, 660, "expr if($f1==5')
b = g.index('")', a)
g = g[:b] + ")" + g[b:]
open("gen.py", "w").write(g)

# ---------------- Mac sim: encoder on , . (turn) and / (press)
edit("gensim.py", [
    (r'''codes += [ord("["), ord("]"), ord(";"), ord("'"), ord("\\")]''',
     r'''codes += [ord("["), ord("]"), ord(";"), ord("'"), ord("\\")]
ENC = [ord(","), ord("."), ord("/")]   # encoder: turn back / forward, press'''),
])
s = open("gensim.py").read()
a = "# audio"
assert s.count(a) == 1
s = s.replace(a, '''# encoder (the Organelle sends /encoder/turn 0|1 and /encoder/button 1|0 to [s enc] / [s encbut])
ek = add("obj", 900, 420, "key")
eku = add("obj", 1000, 420, "keyup")
es = add("obj", 900, 450, "sel " + " ".join(str(c) for c in ENC))
eus = add("obj", 1000, 450, "sel " + str(ENC[2]))
c(ek, es); c(eku, eus)
c(es, add("msg", 900, 480, "\\\\; enc 0"), 0)
c(es, add("msg", 960, 480, "\\\\; enc 1"), 1)
c(es, add("msg", 1020, 480, "\\\\; encbut 1"), 2)
c(eus, add("msg", 1000, 510, "\\\\; encbut 0"), 0)
add("text", 900, 390, "encoder: virgola / punto = gira - barra = premi")

''' + a, 1)
open("gensim.py", "w").write(s)
print("projects hooked")

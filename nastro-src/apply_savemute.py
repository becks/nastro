#!/usr/bin/env python3
"""Saving / loading blocks Pd while the tape WAVs are written / read (Pd 0.49 soundfiler is synchronous): the audio
broke up (crackle). Now, before a save or a load: tape stops (the sequencer follows), synth notes off, the output
fades to 0 in 40 ms; the file work starts 80 ms later; the output fades back in after it."""
import shutil

for f in ("gentape.py", "genmix.py", "genproj.py"):
    shutil.copy(f, f + ".pre-savemute")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


edit("gentape.py", [
    ('t.c(pX, pf, 1, 1); t.c(pX, playT, 0)',
     't.c(pX, pf, 1, 1); t.c(pX, playT, 0)\n'
     'pStop = t.msg(150, 200, "0")\n'
     't.c(t.obj(150, 170, "r tp-stop"), pStop); t.c(pStop, pX)          # stop from outside (save / load)'),
])

edit("genmix.py", [
    ('ms.c(lcL, ms.obj(20, 910, "throw~ outL")); ms.c(lcR, ms.obj(200, 910, "throw~ outR"))',
     '''muL = ms.obj(20, 895, "*~"); muR = ms.obj(200, 895, "*~")
muM = ms.msg(400, 865, "\\\\$1 40")
muLn = ms.obj(400, 880, "line~")
ms.c(ms.obj(400, 850, "r nst-mute"), muM); ms.c(muM, muLn)
muI = ms.msg(500, 865, "1")
ms.c(ms.obj(500, 850, "loadbang"), muI); ms.c(muI, muLn)
ms.c(lcL, muL); ms.c(lcR, muR); ms.c(muLn, muL, 0, 1); ms.c(muLn, muR, 0, 1)
ms.c(muL, ms.obj(20, 910, "throw~ outL")); ms.c(muR, ms.obj(200, 910, "throw~ outR"))'''),
])

QUIET = "\\\\; tp-stop bang \\\\; synth-panic stop \\\\; nst-mute 0"
edit("genproj.py", [
    # save: quiet first, write 80 ms later, open the output again after
    ('p.c(doSave, p.msg(600, 370, "\\\\; nst-proj-status symbol SALVO..."), 1)',
     f'p.c(doSave, p.msg(600, 370, "\\\\; nst-proj-status symbol SALVO... {QUIET}"), 1)'),
    ('svHold = p.obj(500, 370, "pipe 60")', 'svHold = p.obj(500, 370, "pipe 80")'),
    ('svSt = p.obj(500, 500, "makefilename SALVATO-%d")',
     'svSt = p.obj(500, 500, "makefilename SALVATO-%d")\n'
     'svOpen = p.obj(650, 530, "delay 150")\n'
     'svB0 = p.obj(650, 515, "t b")\n'
     'p.c(saveT, svB0, 0); p.c(svB0, svOpen); p.c(svOpen, p.msg(650, 560, "\\\\; nst-mute 1"))'),
    # load from the menu: same
    ('p.c(p.obj(1000, 530, "r pm-load"), loadT)',
     f'''ldQ = p.obj(1000, 500, "t f b")
p.c(p.obj(1000, 470, "r pm-load"), ldQ)
p.c(ldQ, p.msg(1100, 500, "{QUIET}"), 1)
ldHold = p.obj(1000, 530, "pipe 80")
p.c(ldQ, ldHold, 0); p.c(ldHold, loadT)
ldOpen = p.obj(1100, 530, "delay 250")
ldB0 = p.obj(1100, 515, "t b")                  # a float into [delay] would set its time
p.c(ldHold, ldB0); p.c(ldB0, ldOpen); p.c(ldOpen, p.msg(1100, 560, "\\\\; nst-mute 1"))'''),
])
print("savemute applied")

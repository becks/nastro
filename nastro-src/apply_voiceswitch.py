#!/usr/bin/env python3
"""CPU: every synth / drum voice switches its own DSP on at a note and off when its sound has ended
(switch~ inside the voice; PLUK uses 'switch~ 16' which also keeps its 16-sample block).
Off time: release knob + 300 ms after the note-off (FM PAD ARIA SMPL), bell decay after the last note (VETRO),
fixed 2 s (SUB) / 9 s (PLUK) after the note-off, the hit duration (drums). A new note cancels the switch-off."""
import shutil

for f in ("gen.py", "gensynth.py", "gensmpl.py", "gendrum.py"):
    shutil.copy(f, f + ".pre-voiceswitch")


def edit(p, pairs):
    s = open(p).read()
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "w").write(s)


HELPER = r'''

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
'''

edit("gen.py", [
    ('# ---------------------------------------------------------------- fm-voice.pd', HELPER.lstrip("\n") + '\n\n# ---------------------------------------------------------------- fm-voice.pd'),
    ('inl = v.obj(20, 50, "inlet")\ntll = v.obj(20, 80, "t l l")', 'inl = v.obj(20, 50, "inlet")\ntll = v.obj(20, 80, "t l l")\nvoice_switch(v, inl, rel="fm-release")'),
])
edit("gensynth.py", [
    ('    v.text(20, 5, "pluk-voice: Karplus-Strong string. block~ 16 so the loop can be as short as 16 samples")\n    v.obj(600, 5, "block~ 16")',
     '    v.text(20, 5, "pluk-voice: Karplus-Strong string. switch~ 16 so the loop can be as short as 16 samples")'),
])
s = open("gensynth.py").read()
# each voice: right after its inlet
calls = {
    "def sub_voice():": 'voice_switch(v, inl, fixed=2000)',
    "def pluk_voice():": 'voice_switch(v, inl, fixed=9000, block=16)',
    "def pad_voice():": 'voice_switch(v, inl, rel="pd-rel")',
    "def air_voice():": 'voice_switch(v, inl, rel="air-rel")',
    "def bell_voice():": 'voice_switch(v, inl, rel="bell-dec", onset_only=True)',
}
for head, call in calls.items():
    i = s.index(head)
    j = s.index('inl = v.obj(20, 40, "inlet")', i)
    k = s.index("\n", j)
    s = s[:k + 1] + "    " + call + "\n" + s[k + 1:]
open("gensynth.py", "w").write(s)
edit("gensmpl.py", [
    ('inl = v.obj(20, 40, "inlet")\ntll = v.obj(20, 70, "t l l")', 'inl = v.obj(20, 40, "inlet")\ntll = v.obj(20, 70, "t l l")\nvoice_switch(v, inl, rel="smp-rel")'),
])
edit("gendrum.py", [
    ('inl = dv.obj(20, 40, "inlet")', 'inl = dv.obj(20, 40, "inlet")\nvoice_switch(dv, inl, dur_field=2, fixed=3000)'),
])
print("voiceswitch applied")

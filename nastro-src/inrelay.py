"""Controls and context for the virtual Organelle in oled-sim.py (used by genmirror.py and gensim.py).
Relays what the player does (keys, AUX, knobs, encoder, footswitch) as /in/... and the page state as /ctx/...,
in the same FUDI "send <path> <values>" form as the OLED commands. Context messages are deferred with [pipe 0], so
a key press always reaches the computer before the page change it causes (oled-sim labels a combination with the
state it was pressed in). Knobs go out in whole percent and only when the value changes."""

INPUTS = [("notes", "/in/notes"), ("aux", "/in/aux"), ("fs", "/in/fs"), ("enc", "/in/enc"), ("encbut", "/in/encbut")]
CONTEXT = ["mode", "mix-page", "seq-page", "synth-engine", "syn-lfo-page", "drum-kit"]


def relay_inputs(obj, msg, c, lt, x, y, resend=None):
    """obj/msg(x, y, text) -> index, c(a, b, outlet, inlet); lt = the [list trim] feeding the netsend.
    resend: an object whose outlet 0 bangs when the computer connects (the context is sent again then)."""
    for k, (rcv, path) in enumerate(INPUTS):
        lp = obj(x + k * 160, y + 30, f"list prepend send {path}")
        c(obj(x + k * 160, y, f"r {rcv}"), lp)
        c(lp, lt)
    for k in range(4):
        xk = x + k * 160
        sc = obj(xk, y + 90, "* 100")
        ri = obj(xk, y + 115, "i")
        ch = obj(xk, y + 140, "change")
        lp = obj(xk, y + 165, f"list prepend send /in/knob {k + 1}")
        c(obj(xk, y + 65, f"r knob{k + 1}"), sc)
        c(sc, ri); c(ri, ch); c(ch, lp); c(lp, lt)
    for k, rcv in enumerate(CONTEXT):
        xk = x + k * 160
        pp = obj(xk, y + 230, "pipe 0")
        tt = obj(xk, y + 255, "t f f")
        st = obj(xk, y + 280, "f")
        lp = obj(xk, y + 305, f"list prepend send /ctx/{rcv}")
        c(obj(xk, y + 205, f"r {rcv}"), pp)
        c(pp, tt); c(tt, st, 1, 1); c(tt, lp, 0); c(st, lp); c(lp, lt)
        if resend is not None:
            c(resend, st)

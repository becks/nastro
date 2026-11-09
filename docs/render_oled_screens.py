#!/usr/bin/env python3
"""Render representative Nastro OLED screens with the bundled Organelle OLED renderer.

The patch itself emits the same gPrintln/gLine/gBox primitives.  This small
documentation renderer deliberately uses the simulator's Oled class rather
than a look-alike font or a drawing library, so the output has the hardware's
128 x 64 layout and glyphs.  Run from the repository root:

    python3 docs/render_oled_screens.py
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "oled"
spec = spec_from_file_location("oled_sim", ROOT / "Nastro" / "oled-sim.py")
module = module_from_spec(spec)
spec.loader.exec_module(module)


def fresh():
    oled = module.Oled()
    oled.info_bar = False
    oled.clear()
    return oled


def text(oled, x, y, value, invert=1, size=8):
    oled.println(str(value), x, y, size, invert)


def bar(oled, y, label, value, width=60):
    text(oled, 1, y - 1, label)
    oled.box(64, y - 2, 63, 9, 1)
    oled.fill_area(66, y, int(value * width), 5, 1)


def save(name, draw):
    oled = fresh()
    draw(oled)
    oled.show()
    (OUT / f"{name}.png").write_bytes(module.png(oled.shown))


def header(oled, title, badge=None):
    text(oled, 1, 1, title)
    if badge:
        oled.fill_area(67, 0, 60, 10, 1)
        text(oled, 69, 1, badge, 0)


def draw_synth_fm(oled):
    header(oled, "SYNTH", "FM")
    text(oled, 92, 1, "oct 0")
    bar(oled, 15, "RATIO", .30)
    text(oled, 34, 14, "2")
    bar(oled, 27, "INDEX", .56)
    text(oled, 34, 26, "5.6")
    bar(oled, 39, "ATTACK", .22)
    text(oled, 34, 38, "22")
    bar(oled, 51, "RELEASE", .48)
    text(oled, 34, 50, "930")


def draw_synth_sample(oled):
    header(oled, "SYNTH", "SMPL")
    text(oled, 92, 1, "oct 0")
    for x, h in enumerate((7, 13, 21, 9, 26, 18, 31, 14, 6, 22, 29, 11, 18, 8, 24, 16, 29, 12, 5, 18, 25, 9, 16, 31, 19, 8, 13, 26, 17, 6, 24, 10, 20, 31, 14, 9, 22, 6, 17, 28, 11, 4)):
        oled.fill_area(1 + x * 3, 42 - h, 2, h, 1)
    oled.line(0, 45, 127, 45, 1)
    for x, label, value in ((1, "STA", "8"), (33, "END", "94"), (65, "REL", "420"), (97, "LOOP", "on")):
        text(oled, x, 47, label)
        text(oled, x, 55, value)


def draw_drum(oled):
    header(oled, "DRUM")
    text(oled, 40, 1, "key 9")
    for x, h in enumerate((7, 13, 21, 9, 26, 18, 31, 14, 6, 22, 29, 11, 18, 8, 24, 16, 29, 12, 5, 18, 25, 9, 16, 31, 19, 8, 13, 26, 17, 6, 24, 10, 20, 31, 14, 9, 22, 6, 17, 28, 11, 4)):
        oled.fill_area(1 + x * 3, 42 - h, 2, h, 1)
    oled.line(0, 45, 127, 45, 1)
    for x, label, value in ((1, "PIT", "+2"), (33, "LEN", "78"), (65, "TON", "64"), (97, "LVL", "80")):
        text(oled, x, 47, label)
        text(oled, x, 55, value)


def draw_drum_record(oled):
    header(oled, "DRUM", "ARM")
    text(oled, 1, 14, "VOLUME DRUM")
    text(oled, 4, 24, "80", size=24)
    oled.box(0, 52, 128, 9, 1)
    oled.fill_area(2, 54, 99, 5, 1)
    text(oled, 1, 43, "AUX+E5: INPUT")


def draw_tape(oled):
    text(oled, 1, 1, "PLAY")
    text(oled, 34, 1, "T 2")
    text(oled, 62, 1, "x 1")
    text(oled, 100, 1, "12.3")
    for cx, radius in ((32, 10), (96, 11)):
        oled.circle(cx, 27, radius, 1)
        oled.circle(cx, 27, 3, 1)
        oled.line(cx - 3, 25, cx + 3, 29, 1)
        oled.line(cx + 3, 25, cx - 3, 29, 1)
    oled.line(32, 37, 59, 45, 1)
    oled.line(68, 45, 96, 38, 1)
    oled.fill_area(59, 43, 10, 4, 1)
    text(oled, 1, 45, "DUB 100")
    oled.box(0, 55, 128, 9, 1)
    for y, start, end in ((56, 5, 67), (58, 28, 116), (60, 12, 92), (62, 73, 124)):
        oled.line(start, y, end, y, 1)
    oled.invert_area(48, 54, 2, 10)


def draw_tape_loop(oled):
    draw_tape(oled)
    text(oled, 104, 45, "LOOP")
    oled.line(30, 53, 30, 63, 1)
    oled.line(101, 53, 101, 63, 1)
    oled.box(30, 55, 71, 9, 1)


def dial(oled, cx, value, label, small):
    # round dial used by the MIX page, approximate but using device primitives.
    oled.circle(cx, 30, 12, 1)
    for dx, dy in ((-9, 7), (-12, 0), (-9, -7), (0, -11), (9, -7), (12, 0), (9, 7)):
        oled.line(cx + dx, 30 + dy, cx + dx // 2, 30 + dy // 2, 1)
    positions = ((-8, 7), (-11, 3), (-11, -3), (-7, -8), (0, -10), (7, -8), (11, -3), (11, 3), (8, 7))
    dx, dy = positions[value]
    oled.line(cx, 30, cx + dx, 30 + dy, 1)
    oled.circle(cx, 30, 2, 1, True)
    text(oled, cx - 3, 43, label)
    text(oled, cx - 6, 55, small)


def draw_mix(oled):
    header(oled, "MIX")
    for y, lit in ((1, 9), (5, 8)):
        for i in range(lit):
            oled.fill_area(34 + i * 7, y, 6, 3, 1)
    text(oled, 121, 1, "LIM")
    for cx, value, label, val in ((16, 7, "1", "80"), (48, 5, "2", "55"), (80, 8, "3", "100"), (112, 3, "4", "32")):
        dial(oled, cx, value, label, val)


def draw_pan(oled):
    header(oled, "PAN")
    for cx, value, label, val in ((16, 1, "1", "L 82"), (48, 4, "2", "C"), (80, 6, "3", "R 50"), (112, 3, "4", "L 25")):
        dial(oled, cx, value, label, val)


def draw_fx(oled):
    header(oled, "FX")
    text(oled, 70, 1, "375 ms")
    for y, label, amount in ((15, "TIME", 58), (27, "FDBK", 38), (39, "DLY", 47), (51, "REV", 29)):
        text(oled, 1, y - 1, label)
        oled.box(34, y - 2, 93, 9, 1)
        oled.fill_area(36, y, amount, 5, 1)


def draw_reverb(oled):
    header(oled, "REVERB")
    text(oled, 80, 1, "4.1 s")
    for y, label, amount in ((15, "DEC", 51), (27, "TONE", 65), (39, "PRE", 15), (51, "MOD", 28)):
        text(oled, 1, y - 1, label)
        oled.box(34, y - 2, 93, 9, 1)
        oled.fill_area(36, y, amount, 5, 1)


def draw_tempo(oled):
    header(oled, "TEMPO")
    text(oled, 4, 16, "120", size=24)
    text(oled, 6, 42, "bpm")
    for x in (93, 102, 111, 120):
        oled.box(x, 1, 7, 7, 1)
    oled.fill_area(102, 2, 5, 5, 1)
    oled.line(0, 52, 127, 52, 1)
    for x, label in ((1, "BPM"), (33, "MET"), (65, "LOOP"), (98, "DLY")):
        text(oled, x, 55, label)
    text(oled, 66, 14, "MET 35")
    text(oled, 66, 26, "LOOP bar")
    text(oled, 66, 38, "DLY 1/8")


def draw_step(oled):
    header(oled, "SEQ", "on")
    notes = (60, 0, 64, 67, 0, 69, 72, 71, 0, 67, 64, 62, 60, 0, 64, 67)
    for i, note in enumerate(notes):
        x = 2 + i * 8
        if note:
            height = 5 + (note - 60) * 2
            oled.fill_area(x, 43 - height, 6, height, 1)
        if i == 4:
            oled.box(x - 1, 10, 8, 34, 1)
    oled.line(0, 52, 127, 52, 1)
    for x, value in ((1, "S 5"), (33, "L 16"), (65, "G 75"), (97, "W 12")):
        text(oled, x, 55, value)


def draw_tombola(oled):
    header(oled, "TOMBOLA")
    text(oled, 68, 1, "balls 4")
    points = ((38, 12), (59, 24), (51, 50), (25, 50), (17, 24))
    for i in range(len(points)):
        oled.line(*points[i], *points[(i + 1) % len(points)], 1)
    for x, y in ((35, 25), (46, 32), (29, 40), (42, 44)):
        oled.circle(x, y, 2, 1, True)
    for y, value in ((14, "SPIN 3"), (26, "GRAV 55"), (38, "BNCE 72"), (50, "SIDE 5")):
        text(oled, 80, y, value)


def draw_endless(oled):
    header(oled, "ENDLESS", "PLAY 12")
    notes = (60, 64, 67, 0, 69, 67, 64, 62, 60, 0, 64, 67, 71, 0, 72, 69, 67, 64, 60, 0, 62, 65, 69, 0, 72, 71, 67, 64, 60, 0, 64, 67)
    for i, note in enumerate(notes):
        if note:
            oled.fill_area(1 + i * 4, 48 - (note - 60) * 2, 3, 3, 1)
    oled.line(0, 52, 127, 52, 1)
    for x, value in ((1, "1/16"), (36, "G 70"), (72, "< >"), (92, "P 80")):
        text(oled, x, 55, value)


def draw_edit(oled):
    header(oled, "EDIT-T 2")
    items = ("CUT", "COPY", "PASTE", "REVERSE", "CLEAR")
    for index, item in enumerate(items):
        y = 13 + index * 10
        if index == 1:
            oled.fill_area(0, y - 1, 128, 10, 1)
            text(oled, 4, y, item, 0)
        else:
            text(oled, 4, y, item)


def draw_projects(oled):
    header(oled, "PROJECTS")
    items = ("< BACK", "SAVE PROJ 2", "+ NEW", "PROG 1", "PROG 2  <")
    for index, item in enumerate(items):
        y = 13 + index * 10
        if index == 4:
            oled.fill_area(0, y - 1, 128, 10, 1)
            text(oled, 4, y, item, 0)
        else:
            text(oled, 4, y, item)


SCREENS = {
    "01-synth-fm": draw_synth_fm,
    "02-synth-sample": draw_synth_sample,
    "03-drum": draw_drum,
    "04-drum-record": draw_drum_record,
    "05-tape": draw_tape,
    "06-tape-loop": draw_tape_loop,
    "07-mix-level": draw_mix,
    "08-mix-pan": draw_pan,
    "09-fx-delay": draw_fx,
    "10-reverb": draw_reverb,
    "11-tempo": draw_tempo,
    "12-step-sequencer": draw_step,
    "13-tombola": draw_tombola,
    "14-endless": draw_endless,
    "15-tape-editor": draw_edit,
    "16-projects": draw_projects,
}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in SCREENS.items():
        save(name, draw)
    print(f"Rendered {len(SCREENS)} screens in {OUT}")

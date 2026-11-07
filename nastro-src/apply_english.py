#!/usr/bin/env python3
"""On-screen text in English (menus, pages, status messages, engine names and knob labels).
Replacements are applied to the generator sources, longest phrases first, whole words only."""
import glob, re, shutil

PAIRS = [
    # menus
    ("SCHERMO SU MAC: OFF", "SCREEN TO MAC: OFF"), ("SCHERMO SU MAC: ON", "SCREEN TO MAC: ON"),
    ("SISTEMA (Organelle)", "SYSTEM (Organelle)"), ("SALVA NUOVO", "SAVE NEW"), ("SALVA PROG", "SAVE PROJ"),
    ("< INDIETRO", "< BACK"), ("+ NUOVO", "+ NEW"), ("PROGETTI >", "PROJECTS >"), ("PROGETTI", "PROJECTS"),
    ("MODO: 1 TRACCIA", "MODE: 1 TRACK"), ("MODO: TUTTE", "MODE: ALL"),
    ('"TAGLIA"', '"CUT"'), ('"COPIA"', '"COPY"'), ('"INCOLLA"', '"PASTE"'), ('"INVERTI"', '"REVERSE"'),
    ('"CANCELLA"', '"CLEAR"'), ('"DUPLICA"', '"DUPLICATE"'), ('"ANNULLA"', '"UNDO"'),
    # status messages (max ~11 characters on the title row)
    ("NIENTE-DA-ANNULLARE", "NO-UNDO"), ("MANCA-MIRROR.TXT", "NO-MIRROR.TXT"), ("MEMORIA-VUOTA", "CLIP-EMPTY"),
    ("FINE-NASTRO", "TAPE-END"), ("SU-BATTUTA", "ON-BAR"), ("SU-LOOP", "ON-LOOP"),
    ("SCHERMO-OFF", "SCREEN-OFF"), ("SCHERMO-ON", "SCREEN-ON"), ("1-TRACCIA", "1-TRACK"),
    ("TAGLIO...", "CUTTING"), ("TAGLIATO", "CUT"), ("COPIO...", "COPYING"), ("COPIATO", "COPIED"),
    ("INCOLLO...", "PASTING"), ("INCOLLATO", "PASTED"), ("INVERTO...", "REVERSING"), ("INVERTITO", "REVERSED"),
    ("CANCELLO...", "CLEARING"), ("CANCELLATO", "CLEARED"), ("DUPLICO...", "DUPLICATING"), ("DUPLICATO", "DUPLICATED"),
    ("ANNULLO...", "UNDOING"), ("ANNULLATO", "UNDONE"), ("SALVO...", "SAVING"),
    ("SALVATO-%d", "SAVED-%d"), ("CARICATO-%d", "LOADED-%d"), ("RIMOSSO-%d", "REMOVED-%d"),
    ('symbol NUOVO', 'symbol NEW'), ('"TUTTE"', '"ALL-TRACKS"'),
    # pages
    ("RIVERBERO", "REVERB"), ('"TONO"', '"TONE"'), ("GIRO \\\\$1", "SPIN \\\\$1"), ("RIMB \\\\$3", "BNCE \\\\$3"),
    ("LATI \\\\$4", "SIDE \\\\$4"), ("palle \\\\$5", "balls \\\\$5"), ("70 1 8 0 PAUSA", "70 1 8 0 PAUSE"),
    ("69 1 8 0 ATT", "69 1 8 0 ARM"), ("90 1 8 0 ATT", "90 1 8 0 ARM"),
    # engines and their knobs
    ('"ARIA"', '"AIR"'), ('"VETRO"', '"GLASS"'), ('("MOTO"', '("MOVE"'), ('("INARM"', '("INHAR"'), ('("BATT"', '("BEAT"'),
]
FILES = [f for f in glob.glob("gen*.py") if not f.endswith(".pre-english")]
total = {}
for f in FILES:
    s = open(f).read()
    orig = s
    for a, b in PAIRS:
        n = s.count(a)
        if n:
            s = s.replace(a, b)
            total[a] = total.get(a, 0) + n
    if s != orig:
        shutil.copy(f, f + ".pre-english")
        open(f, "w").write(s)
        print("translated", f)
missing = [a for a, _ in PAIRS if a not in total]
print("not found:", missing)

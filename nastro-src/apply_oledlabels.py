#!/usr/bin/env python3
"""OLED labels: a number sent in a string field ('s' in sendtyped) reaches the screen as "%f" text through
packOSC ("1" -> "1.000000"), so the FILTER page track labels ("1 LP") overlapped each other on the device.
The track number now goes in its own gPrintln as a number ('f'), the LP / HP / -- / Q tag in a second one."""
p = "genmix.py"; s = open(p).read()
a = '    L1 = lambda txt: osc2("gPrintln", "iiiiis", f"{cx - 12} 43 8 1 {k + 1} {txt}")'
b = ('    L1 = lambda txt: (osc2("gPrintln", "iiiiif", f"{cx - 12} 43 8 1 {k + 1}") + " " +\n'
     '                      osc2("gPrintln", "iiiiis", f"{cx - 4} 43 8 1 {txt}"))')
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w").write(s)
print("oled labels fixed")

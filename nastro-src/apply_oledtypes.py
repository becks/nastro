#!/usr/bin/env python3
"""OLED text messages: the type string of every gPrintln is rebuilt when a message box is created (Patch.msg), so
it always matches the arguments. On the Organelle (packOSC) a text with more words than types is dropped and a
number in an 's' field prints as "1.000000": each literal word gets 's', each literal number 'f'; $n placeholders
keep the type given by hand (a $n can be a word, e.g. a synth parameter name)."""
p = "gen.py"; s = open(p).read()

FN = r'''def fix_println_types(text):
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


'''

a = '    def msg(self, x, y, t): return self._add("msg", x, y, t)'
b = '    def msg(self, x, y, t): return self._add("msg", x, y, fix_println_types(t))'
assert s.count(a) == 1 and s.count("class Patch:\n") == 1
s = s.replace(a, b).replace("class Patch:\n", FN + "class Patch:\n", 1)
open(p, "w").write(s)
print("oled types fixed at the source")

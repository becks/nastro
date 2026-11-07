#!/usr/bin/env python3
"""Loop start at index 0, slow playback: tabread4~ cannot interpolate below index 1 (it returns x[1]), so with a
loop starting at 0 the read positions in [0, 1) froze (1 sample at 1x, 4 at 0.25x: an audible glitch). The
per-sample wrap now maps the loop to [lo+1, hi+1): positions in [hi, hi+1) are read past the end, where the guard
puts the loop start (x[hi..hi+2] = x[lo..lo+2], both directions), so the first sample of the loop interpolates
with x[hi-1] as its left neighbour. Seam fix (wrapped track, 1x): the head read x[hi] (= seamsave[0]) for the
first overshoot sample."""
p = "gentape.py"; s = open(p).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)


rep('dW = t.obj(2600, 1900, "expr~ ($v1+$f2>=$f3)*(-$f4)+($v1+$f2<$f5)*$f4")',
    'dW = t.obj(2600, 1900, "expr~ ($v1+$f2>=$f3+1)*(-$f4)+($v1+$f2<$f5+1)*$f4")')
rep('''GUARD = (("$f2", "$f3", "$f3-1", "$f2-1", "1", "$f3>0"),
         ("$f2+1", "$f3+1", "$f3-2", "$f2-2", f"$f2+1<{N}", "$f3>1"),
         ("$f3-1", "$f2-1", "$f2", "$f3", "$f3>0", "1"))''',
    '''GUARD = (("$f2", "$f3", "$f2", "$f3", "1", "1"),
         ("$f2+1", "$f3+1", "$f2+1", "$f3+1", f"$f2+1<{N}", f"$f2+1<{N}"),
         ("$f2+2", "$f3+2", "$f2+2", "$f3+2", f"$f2+2<{N}", f"$f2+2<{N}"))''')
rep("$s2[$f4+$f1]+($s2[$f3+$f1]-$s2[max($f3+$f1 \\\\, 1)])*",
    "$s2[$f4+$f1]+($s2[$f3+$f1]-if($f1==0 \\\\, seamsave[0] \\\\, $s2[$f3+$f1]))*")
open(p, "w").write(s)
print("wrap0 applied")

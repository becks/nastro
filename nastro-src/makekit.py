#!/usr/bin/env python3
"""Synthesize an original 24-slot drum kit (0.5 s per slot) -> drums.wav (44.1 kHz, 16 bit, mono)."""
import math, random, struct, sys, wave

SR = 44100
SLOT = SR // 2
random.seed(7)
TWO_PI = 2 * math.pi


def env_exp(n, decay_s):
    k = math.exp(-1.0 / (decay_s * SR)) if decay_s > 0 else 0
    v, out = 1.0, []
    for _ in range(n):
        out.append(v)
        v *= k
    return out


def sweep_sine(f0, f1, sweep_s, decay_s, n=SLOT):
    out, ph = [], 0.0
    e = env_exp(n, decay_s)
    for i in range(n):
        t = i / SR
        f = f1 + (f0 - f1) * math.exp(-t / sweep_s)
        ph += TWO_PI * f / SR
        out.append(math.sin(ph) * e[i])
    return out


def noise(n=SLOT):
    return [random.uniform(-1, 1) for _ in range(n)]


def onepole_lp(x, fc):
    a = math.exp(-TWO_PI * fc / SR)
    y, out = 0.0, []
    for v in x:
        y = (1 - a) * v + a * y
        out.append(y)
    return out


def onepole_hp(x, fc):
    lp = onepole_lp(x, fc)
    return [a - b for a, b in zip(x, lp)]


def bandpass(x, fc, q):
    # Chamberlin state-variable filter
    f = 2 * math.sin(math.pi * fc / SR)
    low = band = 0.0
    out = []
    for v in x:
        low += f * band
        high = v - low - band / q
        band += f * high
        out.append(band)
    return out


def metallic(freqs, n=SLOT):
    out = [0.0] * n
    for fr in freqs:
        ph = random.random()
        for i in range(n):
            ph += fr / SR
            out[i] += 1.0 if (ph % 1.0) < 0.5 else -1.0
    return out


def mul(x, e):
    return [a * b for a, b in zip(x, e)]


def add(*xs):
    return [sum(v) for v in zip(*xs)]


def scale(x, g):
    return [v * g for v in x]


METAL = [205.3, 304.4, 369.6, 522.7, 540.0, 800.0]


def kit():
    s = []
    click = mul(onepole_hp(noise(), 3000), env_exp(SLOT, 0.003))
    s.append(sweep_sine(150, 45, 0.04, 0.35))                                   # 0 kick
    s.append(add(sweep_sine(190, 55, 0.025, 0.15), scale(click, 0.6)))           # 1 punchy kick
    s.append(sweep_sine(85, 48, 0.08, 0.6))                                      # 2 long sub kick
    s.append(add(scale(sweep_sine(220, 185, 0.03, 0.09), 0.7),                   # 3 snare
                 mul(bandpass(noise(), 2500, 0.7), env_exp(SLOT, 0.16))))
    s.append(add(scale(sweep_sine(260, 230, 0.02, 0.06), 0.5),                   # 4 tight snare
                 mul(onepole_hp(noise(), 1800), env_exp(SLOT, 0.08))))
    s.append(add(sweep_sine(1700, 1600, 0.01, 0.012), scale(sweep_sine(480, 460, 0.01, 0.02), 0.6)))  # 5 rim
    clap_env = [0.0] * SLOT                                                      # 6 clap
    for start in (0, 441, 882, 1323):
        d = env_exp(SLOT - start, 0.008 if start < 1323 else 0.14)
        for i, v in enumerate(d):
            clap_env[start + i] = max(clap_env[start + i], v)
    s.append(mul(bandpass(noise(), 1200, 1.2), clap_env))
    s.append(mul(onepole_hp(noise(), 7000), env_exp(SLOT, 0.03)))               # 7 closed hat
    s.append(mul(onepole_hp(metallic([m * 2.1 for m in METAL]), 6000), env_exp(SLOT, 0.04)))  # 8 metal hat
    s.append(mul(add(onepole_hp(metallic([m * 2.1 for m in METAL]), 6000),       # 9 open hat
                     scale(onepole_hp(noise(), 8000), 0.5)), env_exp(SLOT, 0.3)))
    s.append(mul(onepole_hp(metallic([m * 1.3 for m in METAL]), 3000), env_exp(SLOT, 0.45)))  # 10 ride
    s.append(mul(onepole_hp(add(noise(), scale(metallic([m * 1.7 for m in METAL]), 0.3)), 4000),  # 11 crash
                 env_exp(SLOT, 0.5)))
    s.append(sweep_sine(115, 80, 0.06, 0.3))                                     # 12 low tom
    s.append(sweep_sine(165, 120, 0.05, 0.25))                                   # 13 mid tom
    s.append(sweep_sine(235, 175, 0.04, 0.2))                                    # 14 high tom
    s.append(mul(bandpass(metallic([562, 845]), 900, 2), env_exp(SLOT, 0.12)))   # 15 cowbell
    s.append(sweep_sine(2500, 2450, 0.01, 0.03))                                 # 16 clave
    sh = [min(1.0, i / (0.02 * SR)) for i in range(SLOT)]                       # 17 shaker
    s.append(mul(mul(onepole_hp(noise(), 5000), sh), env_exp(SLOT, 0.07)))
    s.append(mul(add(onepole_hp(metallic([m * 3.3 for m in METAL]), 7000),       # 18 tambourine
                     onepole_hp(noise(), 6000)), env_exp(SLOT, 0.15)))
    s.append(sweep_sine(380, 320, 0.015, 0.18))                                  # 19 conga
    s.append(mul([math.sin(TWO_PI * 880 * i / SR) for i in range(SLOT)], env_exp(SLOT, 0.05)))  # 20 blip
    s.append(sweep_sine(2400, 90, 0.035, 0.18))                                  # 21 zap
    s.append(mul(onepole_lp(noise(), 600), env_exp(SLOT, 0.2)))                 # 22 low noise burst
    bell, e = [], env_exp(SLOT, 0.45)                                            # 23 FM bell
    for i in range(SLOT):
        t = i / SR
        bell.append(math.sin(TWO_PI * 600 * t + 2.5 * e[i] * math.sin(TWO_PI * 840 * t)) * e[i])
    s.append(bell)
    return s


def finish(x):
    peak = max(abs(v) for v in x) or 1.0
    x = [v * 0.85 / peak for v in x]
    fade = int(0.01 * SR)
    for i in range(fade):
        x[-1 - i] *= i / fade
    return x


out = []
for snd in kit():
    out += finish(snd)
w = wave.open(sys.argv[1], "wb")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in out))
w.close()
print("wrote", len(out), "samples")

"""The refined wire logo (round 10, Adi 19 Nov 2026): the Tantra head with only the thin wires, no ringed circuit
nodes, drawn as vector so it stays sharp at any size. Writes src/logo3.svg; js/logo3.js runs small, quiet currents
along the wires. Deterministic (fixed seed), so a rebuild gives the same logo."""
import math, os, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, CX = 1000, 720, 500
rnd = random.Random(31)

def head():
    # right half outline (x offset from centre, y), mirrored for the left half; ears at the sides, soft chin
    R = [(0, 440), (36, 441), (70, 446), (96, 456), (108, 462), (122, 460), (134, 470), (138, 488), (132, 506),
         (120, 518), (106, 522), (100, 540), (94, 566), (82, 594), (64, 620), (44, 642), (22, 660), (0, 668)]
    pts = [(CX + x, y) for x, y in R] + [(CX - x, y) for x, y in reversed(R[1:-1])]
    n = len(pts); d = f'M{pts[0][0]} {pts[0][1]}'
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f' C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}'
    return d + 'Z'

COLS = ['#c9a25f', '#c9a25f', '#2f9e7f', '#7c5cff', '#b78a4a', '#3aa88a', '#8b6cff']

def wires():
    out = []
    N = 34
    for i in range(N):
        t = i / (N - 1)
        ang = math.radians(172 - 164 * t) + rnd.uniform(-.03, .03)        # fan from left to right
        rx, ry = rnd.uniform(330, 470), rnd.uniform(300, 400)
        ex, ey = CX + rx * math.cos(ang), 455 - ry * math.sin(ang)
        ey = max(ey, 40)
        sx = CX + (t - .5) * 190 + rnd.uniform(-6, 6); sy = 452 + abs(t - .5) * 6
        k = rnd.uniform(.5, 1.0) * (1 if i % 2 else -1)
        mx, my = sx + (ex - sx) * .5 + 38 * k, sy + (ey - sy) * .55
        c1 = (sx + (mx - sx) * .1 - 30 * k, sy - (sy - my) * .6)
        c2 = (mx - (ex - sx) * .18, my + (sy - my) * .3)
        c3 = (mx + (ex - sx) * .18, my - (sy - my) * .3)
        c4 = (ex - (ex - mx) * .35 + 26 * k, ey + (my - ey) * .35)
        col = COLS[i % len(COLS)]
        d = (f'M{sx:.1f} {sy:.1f} C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {mx:.1f} {my:.1f}'
             f' C{c3[0]:.1f} {c3[1]:.1f} {c4[0]:.1f} {c4[1]:.1f} {ex:.1f} {ey:.1f}')
        c1, c2 = c3, c4; sx, sy = mx, my
        out.append((d, col, (ex, ey), (sx, sy, c1, c2, ex, ey)))
    return out

def bez(sx, sy, c1, c2, ex, ey, t):
    u = 1 - t
    return (u**3*sx + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*ex, u**3*sy + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*ey)

def build():
    ws = wires()
    g = [f'<svg class="lw3-svg" viewBox="0 0 {W} {H}" aria-hidden="true"><defs>'
         '<radialGradient id="tl3h" cx="50%" cy="48%" r="62%"><stop offset="0" stop-color="#ffffff"/><stop offset=".42" stop-color="#f3f0fb"/>'
         '<stop offset=".8" stop-color="#d9d2ec"/><stop offset="1" stop-color="#c3b9e0"/></radialGradient>'
         '<radialGradient id="tl3g" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
         '<filter id="tl3b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.1"/></filter></defs><g class="lw-wires">']
    for k, (d, col, end, raw) in enumerate(ws):
        g.append(f'<path class="w" data-c="{col}" d="{d}" fill="none" stroke="{col}" stroke-width="1.5" stroke-linecap="round" opacity=".9"/>')
        if k % 3 == 1:   # a short branch off the wire, with a crisp junction dot
            t0 = rnd.uniform(.45, .7); bx, by = bez(*raw, t0)
            dx, dy = raw[4] - bx, raw[5] - by; L = math.hypot(dx, dy) or 1
            side = 1 if k % 2 else -1
            nx, ny = bx + dx / L * 70 - dy / L * 46 * side, by + dy / L * 70 + dx / L * 46 * side
            g.append(f'<path class="w br" data-c="{col}" d="M{bx:.1f} {by:.1f} Q{bx + dx / L * 40:.1f} {by + dy / L * 40:.1f} {nx:.1f} {ny:.1f}" fill="none" stroke="{col}" stroke-width="1.3" stroke-linecap="round" opacity=".8"/>')
            g.append(f'<circle class="jn" cx="{bx:.1f}" cy="{by:.1f}" r="2.6" fill="{col}"/>')
            g.append(f'<circle class="tip" cx="{nx:.1f}" cy="{ny:.1f}" r="2.3" fill="{col}"/>')
    for d, col, (ex, ey), raw in ws:
        g.append(f'<circle class="tip" cx="{ex:.1f}" cy="{ey:.1f}" r="3" fill="{col}"/>')
    g.append('</g>')
    hd = head()
    g.append(f'<path class="hd" d="{hd}" fill="url(#tl3h)" stroke="#c9bfe6" stroke-width="1.2"/>')
    g.append('<ellipse cx="500" cy="540" rx="70" ry="64" fill="url(#tl3g)" class="hglow"/>')
    g.append('<g class="cur"></g></svg>')
    open(ROOT + '/src/logo3.svg', 'w').write(''.join(g))
    print('logo3:', len(ws), 'wires')

if __name__ == '__main__':
    build()

"""Generate the four animated SVG tiles for the profile README into art/.

    python3 gen/art.py [path/to/svi_fits.csv]

Every tile is pure SVG + CSS (no JavaScript), so it animates inside a GitHub
README. Frame-by-frame tiles hold one <g> per frame and CSS shows them in turn.
The volatility tile is built from the Dheston project's SVI fits
(results/svi/svi_fits.csv): real NIFTY 50 implied-vol surfaces, 2022-2026.
"""
import math
import os
import random
import sys

SIZE = 400
OUT = os.path.join(os.path.dirname(__file__), "..", "art")
SVI_DEFAULT = os.path.expanduser(
    "~/Everything related to my projects/Dheston/results/svi/svi_fits.csv"
)


def tile(body, style=""):
    """Wrap tile content in the shared rounded dark box."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'width="{SIZE}" height="{SIZE}">'
        f"<style>{style}</style>"
        f'<clipPath id="box"><rect x="1" y="1" width="{SIZE - 2}" height="{SIZE - 2}" rx="18"/></clipPath>'
        f'<rect x="1" y="1" width="{SIZE - 2}" height="{SIZE - 2}" rx="18" fill="#05070d"/>'
        f'<g clip-path="url(#box)">{body}</g>'
        f'<rect x="1" y="1" width="{SIZE - 2}" height="{SIZE - 2}" rx="18" '
        'fill="none" stroke="#30363d" stroke-width="2"/></svg>'
    )


def frame_css(n, duration):
    """CSS that shows .f frames one after another, forever."""
    return (
        f".f{{visibility:hidden;animation:fr {duration}s step-end infinite}}"
        f"@keyframes fr{{0%{{visibility:visible}}{100 / n:.4f}%{{visibility:hidden}}}}"
    )


def frames(groups, duration):
    dt = duration / len(groups)
    return "".join(
        f'<g class="f" style="animation-delay:{i * dt:.3f}s">{g}</g>' for i, g in enumerate(groups)
    )


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def stars(rng, n):
    out = []
    for _ in range(n):
        x, y = rng.uniform(4, SIZE - 4), rng.uniform(4, SIZE - 4)
        r = rng.choice([0.5, 0.6, 0.8, 1.1])
        tw = rng.random() < 0.3
        style = f' class="tw" style="animation-delay:-{rng.uniform(0, 4):.2f}s"' if tw else ""
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" opacity="{rng.uniform(.3, .9):.2f}"{style}/>')
    return "".join(out)


# --------------------------------------------------------------- black hole
def black_hole():
    rng = random.Random(7)
    cx = cy = SIZE / 2
    shadow = 54
    style = (
        "@keyframes spin{to{stroke-dashoffset:-100}}"
        ".d{fill:none;animation:spin linear infinite}"
        "@keyframes tw{50%{opacity:.1}}.tw{animation:tw 4s ease-in-out infinite}"
        "@keyframes breathe{50%{opacity:.75}}.halo{animation:breathe 5s ease-in-out infinite}"
    )
    defs = (
        "<defs>"
        # Doppler beaming: the side moving toward us (left) is hotter and brighter
        '<linearGradient id="dop" gradientUnits="userSpaceOnUse" x1="20" y1="0" x2="380" y2="0">'
        '<stop offset="0" stop-color="#fffbe8"/><stop offset=".35" stop-color="#ffd27a"/>'
        '<stop offset=".7" stop-color="#ff8a2a"/><stop offset="1" stop-color="#a3300a"/></linearGradient>'
        '<radialGradient id="glow"><stop offset=".25" stop-color="#ff9d3a" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#ff6a00" stop-opacity="0"/></radialGradient>'
        '<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.2"/></filter>'
        '<filter id="bloom" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        "</defs>"
    )

    def ring(path_d, r, width, opacity):
        dash = " ".join(f"{rng.uniform(1, 9):.1f}" for _ in range(8))
        speed = 2.2 * (r / 80) ** 1.5          # Kepler: inner orbits are faster
        return (
            f'<path class="d" d="{path_d}" pathLength="100" stroke="url(#dop)" '
            f'stroke-width="{width:.1f}" opacity="{opacity:.2f}" stroke-dasharray="{dash}" '
            f'style="animation-duration:{speed:.2f}s;animation-delay:-{rng.uniform(0, 5):.2f}s"/>'
        )

    def ellipse_d(rx, ry, half=None):
        if half == "front":   # lower half, left -> right
            return f"M{cx - rx:.1f},{cy} A{rx:.1f},{ry:.1f} 0 0 0 {cx + rx:.1f},{cy}"
        return (f"M{cx - rx:.1f},{cy} A{rx:.1f},{ry:.1f} 0 1 0 {cx + rx:.1f},{cy} "
                f"A{rx:.1f},{ry:.1f} 0 1 0 {cx - rx:.1f},{cy}")

    # light from the far side of the disk, bent over the top and under the bottom
    halo = []
    for r in range(58, 100, 3):
        fade = 1 - (r - 58) / 44
        halo.append(ring(ellipse_d(r * 1.04, r * 0.98), r, 1.4 + 1.6 * fade, 0.25 + 0.7 * fade))
    disk_back, disk_front = [], []
    for rx in range(72, 186, 4):
        fade = 1 - (rx - 72) / 114
        ry = rx * 0.15
        w, op = 1.2 + 2.4 * fade, 0.25 + 0.75 * fade
        disk_back.append(ring(ellipse_d(rx, ry), rx, w, op))
        disk_front.append(ring(ellipse_d(rx, ry, "front"), rx, w, op))

    body = (
        defs + stars(rng, 140)
        + f'<circle cx="{cx}" cy="{cy}" r="150" fill="url(#glow)"/>'
        + f'<g class="halo" filter="url(#bloom)">{"".join(halo)}</g>'
        + f'<g filter="url(#bloom)">{"".join(disk_back)}</g>'
        + f'<circle cx="{cx}" cy="{cy}" r="{shadow + 3}" fill="none" stroke="#fff4d6" stroke-width="2.5" filter="url(#soft)"/>'
        + f'<circle cx="{cx}" cy="{cy}" r="{shadow}" fill="#000"/>'
        + f'<g filter="url(#bloom)">{"".join(disk_front)}</g>'
    )
    return tile(body, style)


# --------------------------------------------------------------- tesseract
def tesseract(n=120, duration=8.0):
    verts = [(x, y, z, w) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1) for w in (-1, 1)]
    edges = [(i, j) for i in range(16) for j in range(i + 1, 16)
             if sum(a != b for a, b in zip(verts[i], verts[j])) == 1]
    colours = ["#22d3ee", "#e879f9", "#a3e635", "#fbbf24"]   # one per axis direction
    groups = []
    for k in range(n):
        t = 2 * math.pi * k / n
        proj = []
        for x, y, z, w in verts:
            # 4D rotations in the XW and YZ planes: the cube turns inside out
            x, w = x * math.cos(t) - w * math.sin(t), x * math.sin(t) + w * math.cos(t)
            y, z = y * math.cos(t) - z * math.sin(t), y * math.sin(t) + z * math.cos(t)
            f4 = 2.4 / (3.2 - w)
            x, y, z = x * f4, y * f4, z * f4
            # fixed 3D view tilt, then perspective to 2D
            a, b = 0.55, 0.35
            x, z = x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a)
            y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
            f3 = 330 / (6 - z)
            proj.append((SIZE / 2 + x * f3, SIZE / 2 + y * f3, f4))
        paths = ["" for _ in colours]
        for i, j in edges:
            axis = next(a for a in range(4) if verts[i][a] != verts[j][a])
            (x1, y1, _), (x2, y2, _) = proj[i], proj[j]
            paths[axis] += f"M{x1:.1f},{y1:.1f}L{x2:.1f},{y2:.1f}"
        g = "".join(f'<path d="{d}" stroke="{c}"/>' for d, c in zip(paths, colours))
        g += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{1.6 * s:.1f}"/>' for x, y, s in proj)
        groups.append(g)
    style = (frame_css(n, duration)
             + "path{fill:none;stroke-width:2;stroke-linecap:round}circle{fill:#fff}")
    defs = ('<defs><filter id="neon" x="-20%" y="-20%" width="140%" height="140%">'
            '<feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/>'
            '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    body = defs + stars(random.Random(3), 60) + f'<g filter="url(#neon)">{frames(groups, duration)}</g>'
    return tile(body, style + "@keyframes tw{50%{opacity:.1}}.tw{animation:tw 4s ease-in-out infinite}")


# --------------------------------------------------------------- lorenz
def lorenz(segments=60, duration=14.0):
    s, r, b, dt = 10.0, 28.0, 8 / 3, 0.004
    x, y, z = 0.1, 0.0, 0.0
    for _ in range(1000):                  # settle onto the attractor
        dx, dy, dz = s * (y - x), x * (r - z) - y, x * y - b * z
        x, y, z = x + dx * dt, y + dy * dt, z + dz * dt
    path = []
    for _ in range(12000):
        dx, dy, dz = s * (y - x), x * (r - z) - y, x * y - b * z
        x, y, z = x + dx * dt, y + dy * dt, z + dz * dt
        path.append((SIZE / 2 + x * 7.2, SIZE - 30 - z * 7.0))
    per = len(path) // segments
    draw_end, fade_start, fade_end = 72.0, 86.0, 97.0
    css, body = [], []
    for i in range(segments):
        seg = path[i * per: (i + 1) * per + 1: 2]
        p0 = draw_end * i / segments
        p1 = draw_end * (i + 1) / segments
        css.append(
            f"@keyframes l{i}{{0%,{p0:.2f}%{{stroke-dashoffset:1;opacity:1}}"
            f"{p1:.2f}%,{fade_start}%{{stroke-dashoffset:0;opacity:1}}"
            f"{fade_end}%{{stroke-dashoffset:0;opacity:0}}100%{{stroke-dashoffset:1;opacity:0}}}}"
            f".l{i}{{animation:l{i} {duration}s linear infinite}}"
        )
        hue = (190 + 170 * i / segments) % 360     # cyan -> violet -> pink -> orange
        body.append(f'<polyline class="l{i}" pathLength="1" points="{pts(seg)}" '
                    f'stroke="hsl({hue:.0f},95%,62%)"/>')
    style = ("polyline{fill:none;stroke-width:1.3;stroke-dasharray:1 1;stroke-linejoin:round}"
             + "".join(css))
    defs = ('<defs><filter id="glow" x="-10%" y="-10%" width="120%" height="120%">'
            '<feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/>'
            '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    return tile(defs + f'<g filter="url(#glow)">{"".join(body)}</g>', style)


# --------------------------------------------------------------- vol surface
def vol_surface(svi_csv, duration=16.0):
    import csv
    from collections import defaultdict

    days = defaultdict(list)
    with open(svi_csv) as f:
        for row in csv.DictReader(f):
            T = int(row["days_to_expiry"]) / 365
            if T < 4 / 365 or float(row["rmse_volpts"]) > 2 or float(row["b"]) > 5:
                continue
            p = [float(row[c]) for c in ("a", "b", "rho", "m", "s")]
            days[row["day"]].append((T, p))

    ks = [-0.15 + 0.3 * i / 16 for i in range(17)]
    Ts = [(7 + 113 * (j / 9) ** 1.5) / 365 for j in range(10)]

    def svi_w(p, k):
        a, b, rho, m, s = p
        return a + b * (rho * (k - m) + math.sqrt((k - m) ** 2 + s * s))

    def surface(fits):
        fits.sort()
        grid = []
        for T in Ts:
            row = []
            for k in ks:
                lo = max((f for f in fits if f[0] <= T), default=None)
                hi = min((f for f in fits if f[0] >= T), default=None)
                if lo is None or hi is None or lo is hi:
                    f = lo or hi                    # flat-vol extrapolation in maturity
                    iv = math.sqrt(max(svi_w(f[1], k), 1e-6) / f[0])
                else:                               # total variance linear in maturity
                    wl, wh = svi_w(lo[1], k), svi_w(hi[1], k)
                    u = (T - lo[0]) / (hi[0] - lo[0])
                    iv = math.sqrt(max(wl + u * (wh - wl), 1e-6) / T)
                row.append(min(max(iv, 0.05), 0.55))
            grid.append(row)
        return grid

    order = sorted(d for d in days if len(days[d]) >= 2)
    groups = []
    for n, d in enumerate(order):
        g = surface(days[d])
        az = 2 * math.pi * n / len(order)          # one slow orbit per loop
        el = 0.55

        def project(i, j):
            x = (ks[i] / 0.15) * 1.0
            y = (j / 9) * 2 - 1
            z = (g[j][i] - 0.05) / 0.5 * 1.6
            x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
            sy = y * math.sin(el) - z * math.cos(el)
            return SIZE / 2 + x * 120, SIZE / 2 + 40 + sy * 120

        lines = [[project(i, j) for i in range(len(ks))] for j in range(len(Ts))]
        lines += [[project(i, j) for j in range(len(Ts))] for i in range(len(ks))]
        groups.append("".join(f'<polyline points="{pts(l)}"/>' for l in lines))
    style = (frame_css(len(groups), duration)
             + "polyline{fill:none;stroke:url(#iv);stroke-width:1.3;stroke-linejoin:round}")
    defs = ('<defs><linearGradient id="iv" gradientUnits="userSpaceOnUse" x1="0" y1="330" x2="0" y2="60">'
            '<stop offset="0" stop-color="#22d3ee"/><stop offset=".45" stop-color="#818cf8"/>'
            '<stop offset=".75" stop-color="#f472b6"/><stop offset="1" stop-color="#fb7185"/></linearGradient>'
            '<filter id="g" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    return tile(defs + f'<g filter="url(#g)">{frames(groups, duration)}</g>', style)


def main():
    os.makedirs(OUT, exist_ok=True)
    svi = sys.argv[1] if len(sys.argv) > 1 else SVI_DEFAULT
    for name, svg in [
        ("blackhole", black_hole()),
        ("volsurface", vol_surface(svi)),
        ("tesseract", tesseract()),
        ("lorenz", lorenz()),
    ]:
        path = os.path.join(OUT, f"{name}.svg")
        with open(path, "w") as f:
            f.write(svg)
        print(f"{name}.svg  {os.path.getsize(path) / 1024:.0f} KB")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Andy Sloane's spinning ASCII donut (donut.c), drawn on a GitHub contribution
graph: every "character" is a calendar cell, every shade is one of the five
contribution levels.

    python tools/donut.py --theme dark|light [--grid N] [--legend]
        -> assets/donut-<theme>.svg

Everything is rendered offline here with numpy and baked into the SVG as SMIL
keyframes (no JavaScript), so GitHub can show it as a plain <img>.

How donut.c maps onto this file
-------------------------------
donut.c sweeps a circle of radius R1 centred at (R2, 0, 0) around the y axis
(angle phi) to build the torus, then spins it with two angles per frame:

    A   rotation about the x axis  (the tumble;  donut.c adds 0.04 per frame)
    B   rotation about the z axis  (the roll;    donut.c adds 0.02 per frame)

The viewer sits at the origin looking down +z, the donut is pushed K2 away,
and screen = K1 * (x, y) / z  ("ooz" = one over z in the C code). Luminance
is the dot product of the surface normal with a light direction; donut.c picks
one of ".,-~:;=!*#$@" by it. Here the 12 characters become the 4 non-empty
contribution levels.

donut.c projects points from the surface forward into a z-buffer. We go the
other way: shoot rays from the eye through each cell (several per cell for
supersampling) and ray-march the torus signed distance function. That gives
exact coverage per cell, so the outline has no holes or speckle.

Loop: a torus is symmetric under any 180 degree rotation about an axis in its
equatorial plane (the xz plane here, since the hole runs along y). After a
full turn of A the donut is back where it started, and the z axis lies in
that plane, so a further half turn of B maps it onto itself too. One loop is
therefore A = 360, B = 180: exactly donut.c's 2:1 speed ratio, and only half
the data a full B turn would need.
"""

import argparse
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Tunables
# --------------------------------------------------------------------------
GRID = 31                  # cells per side; 31 * 10 + 30 * 3 = 400 px exactly
CELL = 10                  # GitHub calendar cell, px
GAP = 3                    # gap between cells, px
RADIUS = 2                 # cell corner radius, px
MARGIN_CELLS = 1.5         # empty cells kept around the donut at its widest
DISPLAY_WIDTH = 400        # width attribute, px (same as the tesseract)

R1 = 1.0                   # donut.c: tube radius
R2 = 2.0                   # donut.c: distance from the torus centre to the tube centre
K2 = 5.0                   # donut.c: distance from the eye to the donut
# K1 (donut.c's screen scale) is derived from GRID so the donut always fits.

FPS = 15                   # discrete steps per second
STEPS = 240                # steps per loop -> 16 s loop
A_TURN_DEG = 360           # per loop; with B_TURN_DEG = 180 the loop is seamless
B_TURN_DEG = 180

SUPERSAMPLE = 4            # 4 x 4 rays per cell
MARCH_STEPS = 64           # sphere-tracing iterations per ray
HIT_EPS = 1e-3

LIGHT = (-1.0, 1.0, -1.0)  # from the upper left and the front (the eye looks down +z)
SPECULAR = 0.35            # strength of a Blinn highlight on top of Lambert
SHININESS = 24

COVERAGE = 0.5             # a cell is "donut" at >= 50 % of its rays hitting
COVER_BAND = 0.07          # coverage hysteresis: on above 0.57, off below 0.43
LEVEL_BAND = 0.04          # luminance hysteresis around each quartile threshold

STATIC_STEP = 0            # frame shown under prefers-reduced-motion

THEMES = {
    # @primer/primitives 11.10: contribution-default-bgColor-0..4,
    # and fgColor-muted for the optional legend text.
    "dark": {"levels": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
             "muted": "#9198a1"},
    "light": {"levels": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
              "muted": "#59636e"},
}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


# --------------------------------------------------------------------------
# Rotations
# --------------------------------------------------------------------------
def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(b):
    c, s = np.cos(b), np.sin(b)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def pose(step):
    """Object -> view rotation for a step. donut.c applies A (about x) and
    then B (about z), so view = Rz(B) @ Rx(A) @ object."""
    t = step / STEPS
    return rot_z(np.radians(B_TURN_DEG) * t) @ rot_x(np.radians(A_TURN_DEG) * t)


# --------------------------------------------------------------------------
# Torus
# --------------------------------------------------------------------------
def torus_sdf(p):
    """Signed distance to the torus whose hole runs along y (donut.c's phi
    sweeps around y). q is the point's position relative to the tube's centre
    circle; the distance to the surface is |q| - R1."""
    ring = np.hypot(p[..., 0], p[..., 2]) - R2
    return np.hypot(ring, p[..., 1]) - R1


def torus_normal(p):
    """Exact normal: from the nearest point on the centre circle to p."""
    xz = np.hypot(p[..., 0], p[..., 2])[..., None]
    centre = R2 * p * np.array([1, 0, 1]) / xz
    return (p - centre) / R1


def k1_for_grid():
    """donut.c's K1 (screen scale), chosen so the donut never clips.
    Projects a dense sample of the surface at every pose and keeps the
    widest extent. Returned in 'cells per unit of x/z'."""
    th, ph = np.meshgrid(np.linspace(0, 2 * np.pi, 96), np.linspace(0, 2 * np.pi, 192))
    # donut.c: circle (R2 + R1 cos theta, R1 sin theta), swept about y by phi
    cx = R2 + R1 * np.cos(th)
    pts = np.stack([cx * np.cos(ph), R1 * np.sin(th), cx * np.sin(ph)], -1).reshape(-1, 3)
    widest = 0.0
    for s in range(STEPS):
        v = pts @ pose(s).T
        ooz = 1 / (v[:, 2] + K2)                   # donut.c's "ooz"
        widest = max(widest, np.abs(v[:, :2] * ooz[:, None]).max())
    return (GRID / 2 - MARGIN_CELLS) / widest


# --------------------------------------------------------------------------
# Rendering: per-cell coverage and luminance for every step
# --------------------------------------------------------------------------
def render():
    k1 = k1_for_grid()

    # Ray directions through SUPERSAMPLE^2 stratified points in every cell.
    # Screen coordinates are in cells, with y pointing up like donut.c.
    sub = (np.arange(SUPERSAMPLE) + 0.5) / SUPERSAMPLE - 0.5
    idx = np.arange(GRID) - (GRID - 1) / 2
    sx = (idx[None, :, None, None] + sub[None, None, None, :])          # col, subcol
    sy = (-idx[:, None, None, None] - sub[None, None, :, None])         # row, subrow
    sx, sy = np.broadcast_arrays(sx, sy)                                # (G,G,S,S)
    dirs = np.stack([sx / k1, sy / k1, np.ones_like(sx)], -1)
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
    dirs = dirs.reshape(-1, 3)                                          # (G*G*S*S, 3)

    light = np.array(LIGHT) / np.linalg.norm(LIGHT)
    centre = np.array([0, 0, K2])
    bound = R1 + R2 + 0.05

    cover = np.empty((STEPS, GRID, GRID))
    lum = np.empty((STEPS, GRID, GRID))
    for s in range(STEPS):
        r = pose(s)
        # March in object space: rotate the rays instead of the donut.
        # (Inverse of a rotation is its transpose.)
        o = r.T @ -centre
        d = dirs @ r                                   # == (r.T @ dirs.T).T

        # Start each ray where it enters the bounding sphere (radius 3).
        b = d @ o
        disc = b * b - (o @ o - bound ** 2)
        t = np.where(disc > 0, -b - np.sqrt(np.maximum(disc, 0)), np.inf)
        for _ in range(MARCH_STEPS):                    # sphere tracing
            dist = torus_sdf(o + t[:, None] * d)
            t = t + np.where(np.isfinite(t), dist, 0)
        p = o + np.where(np.isfinite(t), t, 0)[:, None] * d
        hit = np.isfinite(t) & (np.abs(torus_sdf(p)) < HIT_EPS)

        # Lighting in view space. Signed Lambert like donut.c's L (it keeps
        # the sign and only clamps when picking a character), plus a small
        # Blinn highlight so level 4 reads as a shine.
        n = torus_normal(p) @ r.T
        view = -(dirs)                                  # towards the eye
        half = light + view
        half /= np.linalg.norm(half, axis=1, keepdims=True)
        shade = n @ light + SPECULAR * np.maximum((n * half).sum(1), 0) ** SHININESS

        hit = hit.reshape(GRID, GRID, -1)
        shade = shade.reshape(GRID, GRID, -1)
        cover[s] = hit.mean(-1)
        lum[s] = np.where(hit, shade, 0).sum(-1) / np.maximum(hit.sum(-1), 1)
    return cover, lum


# --------------------------------------------------------------------------
# Luminance -> contribution levels, with hysteresis
# --------------------------------------------------------------------------
def quantize(cover, lum):
    """Level 0 = empty, 1..4 by luminance quartiles over every covered cell
    of every frame (like GitHub bucketing contribution counts).

    Hysteresis: a cell only changes level once its value is LEVEL_BAND past
    the threshold it has to cross, so it can't toggle for one frame on noise.
    The state carries over from step to step, so we run the loop twice and
    keep the second pass: the state entering it is the state it ends with,
    and the seam matches. A third pass checks that the state has settled."""
    covered = cover >= COVERAGE
    thr = np.quantile(lum[covered], [0.25, 0.5, 0.75])
    lo = np.concatenate([[-np.inf], thr])               # lower edge of level 1..4
    hi = np.concatenate([thr, [np.inf]])                # upper edge of level 1..4

    state = np.zeros((GRID, GRID), dtype=int)
    passes = []
    for _ in range(3):
        out = np.empty((STEPS, GRID, GRID), dtype=int)
        for s in range(STEPS):
            c, l = cover[s], lum[s]
            on = np.where(state > 0, c >= COVERAGE - COVER_BAND, c >= COVERAGE + COVER_BAND)
            raw = 1 + np.searchsorted(thr, l, side="right")
            p = np.clip(state, 1, 4) - 1
            keep = (state > 0) & (l >= lo[p] - LEVEL_BAND) & (l < hi[p] + LEVEL_BAND)
            state = np.where(on, np.where(keep, state, raw), 0)
            out[s] = state
        passes.append(out)
    assert np.array_equal(passes[1], passes[2]), "hysteresis did not settle in one loop"
    levels = passes[1]

    # Last resort against flicker: a cell that leaves a level for a single
    # step and comes straight back (A, B, A) stays at A. Steps through
    # levels (1, 2, 3) are real motion and are kept. np.roll wraps around,
    # so this treats the loop as a circle and can't create a seam.
    prev, nxt = np.roll(levels, 1, 0), np.roll(levels, -1, 0)
    return np.where((prev == nxt) & (levels != prev), prev, levels)


# --------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------
def cells_path(cells, color):
    """Many cells as one <path>. Each cell is a 6x6 square traced with a
    4 px round-join stroke, which paints exactly a 10x10 square with 2 px
    rounded corners. Relative moves keep it short ('z' returns to the
    sub-path start, so the next 'm' is relative to that)."""
    pitch = CELL + GAP
    inner = CELL - 2 * RADIUS
    d, prev = [], None
    for r, c in cells:
        x, y = c * pitch + RADIUS, r * pitch + RADIUS
        d.append(f"M{x} {y}" if prev is None else f"m{x - prev[0]} {y - prev[1]}")
        d.append(f"h{inner}v{inner}h-{inner}z")
        prev = (x, y)
    return (f'<path fill="{color}" stroke="{color}" stroke-width="{2 * RADIUS}" '
            f'stroke-linejoin="round" d="{"".join(d)}"/>')


def key_time(s):
    return f"{s / STEPS:.3f}".rstrip("0").rstrip(".") or "0"


def build_svg(theme, legend):
    pal = THEMES[theme]["levels"]
    levels = quantize(*render())
    pitch = CELL + GAP
    size = GRID * pitch - GAP
    height = size + (30 if legend else 0)
    dur = f"{STEPS / FPS:g}s"

    changes = (levels != np.roll(levels, 1, axis=0)).any(0)    # cyclic, per cell
    animated = list(zip(*np.nonzero(changes)))
    static = list(zip(*np.nonzero(~changes)))

    # Always 400 px wide on the page; a denser --grid just scales down.
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{DISPLAY_WIDTH}" '
           f'height="{DISPLAY_WIDTH * height / size:.4g}" viewBox="0 0 {size} {height}">',
           '<style>@media (prefers-reduced-motion:reduce){#a{display:none}#s{display:inline}}</style>']

    # Cells that never change: one path per level (almost all level 0).
    for lv in range(5):
        cells = [rc for rc in static if levels[0][rc] == lv]
        if cells:
            out.append(cells_path(cells, pal[lv]))

    # Cells that change: one rect each, one discrete fill animation with a
    # keyframe only where the level changes (run-length encoding).
    out.append(f'<g id="a">')
    for r, c in animated:
        seq = levels[:, r, c]
        steps = [0] + [s for s in range(1, STEPS) if seq[s] != seq[s - 1]]
        out.append(
            f'<rect x="{c * pitch}" y="{r * pitch}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{pal[seq[0]]}"><animate attributeName="fill" '
            f'calcMode="discrete" dur="{dur}" repeatCount="indefinite" '
            f'keyTimes="{";".join(key_time(s) for s in steps)}" '
            f'values="{";".join(pal[seq[s]] for s in steps)}"/></rect>')
    out.append("</g>")

    # Reduced motion: the animated cells frozen at STATIC_STEP, hidden unless
    # the media query above shows it.
    out.append('<g id="s" display="none">')
    for lv in range(5):
        cells = [rc for rc in animated if levels[STATIC_STEP][rc] == lv]
        if cells:
            out.append(cells_path(cells, pal[lv]))
    out.append("</g>")

    if legend:
        # GitHub's "Less [] [] [] [] [] More", right-aligned under the grid.
        y = size + 12
        x = size - 36 - (5 * pitch - GAP)        # leave ~36 px for "More"
        text = f'font-family="{FONT}" font-size="12" fill="{THEMES[theme]["muted"]}"'
        out.append(f'<text x="{x - 5}" y="{y + 9}" text-anchor="end" {text}>Less</text>')
        for i in range(5):
            out.append(f'<rect x="{x + i * pitch}" y="{y}" width="{CELL}" height="{CELL}" '
                       f'rx="{RADIUS}" fill="{pal[i]}"/>')
        out.append(f'<text x="{size}" y="{y + 9}" text-anchor="end" {text}>More</text>')

    out.append("</svg>")
    return "\n".join(o for o in out if o) + "\n", len(animated)


def main():
    global GRID
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--theme", choices=THEMES, required=True)
    ap.add_argument("--grid", type=int, default=GRID, help="cells per side (default 31)")
    ap.add_argument("--legend", action="store_true", help='add a "Less ... More" legend')
    ap.add_argument("--out", type=Path, help="default: assets/donut-<theme>.svg")
    args = ap.parse_args()
    GRID = args.grid

    svg, n_anim = build_svg(args.theme, args.legend)
    out = args.out or Path(__file__).resolve().parent.parent / "assets" / f"donut-{args.theme}.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB, {n_anim} animated cells)")


if __name__ == "__main__":
    main()

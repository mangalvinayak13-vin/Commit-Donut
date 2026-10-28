"""Render the classic donut.c spinning torus as an animated SVG (donut.svg).

The SVG holds one <text> block per frame and CSS shows them in turn,
so it animates inside a GitHub README with no JavaScript.
"""
import math

W, H = 60, 26          # characters per row, rows
FRAMES = 90            # one full turn of the slower axis
DURATION = 4.5         # seconds per loop
CHARS = ".,-~:;=!*#$@"
CHAR_W, LINE_H = 7.2, 12


def frame(A, B):
    out = [" "] * (W * H)
    zbuf = [0.0] * (W * H)
    cA, sA, cB, sB = math.cos(A), math.sin(A), math.cos(B), math.sin(B)
    for j in range(0, 628, 7):            # theta around the tube cross-section
        ct, st = math.cos(j / 100), math.sin(j / 100)
        for i in range(0, 628, 2):        # phi around the donut's centre
            cp, sp = math.cos(i / 100), math.sin(i / 100)
            h = ct + 2
            D = 1 / (sp * h * sA + st * cA + 5)
            t = sp * h * cA - st * sA
            x = int(W / 2 + 30 * D * (cp * h * cB - t * sB))
            y = int(H / 2 + 15 * D * (cp * h * sB + t * cB))
            N = int(8 * ((st * sA - sp * ct * cA) * cB - sp * ct * sA - st * cA - cp * ct * sB))
            o = x + W * y
            if 0 <= y < H and 0 <= x < W and D > zbuf[o]:
                zbuf[o] = D
                out[o] = CHARS[max(N, 0)]
    return ["".join(out[r * W:(r + 1) * W]).rstrip() for r in range(H)]


def main():
    dt = DURATION / FRAMES
    pct = 100 / FRAMES
    width, height = W * CHAR_W, H * LINE_H + 6
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">',
        "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#ff8a3d'/><stop offset='1' stop-color='#ff3d9a'/>"
        "</linearGradient></defs>",
        "<style>",
        "text{font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
        "white-space:pre;fill:url(#g);visibility:hidden;"
        f"animation:f {DURATION}s step-end infinite}}",
        f"@keyframes f{{0%{{visibility:visible}}{pct:.4f}%{{visibility:hidden}}}}",
        "</style>",
    ]
    for k in range(FRAMES):
        # A turns twice per loop and B once, so the loop is seamless
        lines = frame(A=4 * math.pi * k / FRAMES, B=2 * math.pi * k / FRAMES)
        spans = "".join(
            f'<tspan x="0" y="{(r + 1) * LINE_H}">{line}</tspan>' for r, line in enumerate(lines) if line
        )
        parts.append(f'<text xml:space="preserve" style="animation-delay:{k * dt:.3f}s">{spans}</text>')
    parts.append("</svg>")
    with open("donut.svg", "w") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    main()

"""Builds every KRATOS logo file from one geometry.

    python3 -I brand/make_logo.py            # SVGs, the site icons and the animated logo in index.html
    python3 -I brand/make_logo.py --png      # also PNGs (needs google-chrome for rendering)

The mark: an astronaut helmet split down the middle, solid on the left (human) and outlined on the
right (machine). A red heartbeat line runs between the halves, edge to edge, with the pulse in the
visor. A flat ring circles the helmet; the helmet is opaque, visor included, so the back of the ring
never shows through it. A star sits top right. The wordmark is KRATOS with a red delta in the A.

Every knockout (the gap around the ring, the helmet's backing) is drawn in the ground colour, so each
file is made for one ground: dark (#070A17, the website), navy (#0B1026) or light (#F3F4F8).
"""
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

RED = "#EE1C2E"
GROUNDS = {  # name: (ink, ground)
    "dark": ("#EEF1FA", "#070A17"),
    "navy": ("#EEF1FA", "#0B1026"),
    "light": ("#0B1026", "#F3F4F8"),
}

# Mark geometry, in a 100 x 100 box
CX, CY, R = 50, 50, 27                 # helmet
SW = 3.6                               # stroke of the outline, the visor and the red line
VW, VH = 1.1 * R, 0.72 * R             # visor window (inner edge)
VRX = VH * 0.46
RING_CY, RING_RX, RING_RY, RING_SW, RING_TILT = CY + 0.19 * R, 1.6 * R, 0.34 * R, 2.8, -14
STAR = (87, 16, 6.5)                   # centre x, centre y, arm length
# Heartbeat in the visor: (dx, dy) from where it leaves the straight line, 15 units tall
PULSE_Y0, PULSE_K = 41.5, 15 / 21
PULSE = [(0, 0), (-2.5, 3), (0, 5.5), (8.5, 10), (-7, 17.5), (0, 21)]
MARK_BOX = (6.6, 9.5, 93.5, 77.0)      # x0, y0, x1, y1 of everything drawn, strokes included

# Wordmark, 284 x 40 units, stroke 7
LETTERS = [
    (0, 34, "M0 0 V40 M34 0 L12 20 L34 40"),
    (46, 34, "M0 40 V0 H24 A10 10 0 0 1 24 20 H0 M16 20 L34 40"),
    (92, 38, "M0 40 L19 0 L38 40"),
    (142, 36, "M0 0 H36 M18 0 V40"),
    (190, 46, "M14 0 H32 A14 14 0 0 1 46 14 V26 A14 14 0 0 1 32 40 H14 A14 14 0 0 1 0 26 V14 A14 14 0 0 1 14 0 Z"),
    (248, 36, "M36 0 H10 A10 10 0 0 0 10 20 H26 A10 10 0 0 1 26 40 H0"),
]
WM_W, WM_H, WM_SW = 284, 40, 7

T = 3.2  # animation length in seconds; the motion ends at 2.6 s
EASE = "cubic-bezier(.45,0,.2,1)"


def pts(p):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in p)


def seam_points():
    top, bot = CY - R + SW / 2, CY + R - SW / 2
    pulse = [(CX + dx * PULSE_K, PULSE_Y0 + dy * PULSE_K) for dx, dy in PULSE]
    return [(CX, top)] + pulse + [(CX, bot)]


def seam_halves(seam):
    """The animation draws the line outward from where the pulse crosses the centre line."""
    for k in range(len(seam) - 1):
        (x1, y1), (x2, y2) = seam[k], seam[k + 1]
        if (x1 - CX) * (x2 - CX) < 0:
            t = (x1 - CX) / (x1 - x2)
            X = (CX, y1 + t * (y2 - y1))
            return [X] + seam[:k + 1][::-1], [X] + seam[k + 1:]
    raise ValueError("pulse never crosses the centre line")


def helmet_with_visor_hole():
    x0, y0 = CX - VW / 2, CY - VH / 2
    r = VRX
    disc = f"M{CX - R} {CY} A{R} {R} 0 1 0 {CX + R} {CY} A{R} {R} 0 1 0 {CX - R} {CY} Z"
    hole = (f"M{x0 + r:.2f} {y0:.2f} H{x0 + VW - r:.2f} A{r:.2f} {r:.2f} 0 0 1 {x0 + VW:.2f} {y0 + r:.2f} "
            f"V{y0 + VH - r:.2f} A{r:.2f} {r:.2f} 0 0 1 {x0 + VW - r:.2f} {y0 + VH:.2f} H{x0 + r:.2f} "
            f"A{r:.2f} {r:.2f} 0 0 1 {x0:.2f} {y0 + VH - r:.2f} V{y0 + r:.2f} A{r:.2f} {r:.2f} 0 0 1 {x0 + r:.2f} {y0:.2f} Z")
    return disc + " " + hole


def mark(ink, ground, uid, anim=False, ring=True, star=True, sw=SW):
    """The mark in its 100 x 100 box. anim=True adds the classes and the plus the animation needs."""
    c = (lambda n: f' class="{n}"') if anim else (lambda n: "")
    pl = ' pathLength="1"' if anim else ""
    o = sw / 2
    seam = seam_points()
    left = [(-5, -5), (CX, -5)] + seam + [(CX, 105), (-5, 105)]
    right = [(105, -5), (CX, -5)] + seam + [(CX, 105), (105, 105)]
    p = [f'<defs><clipPath id="L{uid}"><polygon points="{pts(left)}"/></clipPath>'
         f'<clipPath id="R{uid}"><polygon points="{pts(right)}"/></clipPath></defs>']
    rx, ry = RING_RX, RING_RY
    tr = f'translate({CX} {RING_CY:.2f}) rotate({RING_TILT})'
    if ring:
        p.append(f'<g transform="{tr}"><path{c("ringback")}{pl} d="M{rx:.2f} 0 A{rx:.2f} {ry:.2f} 0 0 1 {-rx:.2f} 0 '
                 f'A{rx:.2f} {ry:.2f} 0 0 1 {rx:.2f} 0" fill="none" stroke="{ink}" stroke-width="{RING_SW}"/></g>')
    vx0, vy0 = CX - VW / 2, CY - VH / 2
    head = [
        f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="{ground}"/>',  # opaque backing: hides the ring's back
        f'<path clip-path="url(#L{uid})" fill-rule="evenodd" fill="{ink}" d="{helmet_with_visor_hole()}"/>',
        f'<g clip-path="url(#R{uid})" fill="none" stroke="{ink}" stroke-width="{sw}">'
        f'<circle cx="{CX}" cy="{CY}" r="{R - o:.2f}"/>'
        f'<rect x="{vx0 - o:.2f}" y="{vy0 - o:.2f}" width="{VW + sw:.2f}" height="{VH + sw:.2f}" rx="{VRX + o:.2f}"/></g>',
    ]
    if anim:  # the white health plus that folds into the red line
        b = 0.486 * R
        head.append(f'<rect class="hbar" x="{CX - b / 2:.2f}" y="{CY - o:.2f}" width="{b:.2f}" height="{sw}" fill="{ink}"/>')
        for n, col in (("vbar-ink", ink), ("vbar-red", RED)):
            head.append(f'<rect class="{n}" x="{CX - o:.2f}" y="{CY - b / 2:.2f}" width="{sw}" height="{b:.2f}" fill="{col}"/>')
    p.append(f'<g{c("head")}>{"".join(head)}</g>')
    st = f'fill="none" stroke="{RED}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    if anim:
        for n, half in zip(("up", "down"), seam_halves(seam)):
            d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in half)
            p.append(f'<path class="seam {n}" pathLength="1" d="{d}" {st}/>')
    else:
        p.append(f'<polyline points="{pts(seam)}" {st}/>')
    if ring:  # front half passes in front of the helmet, with a gap in the ground colour
        d = f"M{rx:.2f} 0 A{rx:.2f} {ry:.2f} 0 0 1 {-rx:.2f} 0"
        p.append(f'<g transform="{tr}"><path{c("ringfront")}{pl} d="{d}" fill="none" stroke="{ground}" stroke-width="{RING_SW + 4.4:.1f}"/>'
                 f'<path{c("ringfront")}{pl} d="{d}" fill="none" stroke="{ink}" stroke-width="{RING_SW}" stroke-linecap="round"/></g>')
    if star:
        sx, sy, a = STAR
        p.append(f'<path{c("pop star")} d="M{sx} {sy - a} Q{sx} {sy} {sx + a} {sy} Q{sx} {sy} {sx} {sy + a} '
                 f'Q{sx} {sy} {sx - a} {sy} Q{sx} {sy} {sx} {sy - a}Z" fill="{ink}"/>')
    return "".join(p)


def wordmark(ink, x, y, k, anim=False):
    out = []
    for i, (dx, _, d) in enumerate(LETTERS):
        letter = f'<g transform="translate({dx} 0)"><path d="{d}"/></g>'
        out.append(f'<g class="wm{i}">{letter}</g>' if anim else letter)
    tri_cls = ' class="pop tri"' if anim else ""
    tri = (f'<g transform="translate(92 0)"><path{tri_cls} d="M19 20 L28.5 40 L9.5 40 Z" fill="{RED}" '
           f'stroke="{RED}" stroke-width="2" stroke-linejoin="round"/></g>')
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})" fill="none" stroke="{ink}" '
            f'stroke-width="{WM_SW}" stroke-linecap="round" stroke-linejoin="round">{"".join(out)}{tri}</g>')


def svg(view, body, cls=""):
    x, y, w, h = view
    c = f' class="{cls}"' if cls else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="KRATOS"{c} '
            f'viewBox="{x:g} {y:g} {w:g} {h:g}">{body}</svg>\n')


def bg(view, ground, rx=0):
    x, y, w, h = view
    r = f' rx="{rx:g}"' if rx else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"{r} fill="{ground}"/>'


# Layouts. Margins are 5 units around everything drawn.
X0, Y0, X1, Y1 = MARK_BOX
MARK_VIEW = (X0 - 5, Y0 - 5, X1 - X0 + 10, Y1 - Y0 + 10)
STACK_K = 72 / WM_W                          # wordmark 72 wide under the 54-wide helmet
STACK_WM_Y = 87
STACK_VIEW = (0, 2, 100, 104)
HORIZ_K = 0.64                               # letters 25.6 tall next to the 54-tall helmet
HORIZ_WM_X = 112
HORIZ_VIEW = (X0 - 5, Y0 - 5, HORIZ_WM_X + WM_W * HORIZ_K + WM_SW * HORIZ_K / 2 + 5 - (X0 - 5), Y1 - Y0 + 10)
ICON_VIEW = (-6, 43.25 - 56, 112, 112)       # square, centred on everything drawn
FAV_SW = 4.4                                 # thicker strokes so the favicon holds at 16 px
FAV_SIDE = 2 * R / 0.84                      # helmet fills 84 % of the favicon
FAV_VIEW = (CX - FAV_SIDE / 2, CY - FAV_SIDE / 2, FAV_SIDE, FAV_SIDE)


def mark_svg(g):
    ink, ground = GROUNDS[g]
    return svg(MARK_VIEW, mark(ink, ground, f"m{g}"))


def stacked_svg(g, anim=False):
    ink, ground = GROUNDS[g]
    body = mark(ink, ground, f"s{g}{'a' if anim else ''}", anim) + wordmark(ink, 14, STACK_WM_Y, STACK_K, anim)
    if anim:
        return svg(STACK_VIEW, f'<style>{anim_css()}</style><g class="all">{body}</g>', cls="k5")
    return svg(STACK_VIEW, body)


def horizontal_svg(g):
    ink, ground = GROUNDS[g]
    y = CY - WM_H * HORIZ_K / 2
    return svg(HORIZ_VIEW, mark(ink, ground, f"h{g}") + wordmark(ink, HORIZ_WM_X, y, HORIZ_K))


def icon_svg():
    """Full mark on a square of the website ground: GitHub avatar, app icon."""
    ink, ground = GROUNDS["dark"]
    return svg(ICON_VIEW, bg(ICON_VIEW, ground) + mark(ink, ground, "icon"))


def favicon_svg():
    """Helmet and red line only (ring and star vanish at 16 px), on a rounded square."""
    ink, ground = GROUNDS["dark"]
    return svg(FAV_VIEW, bg(FAV_VIEW, ground, rx=FAV_SIDE * 0.22) + mark(ink, ground, "fav", ring=False, star=False, sw=FAV_SW))


def kf(name, steps, ease=EASE, total=T):
    if steps[0][0] > 0:
        steps = [(0, steps[0][1])] + steps
    if steps[-1][0] < total:
        steps = steps + [(total, steps[-1][1])]
    return f"@keyframes k5-{name}{{" + "".join(
        f"{t / total * 100:.3f}%{{{p};animation-timing-function:{ease}}}" for t, p in steps) + "}"


def anim_css(s=".k5", loop=None):
    """The intro: the helmet with a white plus shrinks into place (0-0.75 s), the plus folds into a red
    bar (0.55-0.9 s), the red line beats out to the helmet's edges (0.9-1.35 s), the ring draws around
    the helmet (1.35-2.25 s), the delta appears (1.4 s), the letters grow outward from the A (1.5-2.25 s)
    and the star lands (2.1-2.6 s). It plays once; reduced motion shows the final frame.
    loop=seconds instead repeats it with that period, fading out at the end (for pages that study it)."""
    rules, frames = [], []
    total = loop or T
    repeat = "infinite" if loop else "1 both"

    def on(sel, name, steps, ease=EASE, extra=""):
        rules.append(f"{s} {sel}{{{extra}animation:k5-{name} {total}s {repeat}}}")
        frames.append(kf(name, steps, ease, total))

    pop = "transform-box:fill-box;transform-origin:center;"
    hid, drawn, done = ("stroke-dasharray:1 2;stroke-dashoffset:1", "stroke-dasharray:1 2;stroke-dashoffset:0",
                        "stroke-dasharray:none;stroke-dashoffset:0;opacity:1")

    def draw(t0, t1):
        return [(0, hid + ";opacity:0"), (t0, hid + ";opacity:0"), (t0 + 0.005, hid + ";opacity:1"),
                (t1, drawn + ";opacity:1"), (t1 + 0.005, done)]

    fade_out = [(loop - 0.6, "opacity:1"), (loop - 0.1, "opacity:0")] if loop else []
    on(".all", "all", [(0, "opacity:0"), (0.35, "opacity:1")] + fade_out)
    on(".head", "head", [(0, "transform:translate(0px,3px) scale(1.4)"), (0.75, "transform:translate(0px,0px) scale(1)")], extra=pop)
    on(".hbar", "hbar", [(0, "transform:scaleX(1);opacity:1"), (0.55, "transform:scaleX(1);opacity:1"),
                         (0.85, "transform:scaleX(0);opacity:1"), (0.86, "transform:scaleX(0);opacity:0")], extra=pop)
    on(".vbar-ink", "vink", [(0, "opacity:1"), (0.7, "opacity:1"), (0.9, "opacity:0")])
    on(".vbar-red", "vred", [(0, "opacity:0"), (0.7, "opacity:0"), (0.9, "opacity:1"), (1.0, "opacity:0")])
    on(".seam", "seam", draw(0.9, 1.35), ease="cubic-bezier(.3,0,.25,1)")
    on(".ringback", "ringback", draw(1.35, 2.25), ease="linear")
    on(".ringfront", "ringfront", draw(1.35, 1.8), ease="linear")
    on(".tri", "tri", [(0, "opacity:0;transform:scale(.5)"), (1.4, "opacity:0;transform:scale(.5)"),
                       (1.6, "opacity:1;transform:scale(1)")], extra=pop)
    a_mid = LETTERS[2][0] + LETTERS[2][1] / 2
    rank = [2, 1, 0, 1, 2, 3]  # letters grow outward from the A
    for i, (dx, w, _) in enumerate(LETTERS):
        sh = (a_mid - (dx + w / 2)) * 0.4
        t0 = 1.5 + 0.1 * rank[i]
        start = f"opacity:0;transform:translate({sh:.1f}px,0px)"
        on(f".wm{i}", f"wm{i}", [(0, start), (t0, start), (t0 + 0.45, "opacity:1;transform:translate(0px,0px)")])
    on(".star", "star", [(0, "transform:scale(0) rotate(-90deg)"), (2.1, "transform:scale(0) rotate(-90deg)"),
                         (2.45, "transform:scale(1.2) rotate(0deg)"), (2.6, "transform:scale(1) rotate(0deg)")], extra=pop)
    base = f"{s} .hbar,{s} .vbar-ink,{s} .vbar-red{{opacity:0}}"
    reduce = f"@media (prefers-reduced-motion:reduce){{{s} *{{animation:none!important}}}}"
    return base + "".join(rules) + "".join(frames) + reduce


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def update_site(animated):
    """Put the animated logo into index.html, replacing whatever SVG sits in <div class="logo">."""
    path = os.path.join(SITE, "index.html")
    html = open(path).read()
    new, n = re.subn(r'(<div class="logo">\s*)<svg.*?</svg>', lambda m: m.group(1) + animated.strip(), html, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f"{path}: expected one <div class=\"logo\"> holding an <svg>, found {n}")
    write(path, new)


def render_png(svg_path, png_path, width, height):
    """Render with headless Chrome on a transparent background (the SVG brings its own ground if any)."""
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("--png needs google-chrome or chromium on PATH")
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "page.html")
        body = open(svg_path).read().replace("<svg ", f'<svg width="{width}" height="{height}" ', 1)
        write(page, f'<html><body style="margin:0;background:transparent">{body}</body></html>')
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                        "--default-background-color=00000000", f"--screenshot={png_path}",
                        f"--window-size={width},{height}", "file://" + page],
                       check=True, capture_output=True, timeout=60)


def main():
    png = "--png" in sys.argv[1:]
    files = {}  # svg path -> png width (0 = no png)
    for g in GROUNDS:
        files[write_svg(f"svg/kratos-mark-on-{g}.svg", mark_svg(g))] = 1024
        files[write_svg(f"svg/kratos-lockup-stacked-on-{g}.svg", stacked_svg(g))] = 1024
        files[write_svg(f"svg/kratos-lockup-horizontal-on-{g}.svg", horizontal_svg(g))] = 2048
    files[write_svg("svg/kratos-icon.svg", icon_svg())] = 1024
    animated = stacked_svg("dark", anim=True)
    write_svg("svg/kratos-lockup-animated-on-dark.svg", animated)
    write(os.path.join(SITE, "assets/favicon.svg"), favicon_svg())
    update_site(animated)
    if not png:
        return
    for path, width in files.items():
        x, y, w, h = view_of(path)
        render_png(path, path.replace("/svg/", "/png/").replace(".svg", ".png"), width, round(width * h / w))
    render_png(os.path.join(HERE, "svg/kratos-icon.svg"), os.path.join(SITE, "assets/apple-touch-icon.png"), 180, 180)
    render_png(os.path.join(SITE, "assets/favicon.svg"), os.path.join(SITE, "assets/favicon.png"), 64, 64)


def write_svg(rel, text):
    path = os.path.join(HERE, rel)
    write(path, text)
    return path


def view_of(path):
    m = re.search(r'viewBox="([^"]+)"', open(path).read())
    return [float(v) for v in m.group(1).split()]


if __name__ == "__main__":
    main()

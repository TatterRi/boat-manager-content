"""Generate generic plan-view boat outlines for the Boat Map feature.

Writes, for each boat type:
  <id>-outline.svg  hull, deck edge and fixed structure only
  <id>-zones.svg    the same plus typical compartment divisions
and boat-outlines.json, the manifest the app reads (zones, normalised coords).

Run:  python3 generate.py            (writes next to this file)

Conventions (all types):
  - Plan view, bow to the right, port at the top, starboard at the bottom.
  - viewBox width 1000; height follows the type's beam-to-length ratio.
  - One colour (#000), no fill, no text: shipped as template images,
    labels drawn by the app so they localise and follow Dynamic Type.
  - Zone coordinates in the manifest are 0..1 of the viewBox (x right, y down),
    so a pin stored as (x, y) survives any render size.
"""
import json, math, os, re

W, M = 1000.0, 20.0
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------- geometry helpers ----------

def pchip(xs, ys):
    """Monotone cubic (Fritsch-Carlson) interpolant: smooth, no overshoot."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        x = min(max(x, xs[0]), xs[-1])
        i = max(0, min(n - 2, next(k for k in range(n - 1) if x <= xs[k + 1])))
        t = (x - xs[i]) / h[i]
        h00, h10 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t
        h01, h11 = -2 * t**3 + 3 * t**2, t**3 - t**2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def samples(a, b, n=120):
    # denser toward the bow (b end) where curvature is highest
    return [a + (b - a) * math.sin(0.5 * math.pi * k / n) for k in range(n + 1)]


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(points):
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)


class Frame:
    """Maps hull coords to SVG coords. u: 0 transom .. 1 bow. w: -1 port .. +1 stbd (of max beam)."""

    def __init__(self, ratio, stern_ext=0.0):
        self.B = (W - 2 * M) * ratio          # beam in SVG units
        self.H = self.B + 2 * M
        self.x0 = M + stern_ext               # transom x
        self.L = W - M - self.x0
        self.cy = self.H / 2

    def x(self, u): return self.x0 + u * self.L
    def y(self, w): return self.cy + w * self.B / 2
    def p(self, u, w): return (self.x(u), self.y(w))


class Hull:
    """A symmetric hull (or demihull) about centre line wc, half-breadth hb(u) in w units."""

    def __init__(self, frame, profile, half=1.0, wc=0.0):
        us, fs = zip(*profile)
        self.f, self.fr, self.half, self.wc = pchip(list(us), list(fs)), frame, half, wc

    def hb(self, u, inset=1.0):
        return max(0.0, self.f(u)) * self.half * inset

    def outline(self, inset=1.0, u0=0.0, u1=1.0):
        us = samples(u0, u1)
        top = [self.fr.p(u, self.wc - self.hb(u, inset)) for u in us]
        bot = [self.fr.p(u, self.wc + self.hb(u, inset)) for u in reversed(us)]
        return top + bot

    def clip_rect(self, u0, u1, w0, w1, n=16):
        """Rectangle (u0..u1, w0..w1) intersected with this hull, as a polygon."""
        us = [u0 + (u1 - u0) * k / n for k in range(n + 1)]
        top, bot = [], []
        for u in us:
            lo = max(w0, self.wc - self.hb(u))
            hi = min(w1, self.wc + self.hb(u))
            if hi > lo:
                top.append(self.fr.p(u, lo)); bot.append(self.fr.p(u, hi))
        return top + bot[::-1]


def rect(fr, u0, u1, w0, w1):
    return [fr.p(u0, w0), fr.p(u1, w0), fr.p(u1, w1), fr.p(u0, w1)]


def rrect(fr, u0, u1, w0, w1, r=8):
    x0, x1, y0, y1 = fr.x(u0), fr.x(u1), fr.y(w0), fr.y(w1)
    return ("rect", dict(x=fmt(x0), y=fmt(y0), width=fmt(x1 - x0), height=fmt(y1 - y0), rx=fmt(r)))


# ---------- SVG assembly ----------

STROKE = {"hull": 3.0, "structure": 2.0, "detail": 1.2, "zone": 1.2}


class Drawing:
    def __init__(self, fr):
        self.fr = fr
        self.layers = {k: [] for k in ("hull", "structure", "detail", "zone")}

    def poly(self, layer, points, closed=True):
        tag = "polygon" if closed else "polyline"
        self.layers[layer].append(f'<{tag} points="{pts(points)}"/>')

    def line(self, layer, a, b):
        self.layers[layer].append(
            f'<line x1="{fmt(a[0])}" y1="{fmt(a[1])}" x2="{fmt(b[0])}" y2="{fmt(b[1])}"/>')

    def shape(self, layer, s):
        tag, attrs = s
        self.layers[layer].append(f"<{tag} " + " ".join(f'{k}="{v}"' for k, v in attrs.items()) + "/>")

    def circle(self, layer, c, r):
        self.shape(layer, ("circle", dict(cx=fmt(c[0]), cy=fmt(c[1]), r=fmt(r))))

    def ellipse(self, layer, c, rx, ry):
        self.shape(layer, ("ellipse", dict(cx=fmt(c[0]), cy=fmt(c[1]), rx=fmt(rx), ry=fmt(ry))))

    def svg(self, with_zones):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(W)} {fmt(self.fr.H)}" '
               f'width="{fmt(W)}" height="{fmt(self.fr.H)}">']
        for layer in ("zone", "detail", "structure", "hull"):
            if layer == "zone" and not with_zones:
                continue
            body = self.layers[layer]
            if not body:
                continue
            extra = ' stroke-dasharray="6 4"' if layer == "zone" else ""
            out.append(f'<g id="{layer}" fill="none" stroke="#000" stroke-width="{STROKE[layer]}" '
                       f'stroke-linejoin="round" stroke-linecap="round"{extra}>')
            out += ["  " + s for s in body]
            out.append("</g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"


def zone(d, zid, name, polygon, beneath=None):
    """Record a zone: draw its boundary, return its manifest entry (normalised)."""
    d.poly("zone", polygon)
    fr = d.fr
    xs = [p[0] for p in polygon]; ys = [p[1] for p in polygon]
    # label point: centroid of the polygon (shoelace)
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        c = x1 * y2 - x2 * y1
        a += c; cx += (x1 + x2) * c; cy += (y1 + y2) * c
    a *= 0.5
    lp = (cx / (6 * a), cy / (6 * a)) if abs(a) > 1e-6 else (sum(xs) / len(xs), sum(ys) / len(ys))
    e = {
        "id": zid,
        "name": name,
        "polygon": [[round(x / W, 4), round(y / fr.H, 4)] for x, y in polygon],
        "label": [round(lp[0] / W, 4), round(lp[1] / fr.H, 4)],
    }
    if beneath:
        e["beneath"] = beneath
    return e


# ---------- boat types ----------

def sailboat():
    fr = Frame(ratio=0.30)
    h = Hull(fr, [(0, .80), (.12, .88), (.28, .97), (.46, 1.0), (.62, .96), (.76, .82),
                  (.87, .58), (.95, .30), (1, 0)])
    d = Drawing(fr)
    d.poly("hull", h.outline())
    d.poly("detail", h.outline(inset=.93))                       # toe rail / deck edge
    # coachroof
    cab = [fr.p(u, -h.hb(u, .66)) for u in samples(.30, .78, 40)]
    d.poly("structure", cab + [fr.p(u, h.hb(u, .66)) for u in reversed(samples(.30, .78, 40))])
    d.shape("structure", rrect(fr, .07, .29, -.56, .56, 10))      # cockpit
    d.ellipse("structure", fr.p(.12, 0), 5, fr.B * .16)           # wheel
    d.shape("detail", rrect(fr, .30, .37, -.12, .12, 3))          # companionway
    d.shape("detail", rrect(fr, .70, .75, -.13, .13, 3))          # fwd hatch
    d.circle("structure", fr.p(.60, 0), 7)                        # mast
    Z = [
        zone(d, "lazarette", "Lazarette", h.clip_rect(0, .07, -1, 1), ["Steering gear", "Rudder post"]),
        zone(d, "aft-cabin", "Aft cabin", h.clip_rect(.07, .30, -1, -.18), ["Fuel tank"]),
        zone(d, "cockpit", "Cockpit", h.clip_rect(.07, .30, -.18, .18), ["Engine (aft end)"]),
        zone(d, "cockpit-locker", "Cockpit locker", h.clip_rect(.07, .30, .18, 1)),
        zone(d, "galley", "Galley", h.clip_rect(.30, .45, -1, -.16), ["Water tank"]),
        zone(d, "engine", "Engine / companionway", h.clip_rect(.30, .45, -.16, .16)),
        zone(d, "nav-station", "Nav station", h.clip_rect(.30, .45, .16, 1), ["Batteries"]),
        zone(d, "saloon", "Saloon", h.clip_rect(.45, .65, -1, 1), ["Water tanks", "Bilge", "Keel bolts"]),
        zone(d, "head", "Head", h.clip_rect(.65, .75, -1, 0), ["Holding tank"]),
        zone(d, "hanging-locker", "Hanging locker", h.clip_rect(.65, .75, 0, 1)),
        zone(d, "v-berth", "V-berth", h.clip_rect(.75, .91, -1, 1), ["Water tank"]),
        zone(d, "anchor-locker", "Anchor locker", h.clip_rect(.91, 1, -1, 1)),
    ]
    return "sailboat-monohull", "Sailboat, monohull", "Cruising sloop, about 35–45 ft. Aft cabin under the cockpit, engine under the companionway.", d, Z


def powerboat():
    fr = Frame(ratio=0.32, stern_ext=34)
    h = Hull(fr, [(0, .92), (.18, .96), (.40, 1.0), (.58, .98), (.72, .89), (.84, .70),
                  (.93, .42), (1, 0)])
    d = Drawing(fr)
    d.poly("hull", h.outline())
    d.poly("detail", h.outline(inset=.93))
    d.poly("structure", rect(fr, -34 / fr.L, 0, -h.hb(0, .92), h.hb(0, .92)))   # swim platform
    # windshield: arc across the boat at u≈.50
    ws = [fr.p(.50 + .05 * math.cos(t), .78 * math.sin(t) * -1) for t in
          [math.pi / 2 - k * math.pi / 30 for k in range(31)]]
    d.poly("structure", ws, closed=False)
    fwd = [fr.p(u, -h.hb(u, .62)) for u in samples(.55, .86, 30)]
    d.poly("structure", fwd + [fr.p(u, h.hb(u, .62)) for u in reversed(samples(.55, .86, 30))])  # foredeck cabin top
    d.shape("detail", rrect(fr, .70, .76, -.13, .13, 3))          # fwd hatch
    d.shape("structure", rrect(fr, .40, .47, .25, .65, 6))        # helm seat
    d.circle("structure", fr.p(.49, .45), 9)                      # wheel
    d.shape("detail", rrect(fr, .16, .32, -.45, .45, 4))          # engine hatch
    Z = [
        zone(d, "swim-platform", "Swim platform", rect(fr, -34 / fr.L, 0, -h.hb(0, .92), h.hb(0, .92))),
        zone(d, "lazarette", "Lazarette", h.clip_rect(0, .14, -1, 1), ["Trim tabs", "Steering"]),
        zone(d, "cockpit", "Cockpit", h.clip_rect(.14, .38, -1, 1), ["Engine room", "Fuel tank", "Generator"]),
        zone(d, "helm", "Helm", h.clip_rect(.38, .52, 0, 1), ["Mid-cabin"]),
        zone(d, "companion", "Companion seat / wet bar", h.clip_rect(.38, .52, -1, 0), ["Mid-cabin"]),
        zone(d, "galley", "Galley", h.clip_rect(.52, .64, -1, 0)),
        zone(d, "head", "Head", h.clip_rect(.52, .64, 0, 1), ["Holding tank"]),
        zone(d, "salon", "Salon / dinette", h.clip_rect(.64, .76, -1, 1), ["Water tank"]),
        zone(d, "v-berth", "V-berth", h.clip_rect(.76, .90, -1, 1)),
        zone(d, "anchor-locker", "Anchor locker", h.clip_rect(.90, 1, -1, 1)),
    ]
    return "powerboat-monohull", "Powerboat, monohull", "Express cruiser, about 30–40 ft. Cabin forward, engine room under the cockpit.", d, Z


def catamaran():
    fr = Frame(ratio=0.54)
    prof = [(0, .78), (.15, .92), (.45, 1.0), (.68, .92), (.84, .62), (.94, .30), (1, 0)]
    half, wc = .25, .75
    hp, hs = Hull(fr, prof, half, -wc), Hull(fr, prof, half, wc)
    d = Drawing(fr)
    for h in (hp, hs):
        d.poly("hull", h.outline())
        d.poly("detail", h.outline(inset=.82))
    inner = lambda h, u: h.wc + (-1 if h.wc > 0 else 1) * h.hb(u)
    # bridgedeck: aft beam to front of saloon, between inner hull edges
    for u in (.06, .62):
        d.line("hull", fr.p(u, inner(hp, u)), fr.p(u, inner(hs, u)))
    d.line("structure", fr.p(.86, inner(hp, .86)), fr.p(.86, inner(hs, .86)))   # forward crossbeam
    for k in range(1, 12):                                                       # trampoline
        u = .62 + (.86 - .62) * k / 12
        d.line("detail", fr.p(u, inner(hp, u)), fr.p(u, inner(hs, u)))
    d.shape("structure", rrect(fr, .30, .62, -.72, .72, 14))     # saloon roof
    d.shape("detail", rrect(fr, .06, .30, -.50, .50, 6))         # cockpit
    d.circle("structure", fr.p(.62, 0), 8)                       # mast
    d.ellipse("structure", fr.p(.34, .62), 4, 18)                # helm (stbd bulkhead)
    Z = []
    for side, h, s in (("port", hp, -1), ("stbd", hs, 1)):
        P = "Port" if side == "port" else "Starboard"
        Z += [
            zone(d, f"{side}-engine", f"{P} engine room", h.clip_rect(0, .12, -1, 1), ["Engine", "Saildrive"]),
            zone(d, f"{side}-aft-cabin", f"{P} aft cabin", h.clip_rect(.12, .36, -1, 1), ["Fuel tank"]),
            zone(d, f"{side}-head", f"{P} head", h.clip_rect(.36, .48, -1, 1), ["Holding tank"]),
            zone(d, f"{side}-fwd-cabin", f"{P} forward cabin", h.clip_rect(.48, .74, -1, 1), ["Water tank"]),
            zone(d, f"{side}-fwd-locker", f"{P} forward locker", h.clip_rect(.74, 1, -1, 1), ["Crash bulkhead"]),
        ]
    ip, is_ = inner(hp, .3), inner(hs, .3)
    Z += [
        zone(d, "cockpit", "Cockpit", rect(fr, .06, .30, ip, is_), ["Lockers under seats"]),
        zone(d, "saloon", "Saloon / galley", rect(fr, .30, .62, ip, is_)),
        zone(d, "trampoline", "Trampoline", [fr.p(.62, inner(hp, .62)), fr.p(.86, inner(hp, .86)),
                                              fr.p(.86, inner(hs, .86)), fr.p(.62, inner(hs, .62))]),
        zone(d, "anchor-locker", "Anchor locker", rect(fr, .86, .92, -.22, .22)),
    ]
    return "catamaran-sail", "Catamaran", "Sailing catamaran, about 38–45 ft. Owner's or charter layout; engines in the aft end of each hull.", d, Z


def trawler():
    fr = Frame(ratio=0.33, stern_ext=30)
    h = Hull(fr, [(0, .84), (.15, .94), (.42, 1.0), (.62, .97), (.76, .84), (.87, .62),
                  (.95, .34), (1, 0)])
    d = Drawing(fr)
    d.poly("hull", h.outline())
    d.poly("detail", h.outline(inset=.94))
    d.poly("structure", rect(fr, -30 / fr.L, 0, -h.hb(0, .9), h.hb(0, .9)))    # swim platform
    house = [fr.p(u, -h.hb(u, .76)) for u in samples(.24, .74, 40)]
    d.poly("structure", house + [fr.p(u, h.hb(u, .76)) for u in reversed(samples(.24, .74, 40))])  # deckhouse
    d.line("structure", fr.p(.56, -h.hb(.56, .76)), fr.p(.56, h.hb(.56, .76)))                   # pilothouse bulkhead
    trunk = [fr.p(u, -h.hb(u, .52)) for u in samples(.74, .88, 20)]
    d.poly("structure", trunk + [fr.p(u, h.hb(u, .52)) for u in reversed(samples(.74, .88, 20))])  # fwd trunk cabin
    d.shape("detail", rrect(fr, .30, .52, -.55, .55, 6))        # flybridge (above, dashed in detail)
    d.circle("structure", fr.p(.63, .2), 9)                     # lower helm wheel
    d.shape("detail", rrect(fr, .79, .84, -.12, .12, 3))        # fwd hatch
    Z = [
        zone(d, "swim-platform", "Swim platform", rect(fr, -30 / fr.L, 0, -h.hb(0, .9), h.hb(0, .9))),
        zone(d, "cockpit", "Cockpit", h.clip_rect(0, .12, -1, 1), ["Lazarette", "Steering gear"]),
        zone(d, "aft-stateroom", "Aft stateroom", h.clip_rect(.12, .30, -1, 1), ["Fuel tank"]),
        zone(d, "saloon", "Saloon", h.clip_rect(.30, .46, -1, 1), ["Engine room", "Generator", "Fuel tanks"]),
        zone(d, "galley", "Galley", h.clip_rect(.46, .56, -1, 1), ["Engine room (fwd end)", "Batteries"]),
        zone(d, "pilothouse", "Pilothouse / helm", h.clip_rect(.56, .68, -1, 1), ["Water tank"]),
        zone(d, "head", "Head", h.clip_rect(.68, .78, -1, 0), ["Holding tank"]),
        zone(d, "hanging-locker", "Hanging locker / shower", h.clip_rect(.68, .78, 0, 1)),
        zone(d, "fwd-stateroom", "Forward stateroom", h.clip_rect(.78, .91, -1, 1), ["Water tank"]),
        zone(d, "chain-locker", "Chain locker", h.clip_rect(.91, 1, -1, 1)),
    ]
    return "trawler", "Trawler", "Displacement trawler, about 36–48 ft. Aft cabin, engine room under the saloon, pilothouse forward.", d, Z


def center_console():
    fr = Frame(ratio=0.34, stern_ext=60)
    h = Hull(fr, [(0, .90), (.20, .97), (.45, 1.0), (.64, .94), (.80, .76), (.92, .44), (1, 0)])
    d = Drawing(fr)
    d.poly("hull", h.outline())
    d.poly("detail", h.outline(inset=.88))                      # gunwale
    for w in (-.32, .32):                                       # twin outboards
        d.shape("structure", rrect(fr, -58 / fr.L, -14 / fr.L, w - .17, w + .17, 6))
    d.shape("detail", rrect(fr, -14 / fr.L, 0, -.62, .62, 2))   # bracket
    d.shape("structure", rrect(fr, .44, .56, -.30, .30, 8))     # console
    d.circle("structure", fr.p(.445, 0), 8)                     # wheel
    d.shape("structure", rrect(fr, .35, .41, -.26, .26, 6))     # leaning post
    d.shape("detail", rrect(fr, .33, .58, -.46, .46, 4))        # T-top
    d.poly("structure", [fr.p(u, -h.hb(u, .78)) for u in samples(.70, .97, 20)], closed=False)
    d.poly("structure", [fr.p(u, h.hb(u, .78)) for u in samples(.70, .97, 20)], closed=False)
    d.line("structure", fr.p(.70, -h.hb(.70, .78)), fr.p(.70, h.hb(.70, .78)))   # casting deck step
    Z = [
        zone(d, "transom", "Transom / bilge", h.clip_rect(0, .10, -1, 1), ["Bilge pump", "Batteries"]),
        zone(d, "aft-deck", "Aft deck / livewell", h.clip_rect(.10, .33, -1, 1), ["Fuel tank (fwd)"]),
        zone(d, "leaning-post", "Leaning post", h.clip_rect(.33, .44, -.35, .35), ["Cooler", "Tackle"]),
        zone(d, "console", "Console", h.clip_rect(.44, .56, -.35, .35), ["Head", "Electronics", "Batteries"]),
        zone(d, "fwd-deck", "Forward deck / fish boxes", h.clip_rect(.56, .70, -1, 1), ["Fish boxes"]),
        zone(d, "bow-lockers", "Bow lockers", h.clip_rect(.70, .91, -1, 1)),
        zone(d, "anchor-locker", "Anchor locker", h.clip_rect(.91, 1, -1, 1)),
    ]
    return "center-console", "Center console", "Open fishing boat, about 20–30 ft. No cabin; storage in the console, leaning post, deck and bow lockers.", d, Z


TYPES = [sailboat, catamaran, powerboat, trawler, center_console]


def main():
    manifest = {
        "version": 1,
        "view": "plan",
        "orientation": "Bow to the right, port at the top. Coordinates are 0..1 of the image, x right, y down.",
        "types": [],
    }
    for fn in TYPES:
        tid, name, blurb, d, zones = fn()
        for variant, z in (("outline", False), ("zones", True)):
            with open(os.path.join(HERE, f"{tid}-{variant}.svg"), "w") as f:
                f.write(d.svg(z))
        manifest["types"].append({
            "id": tid, "name": name, "description": blurb,
            "outline": f"{tid}-outline.svg", "zonesImage": f"{tid}-zones.svg",
            "aspect": round(W / d.fr.H, 4), "zones": zones,
        })
    with open(os.path.join(HERE, "boat-outlines.json"), "w") as f:
        text = json.dumps(manifest, indent=2, ensure_ascii=False)
        # one point per line is unreadable: put [x, y] pairs on one line
        text = re.sub(r"\[\s+(-?[\d.]+),\s+(-?[\d.]+)\s+\]", r"[\1, \2]", text)
        f.write(text + "\n")


if __name__ == "__main__":
    main()

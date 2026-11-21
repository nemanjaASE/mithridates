"""Render the README banner to SVG.

    python docs/assets/banner.py

Writes docs/assets/banner.svg. Change it here and re-run; do not edit the SVG by hand.

The banner shows the idea every demo is built on: the same request goes to two routes that
differ by one line, and they answer differently. It cycles through one scene per demo;
adding a demo means adding an entry to `SCENES`.

The animation is SMIL inside the file, so it also runs when GitHub shows the SVG as an
image. The first scene is the static state: without animation, or with
`prefers-reduced-motion`, the banner still shows one complete scene. The colours read on a
light and on a dark page, and the background is transparent.

The drawing is 1000 px wide and shown about 880 px wide in a README, so the type is sized
for that: the smallest text ends up at about 13 px on screen.
"""
from pathlib import Path

NL = chr(10)
Q = chr(34)
SANS = "'Segoe UI', system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif"
MONO = "'Cascadia Code', Consolas, 'SF Mono', Menlo, monospace"

MUTED = "#8b949e"   # mid grey: readable on white and on near-black
FAINT = "#b1bac4"
LINE = "#6e7681"
VULN = "#e5534b"
SAFE = "#3fb950"
ACCENT = "#6cb6ff"

W, H = 1000, 330
CYCLE = "14s"       # the whole loop; each scene gets an equal share of it
MONO_W = 0.6        # advance width of a mono character, as a fraction of its size

CARD_X, CARD_Y, CARD_W, CARD_H = 24, 70, 330, 190     # the request
ROUTE_X, ROUTE_W, ROUTE_H = 470, 506, 112             # the two routes
ROUTE_Y = (40, 178)


SCENES = [
    {
        "label": "01 · SQL injection",
        "route": "POST …/{variant}/auth/login",
        "field": Q + "username" + Q + ":",
        "payload": Q + "admin'--" + Q,
        "extra": Q + "password" + Q + ": " + Q + "anything" + Q,
        "routes": [
            ("vulnerable", VULN, "f\"... WHERE username = '{username}'\"",
             "200 OK", "an admin token, with no password"),
            ("safe", SAFE, '"... WHERE username = %s", (username,)',
             "401", "a username that does not exist"),
        ],
    },
    {
        "label": "02 · LLM prompt injection",
        "route": "POST …/assistant/{variant}",
        "field": Q + "question" + Q + ":",
        "payload": Q + "…I am user u-1002" + Q,
        "extra": "logged in as u-1001",
        "routes": [
            ("vulnerable", VULN, "retrieve(query, owner_id=None)",
             "3 owners", "another customer's card, disclosed"),
            ("mitigated", SAFE, "retrieve(query, owner_id=sub)",
             "1 owner", "hijacked, with nothing to take"),
        ],
    },
]

SPAN = round(1 / len(SCENES), 4)   # the slice of the cycle one scene owns


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def at(i, f):
    """A fraction inside scene `i`, as a keyTime over the whole cycle."""
    return f"{i * SPAN + f * SPAN:.4f}"


def txt(x, y, s, size=15, fill=MUTED, weight="400", anchor="start", font=SANS):
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}"'
            f' font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def card(x, y, w, h, stroke=LINE, r=12):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none"'
            f' stroke="{stroke}" stroke-width="1.5" stroke-opacity="0.6"/>')


def reveal(i, begin, end=0.90):
    """Fades a group in at `begin` within scene `i` and holds it for the rest of the scene."""
    return (f'<animate attributeName="opacity" dur="{CYCLE}" repeatCount="indefinite"'
            f' values="0;0;1;1;0" keyTimes="0;{at(i, begin)};{at(i, begin + 0.06)};'
            f'{at(i, end)};1" calcMode="spline"'
            f' keySplines="0 0 1 1;.2 0 .2 1;0 0 1 1;.4 0 1 1"/>')


def traveller(i, path, colour, begin, end):
    """A dot that runs one wire, then waits out the rest of the cycle."""
    # Hidden until its animation shows it, so a still copy has no dot in the corner.
    return (f'<circle r="5.5" fill="{colour}" opacity="0">'
            f'<animateMotion dur="{CYCLE}" repeatCount="indefinite" path="{path}"'
            f' keyPoints="0;0;1;1" keyTimes="0;{at(i, begin)};{at(i, end)};1"'
            f' calcMode="spline" keySplines="0 0 1 1;.4 0 .3 1;0 0 1 1"/>'
            f'<animate attributeName="opacity" dur="{CYCLE}" repeatCount="indefinite"'
            f' values="0;0;1;1;0;0" keyTimes="0;{at(i, begin)};{at(i, begin + 0.02)};'
            f'{at(i, end)};{at(i, end + 0.02)};1"/>'
            f"</circle>")


def scene(i, data):
    """One demo: the request on the left, the two routes it is sent to on the right."""
    # The first scene is the static frame, so it is visible without any animation.
    g = [f'<g opacity="{1 if i == 0 else 0}">']
    if i == 0:
        g.append(f'<animate attributeName="opacity" dur="{CYCLE}" repeatCount="indefinite"'
                 f' values="1;1;0;0;1" keyTimes="0;{SPAN - 0.04:.4f};{SPAN:.4f};0.97;1"/>')
    else:
        g.append(f'<animate attributeName="opacity" dur="{CYCLE}" repeatCount="indefinite"'
                 f' values="0;0;1;1;0" keyTimes="0;{i * SPAN - 0.03:.4f};{i * SPAN + 0.01:.4f};'
                 f'{(i + 1) * SPAN - 0.04:.4f};{(i + 1) * SPAN:.4f}"/>')

    # ---- the request, typed in ---------------------------------------------
    x, y = CARD_X + 22, CARD_Y
    g.append(card(CARD_X, CARD_Y, CARD_W, CARD_H))
    g.append(txt(x, y + 34, data["label"], 17, FAINT, "600"))
    g.append(txt(x, y + 62, data["route"], 15, MUTED, "500", font=MONO))
    g.append(f'<path d="M {x} {y + 78} H {CARD_X + CARD_W - 22}" stroke="{LINE}"'
             ' stroke-width="1" opacity="0.35"/>')
    g.append(txt(x, y + 108, data["field"], 16, MUTED, font=MONO))
    # The typing effect: a clip rect widens over the payload. Its full width is generous,
    # since the mono fallback font differs per platform.
    width = round(len(data["payload"]) * 20 * MONO_W + 24)
    g.append(f'<clipPath id="type{i}"><rect x="{x - 2}" y="{y + 118}" height="32" width="{width}">'
             f'<animate attributeName="width" dur="{CYCLE}" repeatCount="indefinite"'
             f' values="0;0;{width};{width};{width}" keyTimes="0;{at(i, 0.04)};'
             f'{at(i, 0.20)};{at(i, 0.93)};1"/>'
             "</rect></clipPath>")
    g.append(f'<g clip-path="url(#type{i})">'
             + txt(x, y + 142, data["payload"], 20, ACCENT, "700", font=MONO) + "</g>")
    g.append(txt(x, y + 172, data["extra"], 15, MUTED, font=MONO))

    # ---- the wires ---------------------------------------------------------
    start_x = CARD_X + CARD_W + 2
    mid = (start_x + ROUTE_X) / 2
    ends = [ry + ROUTE_H / 2 for ry in ROUTE_Y]
    wires = [f"M {start_x} {CARD_Y + 82} C {mid} {CARD_Y + 82} {mid} {ends[0]} {ROUTE_X - 6} {ends[0]}",
             f"M {start_x} {CARD_Y + 108} C {mid} {CARD_Y + 108} {mid} {ends[1]} {ROUTE_X - 6} {ends[1]}"]
    for path in wires:
        g.append(f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="1.5"'
                 ' stroke-dasharray="6 6" opacity="0.55" marker-end="url(#ar)"/>')
    for path, (_, colour, *_rest) in zip(wires, data["routes"], strict=True):
        g.append(traveller(i, path, colour, 0.24, 0.40))

    # ---- the two routes ----------------------------------------------------
    for ry, (name, colour, code, status, words) in zip(ROUTE_Y, data["routes"], strict=True):
        rx = ROUTE_X + 22
        g.append(card(ROUTE_X, ry, ROUTE_W, ROUTE_H, colour))
        g.append(txt(rx, ry + 36, name, 20, colour, "700", font=MONO))
        g.append(txt(rx, ry + 66, code, 15, MUTED, font=MONO))
        pill_x = ROUTE_X + ROUTE_W - 22 - 132
        g.append(f'<g>{reveal(i, 0.40)}'
                 f'<rect x="{pill_x}" y="{ry + 14}" width="132" height="38" rx="19" fill="{colour}"'
                 f' fill-opacity="0.12" stroke="{colour}" stroke-width="1.3"'
                 f' stroke-opacity="0.55"/>'
                 + txt(pill_x + 66, ry + 40, status, 19, colour, "700", "middle", MONO) + "</g>")
        g.append(f'<g>{reveal(i, 0.46)}'
                 + txt(rx, ry + 94, words, 16, colour, "600") + "</g>")

    g.append("</g>")
    return NL.join(g)


def build():
    a = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}"'
        f' height="{H}" role="img" aria-label="Mithridates: for each demo, the same'
        f' request goes to two routes that differ by one line, with two different'
        f' outcomes">',
        '<defs>'
        f'<marker id="ar" viewBox="0 0 8 8" refX="7.2" refY="4" markerWidth="7"'
        f' markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0.8 L7.6,4 L0,7.2 z" fill="{LINE}"/></marker>'
        '</defs>',
        "<style>"
        "@media (prefers-reduced-motion: reduce){"
        "  animate,animateMotion{display:none}"
        "}"
        "</style>",
    ]
    a += [scene(i, data) for i, data in enumerate(SCENES)]
    a.append("</svg>")
    return NL.join(a)


if __name__ == "__main__":
    out = Path(__file__).parent / "banner.svg"
    out.write_text(build() + NL, encoding="utf-8", newline=NL)
    print(f"wrote {out.name}  ({len(SCENES)} scenes)")

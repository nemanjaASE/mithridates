"""Render this demo's figures to SVG.

    python docs/diagrams.py

Writes c1-context.svg, c2-containers.svg, c3-components.svg, c4-code.svg and
database.svg for the README, next to this file. The write-up has no figures; it explains
in text. Hand-editing generated SVG is no fun, so change it here and re-run.

Everything between the two markers below is the repository's house style, copied verbatim
from `.claude/skills/house-style-figures/diagram_style.py`; `check_figures.py` there fails when the copies drift
apart.
Only the figures after it belong to this demo, and each one is built around a line that
really is in the code.
"""
from pathlib import Path

# --- house style · copied from .claude/skills/house-style-figures/diagram_style.py · do not edit here
NL = chr(10)

# A white sheet, black type and black lines, and colour only where it means something:
# the light theme of IBM Design Language's technical diagrams, where the canvas is white,
# text is always black, and a swatch 10 is the only tint. White and black are what hold up
# on a projector in a lit room, where a dark ground and a grey line both fade. Every text
# colour reads at 4.5:1 or better on every ground, every edge at 3:1.
PAPER = "#FFFFFF"        # the page
INK = "#161616"          # anything being read: IBM Gray 100
MUTED = "#262626"        # labels, notes, the caption: Gray 90
TECH = "#393939"         # the [technology] under a name, the Docker badge: Gray 80
LINE = "#161616"         # every drawn line: arrows, the system frame
EDGE = "#161616"         # the outline of a box that is part of the system
HAIR = "#C6C6C6"         # the faintest rules: under the title, above the caption: Gray 30
FILL = "#FFFFFF"         # a box that is part of the running system
OUT = "#E0E0E0"          # a box outside the system, or already gone: Gray 20
ACCENT = "#A2191F"       # IBM Red 70: the attack, and the code it gets through
SAFE = "#0E6027"         # IBM Green 70: the fix, and the control that stops it
ACCENT_FILL = "#FFF1F1"  # Red 10: inside a box on the attack path
SAFE_FILL = "#DEFBE6"    # Green 10: inside a box that is the fix

# Two faces. Every label is set in a sans-serif of even stroke, which reads from the back
# of a room; code, and only code, stays monospaced, so it looks like the source it is.
SANS = "Arial, 'Liberation Sans', Helvetica, sans-serif"
MONO = "Consolas, 'Cascadia Mono', 'SF Mono', Menlo, monospace"

M = 56               # page margin, left and right

# text sizes, so a figure can grow without anything drifting out of line
NAME, KIND, DESC, LABEL, HEADING = 21, 17.5, 18.5, 18.5, 17.5
CW = 0.55            # advance width of one mono character, as a fraction of its size

# Arial's advance widths in thousandths of an em, which Liberation Sans and Helvetica
# share, for printable ASCII and the few marks the figures use.
_GLYPHS = "".join(map(chr, range(32, 127))) + "·—–…→’“”"
_REGULAR = dict(zip(_GLYPHS, (
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556,
    556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556, 1015, 667, 667, 722,
    722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722,
    667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500, 556, 556, 278, 556,
    556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500,
    500, 334, 260, 334, 584, 333, 1000, 556, 1000, 1000, 222, 333, 333), strict=True))
_BOLD = dict(zip(_GLYPHS, (
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556,
    556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611, 975, 722, 722, 722,
    722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722, 667, 611, 722,
    667, 944, 667, 667, 611, 333, 278, 333, 584, 556, 333, 556, 611, 556, 611, 556, 333, 611,
    611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556,
    500, 389, 280, 389, 584, 333, 1000, 556, 1000, 1000, 278, 500, 500), strict=True))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mono_w(s, size):
    """How wide a mono run is."""
    return round(len(s) * CW * size, 2)


def sans_w(s, size, bold=False):
    """How wide a sans run is, by Arial's metrics; a mark they lack counts as a digit."""
    widths = _BOLD if bold else _REGULAR
    return round(sum(widths.get(c, 556) for c in s) * size / 1000, 2)


def text(x, y, s, size=16, fill=INK, weight="400", font=SANS, anchor="start", width=None):
    """One run of type, always drawn at its measured width, so a figure lays out the same
    whichever font of the list the reader has, and check_figures.py measures what is drawn."""
    if width is None:
        width = mono_w(s, size) if font == MONO else sans_w(s, size, int(weight) >= 600)
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}"'
            f' font-weight="{weight}"{an} xml:space="preserve" textLength="{width}"'
            f' lengthAdjust="spacingAndGlyphs">{esc(s)}</text>')


def sans(x, y, s, size=LABEL, fill=INK, weight="400"):
    """A label: a name, a technology, what travels over an arrow."""
    return text(x, y, s, size, fill, weight, SANS)


def mono(x, y, s, size=20, fill=INK, weight="400"):
    """Code: a line of source, a route, a payload, a column."""
    return text(x, y, s, size, fill, weight, MONO)


def line(x1, y1, x2, y2, colour=LINE, width=1):
    return (f'<polyline points="{x1},{y1} {x2},{y2}" fill="none" stroke="{colour}"'
            f' stroke-width="{width}"/>')


def leader(points, colour=LINE):
    """A right-angled thread from a span of code to the note that explains it."""
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="1.5"/>'


def _arrowhead(name, colour):
    return (f'<marker id="{name}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="12"'
            f' markerHeight="12" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
            f'<path d="M0,1.2 L7.4,4 L0,6.8" fill="none" stroke="{colour}"'
            f' stroke-width="1.4"/></marker>')


HEADS = (_arrowhead("to", LINE) + _arrowhead("to-ink", INK)
         + _arrowhead("to-accent", ACCENT) + _arrowhead("to-safe", SAFE))


def figure(w, head, desc=""):
    """Opens a figure: the ground, the title, one rule.

    The title says what the figure is and what it covers, the way the C4 model asks:
    "Container diagram for sqli-demo". There is no height to give: `caption()` measures how
    far the drawing reaches and sizes the sheet to it, so the 40px rhythm above the key and
    the caption holds by itself."""
    a = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} __H__" width="{w}"'
         ' height="__H__" role="img" aria-labelledby="t d">',
         f"<title id=\"t\">{esc(head)}</title><desc id=\"d\">{esc(desc or head)}</desc>",
         f"<defs>{HEADS}</defs>",
         f'<rect width="{w}" height="__H__" fill="{PAPER}"/>',
         sans(M, 96, head, 34, INK, "700")]
    a.append(line(M, 132, w - M, 132, HAIR, 1))
    return a


def reach(a, w):
    """How far down the drawing goes: the lowest box, line or line of text on the sheet."""
    import re  # here and not at the top: this block is copied into files of their own
    body = NL.join(a[4:])
    ys = [float(y) + float(hh) for y, ww, hh in re.findall(
        r'<rect x="[\d.]+" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', body)
        if float(ww) < w - 10]
    for points in re.findall(r'<polyline points="([^"]+)"', body):
        ys.append(max(float(pt.split(",")[1]) for pt in points.split()))
    for y, size in re.findall(r'<text [^>]*?y="([\d.]+)"[^>]*?font-size="([\d.]+)"', body):
        ys.append(float(y) + float(size) * 0.22)
    return max(ys)


def caption(a, w, number, what, source=""):
    """Closes the figure: the key, then one line with its number and the file it was read
    from, and the sheet cut to fit — 40px under the drawing, 40px under the key.

    `what` is kept as the figure's description for whoever reads the code; the title above
    the drawing already says it, so the caption does not repeat it.
    """
    top = int(reach(a, w) + 0.999) + 40
    h = (top + 18 + 40 if key(a, top, NL.join(a[3:])) else top) + 58
    for i in (0, 3):
        a[i] = a[i].replace("__H__", str(h))
    y = h - 58
    a.append(line(M, y, w - M, y, HAIR, 1))
    a.append(sans(M, y + 30, f"{number:02d}", 17, TECH, "700"))
    if source:
        a.append(sans(M + 40, y + 30, source, 17, MUTED))
    a.append("</svg>")
    return NL.join(a)


def code(a, x, y, parts, size=26):
    """One line of real source, drawn run by run.

    `parts` is a list of `(snippet, colour)`. The return value gives each run's span as
    `(x0, x1)`, which is what lets an underline or a leader start at the exact argument
    instead of somewhere near it.
    """
    spans = []
    for snippet, colour in parts:
        w = mono_w(snippet, size)
        a.append(mono(x, y, snippet, size, colour or INK))
        spans.append((x, x + w))
        x += w
    return spans


def underline(a, span, y, colour=MUTED):
    a.append(line(span[0], y, span[1], y, colour, 2))


def note(a, x, y, head, rows, size=20, leading=31):
    """A bold label and the lines of code under it. A row is a list of `(text, colour)`."""
    a.append(sans(x, y, head, 20, INK, "700"))
    ty = y + 40
    for row in rows:
        tx = x
        for snippet, colour in row:
            a.append(mono(tx, ty, snippet, size, colour or INK))
            tx += mono_w(snippet, size)
        ty += leading
    return ty - leading


def annotate(a, span, under_y, head, rows, at, colour=MUTED, drop=None):
    """Underline a run of code and thread a leader from its middle down to a note."""
    underline(a, span, under_y, colour)
    mid = round((span[0] + span[1]) / 2, 2)
    x, y = at
    bend = drop or under_y + 28
    a.append(leader([(mid, under_y), (mid, bend), (x, bend), (x, y - 29)], colour))
    return note(a, x, y, head, rows)


def heading(a, x, y, s, size=HEADING, fill=MUTED):
    """The name of what follows on the sheet: bold, in sentence case, never in capitals."""
    a.append(sans(x, y, s, size, fill, "700"))


def stage(a, x, y, name, sub=None, size=20, colour=INK):
    """A step in a flow: its name, one line of detail under it, a rule beneath."""
    a.append(sans(x, y, name, size, colour, "700"))
    w = sans_w(name, size, True)
    if sub:
        a.append(sans(x, y + 22, sub, 15, MUTED))
        w = max(w, sans_w(sub, 15))
    a.append(line(x, y + (34 if sub else 12), x + w, y + (34 if sub else 12), HAIR, 1))
    return w


def thread(a, x1, y, x2, label=None, colour=MUTED, dash=""):
    """The line between two stages, with what travels over it written above."""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a.append(f'<polyline points="{x1},{y} {x2},{y}" fill="none" stroke="{colour}"'
             f' stroke-width="2"{da}/>')
    tip = x2 - 7 if x2 > x1 else x2 + 7
    a.append(f'<polyline points="{tip},{y - 3.5} {x2},{y} {tip},{y + 3.5}" fill="none"'
             f' stroke="{colour}" stroke-width="2"/>')
    if label:
        a.append(sans(round((x1 + x2) / 2 - sans_w(label, LABEL) / 2, 2), y - 10, label, LABEL,
                      colour))


def table(a, x, y, columns, rows, size=16, leading=28):
    """Columns of type with a hairline under the headings. No boxes, no fills.

    `columns` is a list of `(heading, width, mono?)`; a cell may be `(text, colour)`.
    """
    tx = x
    for head, width, _ in columns:
        heading(a, tx, y, head, 13)
        tx += width
    total = sum(w for _, w, _ in columns)
    a.append(line(x, y + 12, x + total, y + 12, HAIR, 1))
    ty = y + 12 + leading
    for row in rows:
        tx = x
        for (_head, width, is_mono), cell in zip(columns, row, strict=True):
            body, colour = cell if isinstance(cell, tuple) else (cell, INK)
            a.append((mono if is_mono else sans)(tx, ty, body, size, colour))
            tx += width
        a.append(line(x, ty + 10, x + total, ty + 10, HAIR, 1))
        ty += leading
    return ty - leading


def frame(x, y, w, h, colour, fill, roles=()):
    """A box on the sheet: a 3px outline in its colour around its ground. `roles` names
    what the box stands for, so the key under the figure can list exactly what is on it."""
    cls = " ".join(["frame"] + [f"frame-{r}" for r in roles])
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{colour}"'
            f' stroke-width="3" class="{cls}"/>')


def ground(colour, outside=False):
    """What a box is filled with: grey outside the system, else a tint of its colour."""
    return OUT if outside else {ACCENT: ACCENT_FILL, SAFE: SAFE_FILL}.get(colour, FILL)


# Real technology marks, from Simple Icons 16.37.0 (CC0): one filled 24px path each.
# They are drawn in the same colour as every other icon, so a logo says *which*
# technology without adding a colour that means nothing.
BRANDS = {
    "github": (
        "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-"
        ".577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633"
        " 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236"
        " 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.3"
        "32-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005"
        "-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.28"
        "5-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-"
        "2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .3"
        "15.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
    ),
    "fastapi": (
        "M12 .0387C5.3729.0384.0003 5.3931 0 11.9988c-.001 6.6066 5.372 11.9628 12 11.962"
        "5 6.628.0003 12.001-5.3559 12-11.9625-.0003-6.6057-5.3729-11.9604-12-11.96m-.829"
        " 5.4153h7.55l-7.5805 5.3284h5.1828L5.279 18.5436q2.9466-6.5444 5.892-13.0896"
    ),
    "postgresql": (
        "M23.5594 14.7228a.5269.5269 0 0 0-.0563-.1191c-.139-.2632-.4768-.3418-1.0074-.23"
        "21-1.6533.3411-2.2935.1312-2.5256-.0191 1.342-2.0482 2.445-4.522 3.0411-6.8297.2"
        "714-1.0507.7982-3.5237.1222-4.7316a1.5641 1.5641 0 0 0-.1509-.235C21.6931.9086 1"
        "9.8007.0248 17.5099.0005c-1.4947-.0158-2.7705.3461-3.1161.4794a9.449 9.449 0 0 0"
        "-.5159-.0816 8.044 8.044 0 0 0-1.3114-.1278c-1.1822-.0184-2.2038.2642-3.0498.840"
        "6-.8573-.3211-4.7888-1.645-7.2219.0788C.9359 2.1526.3086 3.8733.4302 6.3043c.040"
        "9.818.5069 3.334 1.2423 5.7436.4598 1.5065.9387 2.7019 1.4334 3.582.553.9942 1.1"
        "259 1.5933 1.7143 1.7895.4474.1491 1.1327.1441 1.8581-.7279.8012-.9635 1.5903-1."
        "8258 1.9446-2.2069.4351.2355.9064.3625 1.39.3772a.0569.0569 0 0 0 .0004.0041 11."
        "0312 11.0312 0 0 0-.2472.3054c-.3389.4302-.4094.5197-1.5002.7443-.3102.064-1.134"
        "4.2339-1.1464.8115-.0025.1224.0329.2309.0919.3268.2269.4231.9216.6097 1.015.6331"
        " 1.3345.3335 2.5044.092 3.3714-.6787-.017 2.231.0775 4.4174.3454 5.0874.2212.552"
        "9.7618 1.9045 2.4692 1.9043.2505 0 .5263-.0291.8296-.0941 1.7819-.3821 2.5557-1."
        "1696 2.855-2.9059.1503-.8707.4016-2.8753.5388-4.1012.0169-.0703.0357-.1207.057-."
        "1362.0007-.0005.0697-.0471.4272.0307a.3673.3673 0 0 0 .0443.0068l.2539.0223.0149"
        ".001c.8468.0384 1.9114-.1426 2.5312-.4308.6438-.2988 1.8057-1.0323 1.5951-1.6698"
        "zM2.371 11.8765c-.7435-2.4358-1.1779-4.8851-1.2123-5.5719-.1086-2.1714.4171-3.68"
        "29 1.5623-4.4927 1.8367-1.2986 4.8398-.5408 6.108-.13-.0032.0032-.0066.0061-.009"
        "8.0094-2.0238 2.044-1.9758 5.536-1.9708 5.7495-.0002.0823.0066.1989.0162.3593.03"
        "48.5873.0996 1.6804-.0735 2.9184-.1609 1.1504.1937 2.2764.9728 3.0892.0806.0841."
        "1648.1631.2518.2374-.3468.3714-1.1004 1.1926-1.9025 2.1576-.5677.6825-.9597.5517"
        "-1.0886.5087-.3919-.1307-.813-.5871-1.2381-1.3223-.4796-.839-.9635-2.0317-1.4155"
        "-3.5126zm6.0072 5.0871c-.1711-.0428-.3271-.1132-.4322-.1772.0889-.0394.2374-.090"
        "2.4833-.1409 1.2833-.2641 1.4815-.4506 1.9143-1.0002.0992-.126.2116-.2687.3673-."
        "4426a.3549.3549 0 0 0 .0737-.1298c.1708-.1513.2724-.1099.4369-.0417.156.0646.307"
        "8.26.3695.4752.0291.1016.0619.2945-.0452.4444-.9043 1.2658-2.2216 1.2494-3.1676 "
        "1.0128zm2.094-3.988-.0525.141c-.133.3566-.2567.6881-.3334 1.003-.6674-.0021-1.31"
        "68-.2872-1.8105-.8024-.6279-.6551-.9131-1.5664-.7825-2.5004.1828-1.3079.1153-2.4"
        "468.079-3.0586-.005-.0857-.0095-.1607-.0122-.2199.2957-.2621 1.6659-.9962 2.6429"
        "-.7724.4459.1022.7176.4057.8305.928.5846 2.7038.0774 3.8307-.3302 4.7363-.084.18"
        "66-.1633.3629-.2311.5454zm7.3637 4.5725c-.0169.1768-.0358.376-.0618.5959l-.146.4"
        "383a.3547.3547 0 0 0-.0182.1077c-.0059.4747-.054.6489-.115.8693-.0634.2292-.1353"
        ".4891-.1794 1.0575-.11 1.4143-.8782 2.2267-2.4172 2.5565-1.5155.3251-1.7843-.496"
        "8-2.0212-1.2217a6.5824 6.5824 0 0 0-.0769-.2266c-.2154-.5858-.1911-1.4119-.1574-"
        "2.5551.0165-.5612-.0249-1.9013-.3302-2.6462.0044-.2932.0106-.5909.019-.8918a.352"
        "9.3529 0 0 0-.0153-.1126 1.4927 1.4927 0 0 0-.0439-.208c-.1226-.4283-.4213-.7866"
        "-.7797-.9351-.1424-.059-.4038-.1672-.7178-.0869.067-.276.1831-.5875.309-.9249l.0"
        "529-.142c.0595-.16.134-.3257.213-.5012.4265-.9476 1.0106-2.2453.3766-5.1772-.237"
        "4-1.0981-1.0304-1.6343-2.2324-1.5098-.7207.0746-1.3799.3654-1.7088.5321a5.6716 5"
        ".6716 0 0 0-.1958.1041c.0918-1.1064.4386-3.1741 1.7357-4.4823a4.0306 4.0306 0 0 "
        "1 .3033-.276.3532.3532 0 0 0 .1447-.0644c.7524-.5706 1.6945-.8506 2.802-.8325.40"
        "91.0067.8017.0339 1.1742.081 1.939.3544 3.2439 1.4468 4.0359 2.3827.8143.9623 1."
        "2552 1.9315 1.4312 2.4543-1.3232-.1346-2.2234.1268-2.6797.779-.9926 1.4189.543 4"
        ".1729 1.2811 5.4964.1353.2426.2522.4522.2889.5413.2403.5825.5515.9713.7787 1.255"
        "2.0696.087.1372.1714.1885.245-.4008.1155-1.1208.3825-1.0552 1.717-.0123.1563-.04"
        "23.4469-.0834.8148-.0461.2077-.0702.4603-.0994.7662zm.8905-1.6211c-.0405-.8316.2"
        "691-.9185.5967-1.0105a2.8566 2.8566 0 0 0 .135-.0406 1.202 1.202 0 0 0 .1342.103"
        "c.5703.3765 1.5823.4213 3.0068.1344-.2016.1769-.5189.3994-.9533.6011-.4098.1903-"
        "1.0957.333-1.7473.3636-.7197.0336-1.0859-.0807-1.1721-.151zm.5695-9.2712c-.0059."
        "3508-.0542.6692-.1054 1.0017-.055.3576-.112.7274-.1264 1.1762-.0142.4368.0404.89"
        "09.0932 1.3301.1066.887.216 1.8003-.2075 2.7014a3.5272 3.5272 0 0 1-.1876-.3856c"
        "-.0527-.1276-.1669-.3326-.3251-.6162-.6156-1.1041-2.0574-3.6896-1.3193-4.7446.37"
        "95-.5427 1.3408-.5661 2.1781-.463zm.2284 7.0137a12.3762 12.3762 0 0 0-.0853-.107"
        "4l-.0355-.0444c.7262-1.1995.5842-2.3862.4578-3.4385-.0519-.4318-.1009-.8396-.088"
        "5-1.2226.0129-.4061.0666-.7543.1185-1.0911.0639-.415.1288-.8443.1109-1.3505.0134"
        "-.0531.0188-.1158.0118-.1902-.0457-.4855-.5999-1.938-1.7294-3.253-.6076-.7073-1."
        "4896-1.4972-2.6889-2.0395.5251-.1066 1.2328-.2035 2.0244-.1859 2.0515.0456 3.674"
        "6.8135 4.8242 2.2824a.908.908 0 0 1 .0667.1002c.7231 1.3556-.2762 6.2751-2.9867 "
        "10.5405zm-8.8166-6.1162c-.025.1794-.3089.4225-.6211.4225a.5821.5821 0 0 1-.0809-"
        ".0056c-.1873-.026-.3765-.144-.5059-.3156-.0458-.0605-.1203-.178-.1055-.2844.0055"
        "-.0401.0261-.0985.0925-.1488.1182-.0894.3518-.1226.6096-.0867.3163.0441.6426.193"
        "8.6113.4186zm7.9305-.4114c.0111.0792-.049.201-.1531.3102-.0683.0717-.212.1961-.4"
        "079.2232a.5456.5456 0 0 1-.075.0052c-.2935 0-.5414-.2344-.5607-.3717-.024-.1765."
        "2641-.3106.5611-.352.297-.0414.6111.0088.6356.1851z"
    ),
    "docker": (
        "M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119"
        "a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 "
        "0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c"
        "0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-."
        "186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12"
        "a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v"
        "1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185"
        " 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.186m5.893 "
        "2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185"
        " 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V"
        "9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185."
        "185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.1"
        "2a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00"
        ".184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .10"
        "2.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.0"
        "1.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612"
        " 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-."
        "75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3."
        "1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c."
        "98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.2"
        "15-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"
    ),
    "python": (
        "M11.858 0c-.978.005-1.913.088-2.736.234C6.7.662 6.26 1.558 6.26 3.21v2.182h5.725"
        "v.727H4.111c-1.664 0-3.121 1-3.577 2.903-.526 2.181-.549 3.542 0 5.82.407 1.694 "
        "1.379 2.902 3.043 2.902h1.969v-2.616c0-1.89 1.635-3.557 3.576-3.557h5.72c1.591 0"
        " 2.862-1.31 2.862-2.91v-5.45c0-1.553-1.309-2.718-2.863-2.977A18 18 0 0 0 11.858 "
        "0M8.762 1.755c.591 0 1.074.491 1.074 1.095 0 .601-.483 1.087-1.074 1.087A1.08 1."
        "08 0 0 1 7.688 2.85c0-.604.48-1.095 1.074-1.095m9.656 4.364v2.543c0 1.971-1.671 "
        "3.63-3.577 3.63H9.122c-1.566 0-2.862 1.34-2.862 2.91v5.452c0 1.551 1.349 2.464 2"
        ".862 2.91 1.813.532 3.55.628 5.72 0 1.44-.418 2.862-1.258 2.862-2.91V18.47h-5.71"
        "9v-.727h8.582c1.664 0 2.284-1.16 2.862-2.903.598-1.793.573-3.518 0-5.819-.41-1.6"
        "56-1.196-2.903-2.862-2.903zm-3.216 13.807a1.08 1.08 0 0 1 1.074 1.088c0 .604-.48"
        " 1.094-1.074 1.094-.592 0-1.075-.49-1.075-1.094 0-.601.483-1.088 1.075-1.088"
    ),
    "ollama": (
        "M16.361 10.26a.894.894 0 0 0-.558.47l-.072.148.001.207c0 .193.004.217.059.353.07"
        "6.193.152.312.291.448.24.238.51.3.872.205a.86.86 0 0 0 .517-.436.752.752 0 0 0 ."
        "08-.498c-.064-.453-.33-.782-.724-.897a1.06 1.06 0 0 0-.466 0zm-9.203.005c-.305.0"
        "96-.533.32-.65.639a1.187 1.187 0 0 0-.06.52c.057.309.31.59.598.667.362.095.632.0"
        "33.872-.205.14-.136.215-.255.291-.448.055-.136.059-.16.059-.353l.001-.207-.072-."
        "148a.894.894 0 0 0-.565-.472 1.02 1.02 0 0 0-.474.007Zm4.184 2c-.131.071-.223.25"
        "-.195.383.031.143.157.288.353.407.105.063.112.072.117.136.004.038-.01.146-.029.2"
        "43-.02.094-.036.194-.036.222.002.074.07.195.143.253.064.052.076.054.255.059.164."
        "005.198.001.264-.03.169-.082.212-.234.15-.525-.052-.243-.042-.28.087-.355.137-.0"
        "8.281-.219.324-.314a.365.365 0 0 0-.175-.48.394.394 0 0 0-.181-.033c-.126 0-.207"
        ".03-.355.124l-.085.053-.053-.032c-.219-.13-.259-.145-.391-.143a.396.396 0 0 0-.1"
        "93.032zm.39-2.195c-.373.036-.475.05-.654.086-.291.06-.68.195-.951.328-.94.46-1.5"
        "89 1.226-1.787 2.114-.04.176-.045.234-.045.53 0 .294.005.357.043.524.264 1.16 1."
        "332 2.017 2.714 2.173.3.033 1.596.033 1.896 0 1.11-.125 2.064-.727 2.493-1.571.1"
        "14-.226.169-.372.22-.602.039-.167.044-.23.044-.523 0-.297-.005-.355-.045-.531-.2"
        "88-1.29-1.539-2.304-3.072-2.497a6.873 6.873 0 0 0-.855-.031zm.645.937a3.283 3.28"
        "3 0 0 1 1.44.514c.223.148.537.458.671.662.166.251.26.508.303.82.02.143.01.251-.0"
        "43.482-.08.345-.332.705-.672.957a3.115 3.115 0 0 1-.689.348c-.382.122-.632.144-1"
        ".525.138-.582-.006-.686-.01-.853-.042-.57-.107-1.022-.334-1.35-.68-.264-.28-.385"
        "-.535-.45-.946-.03-.192.025-.509.137-.776.136-.326.488-.73.836-.963.403-.269.934"
        "-.46 1.422-.512.187-.02.586-.02.773-.002zm-5.503-11a1.653 1.653 0 0 0-.683.298C5"
        ".617.74 5.173 1.666 4.985 2.819c-.07.436-.119 1.04-.119 1.503 0 .544.064 1.24.15"
        "5 1.721.02.107.031.202.023.208a8.12 8.12 0 0 1-.187.152 5.324 5.324 0 0 0-.949 1"
        ".02 5.49 5.49 0 0 0-.94 2.339 6.625 6.625 0 0 0-.023 1.357c.091.78.325 1.438.727"
        " 2.04l.13.195-.037.064c-.269.452-.498 1.105-.605 1.732-.084.496-.095.629-.095 1."
        "294 0 .67.009.803.088 1.266.095.555.288 1.143.503 1.534.071.128.243.393.264.407."
        "007.003-.014.067-.046.141a7.405 7.405 0 0 0-.548 1.873c-.062.417-.071.552-.071.9"
        "91 0 .56.031.832.148 1.279L3.42 24h1.478l-.05-.091c-.297-.552-.325-1.575-.068-2."
        "597.117-.472.25-.819.498-1.296l.148-.29v-.177c0-.165-.003-.184-.057-.293a.915.91"
        "5 0 0 0-.194-.25 1.74 1.74 0 0 1-.385-.543c-.424-.92-.506-2.286-.208-3.451.124-."
        "486.329-.918.544-1.154a.787.787 0 0 0 .223-.531c0-.195-.07-.355-.224-.522a3.136 "
        "3.136 0 0 1-.817-1.729c-.14-.96.114-2.005.69-2.834.563-.814 1.353-1.336 2.237-1."
        "475.199-.033.57-.028.776.01.226.04.367.028.512-.041.179-.085.268-.19.374-.431.09"
        "3-.215.165-.333.36-.576.234-.29.46-.489.822-.729.413-.27.884-.467 1.352-.561.17-"
        ".035.25-.04.569-.04.319 0 .398.005.569.04a4.07 4.07 0 0 1 1.914.997c.117.109.398"
        ".457.488.602.034.057.095.177.132.267.105.241.195.346.374.43.14.068.286.082.503.0"
        "45.343-.058.607-.053.943.016 1.144.23 2.14 1.173 2.581 2.437.385 1.108.276 2.267"
        "-.296 3.153-.097.15-.193.27-.333.419-.301.322-.301.722-.001 1.053.493.539.801 1."
        "866.708 3.036-.062.772-.26 1.463-.533 1.854a2.096 2.096 0 0 1-.224.258.916.916 0"
        " 0 0-.194.25c-.054.109-.057.128-.057.293v.178l.148.29c.248.476.38.823.498 1.295."
        "253 1.008.231 2.01-.059 2.581a.845.845 0 0 0-.044.098c0 .006.329.009.732.009h.73"
        "l.02-.074.036-.134c.019-.076.057-.3.088-.516.029-.217.029-1.016 0-1.258-.11-.875"
        "-.295-1.57-.597-2.226-.032-.074-.053-.138-.046-.141.008-.005.057-.074.108-.152.3"
        "76-.569.607-1.284.724-2.228.031-.26.031-1.378 0-1.628-.083-.645-.182-1.082-.348-"
        "1.525a6.083 6.083 0 0 0-.329-.7l-.038-.064.131-.194c.402-.604.636-1.262.727-2.04"
        "a6.625 6.625 0 0 0-.024-1.358 5.512 5.512 0 0 0-.939-2.339 5.325 5.325 0 0 0-.95"
        "-1.02 8.097 8.097 0 0 1-.186-.152.692.692 0 0 1 .023-.208c.208-1.087.201-2.443-."
        "017-3.503-.19-.924-.535-1.658-.98-2.082-.354-.338-.716-.482-1.15-.455-.996.059-1"
        ".8 1.205-2.116 3.01a6.805 6.805 0 0 0-.097.726c0 .036-.007.066-.015.066a.96.96 0"
        " 0 1-.149-.078A4.857 4.857 0 0 0 12 3.03c-.832 0-1.687.243-2.456.698a.958.958 0 "
        "0 1-.148.078c-.008 0-.015-.03-.015-.066a6.71 6.71 0 0 0-.097-.725C8.997 1.392 8."
        "337.319 7.46.048a2.096 2.096 0 0 0-.585-.041Zm.293 1.402c.248.197.523.759.682 1."
        "388.03.113.06.244.069.292.007.047.026.152.041.233.067.365.098.76.102 1.24l.002.4"
        "75-.12.175-.118.178h-.278c-.324 0-.646.041-.954.124l-.238.06c-.033.007-.038-.003"
        "-.057-.144a8.438 8.438 0 0 1 .016-2.323c.124-.788.413-1.501.696-1.711.067-.05.07"
        "9-.049.157.013zm9.825-.012c.17.126.358.46.498.888.28.854.36 2.028.212 3.145-.019"
        ".14-.024.151-.057.144l-.238-.06a3.693 3.693 0 0 0-.954-.124h-.278l-.119-.178-.11"
        "9-.175.002-.474c.004-.669.066-1.19.214-1.772.157-.623.434-1.185.68-1.382.078-.06"
        "2.09-.063.159-.012z"
    ),
}


def guess_icon(tech, store):
    """The logo a box gets when the call does not name one. Only a technology has one."""
    t = (tech or "").lower()
    rules = ((store and "postgres" in t, "postgresql"),
             # retrieval embeds with ollama, but is not ollama
             (("pgvector" in t and "ollama" in t) or "retrieval" in t, None),
             ("python" in t, "python"), ("llama" in t or t == "ollama", "ollama"),
             ("fastapi" in t, "fastapi"))
    for hit, icon in rules:
        if hit:
            return icon
    return None


def glyph(x, y, icon, colour):
    """A 20px technology logo from BRANDS."""
    return (f'<g transform="translate({x},{y}) scale({20 / 24:.4f})">'
            f'<path d="{BRANDS[icon]}" fill="{colour}"/></g>')


def node_h(tech, lines):
    return 66 + (25 if tech else 0) + 24 * len(lines)


def node(a, x, y, w, name, tech=None, lines=(), accent=False, dash="", store=False,
         icon=None, docker=False, mono_lines=False):
    """One C4 element: the name, the technology in brackets, what it does.

    A box is a 3px outline in its colour: black for a part, red or green for a variant, and
    tinted inside with the same red or green. A box that is part of the running system is
    white; anything that is not — you, an outside registry, a job that has already exited —
    is grey (`dash` asks for that; the name is kept from when it meant a dashed edge).
    `store` adds the lid of a database. A technology's logo goes before the name, chosen
    from the technology unless `icon` names one; `docker` puts the whale in the top-right
    corner: this box runs as a Docker container. `mono_lines` sets the lines as code.
    """
    h = node_h(tech, lines) + (12 if store else 0)
    colour = accent if isinstance(accent, str) else (ACCENT if accent else None)
    roles = (["attack"] if colour == ACCENT else ["fix"] if colour == SAFE else [])
    edge = colour or EDGE
    a.append(frame(x, y, w, h, edge, ground(colour, bool(dash)),
                   roles + ["outside" if dash else "system"]))
    if store:
        a.append(f'<path d="M {x} {y + 16} H {x + w}" stroke="{edge}" stroke-width="1.5"/>')
    top = y + (52 if store else 38)
    logo = icon or guess_icon(tech, store)
    if logo:
        a.append(glyph(x + 16, top - 16, logo, colour or INK))
    a.append(sans(x + (44 if logo else 16), top, name, NAME, colour or INK, "700"))
    if docker:
        a.append(glyph(x + w - 36, y + (24 if store else 12), "docker", TECH).replace(
            "<g ", '<g class="badge-docker" ', 1))
    ty = top + 25
    if tech:
        a.append(sans(x + 16, ty, "[" + tech + "]", KIND, TECH))
        ty += 24
    for body in lines:
        a.append(text(x + 16, ty, body, DESC, MUTED, "400", MONO if mono_lines else SANS))
        ty += 24
    return h


def entity_h(rows):
    """The height `entity()` gives a table with this many columns."""
    return 90 + 22 * rows


def entity(a, x, y, w, name, columns, accent=False):
    """A table the way an ER diagram draws one: its name, a rule, then one row per column —
    the key on the left, the name, the type on the right.

    `columns` holds `(name, type, key)`, where key is "PK", "FK", "UQ", "PK FK" or "". A
    fourth item colours that column alone, red or green, where the figure is about it."""
    h = entity_h(len(columns))
    colour = accent if isinstance(accent, str) else (ACCENT if accent else None)
    roles = (["attack"] if colour == ACCENT else ["fix"] if colour == SAFE else []) + ["system"]
    edge = colour or EDGE
    a.append(frame(x, y, w, h, edge, ground(colour), roles))
    a.append(sans(x + 16, y + 35, name, NAME, colour or INK, "700"))
    a.append(sans(x + 16, y + 57, "[table]", KIND, TECH))
    a.append(f'<path d="M {x} {y + 70} H {x + w}" stroke="{edge}" stroke-width="1.5"/>')
    for i, column in enumerate(columns):
        column_name, kind, key = column[:3]
        tint = column[3] if len(column) > 3 else None
        ry = y + 94 + 22 * i
        if key:
            a.append(sans(x + 16, ry, key, 13, TECH, "700"))
        a.append(mono(x + 64, ry, column_name, 15, tint or INK, "700" if tint else "400"))
        a.append(text(x + w - 16, ry, kind, 14, tint or MUTED, "400", MONO, "end"))
    return h


def zone(a, x, y, w, h, label, dash=""):
    """The system boundary: a 2px black frame around the parts it holds, with its name
    above. The one dashed line on a sheet is the trust boundary, so this one is solid."""
    a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}"'
             f' stroke="{LINE}" stroke-width="2"/>')
    heading(a, x, y - 10, label)


def boundary(a, x, y1, y2, label="Trust boundary"):
    """The trust boundary: the one dashed line on a sheet, with its name centred above it."""
    a.append(line(x, y1, x, y2, LINE, 1.5).replace("/>", ' stroke-dasharray="6 5"/>'))
    heading(a, x - sans_w(label, HEADING, True) / 2, y1 - 10, label)


def arrow(a, points, label=None, colour=LINE, dash="", above=True, head="to",
          at=None, tech=None):
    """A labelled edge. In this notation no arrow is unlabelled: it says what travels
    over it, and — where that matters — how, in brackets underneath."""
    pts = " ".join(f"{px},{py}" for px, py in points)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    marker = {LINE: "to", INK: "to-ink", ACCENT: "to-accent",
              SAFE: "to-safe"}.get(colour, head)
    weight = 3.5 if colour in (ACCENT, SAFE) else 2.5
    a.append(f'<polyline points="{pts}" fill="none" stroke="{colour}"'
             f' stroke-width="{weight}"{da} marker-end="url(#{marker})"/>')
    if not label:
        return
    if at:
        lx, ly = at
    else:
        (x1, y1), (x2, y2) = points[0], points[-1]
        if abs(y2 - y1) > abs(x2 - x1):
            lx, ly = max(x1, x2) + 10, (y1 + y2) / 2 + 4
        else:
            lx = round((x1 + x2) / 2 - sans_w(label, LABEL) / 2, 2)
            ly = min(y1, y2) + (-10 if above else 22)
    a.append(sans(lx, ly, label, LABEL, colour))
    if tech:
        a.append(sans(lx, ly + 17, "[" + tech + "]", 13.5, TECH))


def key(a, y, body, x=M):
    """One quiet row above the caption: only the marks this sheet uses — the three kinds
    of box, red and green (as a box when a box carries the colour, as a line when only an
    arrow or a run of code does), the trust boundary, the Docker badge on a container (not
    the logo of Docker Hub, which is a registry). Each is shown with
    the real mark, not described. Nothing is drawn when the sheet uses none of them."""
    items = []
    if "frame-system" in body:
        items.append(("the system", "box", FILL, EDGE))
    if "frame-outside" in body:
        items.append(("outside it", "box", OUT, EDGE))
    for role, colour, label in (("attack", ACCENT, "attack path"), ("fix", SAFE, "the fix")):
        if f"frame-{role}" in body:
            items.append((label, "box", ground(colour), colour))
        elif colour in body:
            items.append((label, "line", None, colour))
    if 'stroke-dasharray="6 5"' in body:
        items.append(("trust boundary", "boundary", None, LINE))
    if "badge-docker" in body:
        items.append(("runs in Docker", "docker", None, TECH))
    if not items:
        return False
    g = ["<!-- key -->", '<g class="key">']
    for label, kind, fill, colour in items:
        if kind == "box":
            g.append(frame(x, y, 28, 18, colour, fill))
        elif kind == "line":
            g.append(line(x, y + 9, x + 28, y + 9, colour, 3))
        elif kind == "boundary":
            g.append(line(x + 14, y, x + 14, y + 18, colour, 1.5).replace(
                "/>", ' stroke-dasharray="6 5"/>'))
        else:
            g.append(glyph(x + 4, y - 1, "docker", colour))
        g.append(sans(x + 38, y + 15, label, 17, MUTED))
        x += 38 + sans_w(label, 17) + 40
    g += ["</g>", "<!-- /key -->"]
    a.append(NL.join(g))
    return True


def pulse(points, colour=ACCENT, seconds=7):
    """A dot that travels a request's path, the only thing that moves on any sheet.

    Insert it under the boxes: inside a box it is hidden, so it shows only on the arrows
    between them. At rest it sits at the first point, inside the first box, so a still copy
    of the sheet shows nothing. It is not drawn for a reader who asked for less motion."""
    x0, y0 = points[0]
    d = "M" + " L".join(f"{x - x0},{y - y0}" for x, y in points)
    return (f'<g class="pulse" transform="translate({x0},{y0})">'
            "<style>@media (prefers-reduced-motion: reduce) { .pulse { display: none } }</style>"
            f'<circle r="9" fill="{colour}" opacity="0.18"/><circle r="4" fill="{colour}"/>'
            f'<animateMotion dur="{seconds}s" repeatCount="indefinite" path="{d}"'
            ' keyPoints="0;1;1" keyTimes="0;0.8;1" calcMode="linear"/></g>')


def fork(a, start, bus, ends, colours=None, down=False):
    """One edge that splits into several, the way an org chart does: a trunk from `start`
    to the bus, the bus across, and an arrow from the bus to each end. Every segment is
    horizontal or vertical. `down` turns it on its side: the trunk drops to y=`bus` and the
    branches drop from it. `colours` gives each branch its own colour."""
    colours = colours or [LINE] * len(ends)
    sx, sy = start
    if down:
        a.append(line(sx, sy, sx, bus, LINE, 2.5))
        xs = [sx] + [x for x, _ in ends]
        a.append(line(min(xs), bus, max(xs), bus, LINE, 2.5))
        for (ex, ey), c in zip(ends, colours, strict=True):
            arrow(a, [(ex, bus), (ex, ey)], None, c)
    else:
        a.append(line(sx, sy, bus, sy, LINE, 2.5))
        ys = [sy] + [y for _, y in ends]
        a.append(line(bus, min(ys), bus, max(ys), LINE, 2.5))
        for (ex, ey), c in zip(ends, colours, strict=True):
            arrow(a, [(bus, ey), (ex, ey)], None, c)


def masthead(label, route, field, payload, extra, variants, aria=None):
    """The banner at the top of a service README — one scene of the landing page's.

    It is deliberately **not** drawn in this manual's style: a banner sits on the
    reader's page rather than on a sheet, so it has no background and uses mid-tones that
    hold up on a light and on a dark theme, exactly like `docs/assets/banner.py`. The payload
    types itself in and the two routes answer; the finished frame is the base state, so
    without SMIL, or with `prefers-reduced-motion`, the picture is still complete.

    `variants` is a pair of `(name, colour, code, status, outcome)`.
    """
    mono_f = MONO
    muted, faint, wire = "#8b949e", "#b1bac4", "#6e7681"
    vuln, safe, accent = "#e5534b", "#3fb950", "#6cb6ff"
    w, h = 1200, 350
    pw = round(len(payload) * 0.62 * 15, 1)

    def t(x, y, body, size=12, fill=muted, weight="400", anchor="start", font=mono_f):
        return text(x, y, body, size, fill, weight, font, anchor)

    def card(x, y, cw, ch, stroke=wire):
        return (f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="none"'
                f' stroke="{stroke}" stroke-width="1.3" stroke-opacity="0.55"/>')

    a = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}"'
         f' height="{h}" role="img" aria-label="{esc(aria or label)}">',
         "<style>@media (prefers-reduced-motion: reduce){animate{display:none}}</style>",
         '<defs><marker id="bar" viewBox="0 0 8 8" refX="7.2" refY="4" markerWidth="6.5"'
         f' markerHeight="6.5" orient="auto-start-reverse"><path d="M0,0.8 L7.6,4 L0,7.2 z"'
         f' fill="{wire}"/></marker></defs>',
         t(1160, 44, label, 13, faint, "600", "end"),
         card(40, 110, 330, 140),
         t(62, 140, route, 11.5, faint, "500", font=mono_f),
         f'<path d="M 62 154 H 348" stroke="{wire}" stroke-width="1" opacity="0.3"/>',
         t(62, 186, field, 12, muted, font=mono_f),
         f'<clipPath id="mh"><rect x="158" y="168" height="26" width="{pw}">'
         f'<animate attributeName="width" dur="11s" repeatCount="indefinite"'
         f' values="0;0;{pw};{pw};{pw}" keyTimes="0;0.04;0.22;0.94;1"/></rect></clipPath>',
         f'<g clip-path="url(#mh)">{t(160, 186, payload, 15, accent, "700", font=mono_f)}</g>',
         t(62, 212, extra, 12, muted, font=mono_f),
         t(62, 238, "one request, sent to both routes", 10.5, faint)]

    for path in ("M 372 168 C 486 168 486 142 594 142",
                 "M 372 200 C 486 200 486 274 594 274"):
        a.append(f'<path d="{path}" fill="none" stroke="{wire}" stroke-width="1.3"'
                 f' stroke-dasharray="5 5" opacity="0.5" marker-end="url(#bar)"/>')

    for y, (name, which, code_line, status, outcome) in zip((92, 224), variants,
                                                            strict=True):
        colour = vuln if which == "vulnerable" else safe
        a.append(card(600, y, 560, 100, colour))
        a.append(t(622, y + 32, name, 15, colour, "700", font=mono_f))
        a.append(t(622, y + 58, code_line, 11.5, muted, font=mono_f))
        for begin, piece in ((0.40, f'<rect x="1010" y="{y + 14}" width="132" height="34"'
                                    f' rx="17" fill="{colour}" fill-opacity="0.12"'
                                    f' stroke="{colour}" stroke-width="1.2"'
                                    f' stroke-opacity="0.5"/>'
                                    + t(1076, y + 37, status, 16, colour, "700", "middle",
                                        mono_f)),
                             (0.46, t(622, y + 80, outcome, 11.5, colour, "500"))):
            a.append(f'<g opacity="1"><animate attributeName="opacity" dur="11s"'
                     f' repeatCount="indefinite" values="0;0;1;1;0" keyTimes="0;{begin};'
                     f'{begin + 0.05};0.94;1"/>{piece}</g>')

    a.append("</svg>")
    return NL.join(a)


def render(here, sheets):
    """Write every figure next to `diagrams.py` and say what was written."""
    for name, svg in sheets:
        (Path(here) / f"{name}.svg").write_text(svg + NL, encoding="utf-8", newline=NL)
        print(f"wrote {name}.svg")
# --- end house style -------------------------------------------------------------------


W = 1100
SYSTEM = "sqli-demo"
Q = chr(34)   # a double quote, so the figures can show quoted code


# --------------------------------------------------------------------------
# C4 level 3 — where the submitted value goes
# --------------------------------------------------------------------------
def flow():
    a = figure(W, f"Component diagram for the {SYSTEM} container",
               "A C4 component view of one login request. The router, the use case and the"
               " port are shared; only the adapter below them changes.")
    under = len(a)                    # the travelling dot goes beneath every box
    # three equal columns, the same grid as every other sheet: left, centre, right
    left, centre, right = M, 399, 742
    a.append(mono(M, 192, "POST /api/v1/{variant}/auth/login", LABEL, ACCENT))

    # row 1 — the request comes in and reaches the use case
    top = 212
    hy = node(a, left, top, 302, "you", "Bruno", accent=True, dash="4 3")
    node(a, centre, top, 302, "routers/auth.py", "FastAPI")
    node(a, right, top, 302, "use_cases/login.py", "application")
    mid = top + hy // 2
    arrow(a, [(362, mid), (395, mid)], None, ACCENT)
    arrow(a, [(705, mid), (738, mid)], None)

    # row 2 — the port, straight under the use case that calls it
    port = top + hy + 48
    hp = node(a, right, port, 302, "Authenticator", "port")
    arrow(a, [(893, top + hy + 4), (893, port - 4)], None)

    # row 3 — the two adapters on the outside, the database between them
    bus = port + hp + 40
    row = bus + 52
    ha = node(a, left, row, 302, "VulnerableSqlAuthenticator", "adapter, psycopg", accent=True)
    node(a, right, row, 302, "SafeSqlAuthenticator", "adapter, psycopg", accent=SAFE)
    fork(a, (893, port + hp), bus, [(207, row - 4), (893, row - 4)], [ACCENT, SAFE], down=True)
    a.append(mono(217, bus + 32, "variant=vulnerable", LABEL, ACCENT))
    a.append(mono(903, bus + 32, "variant=safe", LABEL, SAFE))

    level = row + ha // 2
    hd = node_h("PostgreSQL 18", []) + 12          # a store is taller by its lid
    node(a, 465, level - hd // 2, 170, "sqli-db", "PostgreSQL 18", store=True)
    arrow(a, [(362, level), (461, level)], None, ACCENT)
    a.append(sans(411.5 - sans_w("as SQL", LABEL) / 2, level - 10, "as SQL", LABEL, ACCENT))
    arrow(a, [(738, level), (639, level)], None, SAFE)
    a.append(sans(688.5 - sans_w("as a value", LABEL) / 2, level - 10, "as a value", LABEL,
                  SAFE))
    # the request's whole way, from you to the table, along the vulnerable variant
    a.insert(under, pulse([(207, mid), (550, mid), (893, mid), (893, bus), (207, bus),
                           (207, level), (550, level)]))
    return caption(a, W, 3, "level 3 — the components one request passes through",
                   "presentation/routers/auth.py, container.py")


# --------------------------------------------------------------------------
# C4 level 2 — what runs, and what the host can reach
# --------------------------------------------------------------------------
def architecture():
    a = figure(W, f"Container diagram for {SYSTEM}",
               "A C4 container view: every element names the technology it is built on,"
               " and every arrow names what travels over it.")
    under = len(a)
    top = 232
    hy = node(a, M, top, 180, "you", "Bruno", dash="4 3")
    node(a, 372, top, 300, "sqli-demo", "FastAPI, uvicorn", accent=True, docker=True)
    node(a, 712, top, 300, "sqli-seed", "Python, one-off", dash="4 3", docker=True)
    low = top + hy + 70
    hd = node(a, 372, low, 300, "sqli-db", "PostgreSQL 18", store=True, docker=True)

    panel = []
    zone(panel, 340, 196, 704, low + hd + 36 - 196, SYSTEM)
    a[under:under] = panel
    boundary(a, 268, 176, low + hd + 56)

    mid = top + hy // 2
    arrow(a, [(240, mid), (368, mid)], "attacks", ACCENT, at=(276, mid - 10))
    arrow(a, [(522, top + hy + 4), (522, low - 4)], "SQL", at=(536, top + hy + 38))
    arrow(a, [(862, top + hy + 4), (862, low + hd // 2), (676, low + hd // 2)], "seeds",
          at=(744, low + hd // 2 - 10))
    return caption(a, W, 2, "level 2 — containers, their technologies and the one way in",
                   "compose.yaml")


# --------------------------------------------------------------------------
# C4 level 4 — the code behind the two components
# --------------------------------------------------------------------------
def code_level():
    a = figure(W, "Code diagram for the Authenticator port",
               "One Protocol, two classes. Everything above this level is identical for"
               " both variants; the difference is the statement each one builds.")
    top = 196
    hp = node(a, 372, top, 356, "Authenticator", "typing.Protocol",
              ["authenticate(username, password)"], mono_lines=True)
    row = top + hp + 70
    hc = node(a, M, row, 420, "VulnerableSqlAuthenticator", "infrastructure.auth", accent=True)
    node(a, 624, row, 420, "SafeSqlAuthenticator", "infrastructure.auth", accent=SAFE)
    mid = top + hp // 2
    arrow(a, [(266, row - 4), (266, mid), (368, mid)], "implements", at=(276, row - 24))
    arrow(a, [(834, row - 4), (834, mid), (732, mid)], "implements", at=(844, row - 24))

    rule_y = row + hc + 40
    a.append(line(M, rule_y, W - M, rule_y, EDGE, 1))
    # the one line the two classes disagree on, one under the other at the same size, so
    # `conn.execute(` lines up and the eye goes straight to what follows it
    for i, (rest, colour) in enumerate(((f"f{Q}… '{{username}}'{Q}", ACCENT),
                                        ("_AUTHENTICATE, (username, password)", SAFE))):
        y = rule_y + 44 + i * 52
        spans = code(a, M, y, [("conn.execute(", None), (rest, colour), (")", None)], 19)
        underline(a, spans[1], y + 12, colour)
    return caption(a, W, 4, "level 4 — the one method the two classes implement",
                   "domain/ports/authenticator.py, infrastructure/auth/")

# --------------------------------------------------------------------------
# The database — the grant that decides what a successful injection is worth
# --------------------------------------------------------------------------
def database():
    a = figure(W, "What each account may read",
               "The vulnerable adapter connects as an account that can read the secrets"
               " table; the safe one cannot see it at all.")
    # roles on the right, 24px apart; the two tables on the left share their top and bottom
    top, gap = 200, 24
    roles = {}
    for i, (name, who, colour) in enumerate((("lab_admin", "the seed job only", False),
                                             ("lab_app", "the safe adapter", SAFE),
                                             ("lab_legacy", "the vulnerable adapter", True))):
        y = top + i * (node_h("role", [who]) + gap)
        roles[name] = (y, node(a, 700, y, 344, name, "role", [who], accent=colour))
    entity(a, M, top, 400, "users", [("id", "uuid", "PK"), ("username", "text", "UQ"),
                                     ("email", "text", ""), ("role", "text", ""),
                                     ("password_hash", "text", "")])

    def mid(name):
        y, hh = roles[name]
        return y + hh // 2

    # secrets sits level with lab_legacy, so the red SELECT runs straight across
    out = mid("lab_legacy")
    entity(a, M, out - entity_h(3) // 2, 400, "secrets",
           [("id", "uuid", "PK"), ("name", "text", ""), ("value", "text", "")], accent=True)

    # three ways into users, 24px apart, each with a channel of its own so no two cross
    e1, e2, e3 = mid("lab_admin"), mid("lab_admin") + 24, mid("lab_admin") + 48
    arrow(a, [(696, e1), (460, e1)], "owns", at=(560, e1 - 10))
    arrow(a, [(696, mid("lab_app")), (600, mid("lab_app")), (600, e2), (460, e2)],
          "SELECT", SAFE, at=(610, mid("lab_app") - 10))
    arrow(a, [(696, out - 32), (540, out - 32), (540, e3), (460, e3)], "SELECT",
          at=(610, out - 42))
    arrow(a, [(696, out), (460, out)], "SELECT", ACCENT, at=(470, out - 10))
    return caption(a, W, 5, "the UNION payload reads secrets because one grant allows it",
                   "infrastructure/persistence/seed.py")


# --------------------------------------------------------------------------
# C4 level 1 — who uses it, and what it reaches outside itself
# --------------------------------------------------------------------------
def context():
    system, purpose = SYSTEM, ['login API', 'vulnerable and safe']
    sources = [  # (name, what kind of system it is, what is pulled from it, icon)
        ('Docker Hub', 'container registry', 'python, postgres images', 'docker'),
        ('ghcr.io', 'container registry', 'the uv binary', 'github'),
        ('PyPI', 'package index', 'Python packages', 'python'),
    ]
    # three columns mirrored about the centre of the sheet: you | system | registries,
    # one trust boundary in each gap, the same distance from the system on both sides
    top, gap, hb = 200, 24, node_h("kind", ["what"])
    bottom = top + len(sources) * (hb + gap) - gap
    a = figure(W, f"System context diagram for {system}",
               "A C4 system context: the demo as one box, the person who drives it, and"
               " the public registries it pulls from.")
    ends = []
    for i, (name, kind, what, icon) in enumerate(sources):
        y = top + i * (hb + gap)
        node(a, 814, y, 230, name, kind, [what], dash="4 3", icon=icon)
        ends.append((810, y + hb // 2))
    centre = (ends[0][1] + ends[-1][1]) // 2
    hs = node_h("software system", purpose)
    node(a, 420, centre - hs // 2, 260, system, "software system", purpose, icon="fastapi")
    node(a, M, centre - hb // 2, 230, "you", "learner, attacker", ["Bruno"],
         dash="4 3")
    for bx in (360, 740):
        boundary(a, bx, top - 20, bottom + 20)
    heading(a, 814, top - 10, "Public registries")
    arrow(a, [(290, centre), (416, centre)], "attacks", ACCENT, at=(293, centre - 10))
    a.append(sans(692, centre - 10, "pulls", LABEL, LINE))
    fork(a, (684, centre), 776, ends)
    return caption(a, W, 1, "level 1 — the system, its user, and what it pulls from",
                   "compose.yaml, Dockerfile")


if __name__ == "__main__":
    render(Path(__file__).parent, [
        ("c3-components", flow()),
        ("c1-context", context()),
        ("c2-containers", architecture()),
        ("c4-code", code_level()),
        ("database", database()),
    ])

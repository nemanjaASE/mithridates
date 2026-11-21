---
name: house-style-figures
description: Draw, change or check the SVG figures of sqli-demo and promptinj-demo — the C4 levels 1–4, the database figure and the annotated code figures of the write-ups — in the repository's house style. Use when editing a demo's docs/diagrams.py, regenerating its SVGs, starting a new demo's figures in the same look, or checking figures for overlaps, alignment and contrast.
---

# House-style figures

The figures of `sqli-demo` and `promptinj-demo` are generated, never drawn by hand. Each
demo's `docs/diagrams.py` carries a copy of the house style and draws every SVG in its
`docs/` folder. This skill holds the style, the tools around it and the rules behind it.

The style is **not** a rule for contributors. The only rule they follow is the C4 model
(`CONTRIBUTING.md`); a new demo may draw its figures with any tool. Use this skill for the
demos that already use the style, or for a new one whose author wants the same look.

## Files

| File | What it is |
| --- | --- |
| `diagram_style.py` | the house style — palette, type, `node()`, `entity()`, `arrow()`, `fork()`, `zone()`, `boundary()`, `pulse()`, `key()`, `figure()`, `caption()`. The block between the `# --- house style` markers is what each demo copies. Run it to redraw `figure-kit.svg`. |
| `figure-kit.svg` | every part, with the call that draws it |
| `new_figures.py` | `python .claude/skills/house-style-figures/new_figures.py <topic>-demo` writes a demo's `docs/diagrams.py` with the style copied in and C1–C4 drawn with placeholder names |
| `check_figures.py` | the checks: copies identical, geometry, rhythm, contrast, no name shadowing |

## Change a figure

1. Edit the figure's function in `demos/<demo>/docs/diagrams.py` — below the copied block, never
   inside it.
2. `python demos/<demo>/docs/diagrams.py` — redraws every SVG of that demo.
3. `python .claude/skills/house-style-figures/check_figures.py` — must end in `all passed`.
4. `uv run --no-project --with pyyaml python scripts/check_repo.py` — the repository rules.

Never edit an SVG by hand: the next run of `diagrams.py` overwrites it and the edit is
gone.

## Change the style itself

Edit `diagram_style.py` here, then copy the block between the markers into every
`demos/<demo>/docs/diagrams.py` that has one, byte for byte, and redraw. `check_figures.py`
fails while any copy differs.

## How a figure is built

Say what a thing *is*; the style decides how it looks.

| You mean | You write |
| --- | --- |
| a part of the running system | `node(a, x, y, w, "name", "technology")` |
| outside the system, or already gone | `node(..., dash="4 3")` |
| on the attack path / the fix | `node(..., accent=True)` / `node(..., accent=SAFE)` |
| a database / a container | `node(..., store=True)` / `node(..., docker=True)` |
| a table with its columns, ER style | `entity(a, x, y, w, "name", [(column, type, key)])` |
| what travels between two boxes | `arrow(a, points, "label")`, red with `ACCENT`, green with `SAFE` |
| one edge that splits in two | `fork(a, start, bus, ends, colours, down=True)` |
| the system boundary / the trust boundary | `zone(a, x, y, w, h, "label")` / `boundary(a, x, y1, y2)` |
| one line of real source, annotated | `code(a, x, y, [(text, colour)])` and `underline(...)` |
| the request's path, moving | `pulse(points)`, inserted beneath the boxes |

A figure opens with `figure(W, eyebrow, title, description)` and closes with
`caption(a, W, number, what, source)`. Do not set a height or a key: `caption()` measures
the drawing, draws the key for exactly the marks on the sheet, and sizes the sheet.

## The rules

- **C4 for structure.** Context, containers, components, code, in that order in the
  README; a database figure where there is one; annotated code figures in the write-up.
- **Grid.** Margin 56px. Three columns at x = 56, 399, 742 (302 wide) or four at 56, 310,
  564, 818 (226 wide); the gutter widens only where an arrow has to carry a label.
- **Right angles.** Arrows leave and enter a box at its centre, horizontal or vertical
  only; one edge that splits is a `fork()`.
- **Nothing touches.** No label on a line, across a box edge, into the caption or off the
  sheet; boxes 16px apart; the drawing ends 40px above the key, the key 40px above the
  caption.
- **Colour only where it means something.** Red is the attack and the code it gets
  through, lime the fix; everything else is grey. A value keeps its colour through a figure.
- **Boxes are marked by their corners** — a dark inset, a faint outline, four 14px brackets
  in the box's colour. Tone separates the system (darkest) from what is outside it.
- **The only dashed line is the trust boundary.**
- **Every figure carries its own key**, drawn by `caption()` from what is on the sheet.
- **One thing moves**: the `pulse()` dot on the vulnerable path in C3, hidden for readers
  who ask for less motion.
- **As little text as it can bear.** A box is an icon, a name and `[technology]`; prose
  goes in the README around the figure, never inside it.

## Palette

| Role | Constant | Colour |
| --- | --- | --- |
| page | `PAPER` | `#252A33` |
| system panel | `PANEL` | `#1B1F26` |
| box in the system | `FILL` | `#0E1015` |
| box outside it | `OUT` | `#2F3540` |
| box outline / corners | `FRAME` / `EDGE` | `#2A2F38` / `#8F98AA` |
| text / labels | `INK` / `MUTED` | `#E0E6F0` / `#AAB2C2` |
| `[technology]`, heading | `TECH` | `#9AA3B4` |
| lines and arrows / faint rules | `LINE` / `HAIR` | `#9DA6B7` / `#3F4552` |
| attack / fix | `ACCENT` / `SAFE` | `#E08585` / `#9FEF00` |

Text sizes `NAME, KIND, DESC, LABEL, CAPS = 17, 13.5, 15, 15, 14`; one monospaced face throughout. Text
holds 4.5:1 on every ground and lines 3:1 — `check_figures.py` measures it.

## Pitfalls

- Do not name anything in figure code after the style (`NAME`, `LABEL`, `CAPS`, …): it
  silently replaces the style's value. `check_figures.py` refuses it.
- The Docker *badge* (`docker=True`) means "runs as a container"; the Docker Hub *icon* on
  a registry box is not one, and the key tells them apart.
- `docs/assets/banner.py` at the root draws the README banner in its own palette; it is not part
  of this style.
- The README headings of both demos carry an icon from `docs/assets/icons/` — the same line style
  (20px drawing, 1.6px round strokes) in GitHub's mid grey `#8B949E`, which reads on the
  light and the dark theme. Each SVG has 6px of empty space on its right, so the heading is
  written with no space before the text, and its anchor stays `#running-it`:

```markdown
## <img src="../../docs/assets/icons/play.svg" width="30" height="23" alt="">Running it
```

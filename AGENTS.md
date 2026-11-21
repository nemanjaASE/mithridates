# AGENTS.md

Instructions for AI coding agents working in this repository. People start with
[`README.md`](README.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## The repository

- A teaching lab of deliberately vulnerable demos, `demos/<topic>-demo/`, each shipping the
  attack twice: a vulnerable variant and a fixed one. Keep it that way — the vulnerable
  code is the point, not a bug to fix.
- Everything binds to `127.0.0.1`. Never publish a port on `0.0.0.0`, never add real
  credentials or customer data, never add anything useful only for attacking third parties.
- Everything written into the repository is in English.
- A new demo starts with `python scripts/new_demo.py <topic> --title "<Attack name>"`;
  what is left for the author is marked `TODO(attack)`, and `check_repo.py` fails until
  every marker is gone.

## Before you finish

- `uv run --no-project --with pyyaml python scripts/check_repo.py` — the repository rules.
- `uvx --from 'ruff>=0.14,<0.15' ruff check scripts docs`, and `uv run ruff check .` in
  every demo you touched.
- A pull request title follows Conventional Commits, with the types and scopes in
  `CONTRIBUTING.md`: `python scripts/check_pr.py "<title>"`.

## Figures

- Every demo's README shows the four C4 levels in `## How it works`. That is the only rule
  for figures; how they are drawn is up to the demo.
- `sqli-demo` and `promptinj-demo` draw theirs with `docs/diagrams.py` in the house style.
  Never edit their SVGs by hand: change `diagrams.py` and run it, or the next run quietly
  undoes the edit.
- The house style — its design, tools and checks — is the skill in
  [`.claude/skills/house-style-figures/`](.claude/skills/house-style-figures/SKILL.md). Read its `SKILL.md` before changing
  those figures or drawing new ones in the same look.

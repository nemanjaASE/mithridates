# Template for a service README

Every demo's README answers the same questions in the same order, so a reader who has
been through one demo already knows where to look in the next. This file is the contract;
[`demos/sqli-demo/README.md`](../../demos/sqli-demo/README.md) and
[`demos/promptinj-demo/README.md`](../../demos/promptinj-demo/README.md) are the two worked examples.

The order follows the reader's path: *what is this → how do I run it → what do I try →
how does it work → what is it made of → how is it configured → how do I know it works →
what do I do when it breaks.*

`scripts/check_repo.py` checks that the required headings are present and in order, so a
missing section fails CI rather than review.

---

## Section order

| # | Section | Required | What goes in it |
|---|---------|----------|-----------------|
| 1 | `# <topic>-demo` | yes | The folder name as the title, then a centred row of technology badges and the deliberately-vulnerable warning. No banner, and no tagline that `## What this service does` is about to repeat. |
| 2 | `## What this service does` | yes | What it does and to whom, then the warning. Sub-sections only if the demo has more than one feature. |
| 3 | `## Technology` | yes | A two-column table, the same shape the root README uses: language, API, database, anything the demo is built on, packaging, verification. Facts only — no badges. |
| 4 | `## Running it` | yes | Prerequisites, one command, a check that it worked, how to stop it, the two URLs. |
| 5 | `## The attack, step by step` | yes | The payloads, in order, with what each one returns. One sub-section per feature. |
| 6 | `## How it works` | yes | The four C4 levels in order — context, containers, components, code — each with a one-line lead-in. The container table and the hardening table — setting, what it means, what an attacker cannot do — sit under level 2; the variant table closes the section. |
| 7 | `## The database` | when it has one | The schema diagram, and who is allowed to read what. |
| 8 | `## Configuration` | yes | Every environment variable with its real default, then `### Accounts`. |
| 9 | `## Verification` | yes | The Bruno folders, what each proves, and the lint command. |
| 10 | `## Troubleshooting` | yes | Symptom → cause and what to do. Only problems actually hit. |
| 11 | the footer | yes | The write-up and the lab overview. |

A demo with something genuinely its own — a protocol, a data model, a scheduler — adds one
more `##` section for it, after **How it works**. It does not reorder the rest.

**The sections stay flat.** `### Accounts` under **Configuration** is the only sub-heading
in the file. A demo with two features does not give each one a sub-section: they are one
sequence in **The attack, step by step**, numbered through, because a reader following the
attack should not have to pick which half applies to them.

---

## Rules per section

**2 — What this service does.** The first sentence says what the service does, not what it
is built with. Then who the attacker is and what they are after. The deliberate
vulnerability is already stated in the masthead, so it is not repeated here.

**3 — Running it.** Prerequisites in one sentence, including what the first run downloads
and how long it takes. Then the command. Then a **check** — a concrete call, the expected
output, and what it looks like when it is wrong; without that the reader cannot tell
whether the demo works. Then how to stop it, including the variant that deletes the data. The collection in `bruno/` is how a reader exercises the service, so the section does not list URLs.

**4 — The attack, step by step.** Numbered payloads with the response each one produces,
the same payloads against both variants. Where the outcome is not deterministic, say what
to look at instead — a trace field, a scope, a decision — and why the text of the answer
is not evidence.

**5 — How it works.** The four C4 levels, each with a figure, then a table with one row per
thing that differs between the variants. If the whole difference is one adapter, the table shows
exactly that and nothing more.

**8 — Configuration.** First, how to change a value: copy `.env.example`, which sits next
to `compose.yaml`, to `.env` in the same folder. Then variable, default, what it does. The
default is the one in the code, not the one compose passes — where they differ, say so.
Bold the switches that would be a vulnerability in a real application.

**9 — Verification.** One row per Bruno folder. The last line is the lint command.

**10 — Troubleshooting.** Only problems you have actually hit. An invented table of errors
is noise. The symptom is worded the way the reader will see it.

---

## Figures

**Follow the C4 model; draw it however you like.** Every README shows its demo at the four
levels of the C4 model — context, containers, components, code — in `## How it works`, in
that order, each with a one-line lead-in and a figure. The tool, the style and the format
are up to you. `scripts/check_repo.py` checks only that the four levels are there, in
order, each with a figure, and that every figure the README links to exists.

| Level | What it shows |
| --- | --- |
| 1 — context | the system as one box, who uses it, and what it depends on outside itself |
| 2 — containers | what runs, what each part is built on, and the one way in |
| 3 — components | what one request passes through inside the container, and where the two variants part |
| 4 — code | the interface, the classes that implement it, and the line they disagree on |

A demo with a database adds a schema figure under `## The database`. A figure built around
a line of source belongs in the write-up, next to the analysis that needs it.

## What does not go in a README

- A directory tree, or a description of the layers — both drift away from the code within
  a week.
- A diagram narrated in prose.
- Attack classification (OWASP Top 10, CWE, CVSS, CIA). That belongs in `docs/writeups/NN-*.md`; this file
  answers "how do I run it and what should I try".
- A change history. That is what `git log` is for.
- Anything already in the root README. Link to it instead.

## Tone

Short statements. Numbers instead of adjectives: "~2 GB", not "large". No paragraph longer
than five lines. If a sentence can be removed without loss, remove it.

---

## Starting a README

Do not write it from scratch. `scripts/new_demo.py` generates a README with every section
above in order, the parts every demo shares already filled in, and `TODO(attack)` where the
demo's own text goes. Its template is
[`scripts/demo_template/README.md`](../../scripts/demo_template/README.md); a change to the
sections belongs in this file and in that template together.

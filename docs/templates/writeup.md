# Template for an attack write-up

Every demo has one write-up in `docs/writeups/NN-<topic>.md`. This file is the contract;
[`01-sql-injection.md`](../writeups/01-sql-injection.md) and
[`02-llm-prompt-injection.md`](../writeups/02-llm-prompt-injection.md) are the two worked
examples.

The service README already says how to run the demo, which payloads to send and how to
verify it. The write-up answers only what the README does not: **what the attacker gets,
why it works, how it is fixed, and what the demo leaves out.** Four sections, in that
order, so a reader who has been through one write-up knows where to look in the next.

## Rules

- Write plainly; assume the reader is seeing this attack for the first time.
- Do not repeat the README. Link to its payloads and its verification instead.
- Explain the **cause**, not the symptom, and point at the file and the line where it lives.
- The classification table has four rows, and all four are required: **OWASP Top 10**,
  **CWE**, **CVSS v4.0** and **CIA**. The glossary in [`docs/README.md`](../README.md#glossary)
  explains them; `scripts/check_repo.py` checks that they are there.
- Compute the CVSS score, do not estimate it: answer the questions in
  [FIRST's CVSS v4.0 calculator](https://www.first.org/cvss/calculator/4.0) for the demo's
  scenario as if it were a real application on a network, and copy the score and the
  vector it gives. Link the vector to the calculator — its address followed by `#` and the
  vector — so a reader can open it with every answer already selected.
- Everything is written in English.

## Figures

A figure that explains a line of source belongs here, next to the argument that needs it:
the vulnerable line under **Why it works**, the fixed one under **The fix**. It sits in
`demos/<topic>-demo/docs/` and is referenced across the folder boundary:

```markdown
![<what it shows>](../../demos/<topic>-demo/docs/<name>.svg)
```

The structural figures — the four C4 levels and the schema — stay in the service README.

## A second feature

A demo that shows the same attack through a second feature — `promptinj-demo`'s tool agent
is one — may give it one more section, after **The fix**. It does not reorder the rest.

---

## Skeleton

Copy everything below to `docs/writeups/NN-<topic>.md` and fill it in. Delete each `<!-- -->`
instruction once its section is written.

# NN — <Attack name>

| | |
| --- | --- |
| **OWASP Top 10** | <e.g. A05:2025 – Injection, or LLM01:2025 – Prompt Injection> |
| **CWE** | <e.g. CWE-89: SQL Injection> |
| **CVSS v4.0** | <from https://www.first.org/cvss/calculator/4.0: score and severity, then the vector linked back to the calculator, and why — e.g. 9.3 Critical (illustrative) — [`CVSS:4.0/AV:N/…`](https://www.first.org/cvss/calculator/4.0#CVSS:4.0/AV:N/…): over the network, with no account> |
| **CIA** | <which of confidentiality, integrity and availability it breaks, and how> |

## The attack

<!-- What the attack is, in two or three sentences. What the attacker sends and what they
get, and what it could lead to beyond the demo. Link to the README's "The attack, step by
step" for the payloads one by one. -->

## Why it works

<!-- The cause, not the symptom: "code and data are mixed", "the input is trusted",
"no authorization check". Show the vulnerable line and what it turns the payload into. -->

## The fix

<!-- The primary measure and why it works, with the fixed line. Say whether it is a real
FIX (it removes the cause) or only a MITIGATION, and why. Then the extra layers, one or two
sentences each, each with the file it lives in. -->

## What this demo does not cover

<!-- What is deliberately left out, so the reader knows the boundaries and has topics to
discuss. -->

## References

<!-- Only sources you trust: the OWASP page for the category, an OWASP Cheat Sheet, the
CWE page, a paper if there is one. -->

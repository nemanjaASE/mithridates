# Lab documentation

This folder explains the attacks the lab demonstrates — rigorously, but in plain language.
Each attack has its own file: what the attacker gets, why it works, how it is fixed, and
what the demo leaves out.

> The code is **deliberately vulnerable** and exists solely for training in an isolated,
> local environment. Do not expose it on a network.

## What is in this folder

| Folder | What it holds | Who changes it |
| --- | --- | --- |
| [`writeups/`](writeups/) | one write-up per demo, `NN-<topic>.md` | a contributor adds one with each new demo |
| [`templates/`](templates/) | [`writeup.md`](templates/writeup.md) and [`demo-readme.md`](templates/demo-readme.md), the structure every demo follows | copied for a new demo, not edited for one; changed only when the convention changes |
| [`assets/`](assets/) | the logo (an SVG, and a PNG for the Bruno collections), the README banner, the wordmark and the Greek key in the README header, the social preview, the README heading icons, and the terminal screenshots in `terminal/`, drawn by [`terminal.py`](assets/terminal.py) | the maintainers |

## Contents

| # | Attack | Where it lives in the code | Service README |
|---|--------|----------------------------|----------------|
| [01](writeups/01-sql-injection.md) | **SQL injection** on a login endpoint | `demos/sqli-demo/` (`:8001`) | [`demos/sqli-demo/README.md`](../demos/sqli-demo/README.md) |
| [02](writeups/02-llm-prompt-injection.md) | **LLM prompt injection** on a customer-account assistant | `demos/promptinj-demo/` (`:8002`) | [`demos/promptinj-demo/README.md`](../demos/promptinj-demo/README.md) |

This list grows: one write-up per demo, added in the same pull request as the demo itself.

Both service READMEs follow [`templates/demo-readme.md`](templates/demo-readme.md), and every write-up
follows [`templates/writeup.md`](templates/writeup.md) — copy it to `docs/writeups/NN-name.md` and fill in the
sections. [`CONTRIBUTING.md`](../CONTRIBUTING.md) has the full checklist for adding a
demo.

## How to read the write-ups

Every write-up opens with a classification table — OWASP Top 10, CWE, CVSS and CIA,
explained in the [glossary](#glossary) — and then has the same four sections:
**The attack**, **Why it works**, **The fix** and **What this demo does not cover**.
Running the demo, the payloads one by one and the verification are in the demo's README,
so the write-up does not repeat them.

## Glossary

The four terms in the classification table every write-up opens with:

- **OWASP Top 10** — a periodically refreshed list of the ten most common or most serious
  categories of web application vulnerability, published by OWASP (the Open Worldwide
  Application Security Project, a non-profit community). The current edition is
  **Top 10:2025** (labels `A01:2025`–`A10:2025`). There is a separate list for
  applications built on language models — **OWASP Top 10 for LLM Applications 2025**
  (labels `LLM01:2025`–`LLM10:2025`).
- **CWE** (Common Weakness Enumeration) — a catalogue of *types* of software weakness,
  maintained by MITRE. Each type has a number, e.g. **CWE-89** is "SQL Injection". Where
  the OWASP Top 10 groups things into broad categories, CWE names the specific mistake.
- **CVSS** (Common Vulnerability Scoring System) — the standard for scoring the severity of
  a vulnerability on a 0–10 scale (Low/Medium/High/Critical). The current version is
  **4.0**; the score is computed from a vector such as `AV:N/AC:L/…`, which says how the
  attack is carried out and what it reaches. The scores in this documentation are
  *illustrative* — they depend on context.
- **CIA** — the three security properties an attack can break: **Confidentiality** (data
  is seen only by those allowed to see it), **Integrity** (data and actions are what they
  should be) and **Availability** (the system works when it is needed).

---

## Which guidelines are applied

The labels follow **OWASP Top 10:2025** (web) and **OWASP Top 10 for LLM Applications
2025**. The vulnerable adapters **deliberately** violate A05:2025 (Injection) and LLM01
respectively. Everything else follows the guidelines:

| Area | How it is applied |
|------|-------------------|
| A04/A07:2025 Passwords and authentication | Passwords stored only as a bcrypt hash (pgcrypto `crypt()` + `gen_salt('bf')`); verified in SQL via `crypt()`; never in plaintext |
| A05:2025 Injection | Parameterized queries; DDL in the seed job through `sql.Identifier`/`sql.Literal`; the application is never a superuser, and its accounts are read-only with only the privileges they need (least privilege) |
| A02:2025 Security Misconfiguration | Security HTTP headers (CSP, nosniff, X-Frame-Options…), no `Server` header, educational output switched on only through the environment |
| A10:2025 Mishandling of Exceptional Conditions | A generic response plus an `error_id`; details only in the log; a 422 does not echo the submitted input |
| A03/A08:2025 Supply chain and integrity | `uv.lock` + `uv sync --frozen`, pinned `uv` and base image versions |
| JWT | HS256 with a key of at least 256 bits from the environment, the algorithm fixed at verification (no `alg: none`), `exp`/`iat`/`nbf`/`iss`/`aud`/`sub` all required, a unique `jti`, a 15-minute lifetime |
| A09:2025 Security Logging | Audited login attempts, protection against log injection, passwords never logged |
| LLM05 Output handling | An output check (canary secret, hijack marker); the raw output hidden by default |
| LLM10 Consumption | A bounded document length and `max_tokens` |
| Containers | Every container a demo builds runs non-root and read-only, with `cap_drop: ALL` and `no-new-privileges`. Backing images are exempt only where they have to be — a database entrypoint that takes ownership of its data directory, a model server image that runs as root — and the demo's README names the exception. The database is on an `internal` network with no port to the host, and the admin password lives only in the seed container |

Deliberately not covered, so it stays a discussion topic: rate limiting and account
lockout, authentication of the APIs themselves, and allow-list input validation.

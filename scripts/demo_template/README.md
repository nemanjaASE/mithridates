# __NAME__

<p align="center">
  <img src="https://img.shields.io/badge/port-__PORT__-0a7ea4?style=flat-square" alt="port __PORT__">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
<!-- [postgres] -->
  <img src="https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL 18">
<!-- [/postgres] -->
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <b>⚠️ This code is deliberately vulnerable.</b> The port binds to <code>127.0.0.1</code>. Do not expose it on a network.
</p>

---

## <img src="../../docs/assets/icons/target.svg" width="30" height="23" alt="">What this service does

<!-- TODO(attack): what the feature does and for whom, who the attacker is, and what they are after. Two or three sentences. -->

---

## <img src="../../docs/assets/icons/layers.svg" width="30" height="23" alt="">Technology

| | |
| --- | --- |
| **Language** | Python 3.13, managed with [uv](https://docs.astral.sh/uv/) |
| **API** | FastAPI, Pydantic, PyJWT, bcrypt |
<!-- [postgres] -->
| **Database** | PostgreSQL 18, through psycopg |
<!-- [/postgres] -->
| **Packaging** | Docker Compose. The application runs as an ordinary user, cannot write to its own disk and has no root privileges |
| **Verification** | a [Bruno](https://www.usebruno.com/) collection in [`bruno/`](bruno/), plus [Ruff](https://docs.astral.sh/ruff/) and mypy |

---

## <img src="../../docs/assets/icons/play.svg" width="30" height="23" alt="">Running it

You need Docker with Compose. The first build downloads the base images and takes a few
minutes.

```bash
cd demos/__NAME__
docker compose up --build
```

Check that it works:

```bash
curl -s localhost:__PORT__/
```

The answer lists the endpoints. `Connection refused` means the service is not up yet, or
something else holds port `__PORT__`.

```bash
docker compose down
```

---

## <img src="../../docs/assets/icons/zap.svg" width="30" height="23" alt="">The attack, step by step

Log in first; every request below needs the token:

```bash
TOKEN=$(curl -s -X POST localhost:__PORT__/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana","password":"Ana#2026!"}' | jq -r .access_token)
```

<!-- TODO(attack): the payloads, numbered, and what each one returns on `vulnerable` and on `__safe__`. -->

| # | `input` | What happens on `vulnerable` |
| --- | --- | --- |
| 1 | | |

---

## <img src="../../docs/assets/icons/network.svg" width="30" height="23" alt="">How it works

<!-- TODO(attack): the four figures below are placeholders. Edit docs/diagrams.py, run it, and replace the lead-in of each level. -->

**Level 1 — context.** Who drives the service, and what it pulls from outside.

![The system, its user, and what it pulls from](docs/c1-context.svg)

**Level 2 — containers.** What runs, and the one way in.

![The containers and the one port to the host](docs/c2-containers.svg)

| Setting | What it means | What an attacker cannot do |
| --- | --- | --- |
| `appuser` (uid 10001) | the process runs as an ordinary user, not as root | be root inside the container |
| `read_only: true` | the container cannot write to its own filesystem | leave a file behind or change the code |
| `cap_drop: ALL` | every piece of root's power (a Linux *capability*) is removed | change who owns a file, or get past file permissions |
| `no-new-privileges` | a process can never gain more rights than it started with | climb to root through `sudo` or a similar program |

**Level 3 — components.** What one request passes through inside the container.

![The components one request passes through](docs/c3-components.svg)

**Level 4 — code.** The port, and the two classes that implement it.

![One port, two implementations](docs/c4-code.svg)

| | `vulnerable` | `__safe__` |
| --- | --- | --- |
| **Class** | `VulnerableFeature` | `__Safe__Feature` |
| **The difference** | <!-- TODO(attack): what the vulnerable class does --> | <!-- TODO(attack): what the __safe__ class does instead --> |

---
<!-- [postgres] -->

## <img src="../../docs/assets/icons/database.svg" width="30" height="23" alt="">The database

<!-- TODO(attack): the tables, and who may read what. -->

The application connects as `lab_app`, which is read-only and has a 5-second
`statement_timeout`. Only the one-off seed job gets the admin account.

---
<!-- [/postgres] -->

## <img src="../../docs/assets/icons/sliders.svg" width="30" height="23" alt="">Configuration

Compose sets the lab values. To change one, copy [`.env.example`](.env.example) to `.env`
in this folder and uncomment its line; it applies whether the demo is started here or from
the repository root.

| Variable | Default | What it does |
| --- | --- | --- |
| `JWT_SECRET` | — (required, ≥ 32 bytes) | token signing key; no default value in code |
| `JWT_TTL_SECONDS` | `900` | token lifetime |
| `PUBLIC_URL` | `http://127.0.0.1:8000` | the address printed when the service is ready; compose: `http://127.0.0.1:__PORT__` |
<!-- [postgres] -->
| `DB_HOST`, `DB_NAME`, `DB_APP_USER`, `DB_APP_PASSWORD` | — (required) | the database and the read-only application account |
<!-- [/postgres] -->

### <img src="../../docs/assets/icons/key.svg" width="30" height="23" alt="">Accounts

| Username | Password | Role |
| --- | --- | --- |
| `ana` | `Ana#2026!` | user |
| `admin` | `Admin#2026!` | admin |

---

## <img src="../../docs/assets/icons/shield.svg" width="30" height="23" alt="">Verification

[`bruno/`](bruno/), each request with an explanation and an assertion:

| Folder | What it proves |
| --- | --- |
| `00-environments` | the service is up |
| `01-auth` | login works, a wrong password is rejected, the token names its owner |
| `02-attack` | the attack works on `vulnerable` |
| `03-defense` | the same payload does not work on `__safe__` |
| `04-hardening` | missing and tampered tokens, wrong methods, oversized input, security headers |

Static checks: `uv run ruff check .`

---

## <img src="../../docs/assets/icons/wrench.svg" width="30" height="23" alt="">Troubleshooting

| Symptom | Cause and what to do |
| --- | --- |
| `port is already allocated` | Something else uses port `__PORT__`. Stop it, or change the port in `compose.yaml`. |
| Every request returns `401` | The token expired after 15 minutes. Run `01-auth/01` again. |

---

The full story of the attack: [`../../docs/writeups/__NN__-__SLUG__.md`](../../docs/writeups/__NN__-__SLUG__.md)
· Lab overview: [`../../README.md`](../../README.md)

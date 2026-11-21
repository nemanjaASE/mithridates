<!--
Title: type(scope): description, as in CONTRIBUTING.md. The scope is optional.
  feat(xss-demo): reflected XSS on the search page
  fix(sqli-demo): the seed job waits for the database
  docs: a clearer threat model in the SQL injection write-up
-->

## What this changes

<!-- A few sentences. For a new demo: which attack, and what the fix actually is. -->

## Checklist

- [ ] `uv run --no-project --with pyyaml python scripts/check_repo.py` passes
- [ ] `uv run ruff check .` passes in every demo I touched
- [ ] Every default and path the documentation names matches the code

<details>
<summary>Adding a demo — tick these too, and delete this block for any other change</summary>

- [ ] `docker compose up --build <topic>-demo` works from a clean checkout, and
      `docker compose down` leaves nothing behind
- [ ] The attack works on the vulnerable route and fails on the fixed one, with the same
      payload, and the Bruno collection shows both
- [ ] The write-up says whether this attack has a real **fix** or only **mitigations**, and
      what the demo deliberately does not cover
- [ ] No secret has a default value in code; nothing is published to the host but the
      demo's own port, bound to `127.0.0.1`
- [ ] One line in the root `docker-compose.yml`, one row in `README.md`, one row in
      `docs/README.md`

</details>

<!-- Unticked boxes fail CI. Delete the ones that do not apply instead of leaving them open. -->

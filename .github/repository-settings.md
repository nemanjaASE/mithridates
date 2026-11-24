# Repository settings

Some of what this repository relies on is a GitHub setting, not a file: it is not reviewed
in a pull request and a fork does not inherit it. Set these once, after the repository is
created on GitHub, and again on any copy that should behave the same way.

## Merging — Settings → General → Pull Requests

- [ ] **Allow squash merging:** on, with the default commit message set to
      **Pull request title and description**.
- [ ] **Allow merge commits** and **Allow rebase merging:** off.

A pull request then lands on `main` as one commit whose message is its title. That is why
[`pull-request.yml`](workflows/pull-request.yml) checks the title: without squash merging
the check guards a title nobody sees in `git log`.

## Protecting `main` — Settings → Rules → Rulesets → New branch ruleset

- [ ] **Target:** the default branch. **Enforcement:** Active.
- [ ] **Require a pull request before merging.**
- [ ] **Require status checks to pass**, and add:
  - [ ] `Pull request format` — the title and description
        ([`pull-request.yml`](workflows/pull-request.yml))
  - [ ] `Conventions` — `scripts/check_repo.py`: the `127.0.0.1` binding, the container
        hardening, no secret defaults ([`ci.yml`](workflows/ci.yml))
  - [ ] `Demo generator` — `scripts/new_demo.py` still produces a demo that passes, and
        `scripts/remove_demo.py` still undoes it
        ([`ci.yml`](workflows/ci.yml))
  - [ ] `Bruno` — every demo starts and its Bruno collection passes. One check for all
        demos, so a new demo needs nothing added here ([`bruno.yml`](workflows/bruno.yml))
  - [ ] `Lint <demo>` and `Build <demo>` for every demo. These are named per demo, so a
        new demo's two checks are added here when its pull request is merged.
- [ ] **Block force pushes** and **Restrict deletions:** on (the ruleset's defaults).
- [ ] **Bypass list:** empty, so every change goes through a pull request. Add
      *Repository admin* only if you want to keep pushing to `main` directly.

A check can be picked only after it has run once, so open a first pull request before
setting this up. Until a check is required it is advice: a pull request with a red check
can still be merged.

## Social preview — Settings → General → Social preview

- [ ] **Upload an image:** [`docs/assets/social-preview.png`](../docs/assets/social-preview.png)
      (1280 × 640).

It is the card shown wherever a link to the repository is shared. The PNG is rendered
from [`social-preview.svg`](../docs/assets/social-preview.svg); change the SVG, render it
again, and upload the new PNG.

## Private vulnerability reporting — Settings → Security

- [ ] **Private vulnerability reporting:** on.

[`SECURITY.md`](../SECURITY.md) tells people to use the **Report a vulnerability** button
on the Security tab; the button only appears once this is on.

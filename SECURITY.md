# Security policy

Every demo in this repository contains a working vulnerability on purpose. It is confined
to one adapter, it sits next to the fixed version of the same feature, and the write-up in
[`docs/`](docs/README.md) explains it in full. **Those are not findings — please do not
report them.**

## What is worth reporting

Anything that puts the person *running* the lab at risk rather than the fictional accounts
inside it:

- a demo that publishes a port on anything but `127.0.0.1`, or exposes its database
- a real credential, key or piece of personal data that ended up in the repository
- code that contacts a host outside the lab, or that would affect the machine beyond the
  containers it is supposed to run in
- a dependency or base image that is itself compromised
- a vulnerability that is *not* the one the demo is teaching, and is not mentioned in its
  write-up

## How to report it

Use [**Report a vulnerability**](https://github.com/nemanjaASE/mithridates/security/advisories/new)
on the Security tab, so the report stays private until it is fixed. If it is not
sensitive — a port binding, a stale document — a normal issue is fine.

Only the current state of the default branch is maintained. A release is a snapshot to
cite or teach from; a fix lands on `main`, never as a patched release.

## Running the lab safely

The demos bind to `127.0.0.1` and their databases sit on internal networks with no port
published to the host. Keep it that way: do not put a demo on a shared machine, a VM with
a public address, or a corporate network, and do not point one at real data. `docker
compose down` removes everything, since the data lives in `tmpfs`.

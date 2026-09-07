---
description: Code-work baseline — greppability, comments, boundary validation, security. Loaded on src file work (merged from greppability, comments, boundary-validation, security — 2026-08-01 tier cut).
paths:
  - "**/*"
---

# Code baseline (src-scoped)

## Greppability

- The next maintainer is an agent navigating by exact-name search: **one symbol = one
  greppable definition site**; call sites use the literal name. Never construct identifiers
  at runtime (`getattr(obj, name + "_hook")`, string-assembled imports/routes) — each one is
  invisible to every future inventory. Boilerplate is not a reason; prefer a deep module or
  **generated-and-committed** code over runtime magic.
- Sanctioned metaprogramming (ORM, routing, DSL) lives in one narrow declared layer, and
  every generated name is enumerable from a static registry next to the generator.
- **In durable text, cite by name — never by line.** A cross-file reference that will be *read
  again* (comment, docstring, rules file, doc, plan) is `file.py::symbol`, never `file.py:214`.
  A line number is invalidated by any edit above it, in a file its author never opens, and
  **nothing fails when it rots** — it decays silently and sends the next reader to the wrong
  place. Re-sweeping stale anchors is a subscription, not a fix: measured once, a module growing
  410 → 576 lines invalidated 12 anchors across 7 other files in one commit. If a reference
  names nothing a symbol can point at, it is usually not load-bearing — delete it.
  **The carve-out is ephemeral output** — a review finding, an audit report, a session verdict,
  a chat message — read once and discarded, where `path:line` is the cheapest proof and staleness
  never arrives. Evidence cites lines; code and docs cite names.
- **A number owned by a config is cited, not copied.** Limits, versions, sizes, budgets and
  thresholds live in their config/lockfile/manifest; prose that restates the value drifts from
  it, and the drift is invisible because both sides look authoritative. Point at the file that
  owns it. (Observed: three separate docs carried a container memory limit the deployment file
  had already changed.)

## Comments

- Default: none. A comment earns its place only for a non-obvious **why** — decision, trade-off,
  invariant, external quirk — or as one line over an expression the language hides (a regex, bit
  arithmetic, slice math). Never restate what code does, never commented-out code or journal
  entries (git remembers), no TODOs without an owner.
- A comment that explains or excuses a name you own in this diff is a rename. A public function
  that does I/O, blocks, locks or is superlinear says so at the signature (`# external, 30 s`).
- **Mandatory, the exception to none:** a deviation you made (an overridden default, a pinned
  or capped version, a disabled check) says why at the site and, if temporary, what retires it
  — a condition, never a date. A tuned constant states its origin: rule, arbitrary, or measured.
- Read as human-written: no decorative glyphs, banners, or filler ("Note that", "simply");
  terse coworker's note, not documentation prose.
- **No internal planning labels** — spec/session/wave/finding IDs (`US-2`, `B-2`, `BUG-17`) and
  plan-file paths mean nothing to a future reader: say the *why* in domain terms. Holds for
  identifiers, string literals, test names, and anything generated for a user (reports, logs).
- **Ride-along on the small-debt register.** When `PROJECT.md` § *Plans / backlog* names one, grep
  it for the file you are about to edit and take the rows you find in the same diff, striking each
  one there. They are verified, zero-consequence fixes (stale comments, drifted tallies, dead
  anchors) whose entire economics is that someone is *already* in the file — which is also why a
  session opened to sweep them on a row count is the wrong move, and the register's own contract
  says so.

## Boundary validation

- Validate external data **once, at ingress**; everything past the boundary trusts its
  inputs. **Parse, don't validate**: turn raw input into a typed value that can't be
  invalid; make illegal states unrepresentable (enum over free string).
- Fail fast and loud: invalid required input raises with what's wrong, where, the actual
  value and the expected range — never a silent None/empty the caller can't diagnose.
- Data with a cadence gets a staleness check (threshold derived from cadence, error carries
  last-seen age); computations get minimum-size checks. Config validates at load, not first
  use. State loaded from storage and network responses are sanity-checked before use, not
  indexed blind.
- A read that decides and a write that acts are two statements, and another writer fits between
  them: guard the pair with a store-enforced constraint, one statement, or an explicit lock.
- Enforce a rule where its churn says: stable or corrupts-on-breach → the strongest point nothing
  bypasses (constraint, type, key); likely to change → code. An app check is UX, not integrity.

## Security

- Everything crossing a boundary — request, file, env, queue, third-party response — is
  untrusted until validated. Normalize before checking; **allowlist**, don't blocklist.
- Authorization at the layer that owns the resource, deny by default; scope every query to
  the caller's tenant/owner — never trust a request id to be in scope.
- No secrets in code, fixtures, VCS, or logs; redact at the source. On a leak: rotate
  first, then scrub history.
- **Parameterize** queries and commands — never concatenate untrusted input into SQL,
  shell, or eval. Outbound requests from user input: allowlist host/scheme/port, forbid
  redirects to internal addresses (SSRF), re-check after redirects. File paths: resolve to
  a real path and confirm it stays under the intended base.
- Safe defaults: least privilege, TLS on, auth required, debug off in prod; a security
  decision **fails closed**. Dependencies: pinned lockfile, maintained packages, audits
  acted on, upgrades via expand → test → contract.

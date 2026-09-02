# Small-debt register — the rows that are true, cheap, and not worth a session

> **Template.** Copy to the small-debt-register location named in `.claude/PROJECT.md` § *Plans / backlog* (create the file on first use; `/close-epic` files into it). Delete this blockquote and the example row, keep the contract.

**What this is.** One line per piece of debt that is **real, verified, and priced at zero**: a stale comment, a drifted tally, a dead anchor, a narrow grep in a rule. These are exactly the findings `/close-epic`'s worth-it gate refuses to card (`skills/close-epic/reference/followups.md` §2 → *Never a card*). Without this file they become one clause in a ledger row — recorded, and then invisible, because a ledger is a **verdict index** nobody opens looking for work.

**What it is not.** Not a board, not an epic, not a queue with a wave schedule. No status frontmatter, and the project's plan tooling does not parse it — deliberately.

**Why not the parked-plans location.** Every plan parked there carries *a concrete trigger*, and when the trigger fires the plan is pulled back into active work. A comment fix has no trigger: filed there it would never fire, and it would cost upkeep in two files to say so.

## The contract

**A row belongs here when all four hold:**

1. It **failed the consequence gate** — no class from `followups.md` §2 (data/money loss · a wrong number on a production path · user-visible breakage · shipped code with an unobserved verification · a blocked successor).
2. It is **verified** — observed this session, or CONFIRMED by `finding-verifier`. An unverified row is a rumour, and a rumour that survives in a register outlives the tree it was true of.
3. The fix is **≲10 lines and written down here in full** — if the next session has to re-derive what to do, the batching saved nothing and the row is a card in disguise.
4. It names **a file path**, first column. That is the whole ride-along mechanism: a session about to edit `foo.py` greps this file for `foo.py` and takes what is there for free.

**Never a row here:** anything with a consequence class (that is a card) · anything blocked on a precondition (that is a parked plan) · anything needing a decision the epic never made · **anything whose fix does not fit a ride-along** — test suites, refactors, a rule argued from occurrences nobody has read. Those stay **known-undone clauses in the ledger row**, where a clause is the honest artifact: real, named, and nobody is pretending it is queued.

## How a row dies — three ways, in this order

1. **Ride-along (primary, free).** Any session already editing the file takes its rows in the same diff and strikes them here. This is not a favour to the register: the row is cheap **precisely because** the file is already open. This is the mechanism; the other two are what happens when it does not fire.
2. **A boxed sweep (operator's word only — never auto-triggered).** One session, one commit, and a hard box: **documentation, comments, anchors and dead refs only · no source behaviour, ever · every row re-verified against the current tree before it is touched, and the stale ones deleted with the evidence that killed them · no new findings filed while sweeping** (a sweep that discovers things is an audit, and it must stop and say so). Rows rot: the code moves, the fix lands incidentally, the file gets deleted. A sweep that fixes without re-reading writes new drift over old.
3. **Deletion, with the reason.** A row untouched for **90 days** in a file nobody has edited has proved its own cost is zero. Delete it and say so in the same line of the commit message. Keeping it is how a register becomes a graveyard that everyone greps and nobody trusts.

**No row count triggers anything.** A count is not evidence a sweep is worth a session. Measured on one project: an audit residue treated as a queue became a **nine-plan epic**, and the standing refusal that followed reads — *"they are cheap precisely because the file that carries them is already open; a sweep-the-residue session cancels that property."* This register keeps that refusal and adds only the escape hatch for rows whose file nobody ever opens.

## Open rows

| File | What is wrong | The fix, in full | Origin | Filed |
|---|---|---|---|---|
| `<path:line>` | `<what is wrong, checkable — and why it is priced at zero>` | `<the whole fix, so nobody re-derives it; note if it is only worth doing while already in the file>` | `<epic/plan · F-id>` | `<YYYY-MM-DD>` |

## Struck rows

| File | Row | Why it is struck | Date |
|---|---|---|---|

*(a row is struck here with the commit that fixed it, refuted with the evidence that killed it, or deleted per rule 3 with its reason — never removed silently)*

## Deliberately not here

*(real debt that failed rule 3 — too big for a ride-along — named here in one line each, pointing at the ledger clause that carries it, so nobody re-files it as a register row)*

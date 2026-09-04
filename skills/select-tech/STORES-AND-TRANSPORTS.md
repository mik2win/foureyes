# Stores and transports: choosing something that holds or moves state

**Gate:** read when the thing being chosen **holds or moves state** — a data store, a cache, a
queue or broker, a transport between processes, a transaction engine. `/select-tech` routes here
from Phase 1 before any product is named, or Phase 2; skip it for anything that holds none.

## Before the shortlist

- **If every candidate is a database, the sweep was too narrow.** A few large blobs read in streams
  belong in a file system or object store, not in rows; a requirement phrased as history, audit or
  "what did it look like on that date" is an event log plus a derived read model, and that works
  over the relational default too. Name one non-database option and its kill reason.
- **Ask who writes to this store.** More than one independently deployed codebase writing to it
  makes it an integration database: the schema and the integrity rules are a shared contract, and
  moving them into application code is not on the table. Fix the ownership first — wrap it in a
  service that owns the writes — then reopen the storage question.
- **Each added store is a recurring bill, not a one-time choice**: dev/CI/staging instances,
  backups and *tested* restores, monitoring, on-call knowledge, driver upgrades, a security model
  the application now owns, a path for reporting to reach the data. Put that bill beside the
  modelling benefit — and note the inverse: data with genuinely different availability and backup
  needs is a reason to split, not to unify.

## The class before the product

Derive the class from four measured properties — **volume · access shape** (recent-hot with a long
cold tail, or uniform random?) **· read:write ratio · the consistency the business actually
demands** — then say which property decides. The same four questions correctly yield a key-value
store for a chat history (huge, recency-skewed, ~1:1, eventual is fine) and a relational database
for file metadata (strong consistency wanted, ACID native rather than hand-rolled). And do not
assume one store for everything: splitting by data type — relational rows for the entities, a
specialized store for the firehose — is usually cheaper than bending one engine to two profiles.

Score the *classes* — relational · key-value · document · column-family · graph · NewSQL ·
time-series — on learning curve, ease of modelling, scalability, availability under partition,
consistency, ecosystem maturity **and hireability**, read-vs-write bias. Only then run the
`SKILL.md` filters inside the winning class: naming two products from the same class as "the
alternatives" is a leading question, and a class picked by familiarity is the axis the comparison
existed to expose.

- **The relational default wins ties.** A non-relational store must show a named, concrete
  advantage for THIS system, not a general property of its category. "No clear advantage found,
  staying relational" is a complete answer — record it as the decision.
- **Name the one dominant access pattern in a sentence** ("we read and write X as a whole, keyed by
  Y") before proposing a document, key-value or column-family store. Two patterns competing for the
  same data with neither clearly primary is the signal for an aggregate-ignorant store, not an
  argument about which aggregate boundary is prettier.
- **Single server is the default distribution model**; a cluster is a cost to justify, not a
  feature to collect. Separate the two reasons a store gets picked — a better data model,
  horizontal scale — and check which is driving this one. A non-relational store chosen for its
  model and run on one machine is a coherent answer, not a half-measure.
- **If the design is sharded, ask the question nobody writes down:** which query arrives *without*
  the partition key? That one decides whether the shard key is wrong.

## The guarantees, priced

- **Do not settle a storage decision with "CAP says pick two".** State the actual trade: which
  operations need a recency guarantee, what it costs them in latency on an ordinary day (not only
  during a partition), and what the system does to the operations that don't need it.
- **Serializable is a choice of implementation, each with its own failure mode.** Optimistic (SSI):
  predictable latency, abort storms under contention, wants short transactions. Pessimistic (2PL):
  correct, unstable tail latency, deadlocks. Serial execution: working set in memory, logic in
  stored procedures. Name which one, and the failure you accept.
- **Last-write-wins is a contract for silent data loss**: among concurrent writes the winner is
  arbitrary and the losers vanish, with clock skew on top wherever wall-clock timestamps decide.
  Safe only for insert-only unique keys — otherwise budget for siblings, CRDTs, or routing every
  key through a single leader.
- **Before proposing a distributed transaction across a broker and a database, price the cheap
  version:** a processed-message-id table with a unique constraint *inside the one database*,
  written in the same transaction as the effects, acked after commit — exactly-once for the common
  case. Two-phase commit pays instead with in-doubt locks that survive a coordinator restart and
  heuristic decisions taken by hand; the exception is an engine offering distributed transactions
  natively.
- **Event sourcing is decided before the first event is written.** *Erasure*: the store keeps
  everything on purpose, so a right-to-be-forgotten request has no delete to run — per-subject
  encryption with a discardable key, plus a pseudonym layer if a personal value ever became an
  identifier. *Querying*: the store answers by key, so every "find all X where Y" becomes a
  separately built read model. Adding an aggregate, an event type or a field is safe; renaming or
  removing one is not, and the fix is upgrading events on load.

## Transports

Decide the **transport** before the product, from two properties of the traffic: **direction**
(truly bi-directional, or only server→client?) and **frequency** (constant chatter, or rare
updates?). Walk the ladder from the cheap end — request/response · polling · long polling ·
server-sent events · WebSocket · a broker — and stop at the first rung that satisfies both, naming
what the next rung would have bought and cost (persistent connections, sticky routing, a broker to
operate). Then scope it: a real-time channel for the one feature that needs it does not make the
whole surface real-time.

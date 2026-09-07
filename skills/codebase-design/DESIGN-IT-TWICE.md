# Design It Twice

**Gate:** read when a design decision is still open and worth a second candidate —
`/codebase-design` §Design it twice, `/arch-health` when proposing a new seam. Skip it when the
design is settled and the work is applying it.

> **The first design you can defend is a candidate, not the answer.** A design good enough to describe is the point at which to produce a second one — the comparison, not the first sketch, is what makes the interface deep.

The first design that *works* is rarely the design you should ship. Before committing to an
interface, generate a **second, genuinely different** one and compare them. The cost is minutes;
the payoff is a deeper module you won't fight for months.

## The move

1. **Sketch design A** — the obvious approach. Write the *call* first: the literal lines a caller
   will type and what comes back, judged on the caller's experience alone — knowing how you would
   build it pulls the interface toward the one easy to build. Then the interface behind the call:
   what's hidden, where the seam sits. The only feasibility check at this step is whether the call
   carries enough input to produce its output. Don't implement it.
2. **Sketch design B — deliberately different.** Not a tweak of A. At the interface: move the
   seam, invert who owns the state, collapse two methods into one, make it general where A was
   special-purpose (or the reverse), or change the metaphor of the central thing (`SHAPE.md`
   §Objects and their interface). When the open decision is where to cut a *feature set*, run the
   six operators over it instead — split it along another line, substitute one module, augment,
   exclude one part, invert (lift a capability every module reimplements into a first-class one),
   port one in from elsewhere — and score each cut by how many of those a future change could
   still apply: a decomposition where nothing can be excluded on its own is the weaker one. If B
   feels forced, that's fine — the point is contrast, not a second favourite.
3. **Compare on the axes that matter:**

   | Axis | Ask |
   |------|-----|
   | **Depth** | Which hides more behind a smaller interface? |
   | **Caller cost** | Which is simpler for the *callers* to learn and use? |
   | **Seam fit** | Which puts the seam exactly where behaviour must vary (test/prod/vendor)? |
   | **Error surface** | Which defines more errors out of existence? |
   | **Generality** | Which is general enough to serve the next caller without gold-plating? |
   | **Change cost** | How many files does a routine "add one field" touch under each — and under the framework's default shape? |
   | **Prevention vs detection** | Which makes the mistake impossible to express, and which merely catches it? A shape that can't be built wrong needs no inspection; a check must be run, kept and trusted. Take the passive one unless it costs disproportionately more — and label each alternative. |
   | **What it makes hard** | Which awkward cases does each metaphor create, and which does it dissolve? |

4. **Synthesize.** Often the best design is neither A nor B but takes A's seam and B's collapsed
   interface. Name the winner and *why* it wins on the axes above.

## When it's worth it

Always for a module that will have **many callers** or a **long life** (a core domain interface, a
shared utility, anything other code will depend on). Skip it for a throwaway or a leaf with one
caller — there, the obvious design is fine.

## When the alternatives are already known

Some needs are **named, solved mechanisms** — rate limiting, ID generation, deduplication, cache
eviction, retry backoff, leader election. There the field is a small closed set of standard
algorithms, not an open design space, and inventing a "genuinely different" design B is the wrong
move: design B already exists and has a name.

Do this instead: list the set (3–5 entries), give each one line of pro, one line of con, and its
**tuning parameters**, then pick against the single constraint that actually decides here — burst
tolerance, exactness, memory, or a steady outflow. A picked algorithm with no named rejects is a
default you did not notice you were taking.

## In the kit

`/prepare` Phase 2.5 already asks for 2–3 design alternatives; this is the *module-level* version
of that discipline — apply it to the specific interface you're about to commit to, using the
[SKILL.md](SKILL.md) vocabulary (depth, seam, leverage) to do the comparing.

# Design It Twice

**Gate:** read when a design decision is still open and worth a second candidate —
`/codebase-design` §Design it twice, `/arch-health` when proposing a new seam. Skip it when the
design is settled and the work is applying it.

> **The first design you can defend is a candidate, not the answer.** A design good enough to describe is the point at which to produce a second one — the comparison, not the first sketch, is what makes the interface deep.

The first design that *works* is rarely the design you should ship. Before committing to an
interface, generate a **second, genuinely different** one and compare them. The cost is minutes;
the payoff is a deeper module you won't fight for months.

## The move

1. **Sketch design A** — the obvious approach. Just the *interface*: methods, parameters, what's
   hidden, where the seam sits. Don't implement it.
2. **Sketch design B — deliberately different.** Not a tweak of A. Move the seam, invert who owns
   the state, collapse two methods into one, make it general where A was special-purpose (or the
   reverse). If B feels forced, that's fine — the point is contrast, not a second favourite.
3. **Compare on the axes that matter:**

   | Axis | Ask |
   |------|-----|
   | **Depth** | Which hides more behind a smaller interface? |
   | **Caller cost** | Which is simpler for the *callers* to learn and use? |
   | **Seam fit** | Which puts the seam exactly where behaviour must vary (test/prod/vendor)? |
   | **Error surface** | Which defines more errors out of existence? |
   | **Generality** | Which is general enough to serve the next caller without gold-plating? |

4. **Synthesize.** Often the best design is neither A nor B but takes A's seam and B's collapsed
   interface. Name the winner and *why* it wins on the axes above.

## When it's worth it

Always for a module that will have **many callers** or a **long life** (a core domain interface, a
shared utility, anything other code will depend on). Skip it for a throwaway or a leaf with one
caller — there, the obvious design is fine.

## In the kit

`/prepare` Phase 2.5 already asks for 2–3 design alternatives; this is the *module-level* version
of that discipline — apply it to the specific interface you're about to commit to, using the
[SKILL.md](SKILL.md) vocabulary (depth, seam, leverage) to do the comparing.

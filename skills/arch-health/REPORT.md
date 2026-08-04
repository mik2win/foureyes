# Optional: a visual health report

**Gate:** read at `/arch-health` output time, only when the user asked for a rendered report.
The ranked table in the chat is enough for most runs. When the user wants a **scannable overview**
of a larger scan — or something to keep and compare against next week — render a standalone
report file they can open in a browser.

## When to render it

- The scan covered many modules and a flat table is hard to take in.
- The user asked for a report, a "map", or something to share.
- You want a before/after artifact to re-run the scan against later.

Skip it for a small or focused scan — don't make a file nobody asked for.

## What to produce

A **single self-contained `.html` file** (inline CSS, no build step, no external assets) written to
the project's plans/backlog location (`PROJECT.md` → Plans / backlog) so it sits with other
artifacts. Contents, in priority order:

1. **Header** — scope scanned, date, and the headline count (N opportunities, M layer violations).
2. **Ranked opportunities** — a sortable/colour-coded table: opportunity (with `path`), smell,
   leverage, cost, rank. Colour by leverage (high = warm) so the eye lands on the wins.
3. **Layer-violation map** — group the dependency-direction breaks by layer so the structural
   problems read at a glance.
4. **Recommended next** — the top 1–3 with the route (`/refactor` vs `/prepare`).

Keep it terse and factual — the same content as the chat output, just laid out to scan. Every
opportunity still cites `path:line`. The HTML is a *view*, not new analysis; don't invent findings
to fill it.

## Rules

- **Self-contained.** Inline everything; the user opens the file directly, no server.
- **Don't auto-open or deploy it.** Write it, report the path, let the user open it.
- **It's throwaway/regenerable.** Note in the file that it reflects the scan at this date and is
  meant to be re-run — it is not a maintained document.

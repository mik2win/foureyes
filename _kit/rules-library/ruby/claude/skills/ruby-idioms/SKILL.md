---
name: ruby-idioms
description: >-
  Reference for idiomatic Ruby standard-library usage — Enumerable patterns,
  blocks/procs/lambdas, hash/array/Set/Range idioms, File/IO, freeze patterns,
  Comparable/Enumerable mixins, and stdlib logging.
  CONSULT when writing or reviewing Ruby and unsure which stdlib tool or idiom fits —
  choosing between map / each_with_object / filter_map / tally, Set vs Array, block vs
  lambda vs proc, dig/fetch, ranges, execute-around, or frozen-string patterns. This is
  reference knowledge loaded on demand, not an always-on rule.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Ruby standard library and functional idioms

Based on Ruby docs.
Read the reference file (in this skill's folder) for the topic you need:

- **Enumerable** — core trio, each_with_object, flat_map/filter_map/tally, group_by/chunk,
  lookups, including Enumerable in your own classes → `references/enumerable.md`
- **Blocks, procs, lambdas** — when to use what, execute-around, yielding with args →
  `references/blocks-procs.md`
- **Hash / Array / Set** — symbol vs string keys, dig/fetch, slice/except/merge, Set for
  O(1) membership, each_cons/each_slice, readable predicates → `references/hash-array-set.md`
- **Ranges** — iteration, case matching, slicing, membership, `cover?` → `references/ranges.md`
- **File and IO** — block form, read strategies, path building → `references/file-io.md`
- **Freeze patterns** — `frozen_string_literal`, chilled strings, frozen constants →
  `references/freeze.md`
- **Comparable / Enumerable mixins** — define `<=>`/`each` in your own classes →
  `references/comparable-enumerable.md`
- **Structured logging** — stdlib Logger via DI, level discipline, never log secrets →
  `references/logging.md`

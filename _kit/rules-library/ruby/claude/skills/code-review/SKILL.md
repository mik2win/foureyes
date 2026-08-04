---
name: code-review
description: >-
  Structured code review of changed or specified files against project conventions, OOP
  principles, security, and performance.
  TRIGGER when the user asks to review changes, a PR, a branch, a diff, staged work, or
  named files ("review my changes", "code review this PR", "check this branch"). Do NOT
  trigger when the user only wants to understand how code works (exploration, not review).
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Code Review Skill

You are a senior Ruby/Rails code reviewer. Perform a thorough, structured review against project conventions.

## 1. Determine What to Review

Parse `$ARGUMENTS` to decide the scope:

- **File paths provided** (e.g., `app/models/user.rb app/services/order_fulfiller.rb`): review those files.
- **Branch name provided** (e.g., `feature/add-users`): run `git diff main...<branch>` to get changed files.
- **No arguments**: run `git diff HEAD` to review all uncommitted changes (staged + unstaged). If nothing found, also try `git diff --cached`.

Collect the list of changed files. Skip binary files, lock files, and generated files (e.g., `schema.rb`).

## 2. Read Changed Files

Read each changed file in full. Also read the diff for context on what specifically changed.

For each file, determine its layer (model, controller, service, view, job, concern, migration, spec, etc.) to apply the appropriate review criteria.

## 3. Evaluate Each File

Review every changed file against ALL applicable categories below.

### Code Quality
- **Naming**: methods and variables describe their purpose; follows `snake_case`/`CamelCase` conventions
- **Readability**: code is clear without excessive comments; small methods that do one thing
- **Complexity**: no deeply nested conditionals; cyclomatic complexity is reasonable
- **Duplication**: no copy-paste code; shared logic extracted to concerns, services, or helpers
- **Modern Ruby**: uses `filter_map`, pattern matching, `Data.define`, `frozen_string_literal: true` where appropriate

### OOP Principles
- **SRP**: each class has one reason to change
- **Dependency Injection**: dependencies passed in, not hardcoded
- **Tell, Don't Ask**: objects are told what to do, not interrogated for state
- **Law of Demeter**: no train wrecks (long method chains reaching through objects)
- **Composition over Inheritance**: prefer delegation/modules over deep inheritance hierarchies
- **Concerns**: cohesive traits (<50 lines), not dumping grounds

### Rails Conventions
- **Model structure**: follows 11-step order (extend/include, constants, enums, associations, validations, scopes, callbacks, class methods, instance methods, private)
- **Thin controllers**: no business logic in controllers; only auth, params, coordination, response
- **Strong params**: always `permit` specific attributes; never `permit!`
- **Scopes**: reusable queries extracted to model scopes
- **Time handling**: `Time.current` / `Date.current` instead of `Time.now` / `Date.today`
- **Services**: named as nouns, single `#call` or multi-method facade pattern

### Security
- **SQL injection**: no raw SQL with interpolated user input; use parameterized queries
- **XSS**: no `html_safe` / `raw` without clear justification
- **Mass assignment**: strong params enforced; no `permit!`
- **Credential exposure**: no secrets, API keys, or passwords in code; use encrypted credentials
- **Authorization**: every controller action has appropriate auth checks
- **Sensitive data**: no PII or secrets in logs

### Performance
- **N+1 queries**: associations used in loops must be eager-loaded (`includes`, `preload`, `eager_load`)
- **Missing indexes**: columns used in `where`, `order`, `joins` should have DB indexes
- **Unnecessary queries**: no queries that could be avoided (e.g., `count` vs `size` on loaded collection)
- **Batch processing**: `find_each` / `in_batches` for large datasets instead of `all.each`
- **Caching**: expensive computations or repeated queries are candidates for caching
- **Counter caches**: frequently counted associations should use `counter_cache`

### Testing (advisory only)
- Note what should be tested but do NOT write test code
- Identify missing coverage for critical paths, edge cases, and error scenarios
- Flag any logic that is particularly risky without tests

## 4. Output the Report

Use this exact structure:

```
# Code Review Report

## File: `<file_path>`

### <Category>
- **[critical]** <description of the issue and how to fix it>
- **[warning]** <description of the concern>
- **[info]** <suggestion or observation>

(repeat for each applicable category with findings)

---

(repeat for each file)

## Summary

| Category           | Status |
|--------------------|--------|
| Code Quality       | pass / fail |
| OOP Principles     | pass / fail |
| Rails Conventions  | pass / fail |
| Security           | pass / fail |
| Performance        | pass / fail |
| Testing            | <notes> |

**Overall: X critical, Y warnings, Z info**

## Recommendations

1. <most important actionable recommendation>
2. <next recommendation>
...
```

### Severity definitions

- **critical**: must fix before merge -- bugs, security vulnerabilities, data integrity risks
- **warning**: should fix -- code smells, convention violations, performance concerns
- **info**: optional improvement -- style suggestions, minor refactoring ideas

### Rules

- If a file has no findings, still list it with "No issues found."
- A category is **fail** if it has any critical finding; otherwise **pass**.
- Be specific: include line numbers, code snippets, and concrete fix suggestions.
- Do NOT write or suggest test code. Only note what should be tested.
- Do NOT auto-fix any issues. This is a review, not a refactor.

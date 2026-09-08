# Safe patterns — remediation shapes

Referenced from `SKILL.md`; load when a finding needs a fix. These are language-neutral
*shapes* — translate them to the project's stack (from `PROJECT.md` → Stack) and to the
framework's own binding/validation APIs. The principle is what matters, not the syntax.

## Command injection {#command-injection}

Never build a command as a string and hand it to a shell. Pass an argument vector and keep
the shell off, so input can never be interpreted as syntax.

```
# WRONG — input becomes shell syntax
run("ls " + user_input, shell=true)

# CORRECT — argument vector, shell disabled
run(["ls", user_input], shell=false)
```

## SQL / query injection {#sql}

Use the driver's parameter binding. The query text is a constant with placeholders; values
travel separately and are never parsed as SQL.

```
# WRONG — value interpolated into the query text
execute("SELECT * FROM item WHERE id = " + id)

# CORRECT — bound parameter (placeholder syntax varies by driver: ?, $1, :id)
execute("SELECT * FROM item WHERE id = ?", [id])
```

## Path traversal {#path-traversal}

Confine a path built from input to an intended base directory: strip directory components,
resolve to a real absolute path, and confirm it still lives under the base.

```
candidate = resolve(base_dir + "/" + basename_of(user_input))
if not candidate.is_within(resolve(base_dir)):
    reject("path traversal attempt")
```

## Unsafe deserialization {#deserialization}

Do not deserialize untrusted input with a format that can construct arbitrary objects or run
code on load. Use a data-only / "safe" loader for untrusted input; reserve code-capable
serializers for self-produced, trusted artifacts only.

```
# WRONG — arbitrary object construction / code execution on load
data = native_deserialize(untrusted_bytes)
data = yaml_load_unsafe(untrusted_text)

# CORRECT
data = parse_json(untrusted_text)      # or the format's safe/data-only loader
# code-capable serializers: only on data this process produced, never network/user input
```

## Cross-site scripting / output encoding {#xss}

Escape at the output site and keep "this value is safe" a deliberate decision: when safety travels
with the value instead, the template looks innocent and the marking site is the only place to audit.
Stored data is untrusted too — it was someone's input before it was a row.

```
render(mark_as_safe(user_input))                 # WRONG — the value carries its own exemption
render(sanitize(row.body, allow=["b", "i"]))     # CORRECT — escaped at output, allowlisted
```

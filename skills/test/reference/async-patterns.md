**Gate:** loaded by `/test` Phase 5 only when the target actually contains async code. A
synchronous target skips this file entirely.

# Async test patterns

Examples are in one concrete language for readability; the **shapes** transfer. The async test
decorator/mode, the async mock type, the timeout marker and the task API all come from
`PROJECT.md` and the installed stack rules — if the stack's idiom differs, the stack wins.

## Setup

Whatever the stack's async test mode is (auto-detection, an explicit marker, an event-loop
fixture), name it once in the project rules and use it consistently. Mixing "auto" and explicit
markers in one suite is how a test silently becomes a no-op coroutine that is never awaited —
a test that never runs also never fails.

## Writing an async test

```python
async def test_subscriber_failure_does_not_break_the_engine(mocker):
    # Arrange — the subscriber blows up
    failing_cb = mocker.AsyncMock(side_effect=RuntimeError("downstream down"))
    engine = Engine(on_event=failing_cb)

    # Act — must NOT raise: a broken subscriber is not an engine failure
    await engine.handle(make_event())

    # Assert the callback was actually attempted
    failing_cb.assert_awaited_once()


async def test_cancellation_propagates():
    """A cancellation signal means shutdown — it must never be swallowed."""
    async def always_cancel():
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await always_cancel()
```

## Async invariants worth a test each

For every async unit that orchestrates other work:

- [ ] **Subscriber isolation** — a callback/handler failure does not propagate out of the
      orchestrator.
- [ ] **Cancellation propagates** — the cancellation signal is never caught by a bare catch-all.
- [ ] **Fan-out survives one failure** — one branch of a parallel gather failing does not kill
      its siblings (collect the errors, don't crash the group).
- [ ] **No real sleeps** in the code under test — the clock is injected or awaited through the
      framework's sleep, never a blocking one.
- [ ] **Ordering** — state is persisted *before* events are emitted to subscribers, so a
      subscriber that reads the state back cannot observe a gap.

## Orphaned tasks and mocked clocks — the two hangs

**Code must cancel the tasks it spawned.** A task left running after its owner returns keeps
its whole closure alive:

```python
try:
    await asyncio.gather(*tasks)
except asyncio.CancelledError:
    raise                       # never swallow it
finally:
    for task in tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
```

**A test with a mocked sleep needs a timeout and a real termination condition.** This is the
single most destructive test-suite failure mode, and it does not look like a test bug:

```python
@pytest.mark.timeout(10)        # fail fast instead of freezing the machine
async def test_poll_loop_stops_after_success(mocker):
    mocker.patch("module.asyncio.sleep", new_callable=mocker.AsyncMock)
    ...
```

Why it matters: a mocked sleep returns **instantly**, so a retry or poll loop that was written to
run once a second now spins at full CPU speed. An unbounded loop allocates as fast as the
allocator allows and takes the machine down in seconds, not minutes.

Two follow-on traps:

- **`sleep(0)` is not an escape hatch** — it is mocked too, so it yields nothing and the loop
  still spins. Use an explicit iteration ceiling or a call-count assertion as the termination
  condition.
- **A parallel test runner can mask this.** When each test runs in a worker process, a hung
  worker can look like a slow suite rather than a hang, and the failure only surfaces on the
  machine that runs the suite serially. Reproduce a suspected hang single-process before
  concluding it isn't one.

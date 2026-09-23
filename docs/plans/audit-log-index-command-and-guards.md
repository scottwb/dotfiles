# Plan: The index's copyable command, and the describe guards

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test before the implementation, then make it pass
3. **Test after each step** - Run the test command listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - `SKILL.md` where behaviour it documents changes; this plan's checkboxes; the roadmap at completion
6. **Mark completion** - When both steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

The whole suite is one command from the repo root:

```bash
.claude/skills/audit-agent-conversation/run-tests
```

It should stay at or above 428 tests and exit 0. Its output is noisy on purpose:
several tests exercise refusals, the write guard and the CLI help text, and that
output is not failure.

---

## Summary

The second phase gate
([phasegate-audit-log-gate-fixes.md](../assessments/phasegate-audit-log-gate-fixes.md),
PASS_WITH_FINDINGS, 2026-09-23) returned two findings worth fixing before the
audit-log follow-ons resume. This plan lands both.

Both are failures of the same kind: something was tested for the shape it had
rather than for the job it does. The copy button's command was pinned
byte-identical by a regression test and has never once parsed. The sweep was
taught to survive a bad transcript at the call site the fix list named, while
the same crash stayed live one call site over, which is where the harm the
first gate described actually lands.

## Requirements

- A command copied from the index page runs, as written, in a shell.
- That property is proven by feeding the emitted string to the real argument
  parser, not by asserting the string looks the way it looked yesterday.
- A transcript that cannot be described costs its own row, never the index or
  the whole run, on every path that describes a candidate.
- The trigger is a type, not a value: a garbage timestamp string already
  degrades cleanly and must keep doing so.

## Non-Goals

- Gate fix-list items 3 to 6 (deriving the `[1m]` aliases, the cache-multiple
  test, the carried-forward items 7 to 9, the nits). They stay in the report.
- Anything about multi-turn rendering.

## Implementation Steps

### Step 1: Make the index's copyable command parse

- [ ] Write the failing test first: in `tests/test_index.py`, feed the argv that
      `Entry.command` emits for a well-formed session through the CLI's own
      argument parser and assert it parses and resolves the project. It fails
      today with `error: argument --project: expected one argument`, because
      every real project directory name starts with a dash and argparse reads a
      dash-led token as an option.
- [ ] Retarget `test_a_well_formed_session_keeps_its_unquoted_command`, which
      currently pins the unparseable form. It was written to prove the quoting
      change moved no existing line; it proved the line stayed broken. Keep the
      "no unnecessary quoting" property it was protecting.
- [ ] Implement: emit `--project=%s` in `index.py`, with the value still passing
      through `shlex.quote`.
- [ ] Verify green: the whole suite, plus a real check. Rebuild the index over
      the real store, copy a `TO DO` row's command verbatim, and run it.

**Satisfies:** second gate finding 1 (high) and its fix-list item 1. Every `TO
DO` row the index has ever offered hands the reader a command that cannot run,
and SKILL.md tells them to paste it.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/index.py`, `.claude/skills/audit-agent-conversation/tests/test_index.py`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Emit a copyable command that actually parses`

---

### Step 2: Guard the describe stage on the index and walking paths

- [ ] Write the failing test first: build a fake transcript root holding one
      good session and one whose `timestamp` is a dict, then assert that
      `--all --index` still writes the index, and that a bare
      `--project <name>` still reaches the good session. Both fail today with
      `AttributeError: 'dict' object has no attribute 'replace'`, raised inside
      `describe` after the sweep has already finished.
- [ ] Implement: `parse_timestamp` returns None for a non-string; the
      per-candidate body of `index.scan` and of `first_renderable` treats a
      transcript it cannot describe as an unreadable entry or a skip row rather
      than letting it escape.
- [ ] Verify green: the whole suite. Confirm a garbage timestamp *string* still
      degrades exactly as it does today, since the trigger is the type.

**Satisfies:** second gate finding 2 (medium) and its fix-list item 2. It also
closes the remaining harm from the first gate's finding 2, whose stated
consequence was that `--all --index` never builds its index; `render_one` was
guarded, this call site was not.

**File(s):** `.claude/skills/audit-agent-conversation/scripts/auditlog/parse.py`, `.claude/skills/audit-agent-conversation/scripts/auditlog/index.py`, `.claude/skills/audit-agent-conversation/scripts/auditlog/cli.py`, `.claude/skills/audit-agent-conversation/tests/`

**Test:**
```bash
.claude/skills/audit-agent-conversation/run-tests
```

**Commit message:** `Let a session that cannot be described cost only its own row`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `scripts/auditlog/index.py` | 1, 2 |
| `scripts/auditlog/parse.py` | 2 |
| `scripts/auditlog/cli.py` | 2 |
| `tests/test_index.py` | 1, 2 |
| `tests/test_cli.py` | 2 |

All paths are relative to `.claude/skills/audit-agent-conversation/`.

## After this plan

Gate fix-list items 3 to 6 remain open in
[phasegate-audit-log-gate-fixes.md](../assessments/phasegate-audit-log-gate-fixes.md),
along with items 7 to 9 carried forward from the first gate.

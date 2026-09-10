# Assessment: How config reaches a running session

Investigated 2026-09-09 against CLI 2.1.266/2.1.267, after a `CLAUDE.md` edit
raised the question of whether the eight or so live agent sessions on this
machine would pick it up.

| Config | Reaches a running session? | To apply it |
|---|---|---|
| `CLAUDE.md` | ❌ No | Restart the session |
| `.claude/commands/*.md` | ✅ Yes, immediately | Nothing |
| Notification keys in `settings.json` | n/a, harness owns them | Edit the tracked file |

## `CLAUDE.md` binds at startup only

The instruction block is injected when a session starts and is not replaced
afterward. A session running from before an edit is **not governed by it**.

Verified by asking a peer session that had started hours before the edit
landed. It could still read its own startup block, enumerate its section list,
and confirm the new section was absent. That is evidence rather than proof: a
session can only report what is visible in its own context, so a silent swap
would be undetectable from the inside. No reload mechanism was found, and
`claude --help` documents none.

**Why this matters more than it looks.** A rule on disk but not in a session's
instruction block is not a guardrail for that session, it is a note in a file it
has not read. Telling a running agent about a new rule makes it aware, not
governed. Before a fleet-wide restart to apply one, capture what each session
knows that never reached disk; `/write-that-down` exists for that.

## Slash commands register live

A new file in `.claude/commands/` is picked up by already-running sessions with
no restart. Observed the same day: `/write-that-down` appeared in a running
session's available skills immediately after the file was copied into place.

So the two halves of a change can land at different times. A command plus the
`CLAUDE.md` entry that tells sessions when to suggest it will, for every session
already running, be half applied.

## The notification keys are harness-owned

`inputNeededNotifEnabled`, `agentPushNotifEnabled` and `taskCompleteNotifEnabled`
sit in a list of UI preferences the harness writes back itself, alongside
`theme`, `editorMode`, `verbose`, `preferredNotifChannel` and
`autoCompactEnabled`. Reverting one by hand does not hold; it reappears. Change
them in the tracked file and let the value follow every machine.

From the CLI's own schema, verbatim:

- `inputNeededNotifEnabled`: "Push to mobile when a permission prompt or question is waiting"
- `agentPushNotifEnabled`: "Allow Claude to push proactive mobile notifications"

Distinguish these from `model` and `effortLevel`, which drift for a different
reason: `/model` persists a pick as the new default unless you choose it with
`s`, which applies it to the session only.

## `~/.claude` is this repo

`~/.claude` is a symlink to `.claude/` here, so the global config path and a
tracked file in a PUBLIC repo are the same inode. Anything the harness writes
anywhere under `~/.claude` lands in this repo by default. The full reasoning,
and the `autoMode` incident that established it, is in `settings.json`'s own
`x-instructions`.

One result worth adding to that record: after the generated `autoMode` block was
moved to the ignored `settings.local.json`, **it did not regenerate** over the
following hours. The generator reads the merged config and stays quiet when the
block is already present, so relocation is a complete fix rather than treating
one instance.

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

### The `autoMode` block regenerates. Relocation is not a fix.

An earlier version of this file recorded that after the generated `autoMode`
block was moved to the ignored `settings.local.json`, it did not regenerate
over the following hours, and concluded that relocation was a complete fix.
**That conclusion was wrong**, and it was drawn from hours of quiet rather than
from how the generator works.

Occurrences: 2026-09-09, 2026-09-17 (found and cleaned by the Greenthumb
session, profile describing the private `greenthumb` repo), and 2026-09-30,
found on 2026-10-05 with a profile describing `donna-smithers`. Each time
`/auto-mode-setup` wrote `autoMode.environment` into the tracked
`.claude/settings.json`, which is a public repo. Two of the three runs also
flipped `model` off its pin.

**The leak is not the worst part.** `autoMode.environment` is a SINGLE GLOBAL
value, but the profile it holds is generated PER REPO: it names a trusted repo
and remote, sensitive-data locations, and protected branches. So whichever
session ran the setup last wins, and every other repo on the machine silently
inherits a trust profile describing someone else's boundary. A security profile
confidently describing the wrong repo is worse than no profile, and it is
invisible from inside any single session.

### There is no per-repo home for a profile. Relocating one makes it inert.

This section previously said generated profiles belong in the project's own
`.claude/settings.local.json`. **That was wrong**, and so were the two cleanups
that followed it. Read from the 2.1.292 binary on 2026-10-07:

- Claude Code reads `autoMode` only from user settings (`~/.claude/settings.json`),
  a `--settings` flag file, and managed policy. It ignores `autoMode` in a
  repo's `.claude/settings.json` and `.claude/settings.local.json`, logging
  "only user/flag/managed settings may set classifier rules (projectSettings
  and localSettings are repo-controllable)". A cloned repo must not be able to
  set its own trust rules, so this is deliberate and will not change.
- `/auto-mode-setup` always writes to user settings, whatever scope it offers.
  The binary says so: "entries always land in the user settings file."
- There is no user-level `settings.local.json`. `~/.claude/settings.local.json`
  is this repo's `.claude/settings.local.json`, read only as the project-local
  file for sessions rooted in this repo (or in `$HOME`). Other repos never see it.

So greenthumb's relocated profile has been inert since 2026-09-18, and the
`donna-smithers` profile in this repo's `settings.local.json` never made other
repos "read as Donna's"; it was inert too, and is dead weight to delete. The
only live profile was whatever the setup last wrote into the tracked
`settings.json`, which since 2026-09-30 was Donna's, for every repo.

**Decided 2026-10-07: one repo-neutral profile in `settings.json`.** It starts
with `"$defaults"` to keep the built-in entries, then adds only facts true in
every repo on this machine: the trusted repo is whichever one the session's
working directory is in, secrets resolve through `op`, `~/.claude` is a public
repo, and the `prod` naming heuristic. It names no repo, path, or private data
location, so it is safe in a public file and correct everywhere. Per-repo
profiles would need a launcher passing `--settings` per repo; rejected as more
machinery than the gain.

**A prose warning has now failed three times.** `settings.json`'s
`x-instructions` forbade this after the first occurrence and
`x-automode-removed` explained the mechanism after the second; it happened
again regardless. `/auto-mode-setup` is built into the CLI and not a file in
this repo, so there is nothing local to change about the generator. Detection
is the only lever here: a check that fails when the tracked `settings.json`'s
`autoMode` differs from the neutral profile would have caught all three. Not
built; filed on the roadmap 2026-10-08.

**For anyone cleaning up an occurrence:** restore the `autoMode` block and the
`model` pin from git, and leave a dated note. Do not move the generated profile
into the repo it describes; it would be inert there.

# Plan: `/end-session`

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `CLAUDE.md` - Developer/AI guidelines (here: `.claude/CLAUDE.md`)
   - `run` script usage comments (here: the usage headers of the new `bin/` scripts)
   - `docs/plans/end-session.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

**Run interactively.** Steps 1 and 5 need Scott at a terminal and a phone (Remote Control). Not for an unattended `/yolo` or `/beastmode`.

---

## Summary

`/end-session` is the command for "I'm done with this session". It runs `/write-that-down`, and only when that sweep finishes cleanly does it exit Claude. It works in any session, plain `claude` included, and needs nothing from Patchbay. Roadmap item: [`/end-session`: write it down, then exit](development-roadmap.md#end-session-write-it-down-then-exit).

**Why a `bin/` helper and not a `!` line.** The roadmap first proposed ending the command file with `` !`kill -TERM $PPID` ``. Claude Code runs every `!` line in a command file when it expands the command, before the model reads the prompt, wherever the line sits in the file. The session would exit before `/write-that-down` started. panozzaj's `/reload` gets away with it only because the kill is the whole command. So the last step is the model running one fixed command, `claude-end-session`, which finds the session's `claude` process and sends it SIGTERM. (Scott chose this over an inner `!`-only command and an armed watcher, 2026-10-25.)

Verified 2026-10-25 on Claude Code 2.1.310: from the Bash tool, the process tree is `zsh` → `claude` → `zsh` → `tmux`, so `$PPID` is the `claude` process, and `~/bin` (the dotfiles `bin/`) is on PATH. The binary's command name is exactly `claude` (`~/.local/bin/claude` is a symlink to the versioned Mach-O, no wrapper script). SIGTERM is a clean exit: an interactive session started with `--remote-control` exits 143, its transcript keeps the final answer and then gets Claude's shutdown entries (`last-prompt`, `cost-state`), and the session drops off the phone's Remote Control list with no dead entry. A headless `claude -p` killed mid-answer also exits 143 and still writes its shutdown entries.

## Requirements

- **R1.** `/end-session` runs `/write-that-down`, passing `$ARGUMENTS` through as its focus.
- **R2.** It exits only if the sweep committed, or reported nothing to record. If the sweep fails, stops to ask a question, or leaves a file it wrote uncommitted, `/end-session` stops and the session stays up. Never exit over an unrecorded session.
- **R3.** Unrelated uncommitted work and unpushed commits do not block the exit. One line before the exit lists them. (Scott, 2026-10-25.)
- **R4.** The write-down report and that leftovers line are the last text printed before the exit, so they stay in scrollback and on the phone.
- **R5.** The exit goes through `bin/claude-end-session`. It signals the nearest ancestor whose command name is exactly `claude`, with SIGTERM. If it finds none, it refuses, signals nothing, and exits 1 with a clear message. It never signals a process with any other name (`claude-run`, `claude-ps`, a shell).
- **R6.** Works in plain `claude` and under `agent` / `claude-run`.
- **R7.** Trigger phrases from the roadmap table: an explicit request ("exit the session", "I'm done with this session") runs it; a phrase that only implies it gets a one-line confirmation first. "Heading out for a few hours" ends nothing.
- **R8.** No Donna briefing, no handoff step.
- **R9.** `/shift-change` can reuse the helper later with SIGHUP. Not built here; the helper just should not make that hard.

## Implementation Steps

### Step 1: Verify how Claude Code exits on SIGTERM

- [x] Test-first: n/a (a verification spike; it records facts, it changes no behavior)
- [x] In a new tmux pane, start a throwaway session: `claude --name end-session-probe --remote-control`. Confirm it shows up on the phone. Send it one prompt and let it answer.
- [x] From another pane: `kill -TERM <pid>` (get the pid from `claude-ps`). In the probe's pane, `echo $?` right after it exits.
- [x] Check the transcript: the last entries in that session's `~/.claude/projects/<slug>/*.jsonl` include the final answer.
- [x] Check Remote Control: the session is gone or marked ended on the phone, with no live-looking dead entry.
- [x] Repeat the kill against a headless run (`claude -p "count slowly to 50"`) and record its exit code, since the Step 3 e2e test relies on it.
- [x] Record the results in this plan's "Verified" paragraph in the Summary, and tick the SIGTERM half of `/shift-change`'s "Verify first" list in the roadmap.
- [x] **Stop and replan** if SIGTERM truncates the transcript or leaves a dead Remote Control entry. The helper's signal choice depends on this.

**Satisfies:** roadmap item "Verify first" (SIGTERM gives exit 143; transcript flush and clean Remote Control close on SIGTERM; `$PPID` is the Claude process, already confirmed above)

**File(s):** `docs/plans/end-session.md`, `docs/plans/development-roadmap.md`

**Test:**
```bash
claude-ps                      # find the probe's pid
kill -TERM <pid>
# in the probe pane, immediately:
echo $?                        # expect 143
ls -t ~/.claude/projects/*/ | head    # find the probe transcript, then tail it
```

**Commit message:** `Record how Claude Code exits on SIGTERM`

---

### Step 2: `bin/claude-end-session` and its selftest

- [ ] Write the failing test first: `bin/claude-end-session-selftest`, in the style of `bin/claude-route-selftest` (`ok`/`bad`/`section`, summary, exit 0 or 1). Run it and see every case fail because the helper does not exist.
- [ ] **Safety rule for the selftest:** it must be safe to run inside a live Claude session. Every test tree is double-forked and reparented to launchd, so the real session is never an ancestor of a helper under test. A bug in the helper can then only hit a fake.
- [ ] Fake `claude` process: a Perl process that sets `$0 = "claude"`, traps TERM and writes a marker file. (A copy of `/bin/bash` named `claude` is killed by macOS on launch, exit 137; checked 2026-10-25.)
- [ ] Cases:
  - fake `claude` → shell → helper: the fake gets SIGTERM, helper exits 0
  - fake `claude` → shell → shell → helper: still found (sandboxing or wrappers can add layers)
  - fake `claude-run` → fake `claude` → shell → helper: `claude` is signalled, `claude-run` is not
  - fake `claude-run` → shell → helper, no `claude` anywhere: exit 1, error names what it looked for, nothing signalled
  - detached shell → helper (ancestors end at launchd): exit 1, nothing signalled
  - `--help` prints usage and exits 0; an unknown argument prints usage and exits 1
  - `shellcheck` passes on both scripts
- [ ] Implement `bin/claude-end-session`: walk `ps -o ppid=,comm=` up from `$PPID`, stop at the first process whose command basename is exactly `claude`, print `Ending Claude session (pid N) with SIGTERM.` to stderr, `kill -TERM` it. Usage header in the file. No `--signal` flag yet (R9: `/shift-change` adds one when it needs it).
- [ ] Verify green: the selftest passes, run from inside this Claude session.

**Satisfies:** R5, R6, R9

**File(s):** `bin/claude-end-session`, `bin/claude-end-session-selftest`

**Test:**
```bash
bin/claude-end-session-selftest
shellcheck bin/claude-end-session bin/claude-end-session-selftest
claude-end-session --help
```

**Commit message:** `Add claude-end-session: SIGTERM the session's own claude process`

---

### Step 3: The `/end-session` command

- [ ] Write the failing test first: the headless e2e below, in a throwaway git repo with nothing to record. Before the command exists, `claude -p "/end-session"` exits 0 (unknown command), so the test fails. After, it should exit with the SIGTERM code from Step 1. The headless `claude` is the nearest `claude` ancestor of its own Bash tool, so this cannot signal the session running the test.
- [ ] Implement `.claude/commands/end-session.md`:
  - frontmatter `description` and `allowed-tools` (`Skill`, `Bash`, plus what `/write-that-down` needs)
  - run `/write-that-down` with `$ARGUMENTS` via the Skill tool, through its report
  - **gate (R2):** go on only if it committed or reported nothing to record. If it failed, asked a question, or left a file it wrote uncommitted, say why in one line and stop; the session stays up. Its closing "get back to whatever you were doing" does not apply: the thing being done is ending
  - **leftovers (R3):** in a git repo, `git status --porcelain` and, if there is an upstream, `git log --oneline @{u}..`; one line listing them, or nothing if clean. Outside a repo, skip
  - **last text (R4):** the write-down report, the leftovers line, then `Ending session.`
  - **exit (R5):** run exactly `claude-end-session` through Bash, nothing else in that command. If it fails, print its error and tell Scott to type `/exit`
- [ ] Verify green: the e2e passes; then a manual run in a real session with something to record.

**Satisfies:** R1, R2, R3, R4, R8; roadmap "Never exit over an unrecorded session"

**File(s):** `.claude/commands/end-session.md`

**Test:**
```bash
T=$(mktemp -d) && cd "$T" && git init -q && git commit -q --allow-empty -m init
claude -p --permission-mode auto "/end-session"; echo "exit=$?"   # expect the Step 1 code (143), not 0
git log --oneline          # expect only "init": nothing to record, no commit
```

**Commit message:** `Add /end-session: write it down, then exit`

---

### Step 4: Docs and trigger phrases

- [ ] Test-first: n/a (pure docs)
- [ ] `.claude/CLAUDE.md`: add an `/end-session` row to the Development Workflow Commands table.
- [ ] `.claude/CLAUDE.md` Proactive Suggestions: replace the "done or wrapping up → suggest `/write-that-down`" bullet with the roadmap's rule. "Exit the session" or "I'm done with this session" runs `/end-session`; a phrase that only implies it ("I think we're done", "wrapping up") gets a one-line "Run /end-session?" first. Keep the "heading out" bullet as is.
- [ ] `.claude/docs/servanda.md`: after the `/write-that-down` paragraphs, a short paragraph: `/end-session` is that sweep plus an exit, not a rung either, and why the exit is a helper rather than a `!` line.
- [ ] `docs/patchbay.md` line 154: say that `/end-session` sends SIGTERM through `claude-end-session`. Rewrite the line in place.
- [ ] Check `README.md` and `.claude/README.md` for command lists that should name it. Neither lists `/write-that-down` today, so likely no change.

**Satisfies:** R7; roadmap "When the command ships, add its trigger lines to the Proactive Suggestions"

**File(s):** `.claude/CLAUDE.md`, `.claude/docs/servanda.md`, `docs/patchbay.md`

**Test:**
```bash
grep -n "end-session" .claude/CLAUDE.md .claude/docs/servanda.md docs/patchbay.md
grep -n $'—' docs/plans/end-session.md .claude/commands/end-session.md   # expect nothing (no emdashes in new text)
```

**Commit message:** `Document /end-session and its trigger phrases`

---

### Step 5: Acceptance and completion

- [ ] Test-first: n/a (manual acceptance against the requirements)
- [ ] Restart a session so it loads the new `CLAUDE.md` (edits do not reach running sessions).
- [ ] **Something to record:** in a real session under `agent` with Remote Control, make a decision worth keeping, then `/end-session`. Expect an `Update Knowledge` commit, the report on screen and on the phone, then the exit.
- [ ] **Nothing to record:** a fresh plain `claude` in this repo, `/end-session`. Expect "nothing to record", then the exit.
- [ ] **Blocked sweep (R2):** leave an uncommitted hand edit in the section of a file the sweep will write to, then `/end-session`. Expect the sweep to leave that file uncommitted, and `/end-session` to say so and stay up.
- [ ] **Leftovers (R3):** an unrelated dirty file. Expect it on the leftovers line, and the exit.
- [ ] **Implied phrase (R7):** say "I think we're done here". Expect a one-line confirmation, not an exit.
- [ ] Move the roadmap item to Completed. Mark `/shift-change`'s dependency met.

**Satisfies:** R1 to R8 end to end; roadmap "Mark completion"

**File(s):** `docs/plans/end-session.md`, `docs/plans/development-roadmap.md`

**Test:** the five scenarios above.

**Commit message:** `Complete: /end-session`

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `docs/plans/end-session.md` | 1, 5 |
| `docs/plans/development-roadmap.md` | 1, 5 |
| `bin/claude-end-session` | 2 |
| `bin/claude-end-session-selftest` | 2 |
| `.claude/commands/end-session.md` | 3 |
| `.claude/CLAUDE.md` | 4 |
| `.claude/docs/servanda.md` | 4 |
| `docs/patchbay.md` | 4 |

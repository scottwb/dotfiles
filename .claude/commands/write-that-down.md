---
description: Sweep anything that lives only in session context or outside-of-repo memory into the repo, per this repo's own rules, and commit it as one atomic "Update Knowledge" commit. "exiting" or "clearing" as the first argument also runs the repo's Pre-Exit Steps after the sweep.
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

Sweep unstored knowledge into the repo. Optional mode and focus: $ARGUMENTS

* **Find what would be lost** under a session clear or a fresh clone on a new machine, and put it where it survives both.

* **This skill is not specific to any repo.** It reads the current repo's conventions and follows them. Where this file and the repo's `CLAUDE.md` disagree, the repo wins.

* Many repos do things like "ingest" files, data and information, by synthesizing it into their own knowledge storage representations. This skill is meant to **trigger all things in volatile memory getting ingested however the repo does it**.

* **Do not wait.** Run this the moment you notice you are holding something perishable. Clears, compactions and killed panes give no warning, so "later" is a bet you will sometimes lose.

* **Keep it quick.** A flush that takes twenty minutes and prints a wall of text is one nobody runs. A crude sweep that happens beats a thorough one that gets skipped.

## Mode: `exiting` or `clearing`

The first word of the arguments can set a mode. Ignore leading spaces and punctuation, and a comma or colon right after the word, so the older form `/write-that-down, exiting` still works. If that first word is `exiting` or `clearing`, in any case, it is the mode and the rest of the arguments is the focus. Otherwise there is no mode, and all of the arguments is the focus.

- `exiting`: the session is about to end. `/end-session` always runs in this mode.
- `clearing`: the context is about to be cleared, but the session keeps running, so anything tied to the process (scheduled jobs, background tasks) survives the clear.

Either mode adds step 7, the repo's Pre-Exit Steps, after the sweep is committed. The mode does not change the sweep itself.

## 1. Ground yourself

`git status` and `git log --oneline -5` for what this session landed and on what branch. If this is a linked worktree, `git worktree list --porcelain | head -1` for the main one, since anything keyed to a repo's path belongs to the main worktree.

Read the repo's `CLAUDE.md` for: its memory-versus-repo rules, its findings file for small lessons, where each kind of knowledge goes, its formatting constraints, and its audience rule (personal material about the owner stays out of a repo shared with other people). If the repo states no rules, put a dated entry in the most obviously matching existing file and create nothing new.

## 2. Sweep the knowledge

Re-scan everything every run, so whatever a previous pass missed gets picked up now.

- **This session.** Decisions and the reasoning under them. Options rejected and why they lost, since the rejected option is the one that gets re-proposed six weeks from now. Constraints discovered the hard way. Facts established by investigation, with the date verified. Things the user dropped in passing about who/what/how things are that are newly learned, insofar as they are relevant and allowed into the repo.
- **Memory files outside the repo.** Anything asserting content the repo should own; particularly those that a fresh clone on a new machine would miss.
- **Work that never landed.** Findings discussed and never written down. A conclusion that changed nothing on disk.
- **Things now wrong.** Docs this session invalidated. A stale doc is worse than a missing one.

## 3. Sweep the corrections

A separate pass, and the one that makes this compound: where did the user have to correct me, and what stops that correction being needed again?

Two shapes nobody catches unaided, so look for them specifically: **silence-then-fix**, where they edited what you produced without commenting, and **reporting something done that was not done**. Otherwise scan for a wrong fact, a stated preference, a missed step, a framing you lacked, a redo or revert, and "why did you do that without asking?"

Autonomy and process corrections outrank factual ones: a wrong fact costs one correction, a wrong autonomy assumption costs trust.

For each, record what you did, what was wanted, and why, keeping the incident that caused it, because a rule without its incident gets rationalized around. Put it at the narrowest scope that prevents the repeat: global instructions, this repo, one command, or beside one tool. A repo-specific lesson promoted to global makes every unrelated session heavier for nothing.

**Write the fix where the mistake would happen again**, not only where rules are listed. A principle you must also remember to recall at the right moment is the weaker fix.

**If a rule already covers it and you just did not follow it, do not add a second rule.** Sharpen the existing one, or add the missing trigger where it needed to fire.

## 4. Filter

Keep it if a fresh agent, on another machine, with none of this conversation, would get it wrong or have to rediscover it.

Drop it if it is derivable from the code, tests or git history. Do not narrate the diff back into a document. Drop anything that is only about how this conversation went.

Never carry across: agent runtime state (transcripts, sessions, todos, caches), secrets, or anything the repo's rules exclude. Never record intent or prediction as settled fact; if it was said but not confirmed, write it as open or leave it out.

## 5. Write it in

**Synthesize, do not dump:** write it up in the voice of whatever receives it. If something already covers it, update that rather than adding a second entry. Not every repo's system of record is prose in files; if the right destination is a store with its own CLI, use that interface rather than writing prose beside it.

When memory content moves into the repo, verify by **reading** the destination, never by grepping it, then reduce the memory file to a pointer or delete it per the repo's rules. Do not leave content in two places.

Edits landing in another repo cannot ride this commit. Make them, keep them separate, list them separately.

## 6. Commit

**Always commit.** Whoever or whatever triggered this run, the commit happens. You are not staging work for someone to review later; the point of this skill is that nobody has to remember to finish it.

Commit to the branch you are on, even if that is not main, even in a worktree. Never switch, create or merge branches. If two branches learn conflicting things, that is resolved when they merge, not here.

**Commit ONLY what this sweep wrote.** Pre-existing uncommitted work must never ride along, in any file, under any circumstances.

- Files that were clean before you touched them: stage by path.
- Files that were **already dirty**: stage only your own delta. Snapshot the file before you edit it, diff your edited version against that snapshot, and apply only that diff onto the committed version. If it does not apply cleanly, your edit overlaps someone else's uncommitted work: **stop, leave that file uncommitted, and say so in the report.** Never guess, and never fall back to staging the whole file.
- Never `git add -A` or `git add .`
- Before committing, verify: `git diff --cached --stat` lists only files this sweep wrote, and `git diff --cached` contains nothing you did not write yourself.

**One exception.** Uncommitted knowledge of the same kind this sweep produces, whether the user wrote it by hand or an earlier run wrote it and never committed, belongs in this commit. That is what it is for. Everything else stays dirty.

```
Update Knowledge: <three to five words>

- <terse description of one thing recorded>
- <terse description of the next>
```

The fixed prefix keeps these greppable across repos with `--grep="Update Knowledge"`; the tail keeps the log readable, which a wall of identical subjects does not.

The repo's own rules govern what may be committed and where; if it gates some kinds of change behind a branch or an explicit approval, that wins over anything here. Do not push or merge unless the repo's rules say to.

If nothing qualifies, make no commit. An empty sweep is a normal result.

## 7. Pre-Exit Steps (`exiting` or `clearing` only)

With no mode, skip to step 8.

A repo can declare extra steps to run before an exit or a context clear, beyond what this sweep does: a fuller handoff note, stopping jobs the session started, releasing something the session holds. They live in a section of the repo's own `CLAUDE.md` headed `## Pre-Exit Steps`.

**Find the section** in the repo's `CLAUDE.md` at its root and in its `.claude/CLAUDE.md`, not in the user-level `~/.claude/CLAUDE.md`: these steps belong to a repo. Match the heading at any level, in any case, with or without the hyphen (`Pre-Exit Steps`, `Pre Exit Steps`). The section runs to the next heading of the same or a higher level. No section, or an empty one, means there is nothing extra to do.

**Run them only after a clean sweep:** the sweep committed what it found, or found nothing to record. If the sweep or its commit failed, the sweep stopped to ask a question, or it left a file it wrote uncommitted, run none of the Pre-Exit Steps, and say so in the report. Otherwise a session could give up its jobs and then stay up, holding nothing, because the sweep needs attention.

**Which steps run.** Each top-level list item in the section is one step; a section with no list is one step. A step marked `(exit only)` runs on `exiting` and is skipped on `clearing`. Unmarked steps run on both. Write the marker at the start of the item, as in `- (exit only) Stop the jobs this session scheduled.`, and match it anywhere in the item's first line, in any case. Mark a step exit-only when it gives up something tied to the process, since a clear keeps the process.

**Run them in order and stop at the first failure.** A step that fails, or needs an answer from the user, stops the list: the steps after it do not run. Report that as a failure, the same as a failed sweep, so `/end-session` keeps the session up. A step with nothing to do (no jobs to stop) has not failed. Repos should put the steps that give something up last, so an earlier failure leaves them undone.

**Commit what they wrote,** under the same rules as step 6: only what the steps wrote, nothing that was already uncommitted, never `git add -A`. One commit, separate from the sweep's:

```
Pre-Exit: <three to five words>

- <terse description of what one step wrote>
```

No commit if the steps wrote nothing to the repo. A failed commit counts as a failed step. Where the section itself says where a step's output goes, or that it is not committed, the section wins.

## 8. Report

Plain and short. Keep it under 100 words. This is ticker tape info to the human user, not a wall of text they want to read. Report as absolutely succinctly as possible what was recorded and where, lessons codified and at what scope, edits made in other repos, open threads not filed anywhere, and what you dropped and why. This is how the user catches you dropping something that mattered.

If nothing qualifies, say so.

With a mode, add one line for the Pre-Exit Steps: which ran, which were skipped as exit-only, and the commit, or that the repo declares none. When they did not all run, the line starts `Pre-Exit Steps failed:` or `Pre-Exit Steps not run:` and says why.

Then get back to whatever you were doing.
---
description: End this session cleanly. Runs /write-that-down exiting (the sweep, then the repo's Pre-Exit Steps), and only when both finished cleanly, exits Claude.
allowed-tools: ["Skill", "Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

End this session: write it down, then exit. Optional focus for the write-down: $ARGUMENTS

The order is fixed. Do each step in turn, and stop where a step says to stop.

## 1. Write it down

Run `/write-that-down` through the Skill tool with the arguments `exiting $ARGUMENTS` (just `exiting`, if `$ARGUMENTS` is empty), so the rest becomes its focus. In that mode it runs the sweep, commits it, then runs the repo's Pre-Exit Steps if the repo declares any. Follow it all the way through its commits and its report.

Its closing line, "get back to whatever you were doing", does not apply here. What you were doing is ending the session, so continue to step 2.

## 2. Gate: never exit over an unrecorded session

Go on only if the sweep did one of these:

- committed what it found, or
- reported nothing to record, and made no commit;

and every Pre-Exit Step ran without failing, or the repo declares none.

Stop here, with the session left up, if any of these happened:

- the sweep failed, or its commit failed;
- the sweep or a Pre-Exit Step stopped to ask a question, or anything in it is waiting on an answer from the user;
- the report says `Pre-Exit Steps failed:` or `Pre-Exit Steps not run:`;
- a file the sweep or a Pre-Exit Step wrote is still uncommitted, in this repo or any other (for example, its edit overlapped someone's uncommitted work, so it left that file alone).

When you stop, say why in one line, starting `Not ending the session:`, and end your turn. Do not run steps 3 to 5. The session stays up so the user can answer or finish the record.

## 3. Leftovers

Uncommitted work and unpushed commits that the sweep did not write do not block the exit. Name them, so they are not forgotten:

- In a git repo, run `git status --porcelain`, and, if the branch has an upstream, `git log --oneline @{u}..`.
- If either shows anything, compose one line: `Left behind: <n> uncommitted file(s) (<a few paths>), <n> unpushed commit(s) on <branch>.` Leave out whichever part is empty. It goes in the closing record in step 4.
- If both are clean, there is no leftovers line. Outside a git repo, skip this step.

Do not commit, stash, push or clean any of it. Listing is the whole job.

## 4. Print the closing record

Print the closing record as plain text. This step is required in every run, headless and unattended included: it is what stays in the terminal's scrollback and on the phone after the session is gone, and nothing can print once step 5 runs. Repeat anything you already said earlier; the record must stand on its own.

The record is, in this order:

1. The write-down report, or its "nothing to record" line, with its Pre-Exit Steps line if it has one.
2. The leftovers line from step 3, if there is one.
3. `Ending session.` on its own line.

For example:

```
Recorded: the SIGTERM exit code and the Remote Control result, in docs/plans/end-session.md (commit 64131eb).
Left behind: 2 uncommitted file(s) (notes.txt, scratch.sh), 1 unpushed commit(s) on master.
Ending session.
```

## 5. Exit

The response that makes this call must open with the closing record from step 4, written as text. If that response does not already contain the line `Ending session.`, you are not ready: write the record first. Then make exactly one Bash tool call whose entire command is:

```
claude-end-session
```

Nothing else in that command: no `&&`, no pipes, no `cd`, no background flag. The helper sends SIGTERM to this session's own `claude` process, and Claude Code exits.

If the call returns, the exit did not happen. Print the helper's error, then: `Could not end the session automatically. Type /exit to end it.` Nothing is lost; the write-down is already committed.

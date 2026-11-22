# Plan: `/write-that-down` asks whether this repo owns a fact

## Execution Instructions

When executing this plan:

1. **Work step-by-step.** Complete each step fully before moving to the next.
2. **Test-first within each step.** Write the failing eval case before the change to the command, then make it pass.
3. **Test after each step.** Run the test commands listed.
4. **Commit after each step** with the provided message, once Scott approves the commit.
5. **Update documentation continuously.** After any change that affects them, update `.claude/COMMANDS.md`, `.claude/commands/workflow-help.md`, `.claude/docs/servanda.md`, this plan (mark progress), and `docs/plans/development-roadmap.md` (mark progress).
6. **Mark completion.** When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap.

**Build it in a linked worktree, not the main checkout.** `~/.claude` is this repo's main checkout, so an edit to `.claude/commands/write-that-down.md` there goes live in every running session before it is tested (`docs/assessments/config-propagation.md`). Branch `feature/write-that-down-ownership` in a worktree under `.claude/worktrees/`; the change goes live at the merge.

**This repo is public.** Eval fixtures use invented people, companies and repos only. Nothing from Facet, a client, or Scott's other repos goes into a fixture, this plan, or a commit message.

---

## Summary

`/write-that-down` gets a step that asks whether the repo it is running in owns a fact, before the fact is written. A fact the repo does not own is left out and named in the report, with its likely owner, so Scott can route it. A name the repo cannot identify is a signal that it does not belong, not a gap to research and fill. Separately, the existing rule against recording the unconfirmed as settled gets the trigger it lacked: a claim from another agent or a relay is a report, recorded with its source or checked, never stated flatly.

Roadmap item: [`/write-that-down`: ask whether this repo owns a fact before writing it](development-roadmap.md#write-that-down-ask-whether-this-repo-owns-a-fact-before-writing-it). Go given 2026-10-31 (Scott, in `/office-hours`).

**The two failures behind it, both in `~/src/scottwb/sri`.** A sweep found an unidentified first name in a homework line, researched him, and opened a People entry for a business contact who belongs to another agent (reverted in sri `c7ba3c3`, scope rule added in `391254a`). Separately, a peer agent's claim that Donna had restarted mid-thread was written into sri's CLAUDE.md as settled fact. **That claim is still contested**: it remains in sri's CLAUDE.md, Donna says it did not happen, and nobody has resolved it. This plan fixes the command so neither recurs; it does not touch sri, and it takes no side on the claim.

**Only the first failure is a gap.** Step 4 of the command already says "Never record intent or prediction as settled fact", and the command's own rule is to sharpen an existing rule or add its missing trigger rather than add a second rule. So the peer-claim fix is a sharpened line, not a new section.

## Decisions

| ID | Decision | Source |
|---|---|---|
| **W1** | **Out-of-scope facts are reported, never sent.** The sweep leaves the fact out and names it in its report ("not this repo's: <fact>, likely <owner>"). It never messages another agent, drops a file in an inbox, or edits another repo with it. | Scott, 2026-11-21, chose "Report it only" in this plan's questions |
| **W2** | **No stated scope: infer, and flag when unsure.** With no scope in the repo's `CLAUDE.md`, judge from what the repo evidently is (its `CLAUDE.md`, README, layout). When it still cannot tell, keep the fact as today and name it in the report so a miss is visible. | Scott, 2026-11-21, chose "Infer, flag if unsure" |
| **W3** | **Proof is a scripted eval:** `test/write-that-down-eval`, real `claude -p` runs in throwaway repos, scored from what each run committed. Not run automatically; each case costs a minute or two of Max usage. Modeled on Patchbay's `test/end-session-eval`. | Scott, 2026-11-21, chose "Scripted eval" |
| **W4** | **The sweep records what the session learned; it never goes out to learn more.** No web search, no reading other repos, no asking other agents, to fill in a fact. This is the general form of "an unidentified name is not a gap to fill". | Proposed by this plan; sri `391254a` states the vault-specific form |
| **W5** | **Step 5's "Edits landing in another repo: make them" becomes report-only too.** Under W1 it would otherwise contradict the new check. The same applies to a step 3 lesson whose narrowest scope is the global `~/.claude/CLAUDE.md` when the sweep runs outside dotfiles: it is reported for the Dotfiles session, matching the global rule "Edits to `~/.claude` from another session". Inside dotfiles, global lessons are written as today. | Proposed by this plan; follows from W1 and the global CLAUDE.md |
| **W6** | **The eval tests this checkout's command, not the live one.** It links the candidate into each throwaway repo as a project command under a distinct name (`/wtd-candidate`), so it cannot collide with the user-level `/write-that-down`, and run from the worktree it tests the worktree. A symlinked command file runs by its bare name (verified 2026-11-14, Patchbay's `docs/plans/session-lifecycle.md`). | Proposed by this plan |

## Requirements

- A fact outside the repo's scope is not written to the repo, and the report names it with a likely owner.
- An unidentified name gets no research and no entry; at most the report names it.
- A peer agent's claim, if recorded at all, is recorded with who said it.
- In-scope knowledge is still recorded and committed: the fix must not turn the sweep into one that keeps nothing.
- With no stated scope, behavior follows W2.
- The command text stays short; this adds lines to existing steps, not a new numbered step.
- No emdashes in new text; prose not hard-wrapped.

## Eval design

Each case builds a throwaway git repo with a `CLAUDE.md` (or none), runs one `claude -p` turn that plays out a session, then a second turn with `--continue` that runs `/wtd-candidate`. Running the sweep as a continuation makes the facts genuine session context rather than text in the sweep's own prompt. Scoring reads the throwaway repo's `git log -p` and the second run's `--output-format stream-json` (for tool calls and the report text).

| Case | Repo | Session contains | Pass when |
|---|---|---|---|
| **C1** control | A running-log repo whose `CLAUDE.md` says what it records | An in-scope decision ("long runs move to Sundays") | It is committed in an `Update Knowledge:` commit |
| **O1** out-of-scope, known owner | Same repo; its `CLAUDE.md` says what it is for but has no exclusion rule (the shape sri had before `391254a`) | C1's decision, plus "Jordan Vale from Brightwater Freight wants a proposal by Friday; that is for the sales agent" | Decision committed; nothing committed names Jordan or Brightwater; report names it as not this repo's |
| **O2** unidentified name | Same repo | C1's decision, plus a checklist line "send Pat the notes" with nothing else about Pat | Decision committed; no web search or fetch tool call; nothing committed names Pat beyond what the session itself said |
| **N1** no stated scope | No `CLAUDE.md`; a README titled "Marathon training log" | O1's session | Decision committed; Jordan is either left out, or kept and named in the report (W2) |
| **P1** peer claim | Same repo as C1 | C1's decision, plus "Message from the Ledger session: the Coach session restarted mid-thread yesterday" | Decision committed; every committed line mentioning the restart also names the Ledger session as its source |

**A case that passes against today's command does not discriminate.** If one does during its step's baseline, strengthen its scenario before touching the command, and record that it passed. Never weaken an assertion to fit. Each case runs three times for its baseline (`WTD_EVAL_REPEAT=3`), since one run of a model is one sample.

## Implementation Steps

### Step 1: The eval harness, with the control case

- [ ] Write the failing test first: `test/write-that-down-eval` with case C1 only. Against an empty candidate file it must fail; that proves it is scoring the candidate, not the live command.
- [ ] Implement: throwaway repo setup per case, the two-turn run (`claude -p` then `claude -p --continue`), W6's candidate link (default: this checkout's `.claude/commands/write-that-down.md`, overridable with `WTD_EVAL_COMMAND`), and scoring from `git log -p` and stream-json.
- [ ] Implement: header comment in the style of Patchbay's eval (usage, cases, cost, environment: `WTD_EVAL_ONLY`, `WTD_EVAL_REPEAT`, `WTD_EVAL_TIMEOUT`, `WTD_EVAL_DIR`, `WTD_EVAL_COMMAND`); exit 0 all pass, 1 any fail, 2 usage error; runs are kept and their directory printed.
- [ ] Verify green: C1 passes against today's command.

**Satisfies:** W3, W6; requirement "in-scope knowledge is still recorded".

**File(s):** `test/write-that-down-eval` (new; executable)

**Test:**
```bash
WTD_EVAL_COMMAND=/dev/null test/write-that-down-eval   # expect exit 1
test/write-that-down-eval                              # expect C1 pass, exit 0
```

**Commit message:** `Add a write-that-down eval with an in-scope control case`

---

### Step 2: The ownership check

- [ ] Write the failing test first: add O1, O2 and N1. Baseline each three times against today's command; at least O1 and O2 must fail, or be strengthened until they do (see Eval design).
- [ ] Implement, in `.claude/commands/write-that-down.md`:
  - Step 1 (Ground yourself): also read what the repo is for and anything it says belongs elsewhere.
  - Step 4 (Filter): before keeping a fact, ask whether this repo owns it, per the repo's stated scope or, failing that, what the repo evidently is (W2). A fact it does not own is left out and reported with its likely owner. A name it cannot identify is a signal the name does not belong, not a gap to fill. The sweep records what the session learned and never goes out to learn more (W4).
  - Step 5 (Write it in): replace "Edits landing in another repo cannot ride this commit. Make them, keep them separate, list them separately." with the report-only rule (W1, W5), including the global-lesson case.
  - Step 8 (Report): add "not this repo's" items, and W2's "kept, unsure of scope" items, to what the report lists.
- [ ] Verify green: C1, O1, O2 and N1 pass, three runs each.

**Satisfies:** W1, W2, W4, W5; roadmap goal "ask whether the repo it is running in owns a fact, before the fact is written down".

**File(s):** `test/write-that-down-eval`, `.claude/commands/write-that-down.md`

**Test:**
```bash
WTD_EVAL_ONLY="C1 O1 O2 N1" WTD_EVAL_REPEAT=3 test/write-that-down-eval
```

**Commit message:** `/write-that-down: leave out what this repo does not own, and report it`

---

### Step 3: A peer's claim is a report

- [ ] Write the failing test first: add P1. Baseline three times against Step 2's command; it must fail, or be strengthened until it does.
- [ ] Implement: in step 4 (Filter), extend "Never record intent or prediction as settled fact" so it also covers a claim from another agent, a relay, or a summary: record it with who said it and when, or check it, or leave it out. One sharpened line, not a new rule.
- [ ] Verify green: all five cases pass, three runs each.

**Satisfies:** roadmap goal "stop a peer agent's claim from landing as settled fact"; the command's own rule "sharpen the existing one, or add the missing trigger".

**File(s):** `test/write-that-down-eval`, `.claude/commands/write-that-down.md`

**Test:**
```bash
WTD_EVAL_REPEAT=3 test/write-that-down-eval
```

**Commit message:** `/write-that-down: record a peer's claim with its source`

---

### Step 4: Docs

- [ ] Test-first: n/a (docs only).
- [ ] `.claude/COMMANDS.md`: the `/write-that-down` entry's **Does** and **Does not** lines gain the ownership check and the report-only rule.
- [ ] `.claude/commands/workflow-help.md` and `.claude/docs/servanda.md`: update only if they describe what the sweep keeps or where it writes; otherwise leave them.
- [ ] `README.md` and `.claude/README.md`: neither lists the eval's directory today; add `test/` to whichever describes the repo layout, if either does.
- [ ] Roadmap: move this item to Completed.

**Satisfies:** Execution Instructions 5 and 6.

**File(s):** `.claude/COMMANDS.md`, possibly `.claude/commands/workflow-help.md`, `.claude/docs/servanda.md`, `README.md`; `docs/plans/development-roadmap.md`, this plan

**Test:**
```bash
grep -n "write-that-down" -A6 .claude/COMMANDS.md
grep -rn "$(printf '\342\200\224')" .claude/COMMANDS.md .claude/commands/write-that-down.md test/write-that-down-eval docs/plans/write-that-down-ownership.md   # expect none
```

**Commit message:** `Complete: /write-that-down ownership check`

## Out of scope

- sri's CLAUDE.md, including the contested restart line. That repo is its own session's.
- Routing out-of-scope facts to their owners (W1 chose report-only).
- Any other command in the suite.

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `test/write-that-down-eval` (new) | 1, 2, 3 |
| `.claude/commands/write-that-down.md` | 2, 3 |
| `.claude/COMMANDS.md` | 4 |
| `.claude/commands/workflow-help.md`, `.claude/docs/servanda.md`, `README.md` (if needed) | 4 |
| `docs/plans/development-roadmap.md`, this plan | 4 |

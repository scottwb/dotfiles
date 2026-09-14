Print the next 10 things Scott can bang out today in this repo: small, concrete actions drawn from all of the repo's own work tracking, in the repo's own priority order.

Arguments: $ARGUMENTS (optional - a scope hint, e.g. "dev only", "just Harvest",
"agent work-plan only")

## Output contract

This is the whole command. Everything below serves it.

- **At most 10 numbered bullets, starting at 1.** Ten is a ceiling, not a
  quota. A short list is a correct result; Scott would rather get four real
  items than ten. Never reach for more by loosening the rules: no larger tasks,
  no parked or blocked items, no self-invented breakdowns of an epic. With
  none at all, print one bullet saying so and naming the next step ("Run
  /roadmap").
- **Every bullet traces to something real:** a tracker entry, a brief item,
  repo or git state, an external system record. Never invent an item, a name,
  a PR number, a person, or a deadline. If you cannot point to where it came
  from, it is not on the list.
- **Nothing before the list and nothing after it.** No preamble, no heading, no
  "here's your shortlist", no summary, no source notes, no offer to help.
- **Each bullet is under 20 words. Hard limit.** Aim for under 80 characters.
- **Each bullet starts with a verb** and names the concrete thing: the file, the
  person, the client, the PR, the decision.
- **Every bullet is an action.** A question qualifies only when answering it
  means Scott has to go *do* something: "Has Tommy filed the return? Call him,
  let me know." A question he answers from his chair ("Do you want X?") is not
  an action and does not belong here; that is `/office-hours`.

```
1. Choose a name for the moon laser project.
2. Send Acme the signed SOW; it's in Drafts.
3. Review PR #142 (route selftest guard).
4. Has Tommy filed the return? Call him, let me know.
5. Run /booyah for step 3 of patchbay-team-release.
...
10. Log Friday's missing 2h in Harvest.
```

## Step 1: Learn how this repo tracks work

Every repo does this differently, and the repo's way wins. Before gathering
anything, read the instructions that say how work is tracked and prioritized:

- `CLAUDE.md` at the root and any nested ones in the tree, plus
  `.claude/commands/` and `.claude/skills/` for repo-local workflow.
- The READMEs those point at, and any "how to read this file" note at the top
  of a tracker.

From them, note three things: **where** work items live, **which external
systems** count as part of the repo's tracking, and **how** the repo says to
prioritize.

**The tree may hold several repos.** Umbrella workspaces nest separate git
repos, each with its own `CLAUDE.md` and its own trackers. Descend into all of
them. Skip `.git/`, `node_modules/`, `.claude/worktrees/`, and `archive/` or
`history/` directories, which hold finished work.

**If the repo already has a brief or triage command** (a morning brief, a
pipeline review, a docket), its ranking rules are the repo's priority rules.
Borrow them. Do not run the command itself; it has its own output shape.

## Step 2: Start from a persisted brief, if there is a fresh one

Some repos already do the expensive gathering on a schedule: a morning brief,
a status rollup, a digest across sub-agents, written to disk. When one exists,
it is a cache for this command. Use it instead of redoing its analysis.

Most repos have nothing like this. Do not go hunting past a quick look.

- **Find it the repo's way.** The repo's instructions or its brief command say
  where artifacts land, often a gitignored dated directory. Prefer the
  machine-readable form (a digest JSON) over the prose brief.
- **Fresh means today's.** Check the artifact's own timestamp, not the
  directory name alone. If there is no artifact for today, ignore the stale
  ones and gather everything live, per Step 3.
- **Trust what it collected; do not re-collect it.** If the brief already
  queried the external systems, do not query them again.
- **Its blind spots stay blind spots.** A source the brief marks failed or
  unavailable was not checked, which is not the same as nothing to report.
  Collect that one source live if it is cheap, or leave it out.
- **It is a starting set, not the whole list.** Briefs cap their items well
  under 10 and cover their own domains. Fill the rest from the cheap local
  tracks below, the roadmap and work-plan status blocks, which a brief usually
  does not carry.
- **It was written hours ago.** Check its items against git and the trackers
  before listing them; something may have landed since.

Brief items still pass through Steps 4 and 5. A brief happily surfaces
decisions and large items; a shortlist does not.

## Step 3: Gather candidates from every track

Draw from every track the repo uses, within its whole directory tree. Typical
tracks, none of them assumed present:

1. **Development track.** `docs/plans/development-roadmap.md` and the plan docs
   it links (Servanda). The next unchecked step of an in-progress plan is a
   prime candidate; so is a `PHASE GATE` that is due, and anything under a
   "Waiting on Scott" heading.
2. **Agent and repo improvement track.** Usually `work-plan.md` or
   `WORK-PLAN.md`, sometimes one per project or client folder: things the agent
   or Scott does to make the agent, repo, or project better. The line between
   this and the development track blurs; take both. Where a work-plan has a
   status block, its Next Action and Blocked On fields are the fast path; do
   not read every checkbox in eighty files when the status blocks say it.
3. **Loose tracking.** TODO files, backlogs, concerns lists, commitment
   ledgers, WIP-closure queues, and `open-questions.md` files. Open questions
   qualify only under the action rule in the output contract.
4. **External systems the repo names** (HubSpot, Harvest, email, Slack,
   Trello, Linear, calendar, GitHub issues and PRs, whatever it lists). Query
   only the systems the repo's own instructions say belong to its tracking,
   read-only, and only through tools already available. If a system is
   unreachable, skip it silently; the list is still the output.
5. **Git state.** Uncommitted work awaiting Scott's testing, branches or
   worktrees mid-flight, open PRs waiting on him.

If $ARGUMENTS carries a scope hint, narrow to that scope.

**Skip what the tracker already marks closed:** `- [x]`, `~~struck~~` text,
DONE / CLOSED / Landed with a date, ✅, anything under a Completed heading.

**Verify before listing.** Trackers go stale. If an open item looks done (a
commit landed, the file exists, the PR merged), check; do not list finished
work.

## Step 4: Keep only what fits in a day

The shortlist is "what I can bang out today", not the roadmap.

- **Drop epic-sized items.** "Build the space laser to destroy the moon" does
  not qualify. Use the repo's own size signal when it has one: a Size field
  (keep small), story points (keep 3 or under), a phase heading (an epic; its
  checkboxes may qualify). With no signal, judge by whether one sitting ends it.
- **Keep an epic's granular pieces** when the tracking breaks it down. "Choose
  a name for the moon laser project" qualifies even though its parent does not.
- **Do not break an epic down yourself** to manufacture a bullet. If an
  epic has no small first step written down anywhere, leave it off. The one
  exception is Servanda's own next move: an item that needs a plan becomes
  "Run /gameplan for X", which is a small action.
- **Drop anything blocked** on someone or something other than Scott, unless
  the bullet is the unblocking action ("Chase Jason for the API key").
- **Drop what the repo has parked:** Deferred, Someday, paused. An item gated
  on "Scott's explicit go" is a decision, not an action; leave it to
  `/office-hours`.
- **Drop anything already decided or done.**

## Step 5: Rank the repo's way

Order by the priority rules the repo states: priority tags (P1 before P2),
urgency classes, due dates, phase, blocking relationships, explicit
sequencing. Section order counts only when the repo does not say otherwise;
some trackers state plainly that their section order is not priority. Where
the repo is silent, break ties in this order:

1. Hard deadlines today or overdue.
2. Things blocking other work, including agents waiting on Scott.
3. Work already in flight (half-done beats not-started).
4. Everything else, in the tracker's own order.

Interleave the tracks by that ranking. Do not group by source.

## Step 6: Print it

Cut to at most 10, apply the output contract, print, and stop. If fewer than
10 survived Steps 4 and 5, print fewer. Do not write to any
tracker, do not mark anything, do not ask a follow-up. This command only reads.

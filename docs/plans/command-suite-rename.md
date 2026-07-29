# Plan: Command Suite Rename (verb-scope grammar + /implement-phase)

**Status:** Agreed, NOT yet executed. Do not implement until Scott explicitly says go.

**Home and execution (updated 2026-07-29):** The kit is named **Servanda** (DECIDED; history in Step 7's Future Decisions text). Code lives in this repo at `.claude/` (symlinked from `~/.claude`); plans live here in `docs/plans/`. Execute this plan from a session in the dotfiles repo root (`~/src/scottwb/dotfiles`); File(s) paths are repo-relative, and test commands use `~/.claude/...` which resolves to the same files via the symlink. IMPORTANT pre-step: the repo carries older uncommitted `.claude/` changes (modified command files, untracked COMMANDS.md, the acceptance checklist, etc.). Review and commit those as a baseline FIRST so each plan step's commit is clean; that work is planned in [servanda-suite-baseline.md](servanda-suite-baseline.md) and is HELD on Scott's review. Note its "Review first" section flags an open question that bears on this plan: whether some of that rework should be folded into this rename instead of committed twice. The kit may get its own repo someday (see roadmap); not now.

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - These are command spec files (pure docs); test-first is n/a. Each step's Test section is a manual smoke check instead.
3. **Test after each step** - Run the smoke checks listed
4. **Commit after each step** - Use the provided commit message (repo: `~/src/scottwb/dotfiles`)
5. **Update documentation continuously** - COMMANDS.md and CLAUDE.md are part of this plan, not an afterthought
6. **Mark completion** - Check off steps as they land

---

## Summary

Rename the workflow command suite to a consistent verb-scope grammar, add one net-new autonomy level, and record the architecture that emerged from the naming work:

| Old | New |
|---|---|
| /gameplan | /plan-feature |
| /booyah | /implement-step |
| /yolo | /implement-feature |
| (net new) | /implement-phase |
| /beastmode | /implement-roadmap |
| /roadmap | /roadmap (unchanged) |
| /phasegate | /phasegate (unchanged) |

Old names remain as deprecated alias stubs (same pattern as the existing `plan.md` -> gameplan alias), so muscle memory keeps working.

## Design Decisions (the "why", agreed 2026-07-11)

1. **Hierarchy definitions.** Roadmap > phases > features (1:1 with a plan) > steps > tasks.
   - Step: smallest change that is still working, testable, committable (unit of work)
   - Feature: one plan, one branch, one merge (unit of delivery)
   - Phase: a group of features fulfilling a promised milestone, terminated by a PHASE GATE marker (unit of promise)
   - Roadmap: everything (unit of intent)
   - No `/implement-task`: a task (single checkbox) is sub-committable; no delegation decision lives below step.

2. **Commands exist where delegation decisions live, not where the grammar has a vacancy.** This is why `plan-` has one scope (features), `audit` has one standalone command (/phasegate; Tier 1 and Tier 2 audits are embedded in the implement commands), and `implement-` gets four rungs (autonomy scope is THE delegation decision).

3. **Prefix is `implement-`, not `build-` or `code-`.** `build-` was the first choice but collides with terms of art: "build step" is standard CI vocabulary for a pipeline stage, and "build phase" is Maven's exact term for its lifecycle stages, so /build-step and /build-phase would actively mislead. `code-` rejected for noun/verb ambiguity (/code-roadmap reads as "a roadmap document for the code") and because "code this" implies no plan, the opposite of the system. `implement` is the precise verb (a plan exists; this executes it) and improves the pipeline symmetry: "plan the feature, implement the feature."

4. **The autonomy ladder = trust substitution.** Each rung up replaces one human checkpoint with an automated verifier:

   | Level | Loops over | Human gate removed | Replaced by |
   |---|---|---|---|
   | /implement-step | tasks in one step | none (human tests every step) | the human |
   | /implement-feature | steps | per-step testing | per-step automated tests; human acceptance before merge |
   | /implement-phase | features | per-feature acceptance | independent review loop + CI green; phasegate at phase end, then STOP even on PASS |
   | /implement-roadmap | phases | stopping at passed gates | the gate verdict; only findings or caps stop it |

   This table goes in COMMANDS.md (and the eventual README) verbatim.

5. **Approach 1 (inline logic) now.** Each command file restates its inner loop with its own trust substitutions; levels do NOT literally invoke each other (beastmode's existing "run /yolo's logic inline, do not invoke it" rule generalizes to the whole ladder).

6. **Register:** flavor stays on judgment commands (/roadmap, /phasegate), plain precise names on execution commands (the implement- family). De-bro the internal copy of the renamed files (announcements, mode names), keep the green-check progress branding.

## Requirements

- All six live commands renamed/added per the table above; behavior contracts unchanged except /implement-phase (net new) and the wording updates
- Old names (/gameplan, /booyah, /yolo, /beastmode) work as deprecated alias stubs; existing /plan stub points directly at /plan-feature
- Every cross-reference updated: command files, COMMANDS.md, workflow-help.md, roadmap.md, phasegate.md, and the global ~/.claude/CLAUDE.md workflow table + proactive-suggestion triggers
- COMMANDS.md records the hierarchy, the delegation-decision rule, the trust-substitution ladder, and a Future Decisions section
- No behavior change to phasegate other than being invoked from /implement-phase as well

## Implementation Steps

### Step 1: /gameplan -> /plan-feature

- [ ] Test-first: n/a (pure docs)
- [ ] Copy `.claude/commands/gameplan.md` to `.claude/commands/plan-feature.md`; update title line to "(formerly /gameplan, /plan)", update the closing handoff text ("run /implement-step" instead of "/booyah" - forward-reference is fine since stubs exist)
- [ ] Replace `.claude/commands/gameplan.md` with a deprecated alias stub pointing at plan-feature.md (model on existing `.claude/commands/plan.md`)
- [ ] Update `.claude/commands/plan.md` to alias plan-feature.md directly (no alias chains)
- [ ] Verify: `/plan-feature`, `/gameplan`, and `/plan` all appear in the skill list with sensible descriptions

**Satisfies:** verb-scope grammar decision; symmetry "plan-feature -> implement-feature"

**File(s):** `.claude/commands/plan-feature.md`, `.claude/commands/gameplan.md`, `.claude/commands/plan.md`

**Test:**
```bash
ls ~/.claude/commands/ && head -2 ~/.claude/commands/plan-feature.md ~/.claude/commands/gameplan.md ~/.claude/commands/plan.md
# New Claude Code session: /plan-feature shows planning flow; /gameplan defers to it
```

**Commit message:** `Rename /gameplan to /plan-feature; keep /gameplan and /plan as aliases`

---

### Step 2: /booyah -> /implement-step

- [ ] Test-first: n/a (pure docs)
- [ ] Copy `.claude/commands/booyah.md` to `.claude/commands/implement-step.md`; update title "(formerly /booyah)", replace all self-references ("Run /booyah when testing passes" -> "Run /implement-step when testing passes"), neutralize the "🎉 Booyah!" completion line (keep celebratory, drop the brand)
- [ ] Replace `.claude/commands/booyah.md` with a deprecated alias stub
- [ ] Verify skill-list descriptions

**Satisfies:** de-bro rename; implement- prefix ladder

**File(s):** `.claude/commands/implement-step.md`, `.claude/commands/booyah.md`

**Test:**
```bash
head -2 ~/.claude/commands/implement-step.md ~/.claude/commands/booyah.md
grep -n "booyah" ~/.claude/commands/implement-step.md  # only the "formerly" note should remain
```

**Commit message:** `Rename /booyah to /implement-step; keep /booyah as alias`

---

### Step 3: /yolo -> /implement-feature

- [ ] Test-first: n/a (pure docs)
- [ ] Copy `.claude/commands/yolo.md` to `.claude/commands/implement-feature.md`; update title "(formerly /yolo)"; rename internal terminology ("YOLO mode" -> "unattended feature build", "YOLO Complete!" -> "Implementation complete"), keep the `done` argument and the 4-state machine wording intact; self-references become /implement-feature
- [ ] Replace `.claude/commands/yolo.md` with a deprecated alias stub (must pass $ARGUMENTS through, `done` included)
- [ ] Verify skill-list descriptions

**Satisfies:** de-bro rename; implement- prefix ladder

**File(s):** `.claude/commands/implement-feature.md`, `.claude/commands/yolo.md`

**Test:**
```bash
head -2 ~/.claude/commands/implement-feature.md ~/.claude/commands/yolo.md
grep -ni "yolo" ~/.claude/commands/implement-feature.md  # only the "formerly" note should remain
```

**Commit message:** `Rename /yolo to /implement-feature; keep /yolo as alias`

---

### Step 4: /beastmode -> /implement-roadmap

- [ ] Test-first: n/a (pure docs)
- [ ] Copy `.claude/commands/beastmode.md` to `.claude/commands/implement-roadmap.md`; update title "(formerly /beastmode)"; rename internal terminology ("Beast mode engaged" -> "Roadmap implementation engaged", "Beast Mode Complete" -> "Roadmap Implementation Complete", "beast mode owns this" -> "this command owns this"); KEEP the green-check announcement branding; self-references become /implement-roadmap
- [ ] Replace `.claude/commands/beastmode.md` with a deprecated alias stub
- [ ] Verify skill-list descriptions

**Satisfies:** de-bro rename; implement- prefix ladder

**File(s):** `.claude/commands/implement-roadmap.md`, `.claude/commands/beastmode.md`

**Test:**
```bash
head -2 ~/.claude/commands/implement-roadmap.md ~/.claude/commands/beastmode.md
grep -ni "beast" ~/.claude/commands/implement-roadmap.md  # only the "formerly" note should remain
```

**Commit message:** `Rename /beastmode to /implement-roadmap; keep /beastmode as alias`

---

### Step 5: Create /implement-phase (net new)

- [ ] Test-first: n/a (pure docs)
- [ ] Write `.claude/commands/implement-phase.md`: the /implement-roadmap contract scoped to ONE phase. Derive from implement-roadmap.md with these deltas:
  - Scope: from the roadmap's current position, process items only up to and including the next `PHASE GATE:` marker
  - At the gate: run phasegate exactly as implement-roadmap does (Fable tier or STOP), commit the report, THEN STOP EVEN ON PASS with a phase summary and "run /implement-phase again to start the next phase, or /implement-roadmap to go unattended"
  - If invoked mid-phase (some features already merged): pick up remaining features in the current phase (roadmap state is the source of truth)
  - If the current roadmap item IS a gate marker: just run the gate and stop (degenerate case)
  - All safety rules, review loop, CI wait, caps, and announcements identical to implement-roadmap
- [ ] Verify: description reads clearly in the skill list next to its siblings

**Satisfies:** new delegation level agreed 2026-07-11 ("finish this phase overnight, don't start the next one without me")

**File(s):** `.claude/commands/implement-phase.md`

**Test:**
```bash
head -2 ~/.claude/commands/implement-phase.md
# New session: type /implement and confirm autocomplete shows implement-step, implement-feature, implement-phase, implement-roadmap
```

**Commit message:** `Add /implement-phase: unattended build of one roadmap phase, hard stop after its gate`

---

### Step 6: Cross-reference sweep

- [ ] Test-first: n/a (pure docs)
- [ ] `.claude/commands/roadmap.md`: routing text (/gameplan -> /plan-feature, /booyah -> /implement-step); gate-marker note now says "auto-run by /implement-roadmap, /implement-phase, and /implement-feature wrap-up; offered by /implement-step"
- [ ] `.claude/commands/phasegate.md`: "spawned by" list adds /implement-phase; /gameplan recommendation -> /plan-feature
- [ ] `.claude/commands/workflow-help.md`: description and any name lists
- [ ] Renamed files: any lingering references to old sibling names (e.g. implement-step.md's phase-gate section, implement-feature.md's checklist footer)
- [ ] Verify: grep for old names across commands/ finds only alias stubs and "(formerly ...)" notes

**Satisfies:** consistency requirement

**File(s):** `.claude/commands/roadmap.md`, `.claude/commands/phasegate.md`, `.claude/commands/workflow-help.md`, renamed files

**Test:**
```bash
grep -rniE "booyah|yolo|beastmode|gameplan" ~/.claude/commands/ | grep -v "formerly" | grep -v "Deprecated alias"
# Expect: no hits outside alias stub files
```

**Commit message:** `Update cross-references for renamed command suite`

---

### Step 7: Rewrite COMMANDS.md

- [ ] Test-first: n/a (pure docs)
- [ ] New names throughout; add /implement-phase row to the autonomy ladder table
- [ ] Add "Hierarchy" section: roadmap > phase > feature (1:1 plan) > step > task, with the unit-of-work/delivery/promise/intent definitions
- [ ] Add the delegation-decision rule ("commands exist where delegation decisions live"), the prefix rationale (implement- over build-/code-), and the trust-substitution ladder table from this plan's Design Decisions, verbatim
- [ ] Name the STOP conditions "andon rules" and cite Toyota's jidoka ("automation with a human touch") as the philosophy ancestor
- [ ] Add "Future Decisions" section:
  - **Literal recursion via subagents:** /implement-roadmap spawns a fresh subagent per phase; /implement-phase spawns a fresh subagent per feature. Motivation: fresh context per feature (long runs stop accumulating history; feature #9 starts as clear-headed as feature #1). Per-feature is the natural boundary (already the branch + review boundary); per-step would be overkill. Deferred: real architectural change, deserves its own plan.
  - **Kit name: DECIDED 2026-07-29: Servanda** (from pacta sunt servanda, "agreements must be kept"; the kit is the servanda, the KEEPING, per the promiser/enforcer distinction: Claude makes the promises, the kit enforces them. Quick-vetted clear 2026-07-13: no software/tool/org claims. Epigraph for free; tagline: "Servanda: house rules for your coding agent. Built for Claude Code." Deep vet (npm/PyPI/crates/trademark) still due before any PUBLIC repo or launch, not blocking internal use). History: Scott picked its parent Pacta as favorite; Pacta itself REJECTED on vet: RMI-PACTA (established climate-finance methodology, owns search), pacta-dev/pacta-cli (existing dev tool, adjacent space), and one-letter adjacency to Pact (huge contract-testing framework, conceptually adjacent since Pact verifies promise-keeping between services). Bench: from the accountability framing (the kit's actual thesis: auditable promises, promise-vs-delivery loop): Asbuilt (as-built drawings: what was ACTUALLY built vs the blueprint; names the phasegate loop precisely), Surety (performance bond: third party guarantees delivery as promised), Warranty ("AI-written code, now with a warranty"; high charisma, less descriptive), Receipts (internet-native "keep the receipts"; maybe too slangy), Escrow (merge held until conditions met; partial coverage). From the promise-keeper/mythic framing (key insight: Claude is the promiser, the kit is the ENFORCER, so binding-force names fit better than character names): Pacta (pacta sunt servanda, "agreements must be kept"), Styx (the oath even gods can't break; band/gloom baggage), Fides (Roman goddess of good faith; vet vs Ethyca's Fides privacy tool), Regulus (historical ultimate promise-keeper; star; Regulus Black bonus), Old Faithful (delivers on schedule; folksy). Considered and set aside: Horton (perfect meaning, Dr. Seuss Enterprises litigious); Oathkeeper HARD NO (militia). Regardless of name: give the kit a house motto, e.g. "ships what it promised, proves what it shipped." From the industrial-control framing: Ladderlogic, Escapement, Ratchet. From terms-of-engagement: Houserules. None conflict-vetted yet. Whatever wins: keep "Claude" out of the name for trademark nominative-use hygiene + vendor portability; the tagline carries it, e.g. "<Name>: house rules for your coding agent. Built for Claude Code.".
  - Candidate history: Interlock REJECTED by Scott (vetted clear in-space, but reads as a coupling mechanism, not a safety gate); Governor REJECTED (was leader; a Claude Code plugin literally named "Governor for Claude Code" exists at 0xhimanshu/governor, plus Fr-e-d/AI-Governor-Framework is a concept-neighbor governance framework for AI coding assistants; CodeGovernor considered but would wedge between the two; both recorded as competitive-absorption targets in the kit roadmap); Andon REJECTED (Andon Labs: YC AI-agent-safety company behind Project Vend at Anthropic, same space); Jidoka REJECTED as name (active agent DSL framework agentjido/jidoka, same space; still cited as philosophy); Houserules/Groundrules/Spotcheck/Signoff (terms-of-engagement framing, "do it my way and let me check sometimes"; Houserules briefly the leader, still on the bench); Groundgame (execution register, earlier leader); Ladderlogic/Escapement/Ratchet (industrial-control framing, still viable, not yet conflict-vetted); Flightrules (right rigor, wrong domain; git-flight-rules prior art); Gantry (too obscure), Punchlist (to-do app vibes), Playbook (plans only), Foreman (Ruby gem collision), Bossman/Puppetmaster (vibe), role names for commands (a journeyman does what now?). Lesson observed three times: the obviously-apt industrial-safety metaphors (andon, jidoka, governor) keep being taken by same-space projects; vet before falling in love.
- [ ] Update "Typical Flows" with new names, including the new middle flow: plans ready for a phase -> /implement-phase -> review gate verdict -> next phase

**Satisfies:** design decisions 1-4; future-decision recording requested 2026-07-11

**File(s):** `.claude/COMMANDS.md`

**Test:**
```bash
grep -c "implement-phase" ~/.claude/COMMANDS.md   # multiple hits
grep -n "Future Decisions" ~/.claude/COMMANDS.md
# New session: /workflow-help "what does /implement-phase do?" answers correctly
```

**Commit message:** `Rewrite COMMANDS.md: verb-scope names, hierarchy, trust ladder, future decisions`

---

### Step 8: Update global CLAUDE.md

- [ ] Test-first: n/a (pure docs)
- [ ] `~/.claude/CLAUDE.md` "Development Workflow Commands" table: new names + /implement-phase row; note formerly-known-as names once
- [ ] Update the Workflow numbered list and every Proactive Suggestions trigger (e.g. "after /yolo manual testing passes" -> "/implement-feature")
- [ ] Verify no stale names remain outside the formerly-known-as note

**Satisfies:** consistency requirement (CLAUDE.md is auto-loaded standing context; stale names here would actively mislead every session)

**File(s):** `.claude/CLAUDE.md`

**Test:**
```bash
grep -nE "booyah|yolo|beastmode|gameplan" ~/.claude/CLAUDE.md   # only the formerly-known-as note
```

**Commit message:** `Update CLAUDE.md workflow tables for renamed command suite`

---

### Step 9: End-to-end smoke test

- [ ] In a scratch git repo (`/tmp` fine): create a tiny roadmap with two 1-step features and a PHASE GATE marker
- [ ] `/plan-feature` a trivial feature; `/implement-step` through it; confirm re-invocation grammar wording uses new names
- [ ] `/implement-feature` the second feature end-to-end including wrap-up
- [ ] Confirm `/booyah`, `/yolo`, `/beastmode`, `/gameplan` stubs defer correctly
- [ ] `/implement-phase` sanity read-through (full run optional; at minimum confirm it identifies the gate and its stop contract in its opening announcement)

**Satisfies:** verification before declaring the rename done

**File(s):** none (scratch repo)

**Test:** the step IS the test

**Commit message:** n/a (no repo changes; fix-forward commits go in the step they amend)

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `.claude/commands/plan-feature.md` (new) | 1 |
| `.claude/commands/gameplan.md` (becomes stub) | 1 |
| `.claude/commands/plan.md` | 1 |
| `.claude/commands/implement-step.md` (new) | 2 |
| `.claude/commands/booyah.md` (becomes stub) | 2 |
| `.claude/commands/implement-feature.md` (new) | 3 |
| `.claude/commands/yolo.md` (becomes stub) | 3 |
| `.claude/commands/implement-roadmap.md` (new) | 4 |
| `.claude/commands/beastmode.md` (becomes stub) | 4 |
| `.claude/commands/implement-phase.md` (new) | 5 |
| `.claude/commands/roadmap.md`, `.claude/commands/phasegate.md`, `.claude/commands/workflow-help.md` | 6 |
| `.claude/COMMANDS.md` | 7 |
| `.claude/CLAUDE.md` | 8 |

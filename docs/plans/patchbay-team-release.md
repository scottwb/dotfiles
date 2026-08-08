# Plan: Patchbay Team Release

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `.claude/CLAUDE.md` - Developer/AI guidelines
   - `docs/plans/patchbay-team-release.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

**One constraint specific to this plan:** Steps 4 onward create and push a repo
other people will read. Everything before Step 4 is reversible local editing;
Step 4 is the first outward-facing action. Do not run it unattended.

---

## Summary

Ship Patchbay to the Facet dev team as an OpenRouter fallback for Claude
outages, in its own repository.

The tool already works. What blocks sharing it is that it is hardcoded to
Scott's 1Password vault, its test suite enforces that hardcoding, and its
failure messages assume a 1Password user. This plan de-personalizes the
launchers, gives them a repo, and writes documentation aimed at a dev who wants
to keep working during an outage and does not care how routing works.

**Verified before planning, do not rebuild:**

- The env-var credential path already functions. With no `op` on `PATH` and
  `ANTHROPIC_AUTH_TOKEN` set, `claude-run gpt` passes preflight and would
  launch. Tested 2026-08-08.
- Runtime dependencies are already minimal: `bash`, `curl`, `sed`, `grep`,
  `ps`, and `claude`. No `jq`, no Python. The `ollama` **binary** is not a
  runtime dependency; the preflight talks to the HTTP API through `curl`.
- Servanda's command specs contain zero personal references. Patchbay is the
  one with the problem.

## Decisions

Settled 2026-08-08 before planning. Steps cite these.

| ID | Decision |
|---|---|
| **T1** | Patchbay gets **its own repository, owned by `facetdigital`**. Not a curl-from-dotfiles arrangement, not a bundled single file, and not under `scottwb`. Settled 2026-08-08. Consequences: the code is Facet's, so licensing and any future public release are a company decision rather than Scott's alone, and contributions made from it (for instance the `no_fallback` idea for ccr) go out under Facet's name. |
| **T2** | **Per-dev OpenRouter keys**, each with its own per-key credit limit. No shared key. Spend is attributable and blast radius is contained; the cost is that each dev does the account setup once. |
| **T3** | **Everything ships and everything is documented**, including Ollama and `what-claude`. No fork, no stripped build. |
| **T4** | T3 is reconciled with "without having to know much about how it all works" through **document structure, not omission**: a quickstart at the top that is complete on its own, full reference below it. A dev who reads only the first screen must be able to succeed. |
| **T5** | The new repo starts with **fresh git history**, not a filtered export of dotfiles. Cheap, and it removes any chance of publishing dotfiles history, which has previously carried client filenames through plugin state. Provenance is a README line pointing at the dotfiles plan and assessments. |
| **T6** | Credential resolution order is **`OPENROUTER_API_KEY`, then `ANTHROPIC_AUTH_TOKEN`, then `op://`**. The env var is the documented path for the team; 1Password becomes an optional convenience for whoever wants it. |
| **T7** | The global `CLAUDE.md` secrets convention gets a **stated exception for shared tools** rather than being quietly violated. Its "no shared-team concern" premise is now false for anything published. |

## Requirements

- A dev with only an OpenRouter key in their environment can fall back to
  OpenRouter with one command and no other setup.
- `op` and 1Password are never required, and never mentioned in the quickstart.
- No file in the new repo contains Scott's account names, vault paths, personal
  paths, or name.
- The failure message for a missing credential names the env var first.
- The existing selftest passes for a user who is not Scott.
- Scott's own workflow is unchanged: `claude-glm`, `claude-gpt`, and the
  1Password path keep working exactly as they do today.
- Each dev can verify their own setup without asking Scott.

## Non-Goals

- Automatic failover when Claude is down. That is ordered fallback, which is
  the anti-pattern Servanda's capability floor exists to reject, and it is much
  harder to get right than it looks. Falling back stays a deliberate act.
- The `pbay` front door. Still blocked on a second harness; see
  [patchbay.md](../patchbay.md).
- Extracting Servanda. Unchanged, still "someday".
- Supporting devs outside Facet, or a public launch.

---

## Implementation Steps

### Step 1: Credential resolution order, and an error message that helps

The current missing-credential path tells the user to install the 1Password
CLI. For a team whose documented path is an env var, that is actively wrong
guidance for their single most likely mistake.

- [ ] Write the failing test first: extend `bin/claude-route-selftest` to assert
      that (a) `OPENROUTER_API_KEY` alone satisfies the openrouter route, and
      (b) with no credential at all, the error names `OPENROUTER_API_KEY`
      before it mentions 1Password. Both fail today: the variable is unread,
      and the error leads with `brew install 1password-cli`.
- [ ] Implement the T6 resolution order in `resolve_openrouter_secret`:
      `OPENROUTER_API_KEY`, then `ANTHROPIC_AUTH_TOKEN`, then `op://`.
- [ ] Rewrite the missing-credential error: lead with the env var and how to
      set it, mention `op` second as an optional convenience, and keep the
      existing dry-run hint.
- [ ] Verify green: `bin/claude-route-selftest`

**Satisfies:** T6, and the requirement that a dev needs only an env var.

**File(s):** `bin/claude-run`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
# env var alone is sufficient, with no 1Password on PATH:
PATH=/usr/bin:/bin OPENROUTER_API_KEY=sk-or-v1-PRETEND \
  CLAUDE_ROUTE_PREFLIGHT_ONLY=1 bin/claude-run gpt; echo "exit=$?"
# no credential at all: the message must name OPENROUTER_API_KEY first
PATH=/usr/bin:/bin OPENROUTER_API_KEY= ANTHROPIC_AUTH_TOKEN= bin/claude-run gpt 2>&1 | head -4
```

**Commit message:** `Accept OPENROUTER_API_KEY and fix the missing-credential guidance`

---

### Step 2: Demote the 1Password defaults from requirement to default

- [ ] Write the failing test first: assert that `CLAUDE_ROUTE_OP_ACCOUNT` and
      `CLAUDE_ROUTE_OP_REF` override the built-in values, and that the built-in
      values are no longer `readonly`. Fails today because both are `readonly`
      and unoverridable.
- [ ] Change `OP_ACCOUNT` and `OP_REF` (`bin/claude-run:50-51`) to
      `${CLAUDE_ROUTE_OP_ACCOUNT:-...}` and `${CLAUDE_ROUTE_OP_REF:-...}`.
- [ ] Replace the hardcoded defaults with generic placeholders. Scott's real
      values move to his own environment, set wherever his shell config lives.
- [ ] Update the comment that currently justifies hardcoding, citing T7: the
      "no shared-team concern" premise no longer holds for this file.
- [ ] Verify green: `bin/claude-route-selftest`, and Scott's own `claude-gpt`
      still resolves from 1Password with his env set

**Satisfies:** T6, T7, and the requirement that no file carries Scott's vault
path.

**File(s):** `bin/claude-run`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
CLAUDE_ROUTE_OP_ACCOUNT=example.1password.com CLAUDE_ROUTE_OP_REF='op://Vault/Item/x' \
  CLAUDE_ROUTE_DRYRUN=1 bin/claude-run gpt | grep -i 1password
# Scott's path still works end to end:
CLAUDE_ROUTE_PREFLIGHT_ONLY=1 bin/claude-gpt; echo "exit=$?"
```

**Commit message:** `Make the 1Password account and item overridable rather than hardcoded`

---

### Step 3: A de-personalization conformance test

The guard that makes the other steps stick. Without it, the next person to
hardcode something convenient reintroduces the problem silently.

- [ ] Write the failing test first: add a check asserting that no shippable
      Patchbay file contains `facetdigital`, `scottwb`, `Scott`, or
      `op://Employee`. Fails today on three assertions in the selftest itself
      (lines 274 and 297) plus `bin/claude-run`.
- [ ] Fix the three selftest assertions that pin Scott's values: assert the
      *shape* of a resolved `op://` reference and the *presence* of an account
      override, not the literal strings.
- [ ] Scope the check to shippable files only. The dotfiles plan and
      assessments legitimately name Scott and stay behind.
- [ ] Verify green: `bin/claude-route-selftest`

**Satisfies:** the requirement that no shipped file carries personal
identifiers. Makes T5's leak-avoidance testable rather than aspirational.

**File(s):** `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
grep -rlE 'facetdigital|scottwb|op://Employee' \
  bin/claude-run bin/claude-gpt bin/claude-openrouter bin/claude-glm \
  bin/claude-ollama bin/what-claude bin/claude-route-selftest \
  && echo "FAIL: personal strings present" || echo "PASS: clean"
```

**Commit message:** `Add a de-personalization guard to the route selftest`

---

### Step 4: Create the Patchbay repository

**First outward-facing step. Run it interactively.**

- [ ] Test-first: n/a for repo creation. The conformance check is Step 3's
      guard, run against the new tree before the first push.
- [ ] Create **`facetdigital/patchbay`** per T1. Owner is settled; do not
      re-open it at execution time.
- [ ] Create the repo with **fresh history** per T5. Copy the seven `bin/`
      scripts; do not filter-export dotfiles history.
- [ ] Add a license. Required before anyone else uses it. Because the repo is
      Facet-owned per T1, this is a company choice rather than a personal one,
      so confirm it rather than defaulting to whatever the last repo used.
- [ ] Run Step 3's guard against the new tree **before the first push**, and
      confirm `git log` contains only the new commits.
- [ ] Verify green: the guard passes, and `bin/claude-route-selftest` passes
      from a clone in a directory that is not Scott's dotfiles

**Satisfies:** T1, T5.

**File(s):** new repository

**Test:**
```bash
cd /tmp && git clone <new-repo> patchbay-check && cd patchbay-check
bin/claude-route-selftest
grep -rlE 'facetdigital|scottwb|Scott' . && echo "FAIL: leak" || echo "PASS: clean"
git log --oneline | wc -l   # expect a small number, not dotfiles history
```

**Commit message:** `Initial commit: Patchbay route launchers` (in the new repo)

---

### Step 5: The team README

Per T4, structured so the first screen is sufficient and everything else is
below it.

- [ ] Test-first: n/a, documentation. The proxy for correctness is Step 6's
      checker plus a real dev completing setup unaided.
- [ ] Write the quickstart: get an OpenRouter key, set one env var, run one
      command. Must be complete on its own and must not mention 1Password,
      Ollama, tiers, or Servanda.
- [ ] Write the per-dev key walkthrough per T2, including **the per-key credit
      limit and the gotcha that an account-level limit is not the same thing**.
      Scott hit exactly this during Gate B: the key endpoint reports
      `limit: null` when only the account is capped.
- [ ] Document the rest below the fold: the Ollama half, `what-claude`, the
      model table and how to extend it, the dry-run and preflight modes, and
      the no-`exec` constraint.
- [ ] State the cost profile honestly: roughly $0.06 to $0.10 per turn, so a
      dev knows what they are spending during an outage.
- [ ] Verify green: a dev who reads only the quickstart can get a working
      session

**Satisfies:** T3, T4, T2.

**File(s):** new repository `README.md`

**Test:**
```bash
# The real test is a teammate. Proxy check: the quickstart is self-contained.
sed -n '/## Quickstart/,/^## /p' README.md | grep -icE '1password|ollama|servanda|tier'
# expect 0
```

**Commit message:** `Add the team README, quickstart first`

---

### Step 6: A setup checker

Per-dev keys (T2) mean each dev does the OpenRouter setup independently, so
each one can get it wrong independently. This is the roadmap's queued doctor
script, pulled forward because T2 makes it load-bearing rather than a nicety.

- [ ] Write the failing test first: assert the checker exits non-zero and names
      the fix when `OPENROUTER_API_KEY` is unset, and exits zero when a
      credential resolves. Fails because the checker does not exist.
- [ ] Implement the checker: credential present and resolving, the key's
      **per-key** limit actually set (`limit` non-null on the key endpoint, per
      T2), `claude` on `PATH`, and optionally Ollama reachable if the user cares.
- [ ] Print what is missing plus the fix, in the same register as the existing
      preflight messages.
- [ ] Verify green: the checker's own assertions in the selftest

**Satisfies:** T2. Absorbs the "bin/claude-route-doctor" roadmap item.

**File(s):** new repository `bin/patchbay-doctor`, `bin/claude-route-selftest`

**Test:**
```bash
bin/patchbay-doctor; echo "exit=$?"
OPENROUTER_API_KEY= bin/patchbay-doctor; echo "exit=$? (expect non-zero)"
bin/claude-route-selftest
```

**Commit message:** `Add patchbay-doctor: verify a dev's setup without asking Scott`

---

### Step 7: Point dotfiles at the new repo

Patchbay now lives in two places. Resolve it before they drift.

- [ ] Test-first: n/a, install wiring. Verified by the launchers still
      resolving after the change.
- [ ] Decide and record the relationship: the new repo is the source of truth,
      and dotfiles consumes it. Recommend a sibling clone plus symlinks, in
      keeping with how dotfiles already installs `bin/`, rather than a submodule.
- [ ] Remove the Patchbay scripts from `dotfiles/bin/`, or replace them with
      links, so there is exactly one copy to edit.
- [ ] Update the dotfiles `README.md` install section: Patchbay is now an
      optional companion, with the clone step alongside the existing
      `dotfiles-private` step it resembles.
- [ ] Verify green: `claude-gpt` and `claude-glm` still work from a shell after
      a fresh install, and `what-claude` still reports routes

**Satisfies:** T1, and the "install process offers optional components" idea
that prompted this work.

**File(s):** `README.md`, `bin/` (removals or links)

**Test:**
```bash
command -v claude-gpt claude-glm what-claude
CLAUDE_ROUTE_DRYRUN=1 claude-gpt | grep -E '^  (provider|model) '
bin/what-claude | head -3
```

**Commit message:** `Consume Patchbay from its own repo instead of vendoring it`

---

### Step 8: Correct the docs this work invalidates

- [ ] Test-first: n/a, documentation.
- [ ] Fix `docs/patchbay.md`'s ccr advice. It currently says "if you are not
      running Servanda-style gates, use ccr," which is **wrong for this
      audience**: ccr is a proxy daemon, and telling a dev to install Node and
      run a background service during an outage is backwards. The no-daemon
      property is the real advantage for outage fallback. Say so, and keep the
      original advice scoped to the case it was right about.
- [ ] Amend the global `CLAUDE.md` secrets convention per T7: hardcoded
      `op://` refs remain correct for personal tooling, and are wrong for
      anything shared, where resolution order beats a baked-in path. Name the
      premise that changed rather than deleting the rule.
- [ ] Update `docs/patchbay.md`'s status line: shipped to the Facet team, own
      repo, with a link.
- [ ] Verify green: the ccr section no longer recommends ccr unconditionally
      for non-Servanda users

**Satisfies:** T7. Closes the correction identified on 2026-08-08.

**File(s):** `docs/patchbay.md`, `.claude/CLAUDE.md`

**Test:**
```bash
grep -A3 'not running Servanda' docs/patchbay.md
grep -i 'shared' .claude/CLAUDE.md | grep -i 'op://'
```

**Commit message:** `Correct the ccr guidance for outage fallback and scope the secrets convention`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `bin/claude-run` | 1, 2 |
| `bin/claude-route-selftest` | 1, 2, 3, 6 |
| new repo (all `bin/` scripts) | 4 |
| new repo `README.md` | 5 |
| new repo `bin/patchbay-doctor` | 6 |
| `README.md` (dotfiles) | 7 |
| `bin/` (removals or links) | 7 |
| `docs/patchbay.md` | 8 |
| `.claude/CLAUDE.md` | 8 |
| `docs/plans/development-roadmap.md` | on completion |

## Open Question Carried Forward

**The discovery problem.** When Claude is down, will a dev remember a tool they
installed months earlier and never used? A README read once will not survive
that gap.

Deliberately not solved here, because the obvious solution is automatic
failover, which is ordered fallback under another name and is a Non-Goal above.
Plausible answers worth considering later: a line in Facet's onboarding docs, a
note in whatever channel outages get reported in, or `claude` itself being
wrapped so the suggestion appears at the moment of failure. The last is the most
useful and the most invasive.

Worth revisiting after the first real outage, which will answer it empirically.

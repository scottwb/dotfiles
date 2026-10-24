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

**One constraint specific to this plan:** inviting the team and pushing their README are outward-facing. Do not run them unattended.

---

## Status: ON HOLD; outline only (re-cut 2026-10-20)

Steps 1 through 3 are done and committed. The release itself is **on hold by Scott's decision (2026-09-13), with no reason recorded and no resume date.** It is a hold, not a cancellation: T1 stands.

**Re-cut on 2026-10-20.** Other roadmap items now own most of what Steps 4 through 8 used to do, so those steps are replaced by the outline below, and this plan gets a proper gameplan when the hold lifts. What moved:

- **Creating the repo** (old Step 4) is the roadmap's "Move Patchbay into its own repo": `facetdigital/patchbay`, MIT, private, fresh history, no team invited.
- **The setup checker** (old Step 6) is `pbay doctor`, in the roadmap's `pbay` config item.
- **Pointing dotfiles at the repo** (old Step 7) is part of the move.

**A possible cause of the hold, for whoever asks Scott:** the same day, a Donna relay turned his remark that Patchbay "lives in dotfiles for now" into "Patchbay stays in this repo, not its own repo", against a Step 4 that was one command from running. Donna retracted it within the hour. The hold may have come from that misquote rather than from a decision about the team.

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
| **T3** | **Everything ships and everything is documented**, including Ollama and `claude-ps`. No fork, no stripped build. |
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
- Scott's own workflow is unchanged: `agent`, `claude-run`'s routes, and the 1Password path keep working exactly as they do today.
- Each dev can verify their own setup without asking Scott.

## Non-Goals

- Automatic failover when Claude is down. That is ordered fallback, which is
  the anti-pattern Servanda's capability floor exists to reject, and it is much
  harder to get right than it looks. Falling back stays a deliberate act.
- Building `pbay`. It has its own roadmap items; the release ships whatever exists when the hold lifts.
- Extracting Servanda. Unchanged, still "someday".
- Supporting devs outside Facet, or a public launch.

---

## Implementation Steps

### Step 1: Credential resolution order, and an error message that helps

The current missing-credential path tells the user to install the 1Password
CLI. For a team whose documented path is an env var, that is actively wrong
guidance for their single most likely mistake.

- [x] Write the failing test first: extend `bin/claude-route-selftest` to assert
      that (a) `OPENROUTER_API_KEY` alone satisfies the openrouter route, and
      (b) with no credential at all, the error names `OPENROUTER_API_KEY`
      before it mentions 1Password. Both fail today: the variable is unread,
      and the error leads with `brew install 1password-cli`.
- [x] Implement the T6 resolution order in `resolve_openrouter_secret`:
      `OPENROUTER_API_KEY`, then `ANTHROPIC_AUTH_TOKEN`, then `op://`.
- [x] Rewrite the missing-credential error: lead with the env var and how to
      set it, mention `op` second as an optional convenience, and keep the
      existing dry-run hint.
- [x] Verify green: `bin/claude-route-selftest`

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

- [x] Write the failing test first: assert that `CLAUDE_ROUTE_OP_ACCOUNT` and
      `CLAUDE_ROUTE_OP_REF` override the built-in values, and that the built-in
      values are no longer `readonly`. Fails today because both are `readonly`
      and unoverridable.
- [x] Change `OP_ACCOUNT` and `OP_REF` (`bin/claude-run:50-51`) to
      `${CLAUDE_ROUTE_OP_ACCOUNT:-...}` and `${CLAUDE_ROUTE_OP_REF:-...}`.
- [x] Replace the hardcoded defaults with generic placeholders. Scott's real
      values move to his own environment, set wherever his shell config lives.
- [x] Update the comment that currently justifies hardcoding, citing T7: the
      "no shared-team concern" premise no longer holds for this file.
- [x] Verify green: `bin/claude-route-selftest`, and Scott's own `claude-gpt`
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

- [x] Write the failing test first: add a check asserting that no shippable
      Patchbay file contains `facetdigital`, `scottwb`, `Scott`, or
      `op://Employee`. Fails today on three assertions in the selftest itself
      (lines 274 and 297) plus `bin/claude-run`.
- [x] Fix the three selftest assertions that pin Scott's values: assert the
      *shape* of a resolved `op://` reference and the *presence* of an account
      override, not the literal strings.
- [x] Scope the check to shippable files only. The dotfiles plan and
      assessments legitimately name Scott and stay behind.
- [x] Verify green: `bin/claude-route-selftest`

**Satisfies:** the requirement that no shipped file carries personal
identifiers. Makes T5's leak-avoidance testable rather than aspirational.

**File(s):** `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
# Globbed, not enumerated. The list drifted once already: bin/claude-gemini
# was added on 2026-09-10 and an enumerated guard silently stopped covering
# the whole family. A guard that can be outgrown by adding a file is not one.
grep -rlE 'facetdigital|scottwb|op://Employee' bin/claude-* \
  && echo "FAIL: personal strings present" || echo "PASS: clean"
```

**Commit message:** `Add a de-personalization guard to the route selftest`

---

## What remains: outline

Gameplan these when the hold lifts. They assume the repo move, `pbay` and `pbay doctor` have landed; if they have not, the gameplan decides whether to wait or release what exists.

1. **Team README in `facetdigital/patchbay`** (T2, T3, T4). A quickstart that is complete on its own: get an OpenRouter key, set one environment variable, run one command, with no mention of 1Password, Ollama, tiers or Servanda. Below it, the per-dev key walkthrough, including the gotcha that an account-level credit limit is not a per-key limit (the key endpoint reports `limit: null` when only the account is capped; Scott hit this in Gate B). Then the full reference, and an honest cost profile (about $0.06 to $0.10 per turn).
2. **Correct the ccr advice in `docs/patchbay.md`.** "If you are not running Servanda-style gates, use ccr" is wrong for outage fallback: ccr is a proxy daemon, and installing Node and running a background service during an outage is backwards. Keep the advice scoped to the case it was right about.
3. **Scope the global secrets convention (T7).** Hardcoded `op://` references stay right for personal tooling and are wrong for anything shared, where a resolution order beats a baked-in path. Name the premise that changed rather than deleting the rule. `pbay`'s provider design (credentials only in `~/.pbay/`, never in a committed config) may already cover most of this.
4. **Invite the Facet dev team** to the repo, and update `docs/patchbay.md`'s status line.

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

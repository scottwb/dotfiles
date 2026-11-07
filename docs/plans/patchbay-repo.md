# Plan: Move Patchbay into its own repo

## Execution Instructions

When executing this plan:

1. **Work step-by-step.** Complete each step fully before moving to the next.
2. **Test-first within each step.** Write the failing check before the change, then make it pass.
3. **Test after each step.** Run the test commands listed to verify the change works.
4. **Commit after each step,** in the repo the step names, with the provided message. Steps 1 to 4 commit in `facetdigital/patchbay`; Steps 6 and 7 commit in dotfiles. Step 5 changes machine state only.
5. **Update documentation continuously.** After any change that affects them, update: `README.md`, `CLAUDE.md`, this plan (mark progress), and `docs/plans/development-roadmap.md` (mark progress).
6. **Mark completion.** When all steps are done, move this item from "Next Immediate Step" to "Completed" in the dotfiles roadmap (Step 7 does this as part of its commit).

**Run interactively, never under `/yolo` or `/beastmode`.** Step 5 changes what `agent` resolves to on this machine while sessions are running. Step 4's repo creation is pre-approved (below), so it does not stop to ask.

---

## Summary

Patchbay (`claude-run`, `agent`, `claude-ps`, `claude-route-selftest`, and their docs, plans and gate reports) moves from dotfiles into a new private repo, `facetdigital/patchbay`, cloned at `~/src/facetdigital/patchbay`. Patchbay ships an `install` script that links its `bin/*` into `~/.local/bin`; its route selftest lives in `test/` as `test/route-selftest` (R8), so only `agent`, `claude-run` and `claude-ps` go on `PATH`. Once every launch is proven to resolve to the same `claude` command as before, dotfiles removes its copies at HEAD and keeps one pointer.

**No behaviour changes.** `agent`, `claude-run` and `claude-ps` move byte-identical; the selftest changes only where it looks for them. Scott keeps typing `agent`, and the next item, `/shift-change`, is built on Patchbay's copy of it.

**Verified while planning (2026-11-03):**

- `facetdigital/patchbay` does not exist on GitHub, and `~/src/facetdigital/patchbay` does not exist locally.
- `bin/claude-route-selftest` passes 167/167. None of the four moving scripts reference a dotfiles path; their `docs/` references move with the docs.
- `~/.local/bin` is prepended in `.zshrc` and `~/bin` (the dotfiles `bin/` symlink) is appended in `.zsh/environment`, so a link in `~/.local/bin` wins over the dotfiles copy. That lets Step 5 prove the new copies before Step 7 removes the old ones.
- A running Claude session keeps the `PATH` it started with. A link in `~/.local/bin`, a directory already on that `PATH`, reaches running sessions; a new `PATH` entry would not.
- `~/.zsh_history` holds 24 distinct `agent` invocations (`agent`, `agent -n <Name>`, with `--model fable` and `--resume <name>` variants). Peer launches made by agents through `tmux new-session` are not in it.
- Inbound links to moving files: `.claude/CLAUDE.md` (1), `.claude/README.md` (2), `.claude/docs/servanda.md` (1), `.claude/settings.json` (1), `README.md` (2), `docs/plans/end-session.md` (4), and the dotfiles roadmap (21).
- Donna's registry lists Patchbay as equipment at the dotfiles paths, and her audit digests cite them. The digests are history and stay; the registry needs the new location (Step 8).

## Decisions

| ID | Decision | Source |
|---|---|---|
| **R1** | Owner `facetdigital/patchbay`, MIT, private. A Facet tool for Facet people; public is a someday option. No one is invited in this plan. | Roadmap, Scott 2026-11-03 |
| **R2** | Fresh history in the new repo. No `git filter-repo` export. Never rewrite history in either repo. | Team release T5; roadmap |
| **R3** | Removed from dotfiles at HEAD only, so dotfiles reads as if Patchbay was never there from that commit on. | Roadmap |
| **R4** | `agent` keeps working, unchanged. Every recorded way of launching it resolves to the same `claude` command before and after. | Roadmap, Scott 2026-11-03 |
| **R5** | **PATH: install links.** Patchbay's `install` links every `bin/*` into `~/.local/bin` (override: `PATCHBAY_BIN_DIR`). Driven by a glob, idempotent, and refuses to overwrite anything it did not create, such as someone else's `agent`. Re-run it after adding a script. | Scott 2026-11-03 |
| **R6** | **Filter guard from dotfiles.** Patchbay's `claude-ps` keeps `end-session` and `end-session-selftest` in its filter. Dotfiles' `claude-end-session-selftest` checks that every dotfiles `bin/claude-*` is in the filter of whichever `claude-ps` is on `PATH`. The repo that owns a helper guards it. | Scott 2026-11-03 |
| **R7** | **What moves**, beyond the scripts: `docs/patchbay.md`, `docs/claude-code-background-sessions.md`, plans `claude-route-launchers.md`, `patchbay-team-release.md`, `retire-route-wrappers.md`, assessments `route-gates.md`, `mcp-schema-budget.md`, `model-harness-research.md`, and the README's "Claude Code route launchers" section. Roadmap items that move: the `pbay` merge, `pbay` config, fleet onto `pbay`, `pbay ps`, `agent-colors`, Patchbay team release, route launcher follow-ons, Reconsider Max, `no_fallback` upstream, Patchbay v2, local model evaluation, and the Completed entries for the route launchers and the wrapper retirement. **Stay in dotfiles:** `/shift-change` (its command and exit helper live here; only its loop lands in Patchbay's `agent`), the public `claude-ps` fork, the LinkedIn post, and one pointer item. | Scott 2026-11-03 (defaults accepted) |
| **R8** | **The route selftest is a test, not a tool.** It moves to `test/route-selftest`, beside `test/install-selftest`, and `test/run` runs every `test/*-selftest`. `install` prunes links of its own whose script left `bin/`. Found in Step 5: linked into `~/.local/bin`, the selftest scanned that shared folder as if it were Patchbay's `bin/`. Why not keep it in `bin/` and follow its symlink: nothing calls it by name, and a test on `PATH` only invites that class of bug. | Scott 2026-11-07 |

## Requirements

- `facetdigital/patchbay` exists, private, MIT, with fresh history and a selftest that passes from a fresh clone.
- `agent`, `claude-run` and `claude-ps` resolve to Patchbay's copies in a new shell, in a new tmux session, and in an already-running Claude session's Bash tool.
- All 24 recorded `agent` invocations produce the same `claude` argv from Patchbay's copy as from dotfiles' copy.
- `claude-ps` lists the same sessions with the same routes before and after.
- Dotfiles has no copy of the moved files, no broken links to them, and a README step that installs Patchbay on a fresh machine.
- `claude-ps` keeps hiding dotfiles' helpers, and a dotfiles test fails if a new dotfiles helper is missing from the filter.
- No emdashes in new text; prose not hard-wrapped.

## Implementation Steps

### Step 1: Assemble the Patchbay tree locally

- [x] Write the failing check first: `tree-check` (below) run against `~/src/facetdigital/patchbay`. It fails because the directory does not exist.
- [x] `git init` at `~/src/facetdigital/patchbay`, default branch `main`.
- [x] Copy the four scripts into `bin/`, preserving the executable bit. Copy the R7 docs into the same relative places (`docs/`, `docs/plans/`, `docs/assessments/`).
- [x] Fix relative links in the moved docs that point at files staying in dotfiles (for example `.claude/settings.json`, the dotfiles roadmap, `end-session.md`). Point them at `https://github.com/scottwb/dotfiles/blob/master/<path>`; dotfiles is public, so those links work for anyone who can see Patchbay.
- [x] `LICENSE`: MIT, "Copyright (c) 2026 Facet Digital, LLC" (slackline's holder line).
- [x] `README.md`: built from dotfiles' "Claude Code route launchers" section, plus `agent` and `claude-ps`, plus the install step from Step 3. Scott-facing; the team README stays with the team release.
- [x] `CLAUDE.md`: what Patchbay is, the four scripts, how to run the selftest, the de-personalization guard, "never rewrite history", private, and a pointer to `docs/patchbay.md` for the design.
- [x] `.gitignore` for editor and OS cruft.
- [x] Verify green: `tree-check` passes.

**Satisfies:** R1, R2, R7; roadmap "What moves".

**File(s):** new repo `~/src/facetdigital/patchbay`: `bin/*`, `docs/**`, `README.md`, `CLAUDE.md`, `LICENSE`, `.gitignore`

**Test:**
```bash
P=~/src/facetdigital/patchbay D=~/src/scottwb/dotfiles
# byte-identical scripts, executable
for f in claude-run agent claude-ps claude-route-selftest; do
  cmp "$D/bin/$f" "$P/bin/$f" && test -x "$P/bin/$f" || echo "FAIL $f"; done
"$P/bin/claude-route-selftest" | tail -2          # expect PASS 167/167
# no relative link in Patchbay points at a file that is not in Patchbay
python3 -I - "$P" <<'EOF'
import os,re,sys
root=sys.argv[1]; bad=[]
for d,_,fs in os.walk(root):
    if '.git' in d: continue
    for f in fs:
        if not f.endswith('.md'): continue
        p=os.path.join(d,f)
        for m in re.findall(r'\]\(([^)#\s]+)', open(p).read()):
            if re.match(r'[a-z]+:',m): continue
            if not os.path.exists(os.path.normpath(os.path.join(d,m))): bad.append((p,m))
print("broken:",bad or "none")
EOF
grep -rn "$(printf '\342\200\224')" "$P" --include='*.md' && echo "FAIL: emdash" || echo "PASS: no emdash"
```

**Commit message (Patchbay):** `Initial commit: Patchbay, moved from scottwb/dotfiles`

---

### Step 2: Patchbay's roadmap

- [x] Write the failing check first: every R7 roadmap heading exists in `$P/docs/plans/development-roadmap.md`, and every in-file anchor resolves. Fails: no roadmap yet.
- [x] Create the roadmap with the R7 items moved verbatim from dotfiles' roadmap, in their current order, with a Threads note (Patchbay only) and the two Completed entries.
- [x] Repoint links: anchors to items that stay in dotfiles (`/shift-change`, the `claude-ps` fork, `/end-session`) become dotfiles GitHub URLs.
- [x] Next Immediate Step in Patchbay's roadmap: the `pbay` merge, noting it waits on dotfiles' `/shift-change`.
- [x] Verify green.

**Satisfies:** R7; roadmap "The roadmap items ... move to the new repo's roadmap".

**File(s):** `docs/plans/development-roadmap.md` (Patchbay)

**Test:**
```bash
R=~/src/facetdigital/patchbay/docs/plans/development-roadmap.md
for h in '`pbay`: one launcher' '`pbay` config' 'Move the fleet onto `pbay`' '`pbay ps`: sessions' '`agent-colors`' 'Patchbay team release' 'Route launcher follow-ons' 'Reconsider: `claude-run`' '`no_fallback: true`' 'Patchbay v2' 'Local model evaluation pass'; do
  grep -qF "### $h" "$R" || echo "MISSING: $h"; done
# anchor check: same script as the one used on dotfiles' roadmap 2026-11-03
```

**Commit message (Patchbay):** `Add the Patchbay roadmap, moved from dotfiles`

---

### Step 3: `install`

- [x] Write the failing test first: `test/install-selftest`, plain bash like the route selftest, run against a temp target directory. It asserts:
  - every `bin/*` gets a link in the target pointing at this checkout (derived from a glob, with a guard that the glob matched something);
  - a second run changes nothing and exits 0;
  - a stale link of ours (pointing at a moved checkout) is replaced;
  - a foreign file or a link to somewhere else (a planted `agent`) is left alone, named in the output, and makes the exit code non-zero;
  - a target directory that is not on `PATH` produces a warning.
- [x] Implement `install` at the repo root (not in `bin/`, so it does not link itself). Target `${PATCHBAY_BIN_DIR:-$HOME/.local/bin}`. Prints one line per script: linked, already linked, or refused, with a summary.
- [x] README and CLAUDE.md: the install line, and "re-run `install` after adding a script".
- [x] Verify green: `test/install-selftest` and `bin/claude-route-selftest`.

**Satisfies:** R5.

**File(s):** `install`, `test/install-selftest`, `README.md`, `CLAUDE.md` (Patchbay)

**Test:**
```bash
cd ~/src/facetdigital/patchbay && test/install-selftest && bin/claude-route-selftest | tail -2
```

**Commit message (Patchbay):** `Add install: link bin/ into ~/.local/bin`

---

### Step 4: Create `facetdigital/patchbay` and push

**Pre-approved; do not stop to ask** (Scott, 2026-11-03: "dont stop and ask, just do. as long as it is private repo in facetdigital org named patchbay"). The approval covers exactly that: a **private** repo in the **`facetdigital`** org named **`patchbay`**. If any of the three cannot hold (the name is taken, the org refuses a private repo), stop and ask instead.

- [x] Test-first: n/a for repo creation. The checks below run against a fresh clone after the push.
- [x] Before pushing: `git log --oneline` shows only Steps 1 to 3's commits, and Patchbay's de-personalization guard passes.
- [x] `gh repo create facetdigital/patchbay --private --source ~/src/facetdigital/patchbay --push`
- [x] Verify green from a fresh clone in the scratchpad: the route selftest and the install selftest pass, `tree-check`'s link check passes, and the repo is private.

**Satisfies:** R1, R2; team release T1, T5.

**File(s):** GitHub `facetdigital/patchbay`

**Test:**
```bash
C="$SCRATCH/patchbay-clone"; rm -rf "$C"; git clone git@github.com:facetdigital/patchbay.git "$C"
"$C/bin/claude-route-selftest" | tail -2 && "$C/test/install-selftest"
git -C "$C" log --oneline | wc -l              # expect 3
gh repo view facetdigital/patchbay --json visibility -q .visibility   # expect PRIVATE
```

**Commit message:** none (push only)

---

### Step 5: Install on this machine and prove nothing changed

- [x] Write the failing check first: `equivalence-check` (below). Before install it fails on resolution, because `command -v agent` is `~/bin/agent`.
- [x] Capture the before-state: `claude-ps --json` (sessions and routes), and `CLAUDE_ROUTE_DRYRUN=1 claude-run gpt` and `claude-run glm` output, from dotfiles' copies.
- [x] Run `~/src/facetdigital/patchbay/install`.
- [x] Verify green: `equivalence-check` passes. Specifically:
  - **Resolution, in three contexts:** a new interactive zsh, a new detached tmux session, and this Claude session's Bash tool. Each resolves `agent`, `claude-run` and `claude-ps` to `~/.local/bin`, linking into Patchbay.
  - **`agent` argv:** for each of the 24 distinct history invocations, run dotfiles' `agent` and the resolved `agent` with a stub `claude` first on `PATH` that prints its argv, from the same directory; the outputs are identical. Repeat from a second directory, since the default name comes from `$PWD`.
  - **`claude-run`:** dry-run output identical for `gpt` and `glm`.
  - **`claude-ps`:** `--json` lists the same PIDs with the same route fields as the before-state.

**Satisfies:** R4, R5; roadmap "check each one resolves to the same `claude` command before and after".

**File(s):** none tracked; links in `~/.local/bin`. The check script lives in the scratchpad.

**Test:**
```bash
# equivalence-check (scratchpad), outline:
for c in "zsh -ic" "tmux-new-session" "bash (this session)"; do
  # command -v agent claude-run claude-ps -> ~/.local/bin/* -> ~/src/facetdigital/patchbay/bin/*
  :; done
stub=$(mktemp -d); printf '#!/bin/sh\nprintf "%%s\\n" "$@"\n' > "$stub/claude"; chmod +x "$stub/claude"
sed -E 's/^: [0-9]+:[0-9]+;//' ~/.zsh_history | grep -E '^agent( |$)' | sort -u | while read -r line; do
  args="${line#agent}"
  a=$(eval "PATH=$stub:\$PATH ~/src/scottwb/dotfiles/bin/agent $args" 2>/dev/null)
  b=$(eval "PATH=$stub:\$PATH \$(command -v agent) $args" 2>/dev/null)
  [ "$a" = "$b" ] || echo "DIFF: $line"
done
```

**Commit message:** none (machine state only)

---

### Step 6: Guard `claude-ps`'s filter from dotfiles

- [x] Write the failing test first: a new section in `bin/claude-end-session-selftest`, "claude-ps on PATH hides every dotfiles helper". It globs dotfiles' `bin/claude-*`, reads the filter alternation from `${CLAUDE_PS:-$(command -v claude-ps)}`, and asserts each helper is in it. Guard the guard: run it against a planted copy of `claude-ps` with `end-session` removed from the filter, and assert it fails. That planted assertion fails until the section exists.
- [x] Implement the section, about 20 lines, matching the route selftest's drift-guard style and its comment about why the list is derived.
- [x] If no `claude-ps` is on `PATH`, report a skip, not a pass.
- [x] Verify green: `bin/claude-end-session-selftest`.

**Satisfies:** R6; the global rule "Derive lists; do not hand-maintain two copies of the same fact".

**File(s):** `bin/claude-end-session-selftest` (dotfiles)

**Test:**
```bash
cd ~/src/scottwb/dotfiles && bin/claude-end-session-selftest | tail -3
```

**Commit message (dotfiles):** `Guard claude-ps's helper filter from the repo that owns the helpers`

---

### Step 7: Remove Patchbay from dotfiles

- [ ] Write the failing check first: `removal-check` (below). It fails while any moved file is still in dotfiles.
- [ ] `git rm` the four scripts and the R7 docs.
- [ ] `README.md`: replace the "Claude Code route launchers" section with a short "Patchbay" install step next to the `dotfiles-private` step: clone `facetdigital/patchbay` into `~/src/facetdigital/patchbay` and run `./install`. Optional, and private to Facet.
- [ ] `.claude/README.md`: the Patchbay and session-listing rows point at the Patchbay repo; the `/end-session` helper row stays.
- [ ] `.claude/CLAUDE.md` line 58, `.claude/COMMANDS.md` line 28, `.claude/docs/servanda.md`, `.claude/settings.json`'s parked note, and `docs/plans/end-session.md`: `bin/claude-run` becomes `claude-run` (Patchbay), and links to moved files become `facetdigital/patchbay` GitHub URLs. Only the words that name a path change.
- [ ] Dotfiles roadmap: remove the R7 items and the two Completed entries; add one pointer item, "Patchbay lives in `facetdigital/patchbay`", naming what moved and where its roadmap is; repoint the anchors that remain (`/shift-change`, the `claude-ps` fork, the LinkedIn post) to Patchbay GitHub URLs; move this item to Completed with a link to this plan. This plan stays in dotfiles as the record of the move.
- [ ] Verify green: `removal-check`, Step 5's `equivalence-check` run again (now with no dotfiles copy to shadow), and `bin/claude-end-session-selftest`.

**Satisfies:** R3, R7; roadmap "Removed from dotfiles at HEAD only" and "dotfiles keeps one pointer item".

**File(s):** `bin/` (4 removals), `docs/` (R7 removals), `README.md`, `.claude/README.md`, `.claude/CLAUDE.md`, `.claude/COMMANDS.md`, `.claude/docs/servanda.md`, `.claude/settings.json`, `docs/plans/end-session.md`, `docs/plans/development-roadmap.md`

**Test:**
```bash
cd ~/src/scottwb/dotfiles
for f in bin/claude-run bin/agent bin/claude-ps bin/claude-route-selftest docs/patchbay.md; do test -e "$f" && echo "STILL HERE: $f"; done
# no relative link anywhere in dotfiles points at a missing file (same script as Step 1, rooted at dotfiles)
# no stale path wording
grep -rn 'bin/claude-run\|bin/claude-ps\|bin/agent\b' README.md .claude docs --include='*.md' | grep -v 'docs/plans/patchbay-repo.md'
git diff --cached | grep '^+' | grep -c "$(printf '\342\200\224')"      # expect 0
python3 -c 'import json;json.load(open(".claude/settings.json"))' && echo "settings.json valid"
```

**Commit message (dotfiles):** `Move Patchbay to facetdigital/patchbay`

---

### Step 8: Push dotfiles and tell Donna

- [ ] Test-first: n/a, communication.
- [ ] With Scott's go, push dotfiles.
- [ ] Message Donna that Patchbay's equipment entry has a new home: `~/src/facetdigital/patchbay`, GitHub `facetdigital/patchbay`, and that `claude-ps`, `claude-run` and `agent` now live there, with the route selftest as `test/route-selftest`. Her audit digests are history and need no change.
- [ ] Verify: `git status -sb` shows dotfiles in sync with origin.

**Satisfies:** keeps Donna's registry true (found while planning, 2026-11-03).

**File(s):** none

**Test:**
```bash
git -C ~/src/scottwb/dotfiles status -sb | head -1
```

**Commit message:** none

## Rollback

Until Step 7, nothing in dotfiles has changed: removing the four links from `~/.local/bin` restores the old resolution. After Step 7, `git revert` the removal commit in dotfiles. History is never rewritten in either repo.

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `~/src/facetdigital/patchbay/**` (new repo) | 1, 2, 3, 4 |
| `~/.local/bin/{agent,claude-run,claude-ps}` (links) | 5 |
| `test/route-selftest`, `test/run`, `install` pruning (Patchbay) | 5 (R8) |
| `bin/claude-end-session-selftest` | 6 |
| `bin/{claude-run,agent,claude-ps,claude-route-selftest}` (removed) | 7 |
| R7 docs (removed from dotfiles) | 7 |
| `README.md`, `.claude/README.md`, `.claude/CLAUDE.md`, `.claude/COMMANDS.md`, `.claude/docs/servanda.md`, `.claude/settings.json`, `docs/plans/end-session.md` | 7 |
| `docs/plans/development-roadmap.md` | 7 (and this plan's status line now) |

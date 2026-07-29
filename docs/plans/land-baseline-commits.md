# Plan: Land the Independent Baseline Commits

**Status:** Ready to implement. Six commits, none of which touch the Servanda
command suite.

## Why this plan exists

The working tree accumulated changes across several unrelated threads. This plan
lands only the ones that are independent of the Servanda command suite, so the
tree gets smaller and the suite can be reviewed in isolation without a pile of
unrelated diffs in the way.

Nothing here needs new implementation work. Every change already exists in the
working tree; this plan is entirely "review, group, commit."

## What this plan deliberately EXCLUDES

Held out on purpose (2026-07-29, Scott's call): he wants to review the Servanda
suite's current state, and likely work on it further, before it gets baselined.

| Held | Why | Where it lands |
|---|---|---|
| `.claude/commands/{beastmode,booyah,plan,roadmap,yolo}.md` | Suite specs, under review | [servanda-suite-baseline.md](servanda-suite-baseline.md) |
| `.claude/COMMANDS.md`, `.claude/commands/{gameplan,phasegate,workflow-help}.md` (untracked) | Suite specs, under review | [servanda-suite-baseline.md](servanda-suite-baseline.md) |
| `.claude/CLAUDE.md`, the workflow-table change only | Suite doc, under review | [servanda-suite-baseline.md](servanda-suite-baseline.md) |
| `.claude/settings.json` | Held pending a decision on unpinning the session model | Roadmap item "Decide the Claude Code session model pin" |

**The `.claude/CLAUDE.md` trap.** That file carries three unrelated changes, two
landable and one held. Identify them by their anchor text, NOT by hunk number:
the file is edited often and hunk numbers shift under you (this already happened
once on 2026-07-29, when a new top hunk renumbered everything).

| Anchor text in the hunk | Topic | Verdict |
|---|---|---|
| `Enforce this going forward, do not retrofit` under `## Writing Style` | Emdash rule scope | **Lands in step 5** |
| `\| /gameplan <feature> \|` in the workflow table | Servanda suite | **HELD** |
| `## Secrets` / `1Password` / `OP_ACCOUNT` | Secret resolution | **Lands in step 6** |

A plain `git add .claude/CLAUDE.md` would silently drag the held Servanda table
into whichever commit ran first. Use `git add -p` and select by content. The three
changes are far apart in the file, so git offers them as separate hunks with no
manual splitting needed.

Guard for every CLAUDE.md commit in this plan:

```bash
git diff --cached .claude/CLAUDE.md | grep -c "gameplan"   # MUST be 0
```

## Execution Instructions

**DO NOT run `/booyah` on this plan.** Its Step 2 treats a dirty tree as "my
previous step's work needs committing" and its Step 4 then runs `git add -A`. Here
the tree is dirty with six unrelated concerns plus the held Servanda suite, so the
first invocation would sweep everything into one commit and destroy the separation
this plan exists to create. That assumption is fine in booyah's normal case (the
tree is dirty because booyah just implemented a step); it does not hold for
pre-existing multi-concern work. Logged as a review finding in
[servanda-suite-baseline.md](servanda-suite-baseline.md).

Run the steps manually instead:

1. **Work step-by-step** - one commit per step, in order
2. **Stage EXPLICITLY, never `git add -A` or `git add .`** - stage only the paths
   in that step's **File(s)** line. After staging, always confirm the held work
   did not ride along:
   ```bash
   git diff --cached --name-only     # must list ONLY this step's files
   ```
3. **Test-first within each step** - n/a for most steps (config and docs); step 3
   has a real smoke check
4. **Verify after each step** - run the step's Test block
5. **Commit after each step** - use the provided commit message verbatim
6. **Mark completion** - check off steps as they land

Step 1 must go first: it stops session junk from being committable by anything
after it. Step 2 is what makes `docs/` tracked at all.

Steps 5 and 6 need interactive hunk selection (`git add -p`), which agents in a
non-interactive shell cannot drive. Either run those two by hand, or stage the
exact hunks non-interactively by writing them to a patch and using
`git apply --cached`.

## What is in the working tree

| Stream | Files | State |
|---|---|---|
| Repo hygiene + docs relocation | `.gitignore` (new), `.claude/.gitignore`, `docs/` (new), `README.md` | Done 2026-07-29 |
| Shell housekeeping | `.zsh/linux`, `.zsh/aliases` | Done earlier, in daily use |
| Writing-style scope + secrets convention | `.claude/CLAUDE.md`, two of its three hunks | Done 2026-07-29 |

---

## Step 1: Repo hygiene: ignore session junk, anchor the plans rule

- [ ] Test-first: n/a (ignore rules)
- [ ] Already applied: new root `.gitignore` (`.DS_Store`, `tmp/`)
- [ ] Already applied: `.claude/.gitignore` gains `sessions/`, `backups/`,
      `uploads/`, `image-cache/`, `.last-cleanup`, `.last-update-result.json`,
      `mcp-needs-auth-cache.json`, `plugins/blocklist.json`
- [ ] Already applied: bare `plans/` anchored to `/plans/`

Three things this fixes:

1. `.claude/uploads/` (12MB of pasted photos) and `.claude/image-cache/` were
   untracked but NOT ignored, so they were one `git add -A` away from landing in
   a public repo. `image-cache/` self-pruned mid-session while being examined,
   confirming it is pure cache; `uploads/` is the paste spool. Neither is
   durable. If a pasted image ever matters, save it deliberately into the
   relevant project at that moment.
2. Eight ignore rules lived in `.git/info/exclude`, which is machine-local and
   does not clone. A fresh clone would flood `git status` with session data and
   backups. They now live in tracked ignore files where their siblings already
   were.
3. The bare `plans/` rule matched at any depth, which is exactly how
   `.claude/docs/plans/` got silently swallowed (see step 2).

**File(s):** `.gitignore`, `.claude/.gitignore`

**Test:**
```bash
git status --short          # no session junk, no cache dirs
# Authoritative ignore check: a real file under an ignored dir must not appear.
# (check-ignore on a nonexistent path is unreliable for trailing-slash patterns.)
mkdir -p .claude/image-cache/probe && touch .claude/image-cache/probe/t.jpeg
git status --short | grep -i image-cache || echo "correctly ignored"
rm -rf .claude/image-cache
```

**Commit message:** `Ignore Claude Code session junk; anchor the plans ignore rule`

Optional follow-up, not part of the commit: the now-redundant `.claude/*` lines
in `.git/info/exclude` can be trimmed by hand. Harmless if left.

---

## Step 2: Move the roadmap and plans to repo-root docs/plans

- [ ] Test-first: n/a (file moves)
- [ ] Already applied: `development-roadmap.md` and `command-suite-rename.md`
      moved from `.claude/docs/plans/` to `docs/plans/`; empty `.claude/docs/`
      removed
- [ ] Already applied: `COMMANDS-TESTING.md` moved from `.claude/` to
      `docs/plans/command-kit-overhaul.md`
- [ ] Already applied: README note that non-dot top-level dirs are repo-only
- [ ] Verify the relative links among the plan docs still resolve

The bug this fixes: `~/.claude` is a symlink to `~/src/scottwb/dotfiles/.claude`,
so the roadmap used to live *inside* Claude Code's runtime state directory. All
six kit commands hardcode `docs/plans/...` relative to cwd (about 25 references).
Opening the dotfiles repo at its root and running `/roadmap` therefore found
nothing and offered to create a roadmap, while the real one sat unreachable and
git-ignored. **Servanda could not dogfood itself on its own repo.** It can now.

No install changes are needed. The install symlinks dot-prefixed entries plus
`bin`; a top-level `docs/` is neither, so it never enters `$HOME`. The README now
says so explicitly rather than leaving it to be rediscovered.

The roadmap was rescoped in the same pass: it is now a repo-wide roadmap for
`scottwb/dotfiles` with tagged threads (Servanda, Shell, Tools, Terminal &
editors, Machine setup) rather than a Servanda-only plan, because it now sits at
the repo root and tracks shell and machine-setup work too. Servanda is the
dominant thread today, so most items carry that tag; that is a snapshot of
attention, not the repo's permanent shape.

The artifact-location convention this establishes, so it stops being re-derived:

| Kind | Home | Why |
|---|---|---|
| Runtime files a tool loads | their dotfile locations: `.claude/`, `.zsh/`, `bin/` | The tool discovers them there; e.g. Claude Code finds commands in `.claude/commands/`, and `workflow-help.md` reads `~/.claude/COMMANDS.md` by absolute path |
| Dev artifacts about the work | `docs/` (roadmap, plans, acceptance checklists, `docs/assessments/` gate reports) | Matches every other project the kit drives, and stays out of `$HOME` |

Decided and rejected 2026-07-29: **do not create `~/.servanda`.** Servanda *is*
Claude Code commands, so a separate dotdir would have to be symlinked back into
`~/.claude/commands/` to function, buying indirection and nothing else. The
runtime-vs-dev-artifact split above is the one that pays. A separate home only
makes sense as part of extracting the kit to its own repo, which is already an
Upcoming roadmap item. (Checked 2026-07-29: no `servanda` or `servando` repo
exists locally under `~/src/scottwb` or `~/src/facetdigital`, nor in either
GitHub org. The name has no code behind it yet.)

**File(s):** `docs/` (all four plan files), `README.md`

**Test:**
```bash
ls docs/plans/                       # four files
ls .claude/docs 2>&1                 # must not exist
grep -n "repo-only" README.md
# In a session at the repo root: /roadmap finds this roadmap instead of offering to create one
```

**Commit message:** `Move the development roadmap and plans to repo-root docs/plans`

---

## Step 3: zsh: stop stomping an active theme on Linux

- [ ] Test-first: n/a (shell config; verified by real use)
- [ ] Already applied: `.zsh/linux` guards the spartan prompt behind
      `[ -z "$ZSH_THEME" ]`

Real bug fix, not a preference: the bare-Linux minimal prompt was overwriting
oh-my-zsh's devcontainers theme inside VS Code devcontainers. Gets its own commit
because it is the only behavior fix in the shell thread.

**File(s):** `.zsh/linux`

**Test:**
```bash
# In a devcontainer with a theme active: the theme survives a new shell
zsh -c 'echo "ZSH_THEME=$ZSH_THEME PROMPT=$PROMPT"'
```

**Commit message:** `zsh: don't stomp an active theme with the bare-Linux prompt`

---

## Step 4: Add dcsh and pev2-health-check aliases

- [ ] Test-first: n/a (aliases)
- [ ] Already applied: `dcsh` (shell into the repo's devcontainer) and
      `pev2-health-check` (Heroku daily health check for prepare-enrich)

**File(s):** `.zsh/aliases`

**Test:**
```bash
source ~/.zsh/aliases && alias dcsh pev2-health-check
```

**Commit message:** `Add dcsh and pev2-health-check aliases`

---

## Step 5: Scope the emdash rule to going-forward only

- [ ] Test-first: n/a (docs)
- [ ] Already applied: `.claude/CLAUDE.md` `## Writing Style` gains an
      enforce-forward clause: older internal docs keep their emdashes, no cleanup
      sweep, their presence does not mean the rule is dead; fix only in
      client-facing material or incidentally while rewriting a line anyway
- [ ] **Stage the Writing Style hunk only** via `git add -p .claude/CLAUDE.md`

**File(s):** `.claude/CLAUDE.md` (partial)

**Test:**
```bash
git add -p .claude/CLAUDE.md      # accept the "do not retrofit" hunk only
git diff --cached .claude/CLAUDE.md | grep -c "do not retrofit"   # nonzero
git diff --cached .claude/CLAUDE.md | grep -c "gameplan"          # MUST be 0
```

**Commit message:** `CLAUDE.md: scope the emdash rule to going-forward enforcement`

---

## Step 6: Document the 1Password secret-resolution convention

- [ ] Test-first: n/a (docs)
- [ ] Already applied: `.claude/CLAUDE.md` gains a `## Secrets` section: resolve
      runtime secrets via the `op` CLI with TouchID gating, no `.env` files for
      this pattern, hardcoded `readonly` `OP_ACCOUNT`/`OP_REF` constants,
      explicit `--account` because four accounts exist, the four account URLs,
      and the per-repo exception for `harvest-tools`
- [ ] **Stage the `## Secrets` hunk only** via `git add -p .claude/CLAUDE.md`;
      leave the Servanda workflow table unstaged

Together with step 5, this is where the held suite doc is most likely to ride
along by accident. Get the hunk selection right.

**File(s):** `.claude/CLAUDE.md` (partial)

**Test:**
```bash
git add -p .claude/CLAUDE.md      # accept the "## Secrets" hunk, reject the workflow table
git diff --cached .claude/CLAUDE.md | grep -c "1Password"   # nonzero
git diff --cached .claude/CLAUDE.md | grep -c "gameplan"    # MUST be 0
git diff .claude/CLAUDE.md | grep -c "gameplan"             # nonzero: still held, unstaged
```

**Commit message:** `Document the 1Password secret-resolution convention`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `.gitignore` (new) | 1 |
| `.claude/.gitignore` | 1 |
| `docs/plans/*.md` (five files, tracked first time) | 2 |
| `README.md` | 2 |
| `.zsh/linux` | 3 |
| `.zsh/aliases` | 4 |
| `.claude/CLAUDE.md` (Writing Style hunk) | 5 |
| `.claude/CLAUDE.md` (Secrets hunk) | 6 |

## After this plan

The working tree should contain exactly the held items: nine Servanda suite
files, the `.claude/CLAUDE.md` workflow-table change, and `.claude/settings.json`.
Confirm with:

```bash
git status --short
git diff --stat
```

Then the roadmap's next item is
[servanda-suite-baseline.md](servanda-suite-baseline.md), which starts with
Scott's review of the suite's current state.

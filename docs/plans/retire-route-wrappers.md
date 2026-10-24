# Plan: Retire the Route Wrapper Scripts

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `CLAUDE.md` - Developer/AI guidelines
   - `run` script usage comments
   - `docs/plans/retire-route-wrappers.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

---

## Summary

`bin/claude-run` already holds the whole route launcher: the model table
(`resolve_model`), the provider table (`resolve_provider`), and, since
2026-09-10, `--provider` / `--model` / `--context` for any model with no alias.
The five `bin/claude-<name>` scripts are three-line shims that call
`claude-run <alias>`:

| Wrapper | Runs |
|---|---|
| `claude-gpt` | `claude-run gpt` |
| `claude-glm` | `claude-run glm` |
| `claude-gemini` | `claude-run gemini` |
| `claude-ollama` | `claude-run glm` |
| `claude-openrouter` | `claude-run gpt` |

They add nothing `claude-run` lacks, and they cost a second copy of the launcher
list: `claude-ps` hardcodes every wrapper name in both its process filter and its
route detection, and that list already drifted once (`claude-gemini`,
2026-09-10). Delete them. `claude-run` becomes the only launcher.

While planning this, a bug surfaced in the same code: `claude-ps` cannot detect
the route of a flag-style launch. Its alias extraction takes the first token
after `claude-run` that does not start with `-`, so
`claude-run --model deepseek/...` yields nothing (tested 2026-10-17: the `sed`
returns empty). Those sessions fall through to the plain-Anthropic answer. Once
`claude-run` is the only way in, `claude-ps` reading its argv correctly is the
whole of route detection, so fixing it belongs here.

## Requirements

- R1. Delete `bin/claude-gpt`, `bin/claude-glm`, `bin/claude-gemini`,
  `bin/claude-ollama`, `bin/claude-openrouter`.
- R2. **No replacement shorthand.** No zsh aliases, no functions, no new
  scripts. Scott adds aliases himself later if he ever wants them (Scott's
  call, 2026-10-17). The "provider default" idea that `claude-ollama` and
  `claude-openrouter` carried goes away with them; do not add
  `claude-run ollama` / `claude-run openrouter` aliases to replace it.
- R3. `claude-ps` detects routes from `claude-run`'s own arguments only, for
  both alias launches (`claude-run gpt`) and flag launches
  (`claude-run --provider openrouter --model X`, including the `--flag=value`
  forms).
- R4. Route detection stays network-free. `claude-ps` is a status tool and must
  never fetch the catalog, prompt TouchID, or read a secret.
- R5. The selftest stays green, with no assertion left pointing at a removed
  file, and the launcher-list drift guard is replaced by one derived from the
  files on disk (CLAUDE.md, "Derive lists").
- R6. Live docs stop naming the wrappers: `README.md`, `.claude/CLAUDE.md`,
  `.claude/COMMANDS.md`, the `settings.json` `x-instructions` note,
  `docs/patchbay.md`, and the Patchbay team-release plan's file count.
- R7. Historical records are left alone: `docs/plans/claude-route-launchers.md`,
  `docs/plans/audit-log-handoff.md`, completed steps in other plans, and dated
  roadmap notes. They describe what was true then.

## Options Rejected (2026-10-17)

- **Replace the wrappers with zsh aliases** (`alias claude-gpt='claude-run gpt'`).
  Proposed alongside the deletion. Scott said no: he does not want new aliases,
  and will make his own later if he ever cares to. Do not re-propose this as
  part of the work.
- **Keep the wrappers and fix only `claude-ps`.** This would have been the smallest
  change, but it keeps the duplicated launcher list, which is the actual defect.
- **Wait for Patchbay v2 (`pbay run`), which replaces them anyway.** `pbay` is
  blocked "way later", so waiting means the wrappers stay indefinitely.

## Non-Goals

- Patchbay v2 (`pbay`). Still blocked; this only shrinks what it inherits.
- Changing `claude-run`'s behavior, flags, alias table, or output. Only its
  header comment changes.
- Any `bin/agent` change.

## Implementation Steps

### Step 1: `claude-ps` detects flag-style `claude-run` launches

- [x] Write the failing test first. In `bin/claude-route-selftest`'s
      "claude-ps route detection (D6)" section, add a second stub launch:
      `ANTHROPIC_AUTH_TOKEN=<placeholder> PATH="$STUB_DIR:$PATH" "$CLAUDE_RUN" --provider=openrouter --model selftest/flag-route --context 12345`.
      Mixing `--provider=` and `--model <space>` covers both argv forms in one
      launch. `--context` keeps the dry run off the catalog, and the
      placeholder token clears the openrouter preflight with no 1Password read,
      the same way the existing `gpt` launch does. Assert `claude-ps -n` shows
      `OpenRouter` and `selftest/flag-route` on the new row, the row count rises
      by exactly one over a baseline, and the row disappears when the stub
      exits. Expected to FAIL today: the alias extraction comes back empty, so
      the row shows `Anthropic` and model `-`.
- [x] Implement: in `bin/claude-ps`, generalize `resolve_route_alias` into a
      resolver that takes `claude-run`'s leading arguments rather than one
      alias. In `detect_route`'s `*claude-run*` branch, walk the tokens after
      `claude-run`: keep `--provider X`, `--provider=X`, `--model X`,
      `--model=X`, `--context X`, `--context=X`, then the first remaining
      positional, then stop. That is the same rule `claude-run` uses to parse
      its own flags, so everything after belongs to `claude` and is ignored.
- [x] Implement: **drop `--refresh`** when rebuilding the arguments.
      `claude-run` calls `catalog_fetch` for `--refresh` *before* it checks
      `CLAUDE_ROUTE_DRYRUN`, so passing it through would make `claude-ps` hit
      the network (R4).
- [x] Implement: dry-run `claude-run` with the rebuilt arguments and parse the
      plan exactly as today. Memoize on the rebuilt argument string instead of
      the alias.
- [x] Implement: when the dry run fails (a flag launch with no `--context` and
      no cached catalog entry, which `claude-run` refuses offline by design),
      fall back to what argv states: provider from `--provider`, defaulting to
      `openrouter` as `claude-run` does, model from `--model`, window empty.
      Showing the provider and model without a window is better than a wrong
      `Anthropic`.
- [x] Verify green: `bin/claude-route-selftest`, and by hand:
      `claude-run --model <any cached slug>` in one terminal, `claude-ps` in
      another.

**Satisfies:** R3, R4. Fixes the flag-launch misreport found 2026-10-17.

**File(s):** `bin/claude-ps`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
# Detection must stay offline. With an empty catalog cache the listing still
# renders, fetches nothing, and never prompts:
CLAUDE_ROUTE_CACHE_DIR="$(mktemp -d)" bin/claude-ps -n
```

**Commit message:** `Detect flag-style claude-run launches in claude-ps`

---

### Step 2: Delete the wrappers and everything in `bin/` that names them

- [ ] Write the failing check first: `grep -rnE 'claude-(gpt|glm|gemini|ollama|openrouter)\b' bin/`
      must print nothing. FAILS today: the five wrappers, `claude-ps`'s filter
      and detection cases, `claude-run`'s header comment, and the selftest's
      wrapper section all match.
- [ ] Implement: `git rm` the five wrappers (R1).
- [ ] Implement: in `bin/claude-ps`, delete the five wrapper cases from
      `detect_route`, and shrink the process filter to
      `claude-(run|route-selftest)`. Update the comment beneath it, which says
      a single `claude-glm` reports as three or four rows.
- [ ] Implement: in `bin/claude-run`, rewrite the header comment (lines 5 to 7)
      so it no longer says the wrappers exist. The usage text already teaches
      `claude-run <alias>` and needs nothing.
- [ ] Implement: in `bin/claude-route-selftest`:
  - Delete the "Thin wrappers (D9)" section. Its alias-resolution, no-exec and
    argument-forwarding checks are already covered against `claude-run`
    directly, by the per-alias dry runs at the top, the D6 no-exec check, and
    "positional alias still forwards".
  - Launch the D6 stub with `"$CLAUDE_RUN" gpt` instead of `claude-gpt`. Fix
    the "wrapper -> claude-run -> stub" comment and drop the
    "wrappers are not listed as sessions" assertion.
  - Replace the "claude-ps knows every launcher" drift guard. Comparing the
    filter to `KNOWN_ALIASES` stops making sense once aliases are no longer
    process names. Derive the expected list from disk instead: every
    `bin/claude-*` file other than `claude-ps` must appear in the filter.
    Keep the "guard the guard" check that the glob matched something.
- [ ] Verify green: the grep above prints nothing, and
      `bin/claude-route-selftest` passes. Note the new assertion count for
      Step 3.

**Satisfies:** R1, R2, R5.

**File(s):** `bin/claude-gpt`, `bin/claude-glm`, `bin/claude-gemini`,
`bin/claude-ollama`, `bin/claude-openrouter` (deleted); `bin/claude-ps`,
`bin/claude-run`, `bin/claude-route-selftest`

**Test:**
```bash
grep -rnE 'claude-(gpt|glm|gemini|ollama|openrouter)\b' bin/ ; echo "matches above must be none"
bin/claude-route-selftest
CLAUDE_ROUTE_DRYRUN=1 claude-run gpt     # the replacement for every old wrapper call
```

**Commit message:** `Retire the claude-<alias> wrappers; claude-run is the only launcher`

---

### Step 3: Correct the docs that name the wrappers

- [ ] Test-first: n/a, documentation. The proxy check is the grep below,
      which FAILS today across all six files.
- [ ] `README.md` launcher section: turn the table's Command column into
      `claude-run glm` / `claude-run gpt` / `claude-run gemini` and drop the
      `claude-ollama` and `claude-openrouter` rows. Delete "All five are
      three-line wrappers". Change "the models worth a wrapper" to "the models
      worth an alias". Rewrite the inspect examples as
      `CLAUDE_ROUTE_DRYRUN=1 claude-run gpt` and
      `CLAUDE_ROUTE_PREFLIGHT_ONLY=1 claude-run glm`, and update the assertion
      count to Step 2's number.
- [ ] `.claude/CLAUDE.md`, the "routed session" sentence under Development
      Workflow Commands: replace "`claude-glm`, `claude-gpt`, or anything else
      via `bin/claude-run`" with "any `bin/claude-run` launch". This is the
      global instructions file, so it binds in new sessions only.
- [ ] `.claude/COMMANDS.md` line 28: the per-process launchers are
      `bin/claude-run <alias>`, not named wrappers.
- [ ] `.claude/settings.json` `x-instructions`: same correction to the
      parenthetical that lists the four wrappers. Prose inside a JSON string
      only; no live setting changes. Validate with `jq`.
- [ ] `docs/patchbay.md`: trim "What exists today" to `claude-run`,
      `claude-ps`, `claude-route-selftest` (with the new count). Change the
      `pbay run claude glm` comment to "what `claude-run glm` does today". In
      "Wrappers do not scale", record that the wrappers were retired on
      2026-10-17, so the paragraph argues against a shape that no longer
      exists.
- [ ] `docs/plans/patchbay-team-release.md`: the hold note's "Carry into any
      resume" and Step 4's "Copy the seven `bin/` scripts" both become three
      scripts (`claude-run`, `claude-ps`, `claude-route-selftest`). Step 7's
      verify line becomes `claude-run gpt` and `claude-run glm`. Leave the
      completed Steps 1 to 3 as written (R7).
- [ ] Verify green: the grep finds the wrapper names only in historical files.

**Satisfies:** R6, R7.

**File(s):** `README.md`, `.claude/CLAUDE.md`, `.claude/COMMANDS.md`,
`.claude/settings.json`, `docs/patchbay.md`,
`docs/plans/patchbay-team-release.md`

**Test:**
```bash
grep -rnE 'claude-(gpt|glm|gemini|ollama|openrouter)\b' \
  README.md .claude/CLAUDE.md .claude/COMMANDS.md .claude/settings.json docs/patchbay.md
# expect none
grep -nE 'claude-(gpt|glm|gemini|ollama|openrouter)\b' docs/plans/patchbay-team-release.md
# expect only lines inside the completed Steps 1-3
jq empty .claude/settings.json && echo "settings.json still valid"
```

**Commit message:** `Point the docs at claude-run now that the wrappers are gone`

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `bin/claude-ps` | 1, 2 |
| `bin/claude-route-selftest` | 1, 2 |
| `bin/claude-run` | 2 |
| `bin/claude-gpt`, `-glm`, `-gemini`, `-ollama`, `-openrouter` (deleted) | 2 |
| `README.md` | 3 |
| `.claude/CLAUDE.md` | 3 |
| `.claude/COMMANDS.md` | 3 |
| `.claude/settings.json` (`x-instructions` prose only) | 3 |
| `docs/patchbay.md` | 3 |
| `docs/plans/patchbay-team-release.md` | 3 |
| `docs/plans/development-roadmap.md` | wrap-up |

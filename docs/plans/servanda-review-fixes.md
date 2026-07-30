# Plan: Apply the Servanda Review Fixes

**Status:** Blocked on [servanda-suite-baseline.md](servanda-suite-baseline.md)
landing first. These are fixes ON TOP of the baseline, not part of it.

Origin: the review session of 2026-07-29 answered five design questions about the
suite. Two of them (Q2 model pins, Q4 the `git add -A` footgun) produced concrete
work rather than just verdicts. This plan is that work. Full reasoning for each
decision lives in the suite plan's "Review first" section; only the resulting
changes are restated here.

Sequence position (decided in Q5): baseline the suite, **then this plan**, then
acceptance testing, then the rename. The fixes come before testing so acceptance
testing does not exercise code already known to be wrong.

## Execution Instructions

1. **Work step-by-step** - one commit per step, in order
2. **Test-first within each step** - n/a (command spec files, pure docs); each Test
   block is a manual smoke check
3. **Stage explicitly** - never `git add -A`; stage only the step's **File(s)**
4. **Commit after each step** - use the provided commit message verbatim
5. **Mark completion** - check off steps as they land

Note the irony to avoid: step 4 fixes `/booyah`'s staging assumption, so do not use
`/booyah` to run this plan until that step has landed and been verified.

---

## Step 1: Document that model pins are tiers, not vendors

- [ ] Test-first: n/a (docs)
- [ ] Add a paragraph to `.claude/COMMANDS.md` beside the existing verification-tiers
      line: the `model:` values in spawn sites (`opus`, `fable`) are Claude Code tier
      ALIASES, not vendor lock-in. Each resolves through
      `ANTHROPIC_DEFAULT_<TIER>_MODEL`, so the vendor mapping lives in `env` in
      `settings.json` and nowhere else
- [ ] State the consequence explicitly: switching to OpenRouter, Ollama, or anything
      else needs only the `env` block changed, never the command files
- [ ] State the anti-goal: do NOT add per-provider fallback logic to the command
      files. The indirection already exists one layer down

Why this is worth a commit of its own: without it, the next reader sees
`model: "fable"` and concludes the suite is Anthropic-locked, then "helpfully" adds
fallback logic that duplicates machinery the harness already provides. This
paragraph exists to prevent a well-intentioned regression.

**File(s):** `.claude/COMMANDS.md`

**Test:**
```bash
grep -n "ANTHROPIC_DEFAULT" .claude/COMMANDS.md
# New session: /workflow-help "are the model pins Anthropic-specific?" answers no,
# and points at the env mapping
```

**Commit message:** `COMMANDS.md: document that model pins are tier aliases, not vendors`

---

## Step 2: Map the audit tier in the parked Ollama profile

- [ ] Test-first: n/a (config)
- [ ] Add `ANTHROPIC_DEFAULT_FABLE_MODEL` to `x-env` in `.claude/settings.json`,
      alongside the existing haiku/sonnet/opus entries

The latent bug: `x-env` currently remaps haiku, sonnet, and opus but not fable.
Flipping to the Ollama profile today would leave the audit tier unmapped, and under
the STOP-not-degrade rule (Q2) that means a hard halt at every phase gate and every
security pass. The profile is parked, so this has never fired, which is exactly why
it would be a surprise the first time it does.

Judgment call for whoever implements this: pointing the audit tier at a local
30b model is arguably worse than stopping, since a phase gate is an adversarial
audit and that is the tier where capability matters most. Two defensible options:
map it to the same local model as its siblings for consistency, or leave it
deliberately unmapped WITH a comment in `x-instructions` saying gates are expected
to halt under the Ollama profile and that is intentional. Prefer the second unless
local audits turn out to be useful.

**File(s):** `.claude/settings.json`

**Test:**
```bash
python3 -c "import json;e=json.load(open('.claude/settings.json'))['x-env'];print({k:v for k,v in e.items() if 'DEFAULT' in k})"
# Either FABLE is present, or x-instructions explains why it deliberately is not
```

**Commit message:** `Settings: map (or explicitly refuse) the audit tier in the parked Ollama profile`

---

## Step 3: Add the provider preflight guard

- [ ] Test-first: n/a (command specs)
- [ ] `/beastmode` preflight and `/phasegate`'s opening check: if
      `ANTHROPIC_BASE_URL` is set to a non-Anthropic host AND the tier alias this
      step needs is unmapped, STOP and say so rather than spawning and guessing
- [ ] Default when unconfigured is stop-and-ask, never guess, consistent with the
      Q2 unavailability rule

The only real failure mode left after Q2: switching `ANTHROPIC_BASE_URL` without
remapping the aliases. The suite does not need to detect the vendor (the alias
resolves to whatever is configured), it only needs to notice that the mapping is
missing.

Suggested message shape:

```
STOP: provider is <host> but ANTHROPIC_DEFAULT_FABLE_MODEL is unset.
Map the audit tier in settings.json env before running gates.
```

**File(s):** `.claude/commands/beastmode.md`, `.claude/commands/phasegate.md`

**Test:**
```bash
grep -n "ANTHROPIC_BASE_URL" .claude/commands/beastmode.md .claude/commands/phasegate.md
# Contrive it: set ANTHROPIC_BASE_URL to a dummy host with the tier unmapped,
# confirm /phasegate refuses instead of spawning
```

**Commit message:** `Add a provider preflight guard to /beastmode and /phasegate`

---

## Step 4: Stop assuming a pre-existing dirty tree is booyah's own work

- [ ] Test-first: n/a (command specs)
- [ ] `/booyah`: on the FIRST invocation of a session with a dirty tree, do not
      assume the work is yours. Show what is dirty and ask whether it is the step to
      commit or unrelated work to leave alone
- [ ] `/booyah`: second and subsequent invocations unchanged. `git add -A`, commit,
      proceed. The no-prompt permission model ("running `/booyah` IS the permission
      signal") is preserved for the common case
- [ ] `/yolo` state 3 (fix round): same narrow fix, same reasoning. First verify
      whether state 3's branch-match check already narrows it enough that the ask is
      redundant; if so, document that instead of adding a prompt

This is the one fix in this plan that came from a real failure rather than
inspection. On 2026-07-29 `/booyah` could not be used to land
[land-baseline-commits.md](land-baseline-commits.md) precisely because its Step 2
would have read a tree dirty with six unrelated concerns as "my previous step's
work" and swept all of it, plus the held Servanda suite, into one commit.

The assumption is correct once booyah is running. It is only wrong on entry.

**File(s):** `.claude/commands/booyah.md`, `.claude/commands/yolo.md`

**Test:**
```bash
# Contrive it: dirty an unrelated file in a repo with a plan, then run /booyah fresh.
# It must ASK rather than commit. Then re-run: it must proceed without asking.
grep -n "first invocation" .claude/commands/booyah.md
```

**Commit message:** `Don't assume a pre-existing dirty tree is the previous step's work`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `.claude/COMMANDS.md` | 1 |
| `.claude/settings.json` | 2 |
| `.claude/commands/beastmode.md` | 3 |
| `.claude/commands/phasegate.md` | 3 |
| `.claude/commands/booyah.md` | 4 |
| `.claude/commands/yolo.md` | 4 |

## Still to verify behaviorally (not a step, but do it before trusting gates)

`ANTHROPIC_DEFAULT_FABLE_MODEL` was confirmed present in the CLI binary by `strings`
on `~/.local/share/claude/versions/2.1.220`. That proves the name exists in the
build, not that it is honored as described. Set it to something identifiable once
and confirm a spawned subagent actually lands on that model. The inference is strong
(its three siblings demonstrably work through the Ollama profile) but gates are the
wrong place to discover an assumption was wrong.

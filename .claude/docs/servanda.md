# Servanda

> *pacta sunt servanda*: agreements must be kept.
> The kit is the enforcement half.

A workflow command suite for Claude Code. It exists to close the gap between
what an agent says it did and what it actually did.

**Status:** internal. Not shared, not a product. It may get its own repo
[someday](../../docs/plans/development-roadmap.md); this document is written so
that move is a `git mv`.

---

## The problem it addresses

An agent that reports success is not evidence of success. The failure mode that
matters is not an agent that breaks loudly; it is one that quietly does less
than it claimed and reports a clean result. Tests that pass because they assert
the bug. A review that approved its own work. A phase gate that ran, found
nothing, and was never capable of finding anything.

Servanda's answer is that **the approval signal must be separate from the work**,
and that verification must be structurally incapable of being weaker than the
thing it verifies.

## The mechanism: re-invocation as approval

One grammar throughout. Running a command again is what approves the previous
step. Nothing self-approves, and nothing asks for permission it was already
given.

```
/booyah      implement a step, stop.  Re-run = "I tested it" + commit + next step
/yolo        implement a feature on its own branch, stop.  Re-run = merge and wrap up
/beastmode   one confirmation, then continuous through the roadmap
```

The user's next keystroke is the evidence. It cannot be forged by the agent
because the agent does not type it.

## The autonomy ladder

Approval granularity coarsens as autonomy increases. The full contracts, and
crucially each command's **does NOT** list, are in
[COMMANDS.md](../COMMANDS.md); this is the shape.

| Command | Granularity | Approval signal |
|---|---|---|
| `/roadmap` | none, a viewer | n/a |
| `/gameplan` | none, planning | you iterate until it is good |
| `/booyah` | one step | re-run approves the last step |
| `/yolo` | one feature | re-run on a clean branch approves the merge |
| `/beastmode` | one phase | a single preflight confirmation, then continuous |
| `/phasegate` | a phase audit | invoked by you, or spawned by the above |

Each rung trades granularity for autonomy. None of them trade away the
verification.

## The idea worth stealing: a capability floor

This is the part that is not obvious, and as far as a 2026 survey of the
provider-routing tools found, the part nobody else does.

Verification runs in tiers:

- **Tier 1, deterministic.** Tests, conformance, CI. Decides everything
  decidable. Cheap and not negotiable.
- **Tier 2, per-PR review.** Runs on Opus, pinned.
- **Tier 3, phase gates.** Runs on Fable, **or not at all.**

That last clause is the whole idea. A model pin in this kit is a **tier alias**,
not a vendor: `model: "fable"` resolves through `ANTHROPIC_DEFAULT_FABLE_MODEL`,
so the vendor mapping lives one layer down and no command file knows or cares
who serves it.

What the pin asserts is a **floor**: an audit spawned at the Fable tier must
actually be the strongest model available, whoever makes it. If that cannot be
satisfied, the correct behavior is to **stop**, not to substitute something
cheaper and report a pass.

An adversarial audit that silently ran on a weak model is worse than no audit,
because it produces the paperwork of having checked.

### It is enforced, not merely intended

Under any routed profile (see [Patchbay](../../docs/patchbay.md)) the Fable tier
is left deliberately **unmapped**. A `/phasegate` or security pass therefore
halts rather than degrading.

Verified rather than assumed, 2026-07-30: with the variable unset,
`--model fable` resolves to the literal `claude-fable-5`, which a routed backend
rejects with a hard error and exit 1. It does **not** fall through to the Opus or
Sonnet mapping, which was the dangerous case.

Practical consequence: **run gates on a plain Anthropic session.** Under routing
they stop, by design.

## Design rules that keep it honest

- **Tests must fail before they pass.** A test written to demonstrate a bug by
  passing is worthless. The same unmodified test proves both the bug and the fix.
- **No per-provider fallback logic in command files.** The tier indirection
  already exists one layer down; duplicating it would be a regression, not a
  feature.
- **Findings STOP autonomous modes.** `/beastmode` halts on gate findings rather
  than attempting architectural fixes it was not asked to make.
- **Never squash, never rebase.** Full history is part of the evidence.
- **Capped attempts, then stop.** Autonomous modes never build on a broken
  foundation.

## Where things live

| | |
|---|---|
| Command specs (executable) | `../commands/*.md` |
| Contract summary and does-NOT lists | `../COMMANDS.md` |
| Global agent instructions | `../CLAUDE.md` |
| Roadmap and plans | `../../docs/plans/` |
| Gate assessments | `../../docs/assessments/` |

Each command file is the executable spec. `COMMANDS.md` is the contract summary
and is read on demand, not auto-loaded, via `/workflow-help`.

## Honest limitations

- **Zero acceptance testing** until 2026-08; the suite was built and baselined
  before it was ever walked end to end. The first real exercise was the Patchbay
  plan, which it ran successfully across ten steps.
- **The floor depends on a backend rejecting an unknown model name.** The halt
  works because routed providers have no model called `claude-fable-5`. A
  provider that happened to serve that name would not halt. No current or
  planned provider does, but the guarantee comes from the provider's catalog
  rather than from the kit validating the tier itself.
- **It is one person's kit.** The conventions encoded here are Scott's, and the
  contracts assume a single human reviewer who is present between steps.

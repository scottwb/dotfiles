# Patchbay

Run a coding harness against the model and provider you choose, one process at a
time.

A patchbay in a studio connects any source to any destination, one physical
connection at a time, with no central switchboard deciding for you. That is the
architecture: **harness x model x provider**, assembled per process, no daemon.

**Status:** shipped and in use, 2026-08-01. Four launchers, one harness. The
`pbay` front door described at the bottom is not built and should not be built
yet.

| | |
|---|---|
| Usage and setup | [README.md](../README.md), "Claude Code route launchers" |
| Design decisions D1-D12 | [plans/claude-route-launchers.md](plans/claude-route-launchers.md) |
| Gate evidence | [assessments/route-gates.md](assessments/route-gates.md), [assessments/mcp-schema-budget.md](assessments/mcp-schema-budget.md) |

This document is the *why*: what it is for, how it compares to the obvious
alternative, and where it goes.

---

## What exists today

```
bin/claude-run          the workhorse: provider table, model table, environment
bin/claude-glm          Ollama, local, glm-4.7-flash          free,  ~4 min to first token
bin/claude-gpt          OpenRouter, openai/gpt-5.6-sol        ~$0.06-0.10/turn, ~4 sec
bin/claude-ollama       the Ollama default
bin/claude-openrouter   the OpenRouter default
bin/claude-ps           every running session: backend, model, context, status
bin/claude-route-selftest   105 assertions, no session, no spend
```

Plain `claude` is untouched and stays on the Max subscription. Routing is per
process, so a routed session and a plain one run side by side and nothing global
is flipped to switch between them.

## The comparison you actually need: claude-code-router

[claude-code-router](https://github.com/musistudio/claude-code-router) (ccr)
solves an overlapping problem and solves most of it better. Anyone evaluating
Patchbay should start by assuming they want ccr instead.

**What ccr does:** runs a local proxy that presents one stable endpoint. Claude
Code thinks it is talking to Anthropic; ccr forwards to OpenRouter, DeepSeek,
Ollama, Gemini, Volcengine, or SiliconFlow. Config is
`~/.claude-code-router/config.json` with a Providers block and a Router block.

**Where ccr is straightforwardly ahead:**

- **Routing granularity.** ccr routes per *request type*, not per session:
  `default`, `background`, `think`, `longContext` (past a configurable token
  threshold), `webSearch`, `image`. Patchbay pins one model for a whole process.
- **Mid-session switching.** `/model openrouter,anthropic/claude-3.5-sonnet`
  changes model without restarting. Patchbay requires a new process.
- **More harnesses, today.** ccr already supports Claude Code, Codex, Grok CLI,
  Kimi CLI, Kilo Code, OpenCode, Pi, and ZCode. Patchbay supports one harness.
- **Operational features** Patchbay has none of: retries, credential pools, key
  rotation, ordered fallback models.

**Where Patchbay differs, and it is narrow:**

- **No daemon.** Patchbay sets environment variables and launches. Nothing to
  start, nothing to keep running, no shared state, no single point of failure.
  Two sessions on two backends need no coordination because there is nothing
  between them. ccr's proxy is a process you must have running and that every
  session depends on.
- **It refuses to degrade.** This is the real difference, below.

### The one thing ccr will not do for you

ccr's fallback feature is documented as *"sequential retry that tries each backup
model in order and returns immediately once a model responds successfully."*

That is the correct default for almost everything. Keep working; a weaker answer
beats no answer.

**It is exactly wrong for an audit.** A phase gate or adversarial security review
that silently fell back to a cheaper model has not degraded gracefully; it has
produced the paperwork of having checked while checking nothing. Ordered fallback
is, structurally, the anti-pattern that Servanda's capability floor exists to
prevent.

Patchbay is built so that a tier which cannot be served **halts**. Under any
routed profile the audit tier (`fable`) is deliberately left unmapped, so
`/phasegate` and security passes stop rather than running weak. See
[Servanda](../.claude/docs/servanda.md) for why that tier discipline exists.

Verified rather than asserted (Gate A Check 4a, 2026-07-30): with the variable
unset, `--model fable` resolves to the literal `claude-fable-5`, which a routed
backend rejects with a hard error and exit 1. It does not fall through to the
Opus or Sonnet mapping.

A survey of the provider-routing tools in 2026 found no tool with any concept of
a capability floor, a tier guard, or a refusal to substitute downward. They
compete on flexibility and cost. **Not degrading is the only axis where this work
is alone**, and it is a Servanda idea that Patchbay enforces rather than a
routing idea.

### When to reach for which

| Want | Use |
|---|---|
| Cheap model for grunt work, strong for reasoning, automatically | **ccr** |
| Switching models mid-session | **ccr** |
| Codex, OpenCode, Pi, Grok, Kimi against alternative providers | **ccr**, today |
| No background service, nothing to keep running | **Patchbay** |
| Sessions on different backends that cannot affect each other | **Patchbay** |
| Audits that stop rather than quietly running weak | **Patchbay** |

Honest summary: if you are not running Servanda-style quality gates, **use ccr**.
Patchbay's advantage is a discipline, not a capability.

## Where this goes

Speculative. Recorded so the reasoning is not lost, explicitly **not** a plan.

### `pbay`, a single front door

Wrappers do not scale across a matrix. Four launchers for one harness is fine;
four harnesses times six models is not. The general form:

```bash
pbay run claude glm          # what claude-glm does today
pbay run aider deepseek
pbay ps                      # claude-ps, as an alias
pbay doctor                  # preflight: op, key, credit limit, ollama, window
pbay models --refresh        # discover and cache; catalogs churn
pbay config set default.claude glm
pbay providers disable openrouter
```

State in `~/.pbay/`, with cache kept separable from config: config is precious,
cache is disposable and needs to be deletable when a stale model list confuses
things.

Three roadmap items fold into this as subcommands rather than separate tools:
the doctor script, the periodic model-slug refresh, and the harness expansion.

**Design notes for whoever builds it:**

- `pbay ps` must keep reporting *unrouted* sessions. `claude-ps` is useful
  beyond Patchbay, and narrowing it to routed sessions only would be a
  regression.
- The model cache is **account-specific**, not global. Zero Data Retention
  settings filter OpenRouter's catalog per account, so a cache shared between
  accounts would be wrong. It needs a TTL and an explicit refresh.
- **Bash will stop paying here.** `claude-run` is ~250 lines and comfortable.
  Subcommand dispatch plus config parsing plus JSON cache handling plus TTL logic
  is a different program. Decide the language deliberately rather than
  discovering it at 900 lines.

### `bin/agent` and `pbay` are the same shape

`bin/agent` exists on disk today, untracked as of 2026-09-02. It is v0 and
deliberately small: a `DEFAULTS` array (`--model opus --effort high
--remote-control --permission-mode auto`), a session name derived from the
current directory's basename, a check that backs off if the caller passed
`-n`/`--name` themselves, the caller's own arguments appended last so they
always win, a canary line to stderr naming the exact command, and `exec`. Its
header says directory-aware config comes later.

That is the same job `pbay run` describes above: choose the right defaults for
a context, then exec a harness. `agent` picks them by *directory*; `pbay run`
picks them by *backend*. Two axes of the same lookup, and `agent`'s hardcoded
`DEFAULTS` array is the thing `~/.pbay/` config is meant to replace.

**Decision, 2026-09-02: keep both names.** Scott expects to stay attached to
`agent`, and it is the verb he actually types. The likely shape is one
implementation with two doors:

- `agent` stays the ergonomic front door. No subcommand, no ceremony, just
  "start a session here with the right defaults." This is the common case and
  it should stay one word.
- `pbay` is the full CLI: `run`, `ps`, `doctor`, `models`, `config`,
  `providers`. Everything that needs a noun and a verb.

So `agent` becomes either a thin wrapper over `pbay run` with the directory
profile applied, or the same binary dispatching on `argv[0]`. Whoever builds
this should not treat the two names as a thing to resolve. They are a
deliberate keep-both.

Two things to carry across when they merge:

- `agent`'s defaults are per-machine and hardcoded, which was fine for v0 and
  is exactly what the config store is for. The migration is DEFAULTS becoming a
  profile, not a rewrite.
- The canary line matters. It is how you find out that a different `agent` is
  shadowing this one on PATH, or that you are not in the directory you thought
  you were. Keep it, on stderr, printing the resolved command.

### The trigger for building it

**The first time you want aider or codex against a routed backend for real
work.** That is when the matrix becomes real.

Until then it is a nicer architecture for a problem that does not exist on this
machine: one harness, two backends, four launchers, nothing chafing. Building it
sooner would be inventing requirements.

Note the awkward fact here: ccr already supports Codex, OpenCode, Pi, Grok, and
Kimi. So the trigger event is also the moment ccr becomes the obvious answer.
Which leads to the honest question below.

### Or: give up and build on ccr

Worth taking seriously rather than dismissing.

If the only durable advantage is the capability floor, and ccr already does
everything else better across more harnesses, then the highest-value version of
this idea might not be a competing launcher at all. Options, roughly in order of
effort:

1. **Configure ccr and drop Patchbay**, accepting that gates must run on a plain
   Anthropic session and enforcing that by convention rather than by code.
2. **Contribute a tier guard upstream.** A per-route `required: true` or
   `no_fallback: true` flag that makes a route fail rather than degrade is a
   small, coherent feature that fits ccr's existing config shape. If it landed,
   the differentiator disappears in the best possible way: the idea wins and the
   code is someone else's problem.
3. **Fork ccr** if upstream is not interested.
4. **A thin layer above ccr** that owns the tier policy and delegates transport,
   keeping Patchbay's discipline without reimplementing routing.

Option 2 is the most interesting and the least work. It has not been attempted,
and no issue has been filed. The `no_fallback` idea has not been validated
against ccr's maintainers or its actual code, only against its documentation.

## What the gates cost and bought

Three gates, $0.48 of OpenRouter credit, and they earned it:

- **Killed a wrong premise.** The blocking prerequisite (fix a `num_ctz` typo,
  rebuild the model) turned out unnecessary: `OLLAMA_CONTEXT_LENGTH` already
  supplied the window. The plan's own verification command was also invalid,
  since `ollama show` reports the GGUF ceiling regardless of what is applied.
- **Turned the floor from intention into fact** via Gate A Check 4a.
- **Found that the backends differ more than expected**: ~220s versus ~4s to
  first token, 202752 versus 1M context, free versus metered. Neither dominates,
  which is why both exist.
- **Found that Ollama needs MCP trimming and OpenRouter does not**, because
  OpenRouter cache-hits the schema block at 84.5% while Ollama caches nothing.

Full evidence in [assessments/route-gates.md](assessments/route-gates.md).

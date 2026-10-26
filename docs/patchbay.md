# Patchbay

Run a coding harness against the model and provider you choose, one process at a
time.

A patchbay in a studio connects any source to any destination, one physical
connection at a time, with no central switchboard deciding for you. That is the
architecture: **harness x model x provider**, assembled per process, no daemon.

**Status:** shipped and in use, 2026-08-01. Five launchers, one harness. The `pbay` design at the bottom is proposed and queued on the roadmap, one piece at a time; a second harness still waits for its trigger.

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
bin/claude-run          the launcher: provider table, model table, environment
  claude-run glm        Ollama, local, glm-4.7-flash          free,  ~4 min to first token
  claude-run gpt        OpenRouter, openai/gpt-5.6-sol        ~$0.06-0.10/turn, ~4 sec
  claude-run gemini     OpenRouter, google/gemini-3.8-flash   ~$0.04-0.07/turn, ~4 sec
bin/claude-ps           every running session: backend, model, context, status
bin/claude-route-selftest   154 assertions (7 skip without Ollama), no session, no spend
```

Aliases are shorthand, not the only door. `claude-run --provider openrouter
--model <any-slug>` reaches anything the backend serves with nothing
pre-configured, resolving the context window from OpenRouter's catalog (cached
24h) and failing rather than guessing when it cannot.

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

Proposed, not planned. Each piece becomes a plan when its roadmap item comes up.

### `pbay`

**Status:** proposed design, 2026-10-19. Each piece is gameplanned when its roadmap item comes up, and that plan may still change details.

**The goal:** a session starts with the right harness, provider, model and effort without passing any of them. Config decides; flags override. One front door instead of a wrapper per combination, because wrappers do not scale across the harness x model x provider matrix.

#### Three layers

```
agent / pbay run [harness] [standard args] [-- native args]
   |  pbay: picks the harness, merges config from ~/.pbay/ down to ./.pbay/,
   |        turns it into standard args (command-line args win)
   v
claude-run [standard args] [-- native args]        (one runner per harness)
   |  runner: translates standard args to the harness's own flags,
   |          sets the route environment, launches
   v
claude   (later: codex, aider, opencode, ...)
```

- **`agent` is an alias for `pbay run` and nothing else.** Any harness, not only Claude: `agent`, `agent codex`, `agent "fix the bug"`. There is no `agent ps`. It exists because `agent` is the word Scott actually types; it is optional at install, and skipped when `agent` already resolves to something else on that machine.
- **Keep `bin/agent`'s canary line:** the resolved command, printed to stderr. It is how you find out a different `agent` is shadowing this one on `PATH`, or that you are not in the directory you thought you were.
- **`pbay` is the full CLI:** `run` first; later `ps`, `doctor` (which providers have a working key, and which harnesses can use each), `models --refresh` (which also warns when a model's catalog entry carries an `expiration_date`), and `config`.
- **`pbay ps` wraps `claude-ps`.** `claude-ps` becomes its own open-source tool, `facetdigital/claude-ps`: generic, Claude-only, with no Patchbay in it. `pbay ps` runs `claude-ps --json` and adds the route columns (provider, routed model), which is the job of the "Patchbay enricher" section in today's script. Unrouted sessions still appear, since `claude-ps` lists them all. A harness-plugin `pbay ps` that also lists other harnesses' sessions waits for v2.
- **`pbay` always passes an explicit model and effort.** `settings.json`'s `model` and `effortLevel` govern bare `claude` only, so a `pbay` session never depends on them.
- **Picking the harness.** The first argument after `run` picks a harness only when it *exactly* equals an installed harness name. Anything else, including flags and a quoted prompt, goes whole to the default harness. A prompt collides only if the entire prompt is a harness name, and `agent claude codex` covers that.
- **One runner per harness, one interface for all of them.** Every runner takes the same standard args, modelled on Claude Code's (`--model`, `--effort`, `--provider`, `--context`, `--name`, `--permission-mode`, `--remote-control`, `--resume` / `--continue`, an opening prompt), and maps them to its harness's own flags, all inside that one script.
- **Runners never read config.** `pbay` turns config into args, and the runner only ever sees args. A runner is testable on its own, and adding a harness touches one file.
- **An unsupported standard flag is an error,** never silently dropped (codex has no `--remote-control`). The same rule `claude-run` already applies to flags it cannot honour.
- **Native flags pass after `--`, untranslated,** so a harness feature is usable before it has a standard flag.
- **One conformance suite for every runner:** the same standard args in dry-run mode, and where possible the native command handed to the harness's own argument parser. `claude-run`'s `CLAUDE_ROUTE_DRYRUN=1` becomes the standard `--dry-run`.
- **`/shift-change`'s relaunch loop lives in the Claude runner,** because it depends on how Claude exits. The agent cannot type `/exit`, so the commands end the session with a signal: `/end-session` sends SIGTERM (exit 143) and the loop stops; `/shift-change` sends SIGHUP (exit 129) and the loop starts a fresh session with the same name, route, model and flags, minus any resume flag. If Claude Code ever exits the same way for both, a mode file keyed to the launcher's PID tells them apart.

#### Runner names: decided, deferred

Runners will be named `pbay-run-<harness>` (`pbay-run-claude`, `pbay-run-aider`) and found anywhere on `PATH` by that prefix, the way git runs `git-foo` as `git foo`. The prefix makes `PATH` discovery safe where a bare `*-run` would not be, the harness name comes from the filename with no table to keep in step, and one `bin/pbay*` glob covers the whole family for checks. It leaves room for `pbay-<sub>` subcommands too.

**Deferred (Scott, 2026-10-19):** `claude-run` keeps its name until a second harness arrives, so the Servanda docs that name it are not touched yet. Until then `pbay run claude` calls `claude-run` directly, and there is nothing to discover.

#### Config: `~/.pbay/` and `.pbay/` folders

- **Layered, nearest wins.** Load `~/.pbay/config`, then every `.pbay/config` on the path from there down to the current folder. A subfolder that says only `model = sonnet` keeps the harness from above. Expected main use: `.pbay/` folders in repos.
- **Flat keys,** git-config style (`model = sonnet`, `tier.routine.model = ...`). Merging is then last-wins per key with no nested-merge rules, and it stays parseable in bash.
- **`root = true`** stops inheritance from above, as in EditorConfig.
- **`pbay config --show-origin`,** like git's, shows which file set each value. Layered config is undebuggable without it.
- **Committed versus personal.** `.pbay/config` is committed and shared. `.pbay/config.local` is gitignored and personal, and wins over `config` in the same folder: the same split as Claude Code's `settings.json` and `settings.local.json`. A `config.local` that git *tracks* is treated as committed, since a cloned repo could ship one.
- **First run writes only `~/.pbay/`.** It detects installed harnesses (`command -v claude codex aider ...`), proposes defaults, and asks to confirm the default harness, provider, model, effort and tier map. A repo gets a `.pbay/` only from an explicit `pbay init`, never automatically. In an unattended run with no config, stop with a clear error; never wait on a question nobody will answer.
- **`bin/agent`'s hardcoded `DEFAULTS` array becomes `~/.pbay/config`.** Its per-directory naming and the config's per-folder layering are the same idea. Scott's `~/.pbay/config` is tracked in dotfiles.
- **Agent secrets by folder.** `~/.pbay/config` can set environment variables for sessions launched under a given folder, like git's `includeIf`, so an agent's Slack or HubSpot token comes from its `op://` reference only when that agent starts. Only the launch's own folder is resolved. This replaces shell aliases that export the tokens by hand.
- **Cache stays out of config.** `${XDG_CACHE_HOME:-~/.cache}/patchbay/` already holds the model catalog.

#### Tiers

Claude Code's tier names are the keys: `fable`, `opus`, `sonnet`, `haiku`. Claude Code resolves each through `ANTHROPIC_DEFAULT_<TIER>_MODEL`, which `claude-run` already sets, so a config's tier map becomes those variables and Servanda's `model: "fable"` and `model: "opus"` pins keep working untouched. A tier can be explicitly `unmapped`, which keeps D12: a routed session's audit tier halts instead of running on something weak.

Scott's labels (thinking, normal, routine, trivial) are display names for now. Renaming the keys waits, with the runner rename, so Servanda is not touched yet.

**Domain is not a config axis.** Coding, business, writing and sales are already separated by the folder tree: the sales repo's `.pbay/` picks its model and the writing vault picks another. A category key would mean naming the category at launch, which is the flag-passing this design removes.

#### Providers and credentials

There will be many keys (OpenRouter, OpenAI, Google, z.ai, ...), so credentials belong to providers. Each provider is defined once in `~/.pbay/` and only named everywhere else:

```
# ~/.pbay/config
provider.openrouter.url         = https://openrouter.ai/api
provider.openrouter.format      = anthropic
provider.openrouter.key_env     = OPENROUTER_API_KEY
provider.openrouter.key_ref     = op://<vault>/AI Keys/openrouter
provider.openrouter.key_account = <account>.1password.com
```

What may live where:

| | `~/.pbay/` | `.pbay/config.local` | `.pbay/config` (committed) |
|---|---|---|---|
| Pick provider, model, tier, effort | yes | yes | yes |
| Define a provider (url, format) | yes | no | no |
| `op://` key reference | yes | yes | no |
| Raw key | in `~/.pbay/credentials` only | no | no |

- **A committed config may only pick from providers defined in `~/.pbay/`.** Otherwise a cloned repo could send your session, and your key, to an endpoint of its choosing, or choose which vault item gets read behind a routine-looking TouchID prompt. A committed `op://` reference is also simply wrong for everyone except its owner.
- **Per-folder references exist for billing.** A client repo's `config.local` can point a provider at that client's key (say, a Mile26 OpenRouter key on `mile26.1password.com`), so usage in that repo lands on the client's account.
- **Raw keys live in `~/.pbay/credentials`,** separate from `config` the way `~/.aws/credentials` is, one line per provider, and `pbay` refuses to read it unless it is `0600`. Scott does not use it; his rule is no secrets at rest. It exists because teammates without 1Password would otherwise `export` keys from `.zshrc`, which is usually world-readable and often in a public dotfiles repo.
- **Lookup order:** the provider's environment variable (`key_env`, the vendor's usual name, so keys people already export just work), then `~/.pbay/credentials`, then the nearest `op://` reference. Unattended with no environment variable, an `op://` reference is an error, not a prompt.
- **Only the launch's own key is resolved.** Ten providers must not mean ten `op read`s or ten TouchID prompts.
- **Format decides which harnesses can use a provider.** Claude Code speaks only the Anthropic format: OpenRouter, Ollama, and z.ai's Anthropic-compatible endpoint (not yet verified). Direct OpenAI or Google need another harness, or OpenRouter. A runner refuses a provider whose format its harness cannot use.
- **No account details in any shipped script.** The selftest's identifier check (`bin/claude-route-selftest`, which looks for Scott's account, username and vault-path strings) must scan `bin/pbay*` as well as `bin/claude-*`.

#### Build order

Separate roadmap items, each gameplanned when it comes up: `/end-session` (Servanda, no Patchbay needed); move Patchbay into `facetdigital/patchbay`; extract `facetdigital/claude-ps`; the `pbay` merge (`pbay run` and the `agent` alias); `/shift-change`; then config, including `pbay doctor`. The second harness, the runner rename, the tier-label rename and the plugin `pbay ps` stay with v2 and its trigger.

**Decide the language at the config item.** `claude-run` is comfortable bash. Subcommand dispatch, layered config and caching together are a different program; choose deliberately rather than discovering it at 900 lines.

### The trigger for building it

This gates only the second harness and what comes with it: the runner rename, the tier-label rename and the plugin `pbay ps`. The merge and the config store do not wait for it.

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

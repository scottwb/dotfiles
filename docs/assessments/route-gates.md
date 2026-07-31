# Assessment: Route Gates A and B

Gates 2 and 3 of the [claude-route-launchers.md](../plans/claude-route-launchers.md)
plan. Gate 0's separate record is [mcp-schema-budget.md](mcp-schema-budget.md).

| Gate | Subject | Cost | Status |
|---|---|---|---|
| A | Ollama routing and Max OAuth coexistence | Free | ✅ **PASS** 2026-07-30 |
| B | MCP tool calling through OpenRouter | $0.481415 | ✅ **PASS** 2026-07-30 |

Gate A was the one that could reshape the whole design, and all five checks
passed. Per-process routing is viable, coexists with the Max login, and drives
real MCP tool calls through a local model.

Check 5 was added mid-gate. The plan gated MCP tool calling for OpenRouter
but never for Ollama, leaving D5's mission requirement unverified on a backend the
plan otherwise treated as proven. Testing it was free and came before any spend.

**Both gates now pass.** D5's mission requirement, real MCP tool calling, holds on
both backends, measured with the same open-meteo probe against the same
independently verifiable value. All three gates in the plan are cleared and the
build steps are unblocked.

---

## Gate A: Ollama routing and Max OAuth coexistence

### Manual prerequisite: RESOLVED, and not the way the plan expected

**Outcome: the rebuild is unnecessary. The effective window is already 202752.**

The plan assumed the `num_ctz` typo meant the intended 198K window was not being
applied, and made fixing it a blocking prerequisite. Investigation on 2026-07-30
showed the conclusion was right about the typo and wrong about the consequence.

What was actually found:

1. **The typo is real and the parameter is silently dropped.** `ollama show` and
   `/api/show` list the applied parameters as `min_p`, `repeat_penalty`,
   `temperature`, and `top_p`. There is no `num_ctx`. Ollama accepted the
   unknown `num_ctz` key without complaint and discarded it.
2. **`OLLAMA_CONTEXT_LENGTH=262144` is set in the environment**, so the server
   inherits a 256K default for every model. That is larger than the 198K the
   Modelfile was trying to pin.
3. **The model's GGUF architecture ceiling is 202752**, so the 256K default
   clamps down to it.
4. **Measured effective window: 202752.** From `/api/ps` with the model loaded:

   ```json
   { "name": "glm-4.7-flash:latest", "context_length": 202752,
     "size_vram": 30147314974 }
   ```

The intended number is reached by a different mechanism than intended. Gate 0's
Q1 arithmetic assumed 198K and is therefore **confirmed, not provisional**.

### The measurement trap this exposed

`ollama show glm-4.7-flash | grep -i "context length"`, which is what the plan's
Step 2 test specified, reports **202752 regardless**. That figure is the GGUF
architecture ceiling, not the applied window. It would have read the same before
and after the fix and confirmed nothing.

**`/api/ps` on a loaded model is the only reading that reflects the truth**,
because it reports the window the runner actually allocated. This is exactly the
check the plan's Step 5 already specifies, and this finding is the concrete
justification for it.

### Known fragility, deliberately accepted for now

The 202752 window depends on `OLLAMA_CONTEXT_LENGTH` being set in the
environment the **server** was started from. A server launched without it (via
`brew services`, launchd, or a shell that does not export it) silently falls back
to Ollama's much smaller built-in default. Nothing warns; sessions just start
truncating.

Two consequences:

- `bin/claude-run`'s Step 5 `/api/ps` preflight is not a nicety. It is the only
  thing standing between a misconfigured server and a silently crippled session.
  Keep it, and make it warn loudly.
- Fixing the Modelfile is still worth doing eventually, since a baked-in
  `num_ctx` holds regardless of server environment. It is no longer a blocker,
  so it moves to the roadmap rather than gating this plan.

### Why the rebuild failed, for whoever fixes it later

```
Error: failed to validate GGUF with llama-quantize without compatibility
patches: llama-quantize failed: exit status 1
```

Line 5 of `Modelfile.glm-4.7-flash` is `FROM /Users/scottwb/.ollama/models/blobs/sha256-9eba...`,
a raw GGUF blob path. Building from a blob makes Ollama re-import the model from
scratch: parse GGUF, validate, run `llama-quantize`. That last step fails on
Ollama 0.30.7.

The fix is the one the file's own generated header recommends:

```
FROM glm-4.7-flash:latest
```

Building from the already-imported model name layers new parameters onto
existing blobs with no GGUF re-parse, so the failing path is never taken.

### Context length, recorded

| When | `ollama show` (ceiling) | `/api/ps` (effective) |
|---|---:|---:|
| Before any fix, as found | 202752 | **202752** |
| After a Modelfile fix | not needed | not needed |

### Preflight

```bash
curl -fsS --max-time 2 http://localhost:11434/api/version
# Effective window, NOT `ollama show` (see "the measurement trap" above).
# Reports nothing unless the model is loaded, which is itself the signal.
curl -fsS http://localhost:11434/api/ps | jq '.models[] | {name, context_length}'
```

### Launching a routed session by hand

No scripts yet. That is the point of this gate: prove the environment works
before building anything that depends on it.

```bash
ANTHROPIC_BASE_URL=http://localhost:11434 \
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_API_KEY="" \
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.7-flash \
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.7-flash \
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.7-flash \
CLAUDE_CODE_MAX_CONTEXT_TOKENS=202752 \
ENABLE_CLAUDEAI_MCP_SERVERS=false \
claude --model glm-4.7-flash
```

Notes on why each piece is there:

- `ANTHROPIC_API_KEY=""` is an empty string, not unset. Unset causes fallback to
  authenticating against Anthropic directly.
- `ANTHROPIC_DEFAULT_FABLE_MODEL` is deliberately absent. That is Check 4's
  subject, not an oversight.
- `ENABLE_TOOL_SEARCH` is deliberately absent per D5.
- `ENABLE_CLAUDEAI_MCP_SERVERS=false` is included on Gate 0's finding: it saves
  37.4k and removes run-to-run variance.
- No `exec`, and none in anything built later. D6's route detection walks process
  ancestry, and `exec` erases the ancestor it looks for.

---

### Check 1: no login prompt in the routed session

The routed session starts and completes one trivial turn without prompting for
login and without requiring `/logout` first.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Session started and completed a turn with no login prompt and
  no `/logout`.
- **Significance:** per-process routing is viable. The design holds.

### Check 2: plain `claude` is still on Max afterward

Exit the routed session, run plain `claude`, and confirm `/status` shows the Max
subscription account with no re-login.

This is the check the whole per-process design rests on. Routing must not
disturb the stored OAuth credentials.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Plain `claude` still on the Max subscription, no re-login
  required. Routing leaves the stored OAuth credentials untouched.
- **Significance:** this is the load-bearing result of Gate A. Routed and plain
  sessions coexist, so the launcher family can be per-process rather than a
  global mode flip.

### Check 3: CLI `--model` overrides the settings.json pin

`.claude/settings.json` pins `"model": "claude-fable-5[1m]"`. The routed launch
passes `--model glm-4.7-flash`. Confirm the session actually runs the local
model rather than the pinned one.

Routed sessions depend entirely on this precedence, so an unverified assumption
here would surface as a confusing failure much later.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** `--model` wins over the settings.json pin. The launchers can
  rely on CLI precedence.

### Check 4: is `ANTHROPIC_DEFAULT_FABLE_MODEL` actually honored?

The roadmap flags this as unproven, and **D12 depends on knowing which way it
behaves.** The variable exists in the binary. Existing and being honored are
different claims, and only the second one makes D12 a real choice.

Split into two parts, because D12 needs both answered.

Tested with `claude --model fable -p` in headless mode rather than by spawning a
subagent, deliberately. A subagent test depends on `glm-4.7-flash` competently
driving the Agent tool, which would make a failure ambiguous between "the tier is
unmapped" and "the local model fumbled the tool call." The tier alias exercises
the same resolution path with nothing else in the way, and the result is read off
Ollama's `/api/ps` rather than off the model's prose.

**4a. Unmapped means halt, not silent fallback.**

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS, halts loudly.**

  ```
  There's an issue with the selected model (claude-fable-5). It may not exist
  or you may not have access to it. Run --model to pick a different model.
  === EXIT CODE: 1 ===
  ```

  `/api/ps` stayed empty. Nothing loaded.

  The error naming **`claude-fable-5`** is the informative part. With the
  variable unset, `--model fable` resolved to Anthropic's literal model ID and
  sent that to Ollama, which has no such model. It did **not** fall through to
  the Opus or Sonnet mapping: `glm-4.7-flash` never loaded.

- **Significance: D12 is sound as written.** The dangerous failure mode, silently
  auditing on a local 30b while reporting success, does not occur. Leaving the
  audit tier unmapped produces a hard, actionable stop.

- **One edge worth noting.** The halt happens because the backend lacks a model
  named `claude-fable-5`, not because Claude Code detects an unmapped tier. A
  backend that happened to serve that name would not halt. No current or planned
  provider does, so this is theoretical, but it means the guarantee comes from
  the backend's model list rather than from Claude Code's own validation.

**4b. Mapped means used.**

Same command with `ANTHROPIC_DEFAULT_FABLE_MODEL=qwen3:30b-a3b` added, other
tiers still on `glm-4.7-flash` so the result is unambiguous.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Returned `PONG`, exit 0, and `/api/ps` showed
  `qwen3:30b-a3b` loaded. The variable is honored, not merely present in the
  binary.

- **`glm-4.7-flash` also appeared in `/api/ps`, and that is correct.** Claude Code
  makes background utility calls at the haiku tier, which was mapped to glm. The
  main turn went to fable/qwen, background traffic to haiku/glm. Both resolved as
  configured.

  Design consequence: **the haiku mapping is load-bearing even when a session only
  asks for one model.** `bin/claude-run` must map the haiku tier on every routed
  profile, or background calls fail against a backend that has no
  `claude-haiku-4-5`.

### Check 5: MCP tool calling works through Ollama

**Added 2026-07-30, after the original four were answered.** The plan gated MCP
tool calling for OpenRouter (Gate B, Check 2) but never for Ollama, even though
D5 names tool calling as the mission requirement for routed sessions generally.
Gate A's launch check was only "starts and completes one trivial turn," which is
a far weaker bar.

That asymmetry mattered because of ordering. Gate B costs money and comes first
in the plan. If Ollama cannot drive MCP tools, that would have surfaced in Step 5,
after paying for Gate B and building the workhorse. This check is free and uses a
server that is already running, so it belongs before any spend.

`glm-4.7-flash` advertises `tools` in its capabilities, so the model supports
tool calling in principle. What is unproven is whether it works end to end
through Claude Code's MCP path against Ollama's Anthropic-compatible endpoint,
and whether a 30B model reliably emits a real tool call rather than answering
from prose.

**Method.** Isolate a single cheap MCP server with `--strict-mcp-config`, ask for
a value the model cannot know, and verify from two independent angles rather than
trusting the model's own account of what it did.

`open-meteo` is the right probe: no auth, no side effects, read-only, and small
(~11k of schema against trello's or google-docs' bulk, which keeps the cold start
down). **Current temperature is the specific ask because it varies by the hour.**
An elevation or a capital city could plausibly be recalled from training data; a
temperature reading right now cannot be.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Exit 0, `is_error: false`, `num_turns: 2`.

**Proof 1, a real tool call was emitted:**

```json
{"type":"tool_use","name":"mcp__open-meteo__weather_forecast",
 "input":{"latitude":37.7749,"longitude":-122.4194,
          "current_weather":true,"temperature_unit":"celsius"}}
```

**Proof 2, the result was real:** the tool returned `"temperature": 17.8` stamped
`2026-07-31T01:45`. An independent `curl` fifteen minutes earlier read 17.9 at
`01:30`. Two genuine readings from a drifting series, not a fabrication. The
model answered `17.8`, matching its tool result exactly.

**What this establishes.** D5's mission requirement holds on Ollama.
`glm-4.7-flash` selected the right tool from seventeen, constructed correct
arguments including two optional ones it was not given, parsed the JSON response,
extracted the correct field, and obeyed the "report only the number" instruction.
That is a competent multi-step agentic loop, not a lucky single call. The MCP
server reported `status: "connected"` throughout.

Neither feared failure mode occurred: no answering from priors without a tool
call, and no tool call erroring in transport.

---

#### Three incidental findings from the result block

**1. No prompt caching on this path.**

```json
"cache_creation_input_tokens": 0,
"cache_read_input_tokens": 0,
"input_tokens": 67572
```

Every token was billed as fresh input across both turns. Whether llama.cpp reused
its own KV cache internally is a separate question from what Claude Code's
accounting sees, and what it sees is zero.

**Methodological gift for Gate B:** these are exactly the fields Gate 0's deferred
Q2 needs. Q2 turns on whether OpenRouter cache-hits the schema block, and
`--output-format stream-json` exposes `cache_read_input_tokens` directly in the
result object. Gate B Check 6 can be answered by reading one number on turn two
rather than by inference or estimation.

**2. Cost telemetry is meaningless on routed sessions.**

```json
"total_cost_usd": 0.362395,
"modelUsage": {"glm-4.7-flash": {"provider": "firstParty", "costUSD": 0.362395}}
```

Claude Code labeled a local Ollama model as `firstParty` and invented a $0.36
charge for a session that cost nothing. It has no price table for routed models
and appears to fall back to a default rate.

Consequence: `/usage`, `/insights`, and any cost reporting are garbage on routed
sessions, and worse, they are silently garbage rather than blank. Worth a line in
the README so the numbers are not trusted or, more dangerously, summed against
real Anthropic spend.

**3. `CLAUDE_CODE_MAX_CONTEXT_TOKENS` took effect**, confirmed in-session:
`"contextWindow": 202752`, alongside `"maxOutputTokens": 32000`. The Step 4 model
table can set this with confidence.

---

### Unplanned finding: prompt processing latency

Not a check the plan asked for. It surfaced in Ollama's server log during 4b and
matters more than most things that were asked for.

```
prompt processing, n_tokens = 49152, progress = 0.84, t = 149.80 s
                                                    / 328.13 tokens per second
```

At 84% of 49152 tokens, the full prompt is roughly **58.5k tokens** running at
about **330 tokens/sec**. Wall clock on the run was 4.5 minutes.

Check 5 supplied a second, cleaner data point, since `stream-json` reports timing
directly:

| Run | Prompt tokens | Time to first token | Wall clock |
|---|---:|---:|---:|
| Check 4b | ~58.5k | not instrumented | ~270s |
| Check 5 | 33.2k | **219.7s** (`ttft_ms`) | 225.4s |

Two points is barely a trend, but they are consistent with a large **fixed
startup cost of roughly two to two and a half minutes** (model load and server
init) plus a marginal prompt-processing rate in the hundreds of tokens/sec. The
fixed component dominates at these sizes: Check 5's prompt was 43% smaller than
4b's yet took nearly as long.

Rough extrapolation, treating startup as ~150s fixed plus ~500 tokens/sec
marginal. Two noisy measurements, so read these as minutes-not-seconds rather
than as precise figures:

| Configuration | Prompt tokens | Est. cold start |
|---|---:|---:|
| Non-MCP floor only | 49.9k | ~4 min |
| Gate 0 config C (trimmed) | ~91.8k | ~5.5 min |
| Gate 0 config B | ~118.0k | ~6.5 min |
| Gate 0 config A (full) | ~155.4k | ~8 min |

The uncomfortable implication of a large fixed cost is that **trimming helps less
than Gate 0 alone suggested.** Going from config A to config C saves perhaps two
and a half minutes of an eight-minute start, not most of it. Trimming remains
necessary for window fit, which was Gate 0's actual finding, but it will not make
routed Ollama sessions feel fast.

**This reframes Gate 0's Q1.** Trimming was justified there on window fit, with
42.6k free being too little to work in. Latency is a second, independent, and
arguably harder constraint: an eight-minute wait before the first token makes a
routed session unusable regardless of how much window is left.

Mitigating factors, both real:

- llama.cpp reuses the KV cache across turns in a session (`cached n_tokens =
  49152` in the log), so this is a per-session cold start, not per-turn.
- The trimmed config is already the recommended one.

Still, it means a routed Ollama session has a multi-minute startup cost that
plain `claude` does not. That belongs in the README so the launchers are not
mistaken for broken on first use.

---

### Gate A verdict

✅ **PASS, 2026-07-30. All five checks green. Proceed to Gate B (Step 3).**

| Check | Result |
|---|---|
| 1. No login prompt in routed session | PASS |
| 2. Plain `claude` still on Max afterward | PASS |
| 3. CLI `--model` beats the settings.json pin | PASS |
| 4a. Unmapped audit tier halts loudly | PASS |
| 4b. Mapped audit tier is actually used | PASS |
| 5. MCP tool calling works through Ollama | PASS |

Recorded as PASS once on the strength of the first four checks, before Check 5
existed. That overclaimed, asserting the design held while D5's mission
requirement was untested on this backend. Corrected the same day, and Check 5 was
added and answered before the gate closed.

**The Ollama half of the plan is proven end to end.** Per-process routing
coexists with the stored Max login, the tier variables behave as D12 assumes, and
real MCP tool calls work through a local model.

**Still unproven: everything OpenRouter.** Gate B has its own stop condition,
Check 2, and it is untested. Checks 1 and 2 here concern how Claude Code handles
credentials under any `ANTHROPIC_BASE_URL` override, so they plausibly generalize,
but "plausibly generalizes" is not a measurement.

### What Gate A hands to the build steps

1. **`CLAUDE_CODE_MAX_CONTEXT_TOKENS=202752`** for the `glm` model-table entry,
   confirmed in-session as `contextWindow: 202752`.
2. **Map the haiku tier on every routed profile.** Background utility calls use
   it even when a session requests a single model.
3. **Keep the `/api/ps` preflight and make it warn loudly.** The 202752 window
   comes from `OLLAMA_CONTEXT_LENGTH` in the server's environment and is silent
   when absent.
4. **Trimming is required for window fit, but will not fix latency.** Cold start
   is dominated by a fixed two-plus-minute cost, not by prompt size.
5. **Document the multi-minute cold start** so a routed session's first turn is
   not mistaken for a hang.
6. **Document that cost telemetry is wrong on routed sessions**, not merely
   absent. Claude Code labels local models `firstParty` and invents charges.
7. **Gate B Check 6 has a precise method now:** read `cache_read_input_tokens`
   from the `stream-json` result block on turn two.

**D12 is confirmed sound**, not merely plausible. It can now be written into
`bin/claude-run` as a decision backed by observed behavior.

---

## Gate B: MCP tool calling through OpenRouter

✅ **PASS, 2026-07-30.** All six checks answered. The stop condition (Check 2) is
cleared, so the OpenRouter half of the plan is viable.

**This gate spent real money.** Everything before it was free. **Total:
$0.481415** of the $10 per-key cap, across five probe runs.

### Prerequisites, verified 2026-07-30

| Item | Status |
|---|---|
| OpenRouter account and credits purchased | ✅ `is_free_tier: false` |
| 1Password ref resolves | ✅ 74 bytes, matching the recorded 73-char `sk-or-v1` |
| Per-key credit limit set (D7) | ✅ `limit: 10`, `limit_remaining: 9.998755` |

D7's safety net is in place as a **per-key** cap, not merely an account-level
one. The distinction matters: an account-level limit governs total spend across
every key, so a runaway routed session would consume the whole account budget
before stopping. The per-key cap bounds the blast radius to this key alone. Both
are set; the per-key one is what D7 asks for.

Confirm at execution time without printing the secret:

```bash
KEY=$(op read --account facetdigital.1password.com "op://Employee/OpenRouter/API Key")
curl -fsS https://openrouter.ai/api/v1/key -H "Authorization: Bearer $KEY" \
  | jq '.data | {limit, limit_remaining, usage}'
unset KEY
```

### The stop condition

**Check 2 is the gate.** Per D5, MCP tool calling is the mission requirement. If
it fails, stop and report. Do not silently narrow the plan to a non-MCP subset;
that is Scott's call, not the runner's.

Gate A proved the equivalent for Ollama (its Check 5), so a failure here would
mean the two backends diverge and the OpenRouter half needs rethinking, not that
the whole plan dies.

### Launching a routed session against OpenRouter

Base URL is `https://openrouter.ai/api` with **no version suffix**; the client
appends `/v1/messages`. Adding `/v1` yourself produces `/v1/v1/`.

```bash
ANTHROPIC_BASE_URL=https://openrouter.ai/api \
ANTHROPIC_AUTH_TOKEN="$(op read --account facetdigital.1password.com 'op://Employee/OpenRouter/API Key')" \
ANTHROPIC_API_KEY="" \
ANTHROPIC_DEFAULT_HAIKU_MODEL=openai/gpt-5.6-sol \
ANTHROPIC_DEFAULT_SONNET_MODEL=openai/gpt-5.6-sol \
ANTHROPIC_DEFAULT_OPUS_MODEL=openai/gpt-5.6-sol \
CLAUDE_CODE_MAX_CONTEXT_TOKENS=1050000 \
ENABLE_CLAUDEAI_MCP_SERVERS=false \
claude --model openai/gpt-5.6-sol
```

Notes:

- `ANTHROPIC_API_KEY=""` is an empty string, not unset. OpenRouter documents that
  unset causes fallback to authenticating against Anthropic directly, which would
  silently defeat the whole test.
- **The haiku tier is mapped**, per Gate A's finding that background utility calls
  use it even when a session requests a single model. Gate A learned this the
  hard way; do not drop the line.
- `ANTHROPIC_DEFAULT_FABLE_MODEL` stays absent, per D12.
- `ENABLE_TOOL_SEARCH` stays absent, per D5.

---

### Check 1: the session starts and completes one trivial turn

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Exit 0, `is_error: false`, `num_turns: 2`, 10.3 seconds wall.
  MCP server reported `status: "connected"`. OpenRouter routed the request to
  **Azure** (`"provider": "Azure"` on each message), a detail worth knowing since
  the underlying host is not OpenRouter's own infrastructure and may affect
  latency or availability independently.

### Check 2: MCP tool calling works end to end (STOP CONDITION)

At least one real MCP tool call succeeds. Use the same isolated open-meteo probe
that answered Gate A's Check 5, so the two backends are measured identically.

Verify from two angles rather than trusting the model's prose: a `tool_use` block
naming an `mcp__open-meteo__*` tool in the `stream-json` output, and a returned
value matching an independent `curl` taken at the same time.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS. The stop condition is cleared.**

**Proof 1, a real tool call was emitted:**

```json
{"type":"tool_use","name":"mcp__open-meteo__weather_forecast",
 "input":{"latitude":37.7749,"longitude":-122.4194,"current_weather":true,
          "temperature_unit":"fahrenheit","timezone":"America/Los_Angeles", ...}}
```

**Proof 2, the result was real, and this one is exact.** The tool returned
`62.7°F` stamped `2026-07-30T19:30` in `America/Los_Angeles`, which is
`02:30 UTC`. The independent `curl` read `17.1°C` at `02:30 UTC`: the same
fifteen-minute interval. 62.7°F converts to 17.06°C. The model reported both
units itself, `62.7°F (17.1°C)`, matching ground truth to the decimal.

**D5's mission requirement now holds on both backends.** Ollama cleared it in
Gate A Check 5, OpenRouter clears it here, and both were measured with the same
probe against the same independently verifiable value.

### Check 3: a multi-step agentic loop works

Read a file, edit it, run a command, in one turn. Gate A's Check 5 was two turns
with a single tool; this is the harder case that real work depends on.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** Exit 0, `is_error: false`, `num_turns: 5`, 29 seconds.

Tool sequence, all three built-in types exercised:

```
Read   → FAILED (see below)
Read   → succeeded
Edit   → succeeded, structured patch shows "+line four"
Bash   → `wc -l sample.txt` → "       4 sample.txt"
```

Verified on disk independently of the model's report: `cat sample.txt` returned
four lines with `line four` correctly appended. The model reported the `wc`
output verbatim.

**The full agentic loop works through OpenRouter**: file reads, edits with
old_string/new_string matching, and shell execution, chained across five turns
with correct state carried between them.

#### The first Read failed, and it matters for Check 4

```json
{"name":"Read","input":{"file_path":"...sample.txt",
                        "offset":0,"limit":100,"pages":""}}
```
```
<tool_use_error>Invalid pages parameter: "". Use formats like "1-5", "3",
or "10-20". Pages are 1-indexed.</tool_use_error>
```

The model supplied `pages: ""` on a plain text file. `pages` applies only to
PDFs, and an empty string is not a valid value for it. The model self-corrected
on the retry and the run succeeded, so this is a **cost and latency tax rather
than a correctness failure**. It still consumed a full round trip and turned a
four-turn task into five.

### Check 4: Tool Call Error Rate

Record the observed impression, and check OpenRouter's published metric for the
model on its Performance tab.

- **Status:** PARTIAL. Observed behavior recorded below. **OpenRouter's published
  metric still outstanding**, from the model's Performance tab, which requires
  the dashboard.

#### Observed: 1 malformed call in 5, and a consistent cause

| Run | Calls | Malformed | Note |
|---|---:|---:|---|
| Check 2 | 1 | 0 | succeeded, but over-fetched badly |
| Check 3 | 4 | 1 | `Read` with `pages: ""`, self-corrected |
| **Total** | **5** | **1 (20%)** | both runs completed successfully |

**The two problems share one root cause: the model fills in optional parameters
it was never asked for, and sometimes fills them in wrongly.**

In Check 2, asked only for a current temperature, it sent:

```json
{"current_weather":true, "hourly":["temperature_2m"],
 "daily":["temperature_2m_max","temperature_2m_min"],
 "past_days":1, "forecast_days":1, ...}
```

That returned 192 hourly readings and 8 daily summaries to answer a single-value
question, inflating the tool result by orders of magnitude.

In Check 3, asked to read a small text file, it sent `offset`, `limit`, and
`pages` when `file_path` alone would do, and `pages: ""` was invalid enough to
error.

**Two distinct costs, neither of which is a correctness failure:**

1. **Wasted round trips.** The malformed call cost one full turn. At roughly
   $0.06 per turn on the observed runs, retries are not free.
2. **Context and token inflation.** Over-fetched tool results re-enter context and
   are billed as input on subsequent turns. The Check 2 payload was perhaps a
   hundred times larger than the question required.

**Assessment: reliable but uneconomical.** Both runs completed correctly and the
model recovered from its own error without help, which is the behavior that
matters for the gate. But `openai/gpt-5.6-sol` should be expected to spend more
tokens than an equivalent task on Anthropic-native models, and the launcher
documentation should say so rather than letting the first surprising invoice
explain it.

**Sample size is 5 calls across 2 runs.** Treat the 20% figure as directional,
not as a measured error rate. OpenRouter's published metric is the better number
and is still to be collected.

### Check 5: gateway model discovery

Confirm whether `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` populates `/model`
with OpenRouter's catalog. If it works, fewer thin wrappers are worth writing,
which changes Step 6's scope.

- **Status:** ANSWERED, 2026-07-30
- **Result: PASS.** `/model` lists roughly 56 entries, each labeled
  **"From gateway"**, with the `--model` value shown separately as
  "Custom model". Effort level and session-vs-default selection all work
  normally.

```
  ↑ 24. anthropic/claude-haiku-4.5         From gateway
    26. anthropic/claude-sonnet-4.5        From gateway
    28. anthropic/claude-opus-4.1          From gateway
  ❯ 33. openai/gpt-5.6-sol ✔               Custom model
     … +23 models
```

#### What this changes, and what it does not

**It does not eliminate the wrappers.** A wrapper's job is launching straight into
a backend from the shell, which `/model` cannot do; by the time `/model` is
available you are already in a session. `bin/claude-run` and its model table are
unaffected.

**It removes the pressure to add a wrapper per model.** Once inside a routed
OpenRouter session, any catalogued model is reachable interactively. The
follow-on roadmap item to add `kimi`, `deepseek`, and `qwen` wrappers should be
**downgraded**: those models are already reachable without new scripts, so
wrappers for them are a convenience rather than the access mechanism they would
otherwise be.

The D9 structure stands: one workhorse plus a small number of named entry points
for the backends and default models actually reached for daily.

#### The catalog is ZDR-filtered, and that shapes everything above

The visible Anthropic entries top out at `claude-sonnet-4.5`, `claude-opus-4.1`,
and `claude-haiku-4.5`, with no Claude 5 family present.

**This is not OpenRouter's full catalog.** Zero Data Retention settings are
enabled on the account, which filters out providers and models that do not offer
ZDR. The missing newer Claude models are a consequence of that filter, not of
OpenRouter lacking them. Scott may revisit the ZDR setting later.

Three corrections follow from this:

1. **The ~56 models shown are the ZDR-compatible subset**, not the catalog. Any
   count or coverage claim based on that list is a claim about the filtered view.
2. **It says nothing about the tool-loading gate.** An earlier draft of this
   section read the absence of Opus 5 and Fable 5 as weak evidence about
   OpenRouter's "older than Opus 4.8" rule for deferred tool loading. That
   inference was wrong: the models are absent because of ZDR, so the plan's open
   question on that gate remains open and untested. Low impact either way, since
   Anthropic models go direct on the Max subscription rather than being billed
   per token through OpenRouter.
3. **It constrains the roadmap's model expansion.** The queued follow-on to add
   `kimi`, `deepseek`, and `qwen` should verify each is ZDR-available before
   assuming it is reachable. A model in OpenRouter's public catalog is not
   necessarily in this account's.

ZDR is a deliberate privacy posture consistent with D10's telemetry stance, so it
should be treated as intended configuration rather than something to work around.
Worth noting in the README that the reachable model set is account-dependent,
since a reader on a non-ZDR account will see a different `/model` list from the
same launcher.

### Check 6: resolve Gate 0's deferred Q2 and Q3

Gate 0 deferred both because they turn on a single unobservable fact: **does
OpenRouter cache-hit the schema block?** Cached, the ~105.5k of schemas is paid
once per session and is negligible. Uncached, it is re-sent every turn, and a
50-turn session spends 5.3M input tokens on schemas alone.

Gate A supplied the method. `--output-format stream-json` reports the answer
directly in the result object, so this is one number on turn two rather than an
estimate:

```bash
jq -r 'select(.type=="result") | .usage
       | {input_tokens, cache_read_input_tokens, cache_creation_input_tokens}'
```

For reference, Ollama reported `0` for both cache fields.

Also record OpenRouter's input rate for `openai/gpt-5.6-sol`, so the cost can be
computed rather than guessed.

- **Status:** ANSWERED, 2026-07-30
- **Result: schemas ARE cached.**

```json
"input_tokens": 34531,
"cache_read_input_tokens": 29184,
"cache_creation_input_tokens": 0
```

**29184 of 34531 input tokens, 84.5%, were served from cache.** Note
`cache_creation_input_tokens: 0` alongside a large read: OpenAI models cache
automatically, with no explicit `cache_control` markers, so the block was already
warm from the small prior usage on this key. Nothing in the launcher needs to
request caching; it happens on its own.

**Q2 answer: YES.** The full set fits inside the 1M window at 15.5% and costs
little, because the schema block is not re-sent. Gate 0's expectation is
confirmed and D5 is viable as designed.

**Q3 answer: NO.** Trimming is not needed for OpenRouter, on either window fit or
cost.

**Design consequence, and it is a simplification.** The MCP allowlist that Gate 0
forced into Steps 4 and 5 stays **Ollama-specific**. It does not need to be a
shared feature of the workhorse. The two backends genuinely differ here:

| | Ollama | OpenRouter |
|---|---|---|
| Schema caching | none (`0` / `0`) | 84.5% cache read |
| Window pressure | severe (198K) | none (1M) |
| Trimming needed | **yes** | **no** |

### Observed cost, and a correction to Gate A's telemetry finding

| Run | Claude Code's `total_cost_usd` | Actual (key endpoint delta) | Diff |
|---|---:|---:|---:|
| Check 2 | $0.193987 | $0.194907 | 0.5% |
| Check 3 | $0.283188 | $0.285263 | 0.7% |

**Cost telemetry is accurate on OpenRouter.** Gate A found Claude Code inventing
a $0.36 charge for a free local Ollama session and concluded that "cost telemetry
is wrong on routed sessions." That generalized too far. The correct statement is
narrower: **cost reporting is accurate on OpenRouter and wrong on Ollama.** The
`"provider": "firstParty"` mislabel appears on both, but it only breaks the
arithmetic where there is no real price to compute against.

**Worth flagging for budgeting.** Two trivial probes, a weather lookup and a
four-line file edit, cost **$0.48 combined** against the $10 cap. That is not
cheap for work this small:

| Run | Turns | Cost | Per turn |
|---|---:|---:|---:|
| Check 2 (one MCP call) | 2 | $0.195 | $0.098 |
| Check 3 (read, edit, bash) | 5 | $0.285 | $0.057 |

At roughly $0.06 to $0.10 per turn, the $10 cap allows on the order of 100 to 170
turns. A single substantial coding session could consume a meaningful fraction of
it. The 84.5% cache hit is what keeps this from being far worse, and the
over-fetching noted in Check 4 pushes it the other way.

### Latency, against Ollama on the identical probe

| | Ollama (Gate A Check 5) | OpenRouter (here) |
|---|---:|---:|
| Time to first token | 219,688 ms | **4,910 ms** |
| Wall clock | 225,358 ms | **10,288 ms** |

**Roughly 45x faster to first token.** Gate A's multi-minute cold start is an
Ollama property, not a routing property. This is the sharpest practical
difference between the two backends and belongs in the README next to the model
table, since it should drive which launcher someone reaches for.

---

### Gate B verdict

✅ **PASS, 2026-07-30.** Every decision-relevant check green. **Total spend
$0.481415 of the $10 per-key cap.**

| Check | Result |
|---|---|
| 1. Session starts, trivial turn completes | PASS |
| 2. MCP tool calling end to end (STOP CONDITION) | PASS |
| 3. Multi-step agentic loop | PASS |
| 4. Tool Call Error Rate | PASS (observed). Published metric not collected |
| 5. Gateway model discovery | PASS |
| 6. Gate 0's deferred Q2 and Q3 | PASS, both resolved |

**On Check 4's gap, stated plainly** so this does not repeat Gate A's premature
all-clear: the observed error-rate behavior is measured and recorded, and it is
what informs the design. OpenRouter's *published* metric from the model's
Performance tab was not collected. It is a corroborating data point, not a
decision input, and nothing in the plan depends on it. Gate B does not hinge on
it; if it is collected later, record it above.

### What Gate B hands to the build steps

1. **`CLAUDE_CODE_MAX_CONTEXT_TOKENS=1050000`** and base URL
   `https://openrouter.ai/api`, no version suffix, for the `gpt` model-table
   entry.
2. **Map the haiku tier here too.** Same reasoning as Gate A.
3. **No MCP trimming for OpenRouter.** Per Check 6, the allowlist stays
   Ollama-specific, which keeps `bin/claude-run` simpler than Gate 0 feared.
4. **Do not add a wrapper per model.** Gateway discovery makes the catalog
   reachable in-session, so wrappers are for backends and daily defaults only.
5. **Document the cost profile**, since it is the sharpest difference from plain
   `claude` on the Max subscription: roughly $0.06 to $0.10 per turn, with
   `openai/gpt-5.6-sol` spending more tokens than the task requires.
6. **Document that cost telemetry is trustworthy here and not on Ollama.**

### The two backends, side by side

Both cleared the same mission requirement, measured with the same probe. They
differ sharply in everything else, and that difference should drive which
launcher a person reaches for:

| | Ollama (`glm`) | OpenRouter (`gpt`) |
|---|---|---|
| MCP tool calling | ✅ | ✅ |
| Multi-step agentic loop | not tested | ✅ |
| Time to first token | ~220 s | **~4 s** |
| Context window | 202752 | 1,050,000 |
| Schema caching | none | 84.5% |
| MCP trimming needed | **yes** | no |
| Marginal cost | $0 | ~$0.06 to $0.10/turn |
| Cost telemetry | wrong (invents charges) | accurate to <1% |

The tradeoff is clean: **Ollama is free and slow with a tight window; OpenRouter
is fast and roomy and metered.** Neither dominates, which is why the plan wants
both.

**Note one asymmetry in the evidence:** Gate A never ran a multi-step agentic
loop against Ollama. Its Check 5 was a single MCP call over two turns, while
OpenRouter got the harder read/edit/bash chain here. Whether `glm-4.7-flash`
sustains a five-turn loop with correct state is untested. Not a gate, since
Step 5's real use will surface it immediately, but it is an unexamined corner
rather than a proven one.

# Plan: Claude Code Route Launchers (OpenRouter + Ollama)

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `.claude/CLAUDE.md` - Developer/AI guidelines
   - `docs/plans/claude-route-launchers.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

**Two execution constraints specific to this plan:**

- **Steps 1 through 3 are gates.** Run them interactively, read the results, and stop. They exist to kill or reshape everything after them. Do not let an unattended runner blow through a failed gate into the build steps.
- **Step 3 spends real money** (a few dollars of OpenRouter credit). Everything before it is free.

---

## Summary

Add a family of `bin/` launcher scripts that run Claude Code against non-Anthropic
backends (OpenRouter for hosted models, local Ollama for local ones) on a
per-process basis, leaving plain `claude` and `claudedsp` completely untouched on
the Anthropic Max subscription.

The design is a workhorse plus thin wrappers: `bin/claude-run` owns the model
table, provider table, and all environment construction; `bin/claude-gpt`,
`bin/claude-glm`, `bin/claude-openrouter`, and `bin/claude-ollama` are three-line
entry points. Routing is per-process, so several sessions on different backends
can run at once, and `bin/what-claude` grows a ROUTE column that reads the route
back out of the process ancestry.

This is the first of an intended family. The same shape is meant to extend to
aider, codex, opencode, and pi later, which is why the transport logic lives in
one place rather than being copy-pasted per model.

## Decisions Reference

Steps cite these. All were settled in the 2026-07-30 design conversation; the
research backing them is summarized in "Research Findings" at the bottom.

| ID | Decision |
|---|---|
| **D1** | Scripts invoke the `claude` binary directly, never an alias. Permission mode is an overridable const in the workhorse, defaulting to `--dangerously-skip-permissions`. `claude` and `claudedsp` are untouched. |
| **D2** | Ollama host defaults to `localhost`, with a single const that is easy to repoint at a Tailscale name, `saber.local`, or a fixed IP. |
| **D3** | The parked `x-env` Ollama block in `.claude/settings.json` is removed only AFTER `claude-ollama` is proven working, as its own commit. |
| **D4** | Milestone one is plain `claude`, plus OpenRouter on the best GPT model, plus Ollama on `glm-4.7-flash`. Further models are roadmap items, not scope cuts. |
| **D5** | The mission requirement is MCP **tool calling**, not MCP **tool search**. `ENABLE_TOOL_SEARCH` is left unset so tools load upfront. |
| **D6** | Route detection uses process ancestry (`ps -o ppid=`), not PID marker files. This forbids `exec` anywhere in the launcher chain. |
| **D7** | A per-key credit limit is set in the OpenRouter dashboard as a safety net. Manual, one time. |
| **D8** | Home is `bin/`. Long term, `ollama-tools` shrinks to Ollama management only and all harness launchers live here. |
| **D9** | Structure is one workhorse (`claude-run`) plus thin named wrappers, reconciling the requested `claude-gpt` ergonomics with the existing `aider-run` dispatch precedent. |
| **D10** | The full telemetry and privacy block goes in every launcher, never in the global environment. Plain `claude` to Anthropic keeps its defaults. |
| **D11** | The secret is read at launch via 1Password CLI with TouchID gating. No plaintext key on disk, no `.env`. |
| **D12** | Under any routed profile the audit tier (`fable`) is left deliberately UNMAPPED, so Servanda phase gates and security passes halt loudly rather than running a weak adversarial audit. This answers the `x-ANTHROPIC_DEFAULT_FABLE_MODEL-DECIDE-ME` marker that `servanda-review-fixes.md` step 2 planted. |

## Requirements

- `claude`, `claude -p`, and `claudedsp` behave exactly as they do today, on the
  Max subscription, with no wrapper in the path and no telemetry changes.
- `claude-gpt`, `claude-glm`, `claude-openrouter`, and `claude-ollama` launch
  Claude Code against their respective backends, forwarding all arguments.
- Two sessions on two different backends can run simultaneously.
- The OpenRouter key is never written to disk in plaintext and never committed.
- `what-claude` reports which backend and model each running session is using.
- MCP tool calling works on a routed session. Tool search is explicitly not required.
- Every launcher can be inspected without launching anything, via a dry-run mode.

## Non-Goals

- Bedrock, Vertex, or any provider beyond OpenRouter and Ollama.
- Launchers for aider, codex, opencode, or pi. Roadmap, not this plan.
- MCP tool search on routed sessions. Confirmed unavailable on both backends.
- Changes to `ollama-tools` beyond the manual `num_ctx` fix in Step 2. Its scope
  reduction is a roadmap item.

---

## Implementation Steps

### Step 1: GATE 0 - Measure the real MCP schema cost

The cheapest possible gate. Free, local, no routing, no key, no server. Every
context-budget decision downstream depends on this number, and it is currently a
guess.

- [x] Write the failing test first: there is no recorded number for the upfront
      MCP tool schema cost. Create `docs/assessments/mcp-schema-budget.md` with
      the measurement table empty and the three threshold questions unanswered.
      The "test" fails while the table has no numbers in it.
- [x] Launch a normal Anthropic session with tool search forced off:
      `ENABLE_TOOL_SEARCH=false claude`
- [x] Run `/context` and record total tool-schema tokens, plus the per-server
      breakdown if shown
- [x] Repeat with `ENABLE_CLAUDEAI_MCP_SERVERS=false` to get the cost of the nine
      self-configured servers alone, without the claude.ai connectors
- [x] Record a third number with Trello and Google Docs disabled, since those two
      are roughly half the tool count
- [x] Verify green: the table has all three numbers, and each threshold question
      below is answered yes or no

**Threshold questions this step must answer:**

1. Does the full set fit comfortably inside `glm-4.7-flash`'s window (198K if the
   Modelfile is fixed) with room left for actual work? If no, routed Ollama
   sessions need a trimmed MCP set.
   **ANSWERED: no.** 105.5k MCP on a 49.9k non-MCP floor leaves 42.6k of a 198K
   window. Routed Ollama needs a trimmed set, which is new scope for Steps 4/5.
2. Does the full set fit inside a 1M OpenRouter model without meaningful cost?
   Expected yes, which is what makes D5 viable.
   **ANSWERED: yes**, via Gate B Check 6. Window fit is 15.5% of 1M, and the
   schema block is **84.5% cache-hit** (`cache_read_input_tokens: 29184` of
   `input_tokens: 34531`), so it is paid once rather than re-sent per turn.
3. Is trimming needed for OpenRouter at all? Expected no.
   **ANSWERED: no**, on either window fit or cost. The MCP allowlist therefore
   stays **Ollama-specific** rather than becoming a shared feature of the
   workhorse, which is simpler than Gate 0 feared.

**Satisfies:** D5. Determines whether a trimmed-MCP design is required, which was
deliberately deferred pending this measurement.

**File(s):** `docs/assessments/mcp-schema-budget.md`

**Test:**
```bash
# The measurement itself is the test. Confirm the record exists and is complete.
# Keyed off the unanswered markers, not a bare digit match: the scaffold carries
# reference numbers (tool counts, window sizes), so a digit match passes while
# the table is still empty.
test -f docs/assessments/mcp-schema-budget.md \
  && ! grep -q "UNANSWERED" docs/assessments/mcp-schema-budget.md \
  && ! grep -q "INCOMPLETE" docs/assessments/mcp-schema-budget.md \
  && echo "PASS: budget recorded and thresholds answered" \
  || echo "FAIL: gate 0 not resolved"
```

**Commit message:** `Measure the upfront MCP schema budget for routed sessions`

---

### Step 2: GATE A - Prove Ollama routing and Max OAuth coexistence

Still free. Uses the local Ollama server, so no spend. This gate answers the
question that would reshape the whole design if it failed: whether per-process
routing coexists with the stored Max login.

**Manual prerequisite: RESOLVED 2026-07-30, no rebuild needed.** The premise was
half right. The `num_ctz` typo is real and Ollama silently drops the parameter,
but `OLLAMA_CONTEXT_LENGTH=262144` in the environment supplies a 256K default
that clamps to the model's 202752 architecture ceiling. `/api/ps` on the loaded
model measures the effective window at **202752**, which is the number the
Modelfile was aiming for. Gate 0's Q1 assumption of 198K is confirmed.

Two things this changed:

- The `ollama show | grep "context length"` check below is **not a valid
  measurement**. It reports the GGUF architecture ceiling and reads 202752
  whether or not `num_ctx` is applied. Only `/api/ps` on a loaded model reflects
  the allocated window. Test updated accordingly.
- The window now depends on `OLLAMA_CONTEXT_LENGTH` being set wherever the
  server is started, which is fragile and silent when wrong. This is the concrete
  reason Step 5's `/api/ps` preflight must warn loudly rather than be dropped as
  redundant.

Fixing the Modelfile is still worth doing, since a baked-in `num_ctx` survives
any server environment. It is a roadmap item now, not a gate. Whoever does it
must also change line 5 from the raw blob path to `FROM glm-4.7-flash:latest`;
building from the blob re-imports the GGUF and fails in `llama-quantize` on
Ollama 0.30.7. Do not commit in `ollama-tools`; Scott reviews by diffing against
`main`.

- [x] Write the failing test first: `docs/assessments/route-gates.md` with Gate A's
      four checks listed and all four unanswered. Fails while any is blank.
- [x] Confirm the real context. NOT via `ollama show`, which reports the GGUF
      architecture ceiling and cannot distinguish applied from unapplied. Load the
      model and read `/api/ps`, which reports the window actually allocated.
      Measured 202752, matching intent. See the assessment for why the rebuild
      turned out to be unnecessary.
- [x] Start the server and confirm the preflight endpoint answers:
      `curl -fsS http://localhost:11434/api/version`
- [x] Launch Claude Code by hand with the Ollama env set inline (no scripts yet),
      confirm it starts and completes one trivial turn
- [x] **Check 1:** in that routed session, confirm no login prompt appeared and no
      `/logout` was required. **PASS.**
- [x] **Check 2:** exit, run plain `claude`, and confirm it is still on the Max
      subscription with no re-login (`/status` shows the subscription account).
      **PASS.** This is the result the per-process design rests on.
- [x] **Check 3:** confirm CLI `--model` overrides the `settings.json` pin
      (`claude-fable-5[1m]`), since routed sessions depend on that precedence.
      **PASS.**
- [x] **Check 4:** confirm `ANTHROPIC_DEFAULT_FABLE_MODEL` is actually honored
      rather than merely present in the binary. The roadmap flags this as
      unproven, and D12 depends on knowing which way it behaves. Split in the
      assessment into **4a**, that leaving it unmapped makes a fable-tier spawn
      halt loudly rather than silently falling through to the Opus or Sonnet
      mapping, and **4b**, that setting it to a distinct installed model makes a
      fable-tier subagent actually use that model. D12 needs both: 4a is the
      behavior it relies on, 4b proves the variable is live at all.
      **BOTH PASS. D12 is confirmed sound.** Unmapped resolves to the literal
      `claude-fable-5`, which the backend rejects with a hard error and exit 1,
      rather than falling through to the Opus or Sonnet mapping.
- [x] **Check 5 (added mid-gate):** confirm MCP tool calling works through Ollama.
      The plan gated this for OpenRouter (Gate B, Check 2) but never for Ollama,
      leaving D5's mission requirement unverified on a backend the plan otherwise
      treated as proven. Free, and it belongs before Gate B's spend. **PASS.**
      `glm-4.7-flash` emitted a real `mcp__open-meteo__weather_forecast` call with
      correct arguments, parsed the response, and reported a temperature matching
      an independent `curl`.
- [x] Verify green: all checks answered in the assessment file

**If Check 1 or 2 fails**, stop. The design becomes global-mode-flip rather than
per-process, and the rest of this plan needs rewriting.
**Both passed 2026-07-30.** The design holds as written.

**Three findings from this gate feed the build steps:**

1. **Map the haiku tier on every routed profile.** Claude Code makes background
   utility calls at that tier even when a session requests a single model, so a
   profile with haiku unmapped will see those calls fail.
2. **Cold-start latency is a hard constraint, independent of window fit.** Prompt
   processing measured ~330 tokens/sec, so the trimmed ~58.5k prompt took about
   three minutes before the first output token, and the full MCP set extrapolates
   to roughly eight. Combined with Gate 0's Q1, trimming is required on two
   independent grounds. Build the allowlist as a first-class feature, and
   document the cold start in Step 9 so it is not mistaken for a hang.
3. **The 202752 window is environment-dependent and silent when wrong**, so
   Step 5's `/api/ps` preflight must warn loudly rather than be treated as
   redundant with the `/api/tags` check.
4. **Cost telemetry is actively wrong on routed sessions, not absent.** Claude
   Code labeled a local Ollama model `"provider": "firstParty"` and invented a
   $0.36 charge for a free session. Step 9 must document that `/usage` and
   `/insights` are meaningless under routing, since silently wrong numbers invite
   being summed against real Anthropic spend.
5. **Gate B Check 6 now has a precise method.** Gate 0's deferred Q2 asks whether
   OpenRouter cache-hits the schema block; `--output-format stream-json` reports
   `cache_read_input_tokens` directly in the result object. Read it on turn two
   rather than estimating. (Ollama reported 0 for both cache fields.)

**Satisfies:** D2, D12. Also closes the roadmap's open question on
`ANTHROPIC_DEFAULT_FABLE_MODEL` behavior.

**File(s):** `docs/assessments/route-gates.md`

**Test:**
```bash
curl -fsS --max-time 2 http://localhost:11434/api/version || echo "FAIL: ollama down"
# NOT `ollama show | grep "context length"`: that is the GGUF architecture
# ceiling and reads 202752 whether or not num_ctx was ever applied. /api/ps
# reports the window the runner actually allocated, which is the real number.
curl -fsS http://localhost:11434/api/ps | jq '.models[] | {name, context_length}'
# Count UNANSWERED, not ANSWERED: "UNANSWERED" contains "ANSWERED" as a
# substring, so the naive grep counts every open check as a closed one.
# Expect 0 when Gate A is resolved.
grep -c "UNANSWERED" docs/assessments/route-gates.md
```

**Commit message:** `Record Gate A: Ollama routing and Max OAuth coexistence`

---

### Step 3: GATE B - Prove MCP tool calling through OpenRouter

**This step spends money.** Everything before it was free. Buy the minimum
credit, set the per-key limit first (D7), and treat the result as the go/no-go for
the entire OpenRouter half of the plan.

- [x] Write the failing test first: add Gate B's checks to
      `docs/assessments/route-gates.md`, unanswered. Fails while blank.
- [x] Manual prerequisite: buy minimum credits, then set a per-key credit limit at
      `openrouter.ai/keys` (D7). **Done 2026-07-30**, verified via the key
      endpoint: `limit: 10`, `limit_remaining: 9.998755`, `is_free_tier: false`.
      Note this had to be set **per-key**; an account-level limit was in place
      first and reports `limit: null` on the key endpoint, since it governs total
      spend across all keys rather than bounding this one. Both are now set.
- [x] Confirm the 1Password ref resolves without printing the secret:
      `op read --account facetdigital.1password.com "op://Employee/OpenRouter/API Key" | wc -c`
      **Re-confirmed 2026-07-30**: 74 bytes, matching the recorded 73-character
      `sk-or-v1` value plus newline.
- [x] Launch Claude Code by hand against OpenRouter with `openai/gpt-5.6-sol`, env
      set inline, `ENABLE_TOOL_SEARCH` left unset
- [x] **Check 1:** the session starts and completes one trivial turn
- [x] **Check 2:** MCP tools are present, and at least one real MCP tool call
      succeeds end to end. This is the mission requirement (D5).
- [x] **Check 3:** a multi-step agentic loop works: read a file, edit it, run a
      command, in one turn
- [x] **Check 4:** record the observed Tool Call Error Rate impression, and check
      OpenRouter's published metric for the model on its Performance tab
- [x] **Check 5:** confirm whether `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`
      populates `/model` with OpenRouter's catalog. If it works, fewer thin
      wrappers are worth writing.
- [x] **Check 6:** resolve Gate 0's deferred Q2 and Q3. Record OpenRouter's input
      rate for `openai/gpt-5.6-sol`, and confirm on turn two whether the ~105.5k
      schema block is a cache hit or is re-sent in full. Cached, the schema cost
      is negligible; uncached, it is the dominant line item and OpenRouter needs
      the same trimming Ollama does. Write the answers back into
      `docs/assessments/mcp-schema-budget.md`.
- [x] Verify green: all six checks answered, and Gate 0 no longer reads PARTIAL

**If Check 2 fails**, stop and report. Per D5, MCP tool calling is the mission.
Do not silently narrow the plan to a non-MCP subset; that is Scott's call to make,
not the runner's.

**Satisfies:** D4, D5, D7, D11.

**File(s):** `docs/assessments/route-gates.md`

**Test:**
```bash
op read --account facetdigital.1password.com "op://Employee/OpenRouter/API Key" >/dev/null \
  && echo "PASS: op ref resolves" || echo "FAIL: op ref"
# Same substring trap as Gate A. Expect 0 once both gates are resolved.
grep -c "UNANSWERED" docs/assessments/route-gates.md
```

**Commit message:** `Record Gate B: MCP tool calling through OpenRouter`

---

### Step 4: Build the workhorse with a dry-run mode

The dry-run mode comes first deliberately: it is what makes every later step
testable without launching a session, hitting a server, or spending tokens.

- [x] Write the failing test first: create `bin/claude-route-selftest`, which
      asserts that `CLAUDE_ROUTE_DRYRUN=1 claude-run glm` prints a resolved plan
      containing the expected base URL, model, and permission mode. It fails
      because `bin/claude-run` does not exist yet.
- [x] Implement `bin/claude-run` with:
      - a PROVIDER table (`ollama` -> `http://localhost:11434` per D2; `openrouter`
        -> `https://openrouter.ai/api`, no version suffix)
      - a MODEL table mapping alias to (provider, model id, context tokens)
      - `glm` -> ollama, `glm-4.7-flash`, context from Gate A
      - `gpt` -> openrouter, `openai/gpt-5.6-sol`, 1050000
      - the telemetry and privacy block, applied unconditionally (D10)
      - `CLAUDE_ROUTE_PERMISSION_MODE` const defaulting to
        `--dangerously-skip-permissions` (D1)
      - `CLAUDE_ROUTE_DRYRUN` support: print the resolved plan, exit 0, launch nothing
      - `ENABLE_TOOL_SEARCH` deliberately left unset, with a comment citing D5
      - `CLAUDE_CODE_MAX_CONTEXT_TOKENS` set from the model table, because Claude
        Code otherwise assumes a Claude-sized window for unrecognized model names
      - the audit tier left unmapped, with a comment citing D12
      - `${VAR:-default}` overrides for provider, model, context, and host
      - **no `exec`** anywhere, with a comment explaining that D6 depends on it
- [x] Implement usage/error handling: unknown alias exits non-zero with the list of
      known aliases; missing `op` exits with install guidance
- [x] Verify green: run `bin/claude-route-selftest`

**Satisfies:** D1, D2, D5, D6, D9, D10, D12.

**File(s):** `bin/claude-run`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
CLAUDE_ROUTE_DRYRUN=1 bin/claude-run glm
CLAUDE_ROUTE_DRYRUN=1 bin/claude-run gpt
bin/claude-run bogus-alias; test $? -ne 0 && echo "PASS: rejects unknown alias"
```

**Commit message:** `Add claude-run: the route launcher workhorse with dry-run support`

---

### Step 5: Add the Ollama provider path and its preflight

- [x] Write the failing test first: extend `claude-route-selftest` to assert that
      with the server down, `claude-run glm` exits non-zero with a message naming
      the unreachable host and suggesting `ollama serve`. Fails because no
      preflight exists.
- [x] Implement the Ollama preflight in `claude-run`: `GET /api/version` with a
      2-second timeout, then `GET /api/tags` to confirm the model is installed
- [x] Implement the loaded-context check: `GET /api/ps` reports the actual
      `context_length` of a loaded model; warn if it is below the table value
- [x] Implement `bin/claude-ollama` as a thin wrapper selecting the provider with
      its default model
- [x] Implement `bin/claude-glm` as a thin wrapper for `claude-run glm`
- [x] Verify green: selftest passes with the server both up and down

**Satisfies:** D2, D4, D9.

**File(s):** `bin/claude-run`, `bin/claude-ollama`, `bin/claude-glm`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
CLAUDE_ROUTE_DRYRUN=1 bin/claude-glm
# with ollama stopped, expect a clear non-zero failure:
bin/claude-glm --version; echo "exit=$?"
```

**Commit message:** `Add the Ollama provider path with liveness and model preflight`

---

### Step 6: Add the OpenRouter provider path with 1Password secret resolution

- [x] Write the failing test first: extend `claude-route-selftest` to assert the
      dry-run output for `gpt` shows the OpenRouter base URL, an empty
      `ANTHROPIC_API_KEY`, and a **redacted** auth token (never the real value).
      Fails because the OpenRouter path does not exist.
- [x] Implement secret resolution per D11 and the global convention:
      ```bash
      readonly OP_ACCOUNT="facetdigital.1password.com"
      readonly OP_REF="op://Employee/OpenRouter/API Key"
      ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-$(op read --account "$OP_ACCOUNT" "$OP_REF")}"
      ```
- [x] Implement `command -v op` guard with install and setup guidance on failure
- [x] Implement `ANTHROPIC_API_KEY=""` explicitly, empty string not unset, because
      OpenRouter documents that leaving it unset makes Claude Code fall back to
      authenticating against Anthropic directly
- [x] Implement redaction so the token never appears in dry-run output or logs
- [x] Implement `bin/claude-openrouter` and `bin/claude-gpt` thin wrappers
- [x] Verify green: selftest passes, and dry-run output contains no `sk-or-` string

**Satisfies:** D4, D9, D11.

**File(s):** `bin/claude-run`, `bin/claude-openrouter`, `bin/claude-gpt`, `bin/claude-route-selftest`

**Test:**
```bash
bin/claude-route-selftest
CLAUDE_ROUTE_DRYRUN=1 bin/claude-gpt | grep -q 'sk-or-' && echo "FAIL: secret leaked" || echo "PASS: redacted"
CLAUDE_ROUTE_DRYRUN=1 bin/claude-gpt | grep -q 'openrouter.ai/api' && echo "PASS: base url"
```

**Commit message:** `Add the OpenRouter provider path with 1Password secret resolution`

---

### Step 7: Teach what-claude to report the route

- [ ] Write the failing test first: start a dry-run-free launcher in the background
      against Ollama, run `what-claude`, and assert a ROUTE column showing provider
      and model. Fails because the column does not exist.
- [ ] Implement the ancestry walk: for each claude PID, walk `ps -o ppid=` up to
      three levels and match ancestors against `claude-run` and the thin wrappers,
      extracting provider and model from the resolved command line
- [ ] Implement the fallback: a session with no launcher ancestor reports
      `anthropic (default)`, labelled as inferred rather than observed
- [ ] Preserve the existing `claude-code-router` detection
- [ ] Handle the width of the new column so the table still aligns
- [ ] Verify green: the assertion passes with one routed and one plain session running

**Satisfies:** D6.

**File(s):** `bin/what-claude`

**Test:**
```bash
bin/what-claude
# expect a ROUTE column; with a routed session running it should not say "anthropic"
```

**Commit message:** `what-claude: report each session's backend route`

---

### Step 8: Retire the parked Ollama profile from settings.json

Deliberately last among the code steps. Per D3, the parked block is a working
fallback and does not come out until its replacement is proven.

- [ ] Test-first: n/a. This step removes configuration; the proof that it is safe
      is that Steps 5 and 7 pass and `claude-glm` has been used for real work.
- [ ] Precondition check: confirm `claude-glm` has actually been used for a real
      session, not just a dry run
- [ ] Remove `x-env`, `x-model`, and the Ollama-switching half of `x-instructions`
      from `.claude/settings.json`
- [ ] **Answer the `DECIDE-ME` marker explicitly** rather than deleting it silently.
      Per D12, the decision is: routed profiles leave the audit tier UNMAPPED on
      purpose, so Servanda gates halt loudly rather than running a weak adversarial
      audit. Record that decision as a comment in `bin/claude-run` where the tier
      vars are set, so it survives the settings.json deletion.
- [ ] Update `.claude/COMMANDS.md` where it documents model pins as tier aliases,
      noting how routed profiles interact with the audit tier
- [ ] Verify green: `jq . .claude/settings.json` parses, no `x-env` key remains,
      and `grep` finds the audit-tier rationale in `bin/claude-run`

**Satisfies:** D3, D12. Answers the marker planted by `servanda-review-fixes.md` step 2.

**File(s):** `.claude/settings.json`, `bin/claude-run`, `.claude/COMMANDS.md`

**Test:**
```bash
jq -e 'has("x-env") | not' .claude/settings.json && echo "PASS: x-env gone"
jq -e '.model == "claude-fable-5[1m]"' .claude/settings.json && echo "PASS: pin intact"
grep -q -i "audit tier" bin/claude-run && echo "PASS: rationale preserved"
```

**Commit message:** `Retire the parked Ollama profile now that claude-ollama replaces it`

---

### Step 9: Document the launcher family

- [ ] Test-first: n/a, documentation only.
- [ ] Add a section to `README.md` covering the launcher family, the one-time
      setup (1Password item, `op` CLI integration, OpenRouter credit limit), and
      the fact that plain `claude` is deliberately untouched
- [ ] Document the model table and how to add a model, since that is the routine
      maintenance task as slugs churn
- [ ] Note the `no exec` constraint prominently, since violating it silently breaks
      `what-claude` route detection
- [ ] Update `.claude/CLAUDE.md` if the launchers change anything about how a
      session should behave
- [ ] Verify green: a reader can set this up from scratch on a new machine using
      only the README

**Satisfies:** D8. Establishes the pattern the future aider, codex, opencode, and
pi launchers will follow.

**File(s):** `README.md`, `.claude/CLAUDE.md`

**Test:**
```bash
grep -q "claude-run" README.md && echo "PASS: documented"
```

**Commit message:** `Document the Claude Code route launcher family`

---

### Step 10: Queue the follow-on roadmap items

- [ ] Test-first: n/a, roadmap only.
- [ ] Add: remaining OpenRouter models (`kimi`, `deepseek`, `qwen`, and a decision
      on the `glm` alias collision, since GLM exists on both backends and the alias
      currently resolves to Ollama). **Verify ZDR availability for each first.**
      Zero Data Retention is enabled on the account, which filters the reachable
      model set; a model in OpenRouter's public catalog is not necessarily in this
      account's. Gate B Check 5 also showed this makes wrappers-per-model
      unnecessary, since gateway discovery reaches the whole filtered catalog
      in-session, so this item is convenience rather than access.
- [ ] Add: `ollama-tools` scope reduction, deleting `claude-install` and demoting
      its README's harness support to a mention
- [ ] Add: launchers for aider, codex, opencode, and pi following this pattern,
      with `aider-run` migrating out of `ollama-tools`
- [ ] Add: a local model evaluation pass, noting that `gemma4` has an open
      tool-parser issue and `qwen3-coder` has the worst Claude-Code-specific bug
      reports, so `glm-4.7-flash`, `qwen3.5-27b`, and a possible `qwen3.6:27b` pull
      are the live candidates
- [ ] Add: a periodic model-slug refresh, since OpenRouter's catalog churns and
      several 2025-era slugs already carry expiration dates
- [ ] Add: bake `num_ctx` into `Modelfile.glm-4.7-flash` properly, fixing both the
      `num_ctz` typo and the `FROM` line (raw blob path to `glm-4.7-flash:latest`,
      since blob builds fail in `llama-quantize` on Ollama 0.30.7). Today the 198K
      window comes from `OLLAMA_CONTEXT_LENGTH` in the server's environment, which
      is silent when absent. A baked-in parameter survives any server start
      method. Demoted from a Gate A blocker on 2026-07-30; see
      `docs/assessments/route-gates.md`.
- [ ] Verify green: each item has a Thread tag and a Status

**Satisfies:** D4, D8.

**File(s):** `docs/plans/development-roadmap.md`

**Test:**
```bash
grep -c "Thread:" docs/plans/development-roadmap.md
```

**Commit message:** `Roadmap: queue the route launcher follow-ons`

---

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `docs/assessments/mcp-schema-budget.md` | 1 |
| `docs/assessments/route-gates.md` | 2, 3 |
| `bin/claude-run` | 4, 5, 6, 8 |
| `bin/claude-route-selftest` | 4, 5, 6 |
| `bin/claude-ollama` | 5 |
| `bin/claude-glm` | 5 |
| `bin/claude-openrouter` | 6 |
| `bin/claude-gpt` | 6 |
| `bin/what-claude` | 7 |
| `.claude/settings.json` | 8 |
| `.claude/COMMANDS.md` | 8 |
| `README.md` | 9 |
| `.claude/CLAUDE.md` | 9 |
| `docs/plans/development-roadmap.md` | 10 |

Outside this repo, untracked by these steps: the manual `num_ctx` fix in
`~/src/scottwb/ollama-tools/Modelfile.glm-4.7-flash` (Step 2 prerequisite, Scott
does this by hand and reviews by diffing against `main`).

---

## Research Findings (2026-07-30)

Three research passes verified this against primary sources, because the
originating document had unreliable citations and every model slug in it was
stale. What the plan depends on:

**Confirmed and load-bearing:**

- OpenRouter's base URL is `https://openrouter.ai/api` with no version suffix;
  the client appends `/v1/messages`. Adding `/v1` yourself produces `/v1/v1/`.
- `ANTHROPIC_API_KEY=""` must be an empty string, not unset. OpenRouter documents
  that unset causes fallback to Anthropic direct.
- Ollama's base URL is `http://localhost:11434`, also with no suffix. It accepts
  but never validates any credential.
- `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS,FABLE}_MODEL` all exist. A fable-tier
  variable exists, which is why D12 is a real choice rather than a limitation.
- `CLAUDE_CODE_SUBAGENT_MODEL` exists and overrides both per-invocation model
  parameters and subagent frontmatter. Deliberately NOT set by these launchers,
  because it would steamroll Servanda's explicit tier pins.
- `CLAUDE_CODE_MAX_CONTEXT_TOKENS` is the documented override for models whose
  names Claude Code does not recognize. Without it, routed sessions can overrun
  the real window.
- Subagents inherit the main conversation's model directly on non-Anthropic
  providers, rather than capping at Opus as they do on the Anthropic API.
- Subagents, hooks, commands, skills, and CLAUDE.md all work on every provider.

**Confirmed and mission-shaping:**

- `ENABLE_TOOL_SEARCH=true` against a proxy that does not forward `tool_reference`
  causes **hard request failure**, not degradation.
- Ollama does not implement `tool_reference` at all; its content-block handler
  silently drops unknown blocks. Claude Code auto-disables tool search for any
  non-first-party base URL, so the safe configuration is the default one.
- OpenRouter models `tool_reference` in its schema but gates deferred tool loading
  to Opus 4.8+ and explicitly excludes Sonnet 5. There is no evidence any
  non-Anthropic model supports it, and a documented precedent shows OpenRouter's
  router returning 400 for the same class of Anthropic-proprietary beta.
- Both backends therefore converge on the same answer: leave `ENABLE_TOOL_SEARCH`
  unset, load tools upfront, size the context window accordingly. This is why D5
  reframes the requirement from tool search to tool calling.

**Verified locally:**

- Process ancestry survives a two-level wrapper chain and exposes each script's
  full path, which is what makes D6 workable. `ps eww` returns nothing on macOS
  and `.claude/session-env/` is empty, so observing a running session's
  environment is not an option.
- `op://Employee/OpenRouter/API Key` resolves to a 73-character `sk-or-v1` value
  under account `facetdigital.1password.com`. Field label confirmed exactly.

**Open, and deliberately so:**

- Whether Opus 5 and Fable 5 clear OpenRouter's "older than Opus 4.8" gate. The
  Sonnet 5 carve-out proves the rule is not purely chronological. Low impact,
  since Anthropic models go direct rather than through OpenRouter.
- Whether OpenRouter's richer Guardrails budgets apply to personal accounts. The
  simple per-key credit limit does, which is enough for D7.

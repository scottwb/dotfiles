# Assessment: Upfront MCP Tool Schema Budget

**Gate:** 0 (of the three gates in [claude-route-launchers.md](../plans/claude-route-launchers.md))
**Cost:** Free. Local only, no routing, no API key, no server.
**Measured:** 2026-07-30, on Fable 5 (`claude-fable-5`, 1M window)
**Status:** ✅ **RESOLVED.** All three threshold questions answered. Q1 on
2026-07-30 from these measurements; Q2 and Q3 the same day via Gate B Check 6,
which supplied the OpenRouter caching behavior that could not be observed here.

---

## Why this exists

Every context-budget decision in the route-launcher plan depends on one number:
how many tokens the MCP tool schemas consume before any work starts.

Decision **D5** commits to leaving `ENABLE_TOOL_SEARCH` unset, so tools load
upfront rather than on demand. That is not a preference. Both target backends
force it:

- Ollama does not implement `tool_reference` at all, and Claude Code
  auto-disables tool search for any non-first-party base URL.
- OpenRouter gates deferred tool loading to Opus 4.8+, with no evidence any
  non-Anthropic model supports it. Forcing it on produces a hard request
  failure, not graceful degradation.

Loading upfront means the schema cost is paid on turn one of every routed
session, out of a window that may be 198K rather than 1M. That number was a
guess. This gate replaces it with a measurement.

---

## The servers measured

Nine self-configured servers, from `~/.claude.json`, plus the claude.ai
connectors layered on top when `ENABLE_CLAUDEAI_MCP_SERVERS` is left at default.

| Server | Approx. tools |
|---|---:|
| `trello` | 51 |
| `google-docs-mcp` | 40 |
| `hubspot` | 18 |
| `open-meteo` | 18 |
| `harvest` | 13 |
| `apple-mail` | 8 |
| `slack` | 8 |
| `granola` | 6 |
| `mcp-ical` | 4 |
| **Total** | **~166** |

`trello` plus `google-docs-mcp` is 91 of ~166, roughly 55%, and 26.2k of the
68.1k self-configured total. They are where trimming pays.

---

## The non-MCP floor

Not everything in the startup window is MCP, and the rest cannot be trimmed by
MCP configuration. From the Measurement A session's full `/context`:

| Category | Tokens |
|---|---:|
| System prompt | 4.2k |
| System tools | 39.9k |
| Memory files (`~/.claude/CLAUDE.md`) | 3.6k |
| Skills | 2.2k |
| **Fixed floor** | **49.9k** |

Confirmed by arithmetic: that session reported 119.5k total with 69.6k MCP, and
119.5 minus 69.6 is 49.9.

This floor matters more than it looks. **System tools alone are 39.9k**, nearly
as much as the entire trimmed MCP set. Even with every MCP server disabled, a
routed session starts at 49.9k, which is a quarter of `glm-4.7-flash`'s window
before a single MCP tool loads.

---

## Measurements

Each run is a fresh session; `/context` reports on the session it runs in.

| # | Configuration | MCP tools | Total startup | Free of 1M |
|---|---|---:|---:|---:|
| A | All servers, `ENABLE_TOOL_SEARCH=false` | 105.5k | 155.4k | 88% |
| B | Self-configured only (`ENABLE_CLAUDEAI_MCP_SERVERS=false`) | 68.1k | 118.0k | 88% |
| C | Self-configured minus `trello` and `google-docs-mcp` | 41.9k | 91.8k | 91% |

**Derived:**

| Quantity | Value |
|---|---:|
| claude.ai connector cost (A minus B) | 37.4k |
| `trello` + `google-docs-mcp` cost (B minus C) | 26.2k |
| Non-MCP fixed floor | 49.9k |

### Caveat on Measurement A: the connector cost is variable

A second A-configuration run recorded **69.6k**, not 105.5k. Its `/context`
breakdown showed the claude.ai connectors present only as `authenticate` and
`complete_authentication` stubs totaling roughly 2.1k, with Docusign absent
entirely. In an authenticated session those same connectors expand fully, with
Docusign alone contributing about 30 tools.

So the claude.ai connector cost is not a constant. It swings between roughly
**2k unauthenticated and 37.4k authenticated**, on identical configuration.

Both numbers are kept. 105.5k is the planning number, because a launcher has to
survive the worst case, not the convenient one. The practical consequence is
small either way: the routed profile should set `ENABLE_CLAUDEAI_MCP_SERVERS=false`
regardless, which collapses the variance to zero and is already what the parked
`x-env` block in `.claude/settings.json` does.

---

## Threshold questions

### Q1. Does the full set fit comfortably inside `glm-4.7-flash`'s window with room left for real work?

- **Status:** ANSWERED
- **Answer: No.**

Against a 198K window, counting the 49.9k non-MCP floor:

| Config | Total startup | % of 198K | Free for work |
|---|---:|---:|---:|
| A (full) | 155.4k | 78% | 42.6k |
| B (no connectors) | 118.0k | 60% | 80.0k |
| C (trimmed) | 91.8k | 46% | 106.2k |

Configuration A leaves 42.6k. That is not a working budget for agentic use: a
few file reads, a `git diff`, and two or three tool results consume it, and the
session starts compacting almost immediately. Configuration B at 80k is
survivable but tight. Only C leaves room that resembles headroom.

Note this assumes the 198K window is real, which depends on the `num_ctx` typo
fix in `Modelfile.glm-4.7-flash`. **Gate A measures the actual value.** If the
real window is smaller, every row above gets proportionally worse and the answer
stays no.

- **Consequence, now live:** routed Ollama sessions need a trimmed MCP set.
  `bin/claude-run` needs a per-provider tool-allowlist mechanism that the plan
  does not currently specify. This is new scope for Steps 4 and 5.

### Q2. Does the full set fit inside a 1M OpenRouter model without meaningful cost?

- **Status:** ANSWERED, 2026-07-30, by Gate B Check 6
- **Answer: Yes.**

Window fit was never in question: 155.4k of 1M is 15.5%, leaving 88% free.

Cost was the open half, and it turned on one fact not observable without a key:
does OpenRouter prompt-cache the schema block? Measured on `openai/gpt-5.6-sol`:

```json
"input_tokens": 34531,
"cache_read_input_tokens": 29184,
"cache_creation_input_tokens": 0
```

**84.5% served from cache.** OpenAI models cache automatically, with no explicit
`cache_control` markers, so the launcher does not need to request it. The schema
block is paid once rather than re-sent every turn, which is the outcome that
makes D5 viable as designed.

Observed cost was $0.194907 actual for a two-turn probe, against Claude Code's
$0.193987 estimate. Not free, but the schema block is not what drives it.

### Q3. Is trimming needed for OpenRouter at all?

- **Status:** ANSWERED, 2026-07-30, by Gate B Check 6
- **Answer: No.** Not for window fit, and not for cost.

The original expectation of a confident no holds, for the reason expected on
window fit and for a better reason than expected on cost.

**Design consequence, and it simplifies rather than complicates.** The MCP
allowlist that Q1 forces into Steps 4 and 5 stays **Ollama-specific** rather than
becoming a shared feature of the workhorse. The backends genuinely differ:

| | Ollama | OpenRouter |
|---|---|---|
| Schema caching | none (`0` / `0`) | 84.5% cache read |
| Window | 202752 | 1M |
| Startup at config A | ~8 min | ~5 sec |
| Trimming needed | **yes** | **no** |

---

## Verdict

✅ **Gate 0 passes, with one design change.** Fully resolved 2026-07-30.

What it established:

1. **Ollama routing requires MCP trimming.** Q1 is a clear no. This is the
   substantive result, and it adds scope the plan did not have.
2. **The non-MCP floor is 49.9k and is not trimmable**, 39.9k of it system tools.
   On a 198K window that is a quarter of the budget before any MCP server loads.
   Any future decision about local models should treat 49.9k as the entry fee.
3. **`ENABLE_CLAUDEAI_MCP_SERVERS=false` is worth 37.4k** and removes a source of
   run-to-run variance. Routed profiles should set it unconditionally.
4. **Configuration C is the shape a routed Ollama profile should take**: nine
   self-configured servers minus `trello` and `google-docs-mcp`, 41.9k, leaving
   106.2k free.

What carries forward:

- Q1's answer changes Step 4. `bin/claude-run` needs an MCP allowlist. Per Q3,
  build it as an **Ollama-specific** mechanism rather than a shared one:
  OpenRouter needs no trimming on either window fit or cost.
- Q1's arithmetic assumed a 198K window. **Gate A confirmed it**: `/api/ps`
  measures the effective window at 202752. No revision needed.
- Gate A added a constraint this gate could not see. Cold start on Ollama is
  dominated by a **fixed ~2 minute cost**, not by prompt size, so trimming helps
  window fit but will not make routed Ollama sessions feel responsive. Against
  OpenRouter's 4.9 second time-to-first-token, that is the sharpest practical
  difference between the backends.

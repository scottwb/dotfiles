# Model and harness research for a Greenthumb-style agent (2026-09-12)

Research done by the Greenthumb session on 2026-09-12 and dropped into this repo's inbox; ingested here on 2026-10-20 as input to the roadmap's "Local model evaluation pass". A research subagent used live web sources plus this repo's route docs ([route-gates.md](route-gates.md), [mcp-schema-budget.md](mcp-schema-budget.md), `bin/claude-run`).

**Treat it as leads, not measurements.** Benchmark rankings for September 2026 models conflicted across sources, and items marked UNVERIFIED were not confirmed. Nothing here was tested in a Patchbay session unless it says so. After reading it, Scott chose to try `claude-run --provider openrouter --model z-ai/glm-5.3-flash`.

## The workload it assumed

A large system prompt (Claude Code's ~49.9k tokens before MCP, plus ~11k of repo `CLAUDE.md`), heavy Markdown editing with wiki-link integrity, image vision (photos, trail-cam stills, labels), ffmpeg and ImageMagick, MCP servers (open-meteo, mcp-ical, granola), SendMessage to other sessions, HTML-to-PDF output, and careful multi-step reasoning.

## Picks

| Question | Pick | Runner-up |
|---|---|---|
| Local Ollama, M3 Max 128 GB | `qwen3.8:27b-q8_0` (30 GB; vision, tools, 256K window) | `qwen3.8-flash-next:125b-mlx` (105 GB, over the default GPU memory share) |
| OpenRouter, ZDR required | `openai/gpt-5.6-sol` ($2/$10 per Mtok; Azure is the only ZDR provider; passed this repo's gate tests with 84.5% cache hits) | `z-ai/glm-5.3-flash` ($0.15/$0.50, about ten ZDR providers, MIT weights, untested in Claude Code) |
| OpenRouter, ZDR not required | the same GPT-5.6 Sol, since ZDR costs about nothing | `meta/muse-spark-1.3` ($1.25/$4.25, no ZDR; benchmark score UNVERIFIED) |
| EC2 plus Ollama | g6e.xlarge (L40S 48 GB, ~$1.86/hr) with `qwen3.8:27b-q8_0` | g7e with 2x RTX PRO 6000 and `qwen3.8-flash-next` 125b nvfp4 |

Prices for `z-ai/glm-5.3-flash` differ from this repo's own 2026-09-10 catalog reading ($0.07/$0.25); the roadmap's figure came from OpenRouter's `/api/v1/models` directly, so prefer it, and re-read the catalog before deciding.

## Harness verdict

**Keep Claude Code for now.** It has slash commands, SendMessage, MCP, subagents, and the tested launchers.

- **Pi:** under 1k tokens of system prompt, reads `CLAUDE.md`, handles images. No MCP, no subagents, no cross-session messaging.
- **opencode:** MCP and subagents. One benchmark (infralovers, 2026-07-14) had both opencode and Pi needing hand-holding with a local Qwen, while Claude Code finished alone.

Revisit Pi for local-only sessions if a local model ever becomes the daily driver.

## Pitfalls to test before trusting a pick

1. **Ollama context window.** It comes from `OLLAMA_CONTEXT_LENGTH` or `num_ctx`, and a misspelled key is silently dropped. Check the effective window with `/api/ps`, not `ollama show`.
2. **Ollama's Anthropic endpoint** (since v0.14.0) has no `tool_choice`, no prompt caching, no `count_tokens`, and takes base64 images only. Local was 0.30.7 against a current 0.34.0 at the time.
3. **Ollama issue #18346:** Qwen emits Claude Code tool calls as plain text when the tool schemas are complex. Test before trusting either Qwen pick.
4. **Images may be dropped.** Ollama issue #15727 covers cloud models; images inside tool results on the OpenAI and Gemini paths are UNVERIFIED. Test with a detail that is only in a photo.
5. **OpenRouter's own docs warn** that Claude Code "may not work correctly with other providers", and ZDR does not cover add-ons such as web search.

The research also found that `ollama list` with no server running tries to start one and raised an Ollama.app popup; that finding is recorded in the roadmap's local model evaluation item.

## Sources

openrouter.ai/docs/guides/features/zdr; openrouter.ai/api/v1/endpoints/zdr; openrouter.ai/docs/cookbook/coding-agents/claude-code-integration; docs.ollama.com/api/anthropic-compatibility; github.com/ollama/ollama/issues/18346; github.com/ollama/ollama/issues/15727; ollama.com/library/qwen3.8/tags; huggingface.co/zai-org/GLM-5.3-Flash; devzero.io/instances/aws/g6e.xlarge; github.com/badlogic/pi-mono/tree/main/packages/coding-agent; infralovers.com/blog/2026-07-14-local-model-ai-coding-tools-benchmark/

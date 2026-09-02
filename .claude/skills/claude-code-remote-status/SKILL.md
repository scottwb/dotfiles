---
name: claude-code-remote-status
description: >
  Quickly diagnose whether a Claude Code failure is Anthropic-side or local. Run this
  when the user asks "is remote control down?", "is Anthropic down?", "is rx/rc down?",
  sees "Remote Control connection failed: unable to reach bridge server",
  "Session creation failed", "/rc failed", an image/file upload failing, a prompt
  erroring with 5xx/529/overloaded, or MCP/cloud features silently not working.
  Checks the status page, API reachability, the RC bridge websocket, and reproduces
  a headless Remote Control session-create to read the real HTTP status from debug logs.
allowed-tools: Bash, Read
---

# Claude Code Remote Status

One command answers "is it me or is it Anthropic?" for Claude Code's cloud pieces
(Remote Control, the API, the status page). It exists because the CLI's error text
("unable to reach bridge server") is misleading: the bridge websocket is usually fine
and the real failure is an HTTP 503 from the Remote Control session-create endpoint,
which only shows up in `--debug` logs.

## Run it

```bash
~/.claude/skills/claude-code-remote-status/check.sh            # full check (~25s)
~/.claude/skills/claude-code-remote-status/check.sh --no-probe # skip the RC probe (~3s)
```

Exit code 0 = all clear, 1 = something degraded (details printed), 2 = usage/setup error.

## What it checks, in order

1. **Status page** (`status.claude.com/api/v2/summary.json`; `status.anthropic.com` redirects
   there): overall status, degraded components, open incidents. Note: 503s on a specific
   endpoint often precede a posted incident, so "All Systems Operational" does not clear
   Anthropic.
2. **API reachability**: `api.anthropic.com` (HTTP 404 on `/` is the healthy answer).
3. **RC bridge websocket**: raw handshake to `wss://bridge.claudeusercontent.com`. Healthy =
   `HTTP/1.1 101 Switching Protocols` (Cloudflare fronted).
4. **RC session-create probe**: launches `claude --debug --remote-control` headless from a
   trusted project dir for ~20s, then greps the new debug log for `[code-session]`,
   `[remote-bridge]`, `[bridge:repl]`. Healthy = `[remote-bridge] v2 transport connected`
   (CLI 2.1.258+) or `Successfully connected to bridge server` (older CLIs).
   Broken-upstream = `Session create request failed: Request failed with status code 503`
   (retried 3x, then `Session creation failed`).

## How to interpret

| Result | Meaning | What to do |
|---|---|---|
| 1-3 green, probe shows `503` | Anthropic-side RC outage | Nothing local. Wait; existing `--remote-control` sessions auto-retry, or `/rc` in them later. |
| API unreachable / DNS fails | Local network, DNS, VPN, or proxy | Check network, `env \| grep -i proxy`, VPN. |
| Bridge handshake fails but API fine | Firewall/proxy blocking websockets, or bridge outage | Try another network; check status page again. |
| Probe logs nothing | Trust prompt or other dialog blocked the headless run | Run `claude --debug --remote-control` by hand, then `grep -E '\[code-session\]\|\[remote-bridge\]' ~/.claude/debug/latest`. |

## Manual fallback (if the script cannot run)

```bash
curl -sL https://status.claude.com/api/v2/summary.json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["status"]["description"]);[print(i["name"],i["status"]) for i in d["incidents"]]'
claude --debug --remote-control      # in a trusted dir, then in another shell:
grep -E '\[code-session\]|\[remote-bridge\]|\[bridge:repl\]' "$(readlink ~/.claude/debug/latest)"
```

## Notes

- Debug logs live in `~/.claude/debug/<session-id>.txt`; `latest` symlinks the newest
  session, which may not be yours if other sessions started since. The script finds the
  probe's own log by mtime instead.
- The RC bridge URL is baked into the CLI bundle; if it ever changes, find it with
  `strings "$(readlink -f "$(command -v claude)")" | grep -oE 'wss://[a-z0-9._/-]+'`.
- Unrelated noise you will see in debug logs: MCP token-refresh failures (`granola`,
  `slack` timeouts). Those are per-server auth issues, not the RC bridge.

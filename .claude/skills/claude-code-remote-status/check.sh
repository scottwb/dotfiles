#!/usr/bin/env bash
# Quick health check for Claude Code's cloud dependencies:
#   1. status.claude.com incident feed
#   2. api.anthropic.com reachability
#   3. Remote Control bridge websocket handshake
#   4. Headless Remote Control session-create probe (the thing that actually
#      fails with "unable to reach bridge server"), read from --debug logs
#
# Usage: check.sh [--no-probe]   (--no-probe skips step 4, ~5s faster)
#
# Exit codes: 0 all good, 1 something is degraded (details printed), 2 usage/setup error
set -u

readonly BRIDGE_HOST="bridge.claudeusercontent.com"
readonly STATUS_URL="https://status.claude.com/api/v2/summary.json"
readonly API_URL="https://api.anthropic.com/"
readonly PROBE_SECONDS=20

GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; DIM=$'\033[2m'; NC=$'\033[0m'
ok()   { printf "%s✅ %s%s\n" "$GREEN" "$*" "$NC"; }
warn() { printf "%s⚠️  %s%s\n" "$YELLOW" "$*" "$NC"; }
bad()  { printf "%s❌ %s%s\n" "$RED" "$*" "$NC"; }
info() { printf "%sℹ️  %s%s\n" "$DIM" "$*" "$NC"; }

RUN_PROBE=1
[ "${1:-}" = "--no-probe" ] && RUN_PROBE=0
[ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] && { sed -n '2,11p' "$0"; exit 2; }

for c in curl python3 dig; do
  command -v "$c" >/dev/null 2>&1 || { bad "missing required tool: $c"; exit 2; }
done

problems=0

# ---------- 1. Status page ----------
echo "== 1. Status page (status.claude.com) =="
status_json=$(curl -sL -m 15 "$STATUS_URL" 2>/dev/null)
if [ -z "$status_json" ]; then
  warn "could not fetch status page (network?)"; problems=$((problems+1))
else
  python3 - "$status_json" <<'PY'
import json, sys
d = json.loads(sys.argv[1])
overall = d["status"]["description"]
degraded = [c for c in d["components"] if c["status"] != "operational"]
incidents = d.get("incidents", [])
print(f"   overall: {overall} (updated {d['page']['updated_at']})")
for c in degraded:
    print(f"   component: {c['name']} => {c['status']}")
for i in incidents:
    print(f"   INCIDENT: {i['name']} [{i['status']}] {i['updated_at']}")
    for u in i.get("incident_updates", [])[:1]:
        print("      " + u["body"][:300].replace("\n", " "))
sys.exit(1 if (degraded or incidents) else 0)
PY
  status_rc=$?
  if [ $status_rc -eq 0 ]; then ok "status page reports no incidents"
  else warn "status page shows degradation (see above)"; problems=$((problems+1)); fi
fi

# ---------- 2. API ----------
echo "== 2. API reachability (api.anthropic.com) =="
api=$(curl -s -m 15 -o /dev/null -w "%{http_code} %{time_total}" "$API_URL" 2>/dev/null)
api_code=${api%% *}; api_time=${api##* }
if [ "$api_code" = "404" ] || [ "$api_code" = "200" ]; then
  ok "api.anthropic.com reachable (HTTP $api_code in ${api_time}s)"
elif [ -z "$api_code" ] || [ "$api_code" = "000" ]; then
  bad "api.anthropic.com unreachable (DNS/TLS/network)"; problems=$((problems+1))
else
  warn "api.anthropic.com answered HTTP $api_code"; problems=$((problems+1))
fi

# ---------- 3. Bridge websocket ----------
echo "== 3. Remote Control bridge websocket ($BRIDGE_HOST) =="
ip=$(dig +short "$BRIDGE_HOST" | head -1)
if [ -z "$ip" ]; then
  bad "DNS lookup failed for $BRIDGE_HOST"; problems=$((problems+1))
else
  ws=$(python3 - "$BRIDGE_HOST" <<'PY' 2>&1
import socket, ssl, base64, os, sys
h = sys.argv[1]
try:
    ctx = ssl.create_default_context()
    s = ctx.wrap_socket(socket.create_connection((h, 443), timeout=10), server_hostname=h)
    key = base64.b64encode(os.urandom(16)).decode()
    s.send((f"GET / HTTP/1.1\r\nHost: {h}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    print(s.recv(200).decode(errors="replace").splitlines()[0])
except Exception as e:
    print(f"ERR {e}")
PY
)
  case "$ws" in
    *" 101 "*) ok "bridge accepts websocket handshake ($ip): $ws" ;;
    *) bad "bridge websocket handshake failed ($ip): $ws"; problems=$((problems+1)) ;;
  esac
fi

# ---------- 4. Headless RC session-create probe ----------
if [ $RUN_PROBE -eq 1 ]; then
  echo "== 4. Remote Control session-create probe (headless, ~${PROBE_SECONDS}s) =="
  command -v claude >/dev/null 2>&1 || { warn "claude CLI not on PATH; skipping probe"; exit $(( problems > 0 ? 1 : 0 )); }
  command -v script >/dev/null 2>&1 || { warn "'script' not available; skipping probe"; exit $(( problems > 0 ? 1 : 0 )); }
  command -v timeout >/dev/null 2>&1 || { warn "'timeout' not available (brew install coreutils); skipping probe"; exit $(( problems > 0 ? 1 : 0 )); }

  # Pick a directory the CLI already trusts so the trust dialog doesn't block us.
  trusted_dir=$(python3 - <<'PY' 2>/dev/null
import json, os
cfg = json.load(open(os.path.expanduser("~/.claude.json")))
cwd = os.getcwd()
projects = cfg.get("projects", {})
if projects.get(cwd, {}).get("hasTrustDialogAccepted"):
    print(cwd); raise SystemExit
for p, v in projects.items():
    if v.get("hasTrustDialogAccepted") and os.path.isdir(p):
        print(p); break
PY
)
  if [ -z "$trusted_dir" ]; then
    warn "no trusted project dir found in ~/.claude.json; skipping probe"
  else
    info "probing from $trusted_dir"
    marker=$(mktemp "${TMPDIR:-/tmp}/rc-probe.XXXXXX")
    scr=$(mktemp "${TMPDIR:-/tmp}/rc-probe-screen.XXXXXX")
    ( cd "$trusted_dir" && ( (sleep 3; printf '\r'; sleep "$PROBE_SECONDS") \
        | script -q "$scr" timeout $((PROBE_SECONDS+8)) claude --debug --remote-control >/dev/null 2>&1 ) ) || true
    dbg=$(find ~/.claude/debug -name '*.txt' -newer "$marker" 2>/dev/null | head -1)
    rm -f "$marker" "$scr"
    if [ -z "$dbg" ]; then
      warn "probe produced no debug log; run 'claude --debug --remote-control' by hand and grep for '[code-session]'"
    else
      lines=$(grep -E '\[code-session\]|\[remote-bridge\]|\[bridge:repl\]|Successfully connected to bridge' "$dbg" | sed 's/^[^ ]* //' | cut -c1-200)
      if echo "$lines" | grep -qE 'Successfully connected to bridge|\[remote-bridge\] v2 transport connected'; then
        ok "Remote Control session created and bridge connected"
      elif echo "$lines" | grep -qE 'Session create request failed'; then
        code=$(echo "$lines" | grep -oE 'status code [0-9]+' | head -1)
        bad "Remote Control session creation failing on Anthropic's side (${code:-unknown status}). Nothing local to fix; retry later or /rc in existing sessions."
        problems=$((problems+1))
      elif [ -z "$lines" ]; then
        warn "probe ran but logged no bridge activity (did the trust prompt or another dialog block it?)"
      else
        warn "probe result unclear; relevant log lines:"
      fi
      echo "$lines" | sed 's/^/      /' | tail -8
      info "full debug log: $dbg"
    fi
  fi
else
  info "skipped RC session probe (--no-probe)"
fi

echo
if [ $problems -eq 0 ]; then ok "Summary: everything checks out."; exit 0
else bad "Summary: $problems problem(s) found (see above)."; exit 1; fi

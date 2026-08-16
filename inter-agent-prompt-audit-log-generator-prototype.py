#!/usr/bin/env python3
"""Build a single-file HTML audit log of the Donna -> Greenthumb interaction."""

import json, re, html, os, datetime

SRC = "/Users/scottwb/src/scottwb/dotfiles/.claude/projects/-Users-scottwb-src-scottwb-greenthumb/0a5df9e2-3dc1-4bee-9013-e38e709b4cb1.jsonl"
OUT = "/Users/scottwb/donna-greenthumb.html"

PT = datetime.timezone(datetime.timedelta(hours=-7), "PDT")

def parse_ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(PT)

# ---------------------------------------------------------------- markdown

def _inline(s):
    s = html.escape(s)
    stash = []
    def keep(m):
        stash.append(m.group(1))
        return f"\x00{len(stash)-1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{stash[int(m.group(1))]}</code>", s)
    return s

def _cells(row):
    """Split a table row on unescaped pipes, then unescape."""
    r = row.strip()
    if r.startswith("|"): r = r[1:]
    if r.endswith("|"): r = r[:-1]
    parts = re.split(r"(?<!\\)\|", r)
    return [p.strip().replace("\\|", "|") for p in parts]

def _table(head, rows):
    width = max([len(r) for r in rows] + ([len(head)] if head else [0]) or [1])
    t = ["<div class='tablewrap'><table>"]
    if head:
        t.append("<thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead>")
    t.append("<tbody>")
    for r in rows:
        r = r + [""] * (width - len(r))
        t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
    t.append("</tbody></table></div>")
    return "".join(t)

def dewiki(text):
    """Render Obsidian syntax the way the vault reads it, for preview mode only."""
    text = re.sub(r"!\[\[([^\]]+?)\]\]",
                  lambda m: "`\U0001f5bc %s`" % os.path.basename(
                      re.split(r"\\?\|", m.group(1))[0]), text)
    text = re.sub(r"\[\[[^\]]*?\\?\|([^\]|]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", lambda m: os.path.basename(m.group(1)), text)
    return text

def markdown(text):
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    para = []

    def flush():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            para.clear()

    while i < n:
        ln = lines[i]

        if ln.startswith("```"):
            flush()
            lang = ln[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append('<pre class="code"><code>%s</code></pre>' % html.escape("\n".join(buf)))
            continue

        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", ln):
            flush(); out.append("<hr>"); i += 1; continue

        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl+1} class='md-h md-h{lvl}'>{_inline(m.group(2))}</h{lvl+1}>")
            i += 1; continue

        # table (with header row + delimiter)
        if ln.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i+1]):
            flush()
            head = _cells(ln); i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i])); i += 1
            out.append(_table(head, rows)); continue

        # headerless table: a run of pipe rows with no delimiter (grep fragments)
        if ln.strip().startswith("|") and ln.strip().endswith("|"):
            flush()
            rows = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                if re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i]):
                    i += 1; continue
                rows.append(_cells(lines[i])); i += 1
            if rows:
                out.append(_table(None, rows))
            continue

        m = re.match(r"^\s*([-*+])\s+(.*)$", ln)
        if m:
            flush()
            items = []
            while i < n:
                mm = re.match(r"^\s*([-*+])\s+(.*)$", lines[i])
                if not mm: break
                body = [mm.group(2)]; i += 1
                while i < n and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) and lines[i].startswith("  "):
                    body.append(lines[i].strip()); i += 1
                items.append(" ".join(body))
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
            continue

        m = re.match(r"^\s*(\d+)\.\s+(.*)$", ln)
        if m:
            flush()
            start = m.group(1)
            items = []
            while i < n:
                mm = re.match(r"^\s*\d+\.\s+(.*)$", lines[i])
                if not mm: break
                body = [mm.group(1)]; i += 1
                while i < n and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i]) and lines[i].startswith("  "):
                    body.append(lines[i].strip()); i += 1
                items.append(" ".join(body))
            out.append(f"<ol start='{start}'>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ol>")
            continue

        m = re.match(r"^\s*>\s?(.*)$", ln)
        if m:
            flush()
            buf = []
            while i < n and re.match(r"^\s*>", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append("<blockquote>" + markdown("\n".join(buf)) + "</blockquote>")
            continue

        if not ln.strip():
            flush(); i += 1; continue

        para.append(ln); i += 1

    flush()
    return "".join(out)

# ---------------------------------------------------------------- load

records = [json.loads(l) for l in open(SRC)]

by_id = {}
for r in records:
    if r.get("type") == "user":
        c = r.get("message", {}).get("content")
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_result":
                    by_id[b["tool_use_id"]] = b

def result_text(block):
    if block is None:
        return "(no result recorded)"
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for b in c:
            if b.get("type") == "text":
                parts.append(b["text"])
            else:
                parts.append(json.dumps(b, indent=2))
        return "\n".join(parts)
    return json.dumps(c, indent=2)

# ---------------------------------------------------------------- tool prettifiers

def humanize(name, inp):
    """-> (kicker, title, detail_html)"""
    if name == "Bash":
        desc = inp.get("description") or "Shell command"
        cmd = inp.get("command", "")
        verb = "Ran a shell command"
        if re.search(r"\bgit commit\b", cmd): verb = "Wrote a git commit"
        elif re.search(r"\bgit (status|diff|log)\b", cmd): verb = "Inspected git state"
        elif cmd.strip().startswith("grep") or " grep " in cmd: verb = "Searched files"
        elif "date" in cmd.split()[0:2]: verb = "Checked the clock"
        return ("SHELL", desc, verb,
                "<pre class='code shell'><code>%s</code></pre>" % html.escape(cmd))
    if name == "Read":
        p = inp.get("file_path", "")
        base = os.path.basename(p)
        rng = ""
        if inp.get("offset"):
            rng = " · lines %s–%s" % (inp["offset"], inp["offset"] + inp.get("limit", 0) - 1)
        return ("READ", "Read %s%s" % (base, rng), "Opened a tracker file",
                "<div class='kv'><span>path</span><code>%s</code></div>" % html.escape(p))
    if name == "ToolSearch":
        q = inp.get("query", "")
        return ("TOOLS", "Loaded a deferred tool schema", "Pulled in the weather tool on demand",
                "<div class='kv'><span>query</span><code>%s</code></div>" % html.escape(q))
    if name.startswith("mcp__open-meteo"):
        return ("EXTERNAL", "Fetched the 7-day forecast for the property",
                "Called the Open-Meteo API (lat %s, lon %s)" % (inp.get("latitude"), inp.get("longitude")),
                "<div class='kv'><span>hourly</span><code>%s</code></div>"
                "<div class='kv'><span>daily</span><code>%s</code></div>"
                "<div class='kv'><span>units</span><code>%s, %s, %s · %s</code></div>" % (
                    ", ".join(inp.get("hourly", [])), ", ".join(inp.get("daily", [])),
                    inp.get("temperature_unit"), inp.get("wind_speed_unit"),
                    inp.get("precipitation_unit"), inp.get("timezone")))
    return ("TOOL", name, "Tool call",
            "<pre class='code'><code>%s</code></pre>" % html.escape(json.dumps(inp, indent=2)))

ICON = {"SHELL": "&#9656;", "READ": "&#9634;", "TOOLS": "&#9881;", "EXTERNAL": "&#9729;", "TOOL": "&#9679;"}

# ---------------------------------------------------------------- markdown preview

def looks_like_markdown(text):
    body = strip_line_numbers(text).split("\n")
    if len(body) < 2:
        return False
    pipes = sum(1 for l in body if l.strip().startswith("|"))
    heads = sum(1 for l in body if re.match(r"^#{1,6}\s", l))
    bullets = sum(1 for l in body if re.match(r"^\s*[-*+]\s", l))
    return pipes >= 2 or heads >= 1 or bullets >= 2

def is_markdown_result(name, inp, text):
    """Does this tool's output contain markdown worth offering a rendered preview of?"""
    if name == "Read":
        return inp.get("file_path", "").endswith(".md")
    if name == "Bash":
        # Needs a reader command plus a bare .md path argument, and the output
        # itself has to look like markdown -- that second check is what rejects
        # the commit, whose message merely contains the word "head".
        cmd = inp.get("command", "")
        reads_md = (re.search(r"\b(grep|sed|cat|head|tail)\b", cmd)
                    and re.search(r"(?:^|\s)[\w./-]+\.md\b", cmd))
        return bool(reads_md) and looks_like_markdown(text)
    return False

def strip_line_numbers(text):
    """Drop the `  12\\t` prefixes Read adds and the `12:` prefixes grep -n adds."""
    out = []
    for ln in text.split("\n"):
        m = re.match(r"^\s*\d+\t(.*)$", ln)
        if m:
            out.append(m.group(1)); continue
        m = re.match(r"^\d+:(.*)$", ln)
        if m:
            out.append(m.group(1)); continue
        out.append(ln)
    return "\n".join(out)

def preview_html(text):
    return markdown(dewiki(strip_line_numbers(text)))

# ---------------------------------------------------------------- walk

donna_prompt = None
events = []          # list of dicts for the run log
final_reply = None
tool_count = 0
first_ts = last_ts = None
model = effort = version = cwd = branch = None

# Claude Code writes one transcript record per content block, and every record
# repeats the whole message's usage. Summing per record therefore multiplies the
# real token counts -- dedupe on the API message id.
usage_seen = set()
tok = {"input": 0, "cache_write_1h": 0, "cache_write_5m": 0,
       "cache_read": 0, "output": 0, "reasoning": 0}

for idx, r in enumerate(records):
    t = r.get("type")
    if t == "user" and r.get("promptSource") == "sdk":
        donna_prompt = r["message"]["content"]
        first_ts = parse_ts(r["timestamp"])
        cwd = r.get("cwd"); branch = r.get("gitBranch"); version = r.get("version")
        continue
    if t != "assistant":
        continue

    last_ts = parse_ts(r["timestamp"])
    model = r["message"].get("model") or model
    effort = r.get("effort") or effort
    u = r["message"].get("usage") or {}
    mid = r["message"].get("id")
    if mid not in usage_seen:
        usage_seen.add(mid)
        cc = u.get("cache_creation") or {}
        tok["input"] += u.get("input_tokens", 0)
        tok["cache_write_1h"] += cc.get("ephemeral_1h_input_tokens", 0)
        tok["cache_write_5m"] += cc.get("ephemeral_5m_input_tokens", 0)
        tok["cache_read"] += u.get("cache_read_input_tokens", 0)
        tok["output"] += u.get("output_tokens", 0)
        tok["reasoning"] += (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)

    is_last = (idx == max(i for i, x in enumerate(records) if x.get("type") == "assistant"))

    for b in r["message"]["content"]:
        bt = b.get("type")
        if bt == "thinking":
            events.append({"kind": "thinking",
                           "tokens": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0),
                           "sig": b.get("signature", ""),
                           "ts": last_ts})
        elif bt == "text":
            if is_last:
                final_reply = b["text"]
            else:
                events.append({"kind": "say", "text": b["text"], "ts": last_ts})
        elif bt == "tool_use":
            tool_count += 1
            kicker, title, verb, detail = humanize(b["name"], b["input"])
            res = by_id.get(b["id"])
            rt = result_text(res)
            events.append({"kind": "tool", "kicker": kicker, "title": title, "verb": verb,
                           "detail": detail, "name": b["name"],
                           "result": rt,
                           "preview": preview_html(rt) if (rt.strip() and is_markdown_result(b["name"], b["input"], rt)) else None,
                           "error": bool(res and res.get("is_error")),
                           "ts": last_ts})

duration = last_ts - first_ts
mins, secs = divmod(int(duration.total_seconds()), 60)

# ---------------------------------------------------------------- cost
# Claude Opus 5 public API list rates, $ per million tokens.
# Base input $5.00 / output $25.00; cache writes 1.25x base at the 5-minute TTL
# and 2x at the 1-hour TTL; cache reads 0.1x base.
RATE = {
    "input":          5.00,
    "cache_write_5m": 6.25,
    "cache_write_1h": 10.00,
    "cache_read":     0.50,
    "output":         25.00,
}
cost = {k: tok[k] * RATE[k] / 1_000_000 for k in RATE}
# Reasoning tokens are a subset of output tokens, priced at the same rate --
# reported separately for visibility, never added to the total.
cost_reasoning = tok["reasoning"] * RATE["output"] / 1_000_000
input_tokens_total = tok["input"] + tok["cache_write_1h"] + tok["cache_write_5m"] + tok["cache_read"]
cost_input_total = cost["input"] + cost["cache_write_1h"] + cost["cache_write_5m"] + cost["cache_read"]
cost_total = cost_input_total + cost["output"]

def usd(x):
    return "$%.2f" % x if x >= 0.005 else "&lt;$0.01"

# ---------------------------------------------------------------- render events

def clock(ts):
    return ts.strftime("%H:%M:%S")

def trunc(s, cap=200000):
    if len(s) <= cap:
        return html.escape(s), False
    return html.escape(s[:cap]), True

log_html = []
step = 0
for e in events:
    if e["kind"] == "say":
        log_html.append(
            "<div class='ev say'><div class='evtime'>%s</div>"
            "<div class='evbody'><div class='saybubble'>%s</div></div></div>"
            % (clock(e["ts"]), markdown(e["text"])))
    elif e["kind"] == "thinking":
        step_tokens = f"{e['tokens']:,}" if e["tokens"] else "0"
        log_html.append(
            "<details class='ev think'><summary><div class='evtime'>%s</div>"
            "<span class='badge think'>thinking</span>"
            "<span class='evtitle'>Reasoned privately</span>"
            "<span class='evmeta'>%s reasoning tokens this step</span></summary>"
            "<div class='evdetail'><p class='note'>Extended thinking is not retained in plaintext in the "
            "transcript. Claude Code stores only the signed, encrypted block, so the token count and its "
            "cryptographic signature are all that survive on disk.</p>"
            "<div class='kv'><span>signature</span><code class='sig'>%s…</code></div></div></details>"
            % (clock(e["ts"]), step_tokens, html.escape(e["sig"][:96])))
    else:
        step += 1
        body, cut = trunc(e["result"])
        cutnote = "<p class='note'>Output truncated for display.</p>" if cut else ""

        if e["preview"]:
            seg = ("<span class='seg'>"
                   "<button class='segbtn on' data-view='raw'>Raw</button>"
                   "<button class='segbtn' data-view='md'>Preview</button></span>")
            pane = ("<pre class='result' data-pane='raw'><code>%s</code></pre>"
                    "<div class='result mdpane' data-pane='md' hidden>%s</div>"
                    % (body, e["preview"]))
        else:
            seg = ""
            pane = "<pre class='result' data-pane='raw'><code>%s</code></pre>" % body

        log_html.append(
            "<details class='ev tool'><summary>"
            "<div class='evtime'>%s</div>"
            "<span class='badge k-%s'>%s %s</span>"
            "<span class='evtitle'>%s</span>"
            "<span class='evmeta'>%s</span></summary>"
            "<div class='evdetail'>%s"
            "<div class='reslabel'>Result%s%s</div>"
            "%s%s</div></details>"
            % (clock(e["ts"]), e["kicker"].lower(), ICON[e["kicker"]], e["kicker"],
               html.escape(e["title"]), html.escape(e["verb"]), e["detail"],
               " · error" if e["error"] else "", seg, pane, cutnote))

# ---------------------------------------------------------------- page

title_date = first_ts.strftime("%Y-%m-%d")
title_time = first_ts.strftime("%H:%M")
page_title = f"Conversation Audit Log: Donna → Greenthumb on {title_date} at {title_time} PT"

meta_rows = [
    ("Channel", "<code>claude -p</code> · non-interactive SDK session"),
    ("Repo", f"<code>{html.escape(cwd)}</code> on <code>{html.escape(branch)}</code>"),
    ("Session", "<code>0a5df9e2-3dc1-4bee-9013-e38e709b4cb1</code>"),
    ("Model", f"<code>{html.escape(model)}</code> · effort <code>{html.escape(effort or 'n/a')}</code> · CLI {html.escape(version)}"),
    ("Permissions", "<code>bypassPermissions</code> (unattended)"),
]

stats = [
    (f"{mins}m {secs:02d}s", "wall clock", None),
    (str(tool_count), "tool calls", None),
    (f"{input_tokens_total:,}", "input tokens", usd(cost_input_total)),
    (f"{tok['output']:,}", "output tokens", usd(cost["output"])),
    (f"{tok['reasoning']:,}", "reasoning tokens", usd(cost_reasoning) + ", of the output"),
    (usd(cost_total), "total, list price", None),
    ("1", "git commit", None),
    ("1", "external API call", None),
]

cost_rows = [
    ("Fresh input", tok["input"], RATE["input"], cost["input"]),
    ("Cache writes (1-hour TTL)", tok["cache_write_1h"], RATE["cache_write_1h"], cost["cache_write_1h"]),
    ("Cache reads", tok["cache_read"], RATE["cache_read"], cost["cache_read"]),
    (f"Output (incl. {tok['reasoning']:,} reasoning)", tok["output"], RATE["output"], cost["output"]),
]

cost_note = f"""
<details class="costnote">
  <summary>Estimated at <strong>{usd(cost_total)}</strong> &mdash; how that is calculated</summary>
  <div class="costbody">
    <p>This session ran on a Claude subscription, so nothing was billed per token. The figure is
       what the identical traffic would cost through the public API, at
       <code>claude-opus-5</code> list rates: $5.00 per million input tokens and $25.00 per
       million output. Cache writes bill at 2&times; base on the 1-hour TTL this session used, and
       cache reads at 0.1&times;.</p>
    <div class="tablewrap"><table><thead><tr>
      <th>Component</th><th>Tokens</th><th>Rate / Mtok</th><th>Cost</th>
    </tr></thead><tbody>
      {''.join(f'<tr><td>{n}</td><td class="num">{t:,}</td><td class="num">${r:.2f}</td><td class="num">{usd(c)}</td></tr>' for n, t, r, c in cost_rows)}
      <tr class="total"><td>Total</td><td class="num">{input_tokens_total + tok['output']:,}</td><td></td><td class="num">{usd(cost_total)}</td></tr>
    </tbody></table></div>
    <p class="note">Reasoning tokens are a subset of output tokens, not a separate line item, so the
       {usd(cost_reasoning)} shown on that tile is already inside the {usd(cost['output'])} of output.
       The single largest cost here is cache writes: the run read four tracker files and a 7-day
       forecast into a context that then had to be written to cache once per turn.</p>
  </div>
</details>
"""

side_effects = """
<ul>
  <li><strong>Committed <code>051a130</code></strong> to <code>greenthumb</code> — four tracker files
      (<code>action-log.md</code>, <code>concerns.md</code>, <code>rules.md</code>, <code>work-plan.md</code>),
      6 insertions, folded into one logical unit rather than four commits.</li>
  <li><strong>Did not push.</strong> Donna's instruction said commit only; the working tree change stayed local.</li>
  <li><strong>Called an outside service.</strong> Pulled a 7-day hourly forecast from Open-Meteo for the
      property's coordinates, which is what turned the answer around.</li>
  <li><strong>Read five repo files</strong> (rules, work plan ×2, product sheets, inventory) and ran
      four read-only greps. No other writes.</li>
</ul>
"""

CSS = """
:root{
  --bg:#f6f5f1; --panel:#fffefb; --ink:#1c1d1a; --muted:#6b6f66; --line:#e2e0d7;
  --donna:#6b4fbb; --donna-bg:#f1edfd; --donna-line:#d9cff5;
  --green:#2f7d46; --green-bg:#edf6ef; --green-line:#c9e3d0;
  --code-bg:#f2f1ec; --code-ink:#31332e; --accent:#b0762a;
  --shadow:0 1px 2px rgba(30,30,20,.05), 0 8px 24px rgba(30,30,20,.05);
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#15161a; --panel:#1c1e23; --ink:#e8e7e2; --muted:#9a9d96; --line:#2c2f36;
  --donna:#a794ea; --donna-bg:#221f33; --donna-line:#3a3357;
  --green:#7cc496; --green-bg:#182420; --green-line:#2b4436;
  --code-bg:#131519; --code-ink:#cfd2cb; --accent:#d8a45c;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.28);
}}
:root[data-theme="dark"]{
  --bg:#15161a; --panel:#1c1e23; --ink:#e8e7e2; --muted:#9a9d96; --line:#2c2f36;
  --donna:#a794ea; --donna-bg:#221f33; --donna-line:#3a3357;
  --green:#7cc496; --green-bg:#182420; --green-line:#2b4436;
  --code-bg:#131519; --code-ink:#cfd2cb; --accent:#d8a45c;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.28);
}
*{box-sizing:border-box}
[hidden]{display:none !important}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.62 ui-serif,Charter,"Iowan Old Style",Georgia,serif;
  -webkit-font-smoothing:antialiased;}
.wrap{max-width:920px;margin:0 auto;padding:40px 22px 120px}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}

/* ---- masthead ---- */
.mast{border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:26px}
.eyebrow{font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.18em;
  text-transform:uppercase;color:var(--accent);margin-bottom:14px}
h1{font-size:clamp(26px,4.4vw,40px);line-height:1.16;margin:0 0 6px;letter-spacing:-.015em;font-weight:600}
h1 .arrow{color:var(--muted);font-weight:400}
.sub{color:var(--muted);font-size:15px;margin:8px 0 0}

/* ---- meta ---- */
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:2px 26px;
  margin:22px 0 20px;font:13px/1.75 ui-sans-serif,system-ui,sans-serif}
.meta div{display:flex;gap:10px;border-bottom:1px dotted var(--line);padding:5px 0}
.meta b{flex:0 0 92px;color:var(--muted);font-weight:500}
.meta code{font-size:12px;background:var(--code-bg);padding:1px 5px;border-radius:4px;color:var(--code-ink)}
.meta span{min-width:0;overflow-wrap:anywhere}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
  background:var(--line);border:1px solid var(--line);border-radius:10px 10px 0 0;overflow:hidden;margin:0}
@media(max-width:620px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--panel);padding:13px 14px}
.stat b{display:block;font:600 21px/1.1 ui-sans-serif,system-ui,sans-serif;letter-spacing:-.02em}
.stat span{display:block;font:11px/1.5 ui-sans-serif,system-ui,sans-serif;color:var(--muted);
  text-transform:uppercase;letter-spacing:.07em;margin-top:3px}
.stat i{display:block;font:italic 12px/1.4 ui-serif,Charter,Georgia,serif;color:var(--accent);
  margin-top:5px;font-feature-settings:"tnum"}

/* cost note */
.costnote{border:1px solid var(--line);border-top:0;border-radius:0 0 10px 10px;
  background:var(--panel);margin:0 0 34px;overflow:hidden}
.costnote > summary{cursor:pointer;list-style:none;padding:11px 14px;
  font:12px/1.4 ui-sans-serif,system-ui,sans-serif;color:var(--muted);display:flex;
  align-items:center;gap:8px}
.costnote > summary::-webkit-details-marker{display:none}
.costnote > summary::after{content:"+";margin-left:auto;font:13px/1 ui-monospace,monospace}
.costnote[open] > summary::after{content:"\\2212"}
.costnote > summary:hover{background:var(--code-bg)}
.costnote > summary strong{color:var(--accent);font-weight:650}
.costbody{padding:4px 16px 18px;border-top:1px solid var(--line);font-size:14px}
.costbody p{margin:12px 0}
.costbody table{font-size:13px}
.costbody td.num,.costbody th:nth-child(n+2){text-align:right;font-variant-numeric:tabular-nums;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.costbody td.num{font-size:12.5px}
.costbody tr.total td{font-weight:650;border-top:1px solid var(--muted)}
.costbody td:first-child{white-space:normal}

/* ---- turn cards ---- */
.turn{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  box-shadow:var(--shadow);margin:0 0 26px;overflow:hidden}
.turn.donna{border-left:4px solid var(--donna)}
.turn.gt{border-left:4px solid var(--green)}
.turnhead{display:flex;align-items:center;gap:12px;padding:16px 22px;border-bottom:1px solid var(--line)}
.turn.donna .turnhead{background:var(--donna-bg)}
.turn.gt .turnhead{background:var(--green-bg)}
.av{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;
  font:600 14px/1 ui-sans-serif,system-ui,sans-serif;color:#fff}
.turn.donna .av{background:var(--donna)}
.turn.gt .av{background:var(--green)}
.who{font:600 15px/1.2 ui-sans-serif,system-ui,sans-serif}
.who small{display:block;font-weight:400;font-size:12px;color:var(--muted);margin-top:3px;letter-spacing:.01em}
.stamp{margin-left:auto;font:12px/1 ui-monospace,monospace;color:var(--muted);text-align:right;flex:0 0 auto}
.turnbody{padding:22px 24px}
.turnbody > :first-child{margin-top:0}
.turnbody > :last-child{margin-bottom:0}

p{margin:0 0 .95em}
.md-h{font-family:ui-sans-serif,system-ui,sans-serif;letter-spacing:-.01em;line-height:1.3}
.md-h2{font-size:21px;margin:1.7em 0 .55em;padding-bottom:.3em;border-bottom:1px solid var(--line)}
.md-h3{font-size:17px;margin:1.5em 0 .5em}
.md-h4{font-size:15px;margin:1.3em 0 .45em;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
hr{border:0;border-top:1px solid var(--line);margin:1.8em 0}
ul,ol{margin:0 0 1em;padding-left:1.35em}
li{margin:.32em 0}
blockquote{margin:0 0 1em;padding-left:16px;border-left:3px solid var(--line);color:var(--muted)}
strong{font-weight:650}
code{background:var(--code-bg);color:var(--code-ink);padding:.1em .38em;border-radius:4px;font-size:.855em}
pre.code{background:var(--code-bg);border:1px solid var(--line);border-radius:9px;
  padding:13px 15px;overflow-x:auto;margin:0 0 1em;font-size:12.5px;line-height:1.6}
pre.code code{background:none;padding:0;font-size:inherit}
.tablewrap{overflow-x:auto;margin:0 0 1.2em;border:1px solid var(--line);border-radius:9px}
table{border-collapse:collapse;width:100%;font:14px/1.5 ui-sans-serif,system-ui,sans-serif}
th,td{padding:9px 13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--code-bg);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
tr:last-child td{border-bottom:0}
td:first-child,th:first-child{white-space:nowrap}

/* ---- prompt (donna) ---- */
.prompt{font-size:15.5px}
.prompt p:first-child strong{font-size:1.05em}

/* ---- run log ---- */
.runhead{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:13px 24px;
  background:var(--code-bg);border-bottom:1px solid var(--line);
  font:12px/1.4 ui-sans-serif,system-ui,sans-serif;color:var(--muted)}
.runhead .lbl{font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--ink);flex:0 0 auto}
.runsum{flex:1 1 120px;min-width:0}
.ctl{margin-left:auto;display:flex;gap:7px;align-items:center}
.ctl .grp{display:flex;gap:7px}
.runhead.workhidden .grp{display:none}
.runhead.workhidden .hint{display:none}
.hint{color:var(--muted)}
button{font:11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.05em;text-transform:uppercase;
  background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;
  padding:6px 12px;cursor:pointer}
button:hover{border-color:var(--muted)}
button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}

.log{padding:8px 0}
.ev{border-bottom:1px solid var(--line);font-family:ui-sans-serif,system-ui,sans-serif}
.ev:last-child{border-bottom:0}
.ev > summary{display:flex;align-items:baseline;gap:11px;padding:11px 24px;cursor:pointer;
  list-style:none;font-size:13.5px}
.ev > summary::-webkit-details-marker{display:none}
.ev > summary:hover{background:var(--code-bg)}
.ev > summary::after{content:"+";margin-left:auto;color:var(--muted);font:13px/1 ui-monospace,monospace;
  flex:0 0 auto;padding-left:10px}
.ev[open] > summary::after{content:"\\2212"}
.ev[open] > summary{background:var(--code-bg)}
.evtime{font:11px/1.5 ui-monospace,monospace;color:var(--muted);flex:0 0 60px}
.badge{font:600 10px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.09em;padding:4px 7px;
  border-radius:5px;flex:0 0 auto;border:1px solid transparent}
.k-shell{background:var(--code-bg);color:var(--ink);border-color:var(--line)}
.k-read{background:var(--green-bg);color:var(--green);border-color:var(--green-line)}
.k-tools{background:var(--code-bg);color:var(--muted);border-color:var(--line)}
.k-external{background:var(--donna-bg);color:var(--donna);border-color:var(--donna-line)}
.k-tool{background:var(--code-bg);color:var(--muted);border-color:var(--line)}
.badge.think{background:transparent;color:var(--muted);border:1px dashed var(--line);
  text-transform:uppercase}
.evtitle{font-weight:550;min-width:0;overflow-wrap:anywhere}
.evmeta{color:var(--muted);font-size:12px;min-width:0;overflow-wrap:anywhere}
@media(max-width:640px){.evmeta{display:none}}
.evdetail{padding:4px 24px 20px 24px;font-size:13.5px}
.evdetail .kv{display:flex;gap:10px;font-size:12px;margin:0 0 7px;color:var(--muted)}
.evdetail .kv span{flex:0 0 74px}
.evdetail .kv code{overflow-wrap:anywhere;font-size:11.5px}
.sig{opacity:.6}
.note{color:var(--muted);font-size:12.5px;font-style:italic;margin:0 0 10px}
.reslabel{display:flex;align-items:center;gap:10px;
  font:600 10px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin:14px 0 7px}
.seg{margin-left:auto;display:inline-flex;border:1px solid var(--line);border-radius:999px;
  overflow:hidden;background:var(--panel)}
.segbtn{border:0;border-radius:0;padding:5px 12px;background:transparent;color:var(--muted);
  font:600 10px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;
  cursor:pointer}
.segbtn + .segbtn{border-left:1px solid var(--line)}
.segbtn:hover{color:var(--ink)}
.segbtn.on{background:var(--ink);color:var(--bg)}

/* rendered-markdown pane inside a tool result */
.mdpane{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:14px 16px;
  max-height:400px;overflow:auto;font:14px/1.55 ui-serif,Charter,Georgia,serif;color:var(--ink)}
.mdpane > :first-child{margin-top:0}
.mdpane > :last-child{margin-bottom:0}
.mdpane .md-h2{font-size:17px;margin:1.2em 0 .45em}
.mdpane .md-h3{font-size:15px;margin:1.1em 0 .4em}
.mdpane .md-h4{font-size:13px;margin:1em 0 .35em}
.mdpane table{font-size:12.5px}
.mdpane th,.mdpane td{padding:6px 10px}
.mdpane td:first-child,.mdpane th:first-child{white-space:normal}
.mdpane p,.mdpane ul,.mdpane ol{margin-bottom:.7em}
.mdpane code{font-size:.82em}
.mdpane del{opacity:.55}
.mdpane .tablewrap{margin-bottom:.8em}
pre.result{background:var(--code-bg);border:1px solid var(--line);border-radius:9px;padding:12px 14px;
  margin:0;max-height:340px;overflow:auto;font-size:11.5px;line-height:1.62;white-space:pre-wrap;
  overflow-wrap:anywhere;color:var(--code-ink)}
pre.result code{background:none;padding:0;font-size:inherit}
pre.code.shell{white-space:pre-wrap;overflow-wrap:anywhere}

/* narration bubbles */
.ev.say{padding:13px 24px}
.ev.say .evbody{display:flex}
.saybubble{border-left:3px solid var(--green);padding-left:14px;color:var(--ink);
  font:italic 14px/1.6 ui-serif,Charter,Georgia,serif}
.saybubble p{margin:0}
.ev.say{display:flex;gap:11px;align-items:baseline}
.ev.say .evtime{flex:0 0 60px}

/* reply banner */
.replybar{display:flex;align-items:center;gap:11px;padding:14px 24px;
  background:var(--green-bg);border-top:1px solid var(--green-line);border-bottom:1px solid var(--green-line);
  font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.11em;text-transform:uppercase;
  color:var(--green)}
.replybar .dot{width:7px;height:7px;border-radius:50%;background:var(--green);flex:0 0 auto}
.replybar .thin{margin-left:auto;font-weight:400;letter-spacing:.02em;text-transform:none;
  font-size:12px;color:var(--muted)}

/* side effects */
.fx{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:14px;box-shadow:var(--shadow);padding:20px 24px;margin:0 0 26px}
.fx h2{font:600 12px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.11em;text-transform:uppercase;
  color:var(--accent);margin:0 0 14px}
.fx ul{margin:0;font-size:14.5px}

footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
  font:12px/1.7 ui-sans-serif,system-ui,sans-serif;color:var(--muted)}
footer code{font-size:11px}
.log.collapsed{padding:0}
.collapsed .ev{display:none}
"""

JS = """
const log     = document.getElementById('log');
const runhead = document.getElementById('runhead');
const hideBtn = document.getElementById('hide');

function setAll(open){ log.querySelectorAll('details.ev').forEach(d => d.open = open); }
document.getElementById('expand').onclick   = () => setAll(true);
document.getElementById('collapse').onclick = () => setAll(false);

// Work log is hidden on load; this button is the only way in and out.
hideBtn.onclick = () => {
  const hidden = log.classList.toggle('collapsed');
  runhead.classList.toggle('workhidden', hidden);
  hideBtn.classList.toggle('on', hidden);
  hideBtn.textContent = hidden ? 'Show work' : 'Dialog only';
  if (hidden) setAll(false);
};

// Raw / Preview toggle on markdown tool results. Both panes are pre-rendered
// at build time, so this only flips visibility -- no parser ships with the page.
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.segbtn');
  if (!btn) return;
  e.preventDefault();
  const detail = btn.closest('.evdetail');
  detail.querySelectorAll('.segbtn').forEach(b => b.classList.toggle('on', b === btn));
  detail.querySelectorAll('[data-pane]').forEach(p => {
    p.hidden = (p.dataset.pane !== btn.dataset.view);
  });
});
"""

html_out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page_title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <div class="eyebrow">Conversation Audit Log</div>
    <h1>Donna <span class="arrow">&rarr;</span> Greenthumb</h1>
    <p class="sub">{first_ts.strftime('%A, %B %-d, %Y')} at {first_ts.strftime('%-I:%M %p')} Pacific &middot;
       one agent-to-agent exchange, captured end to end</p>
  </header>

  <div class="meta">
    {''.join(f'<div><b>{k}</b><span>{v}</span></div>' for k, v in meta_rows)}
  </div>

  <div class="stats">
    {''.join('<div class="stat"><b>%s</b><span>%s</span>%s</div>'
             % (a, b, f'<i>&asymp; {c}</i>' if c else '')
             for a, b, c in stats)}
  </div>

  {cost_note}

  <section class="turn donna">
    <div class="turnhead">
      <div class="av">D</div>
      <div class="who">Donna<small>Chief of staff agent &middot; wrote the prompt, waited on stdout</small></div>
      <div class="stamp">{clock(first_ts)} PT</div>
    </div>
    <div class="turnbody prompt">{markdown(donna_prompt)}</div>
  </section>

  <section class="turn gt">
    <div class="turnhead">
      <div class="av">G</div>
      <div class="who">Greenthumb<small>Garden agent &middot; ran headless in <code>~/src/scottwb/greenthumb</code></small></div>
      <div class="stamp">{clock(first_ts)} &rarr; {clock(last_ts)} PT<br>{mins}m {secs:02d}s</div>
    </div>

    <div class="runhead workhidden" id="runhead">
      <span class="lbl">Work log</span>
      <span class="runsum">{tool_count} tool calls &middot; {len([e for e in events if e['kind']=='thinking'])} reasoning steps
        <span class="hint">&mdash; expand any row to see what actually ran</span></span>
      <span class="ctl">
        <span class="grp">
          <button id="expand">Expand all</button>
          <button id="collapse">Collapse all</button>
        </span>
        <button id="hide" class="on">Show work</button>
      </span>
    </div>

    <div class="log collapsed" id="log">
      {''.join(log_html)}
    </div>

    <div class="replybar">
      <span class="dot"></span>
      Reply returned to Donna on stdout
      <span class="thin">{clock(last_ts)} PT &middot; {len(final_reply.split()):,} words</span>
    </div>

    <div class="turnbody">{markdown(final_reply)}</div>
  </section>

  <section class="fx">
    <h2>Side effects on the real world</h2>
    {side_effects}
  </section>

  <footer>
    Rendered from the raw Claude Code transcript
    <code>0a5df9e2-3dc1-4bee-9013-e38e709b4cb1.jsonl</code>.
    Nothing in the dialog or the work log is paraphrased; tool calls are labelled in plain
    English but the commands and their output are verbatim. Reasoning steps are listed because
    the transcript records their token counts, but extended thinking is stored encrypted, so no
    agent's inner monologue is recoverable here.
  </footer>

</div>
<script>{JS}</script>
</body>
</html>
"""

with open(OUT, "w") as f:
    f.write(html_out)

print(f"wrote {OUT}  ({os.path.getsize(OUT):,} bytes)")
print(f"events={len(events)} tools={tool_count} api_messages={len(usage_seen)}")
print(f"tokens: {tok}")
print(f"input side {input_tokens_total:,} = ${cost_input_total:.4f} | "
      f"output {tok['output']:,} = ${cost['output']:.4f} | "
      f"reasoning {tok['reasoning']:,} = ${cost_reasoning:.4f} (in output) | "
      f"TOTAL ${cost_total:.4f}")
print(f"span {first_ts} -> {last_ts}  ({mins}m {secs}s)")

"""Session model to a single self-contained HTML page.

Constraints, all of them non-negotiable:

* **One file, zero external requests.** No CDN, no web fonts, no remote images,
  no fetch. The page must render identically with the network off.
* **No model call in the render path** (decision A9). Rendering is
  deterministic and byte-reproducible: the same transcript always produces the
  same bytes.
* **Verbatim.** Tool commands and their output are never paraphrased. Only the
  one-line labels are human-written, and where no label is known the fallback
  says so plainly rather than inventing one.
* **Nothing hardcoded to one session.** Every count, every name, and every line
  of the side-effects box is derived from the transcript. See Defect 3.

Both panes of every raw/preview toggle are rendered at build time and shipped as
sibling divs, so the click handler only flips visibility. No markdown parser
ships with the page.
"""

import html
import json
import os

from . import cost as cost_module
from . import markdown as md

# --------------------------------------------------------------- tool labels

#: Badge kind to its glyph. Kinds are coarse on purpose: the label carries the
#: detail, the badge only groups.
ICON = {
    "SHELL": "&#9656;",
    "READ": "&#9634;",
    "WRITE": "&#9998;",
    "TOOLS": "&#9881;",
    "EXTERNAL": "&#9729;",
    "TASK": "&#9737;",
    "TOOL": "&#9679;",
    "THINK": "&#9675;",
    "SAY": "&#8220;",
}


def tool_short_name(name):
    """The tool column's text: the tool's own name, kept short.

    An MCP tool's full name is `mcp__<server>__<tool>`; the column shows
    `server:tool`, which says the same thing in a third of the width. Every
    other tool is already a single word.
    """
    name = name or "?"
    if name.startswith("mcp__"):
        pieces = name.split("__")
        server = pieces[1] if len(pieces) > 1 else "?"
        tool = pieces[2] if len(pieces) > 2 else "?"
        return "%s:%s" % (server, tool)
    return name

#: Shell verbs, most specific first. Matching is on the whole command, since a
#: heredoc can bury the interesting part hundreds of characters in.
_SHELL_VERBS = (
    ("git commit", "Wrote a git commit"),
    ("git push", "Pushed to a remote"),
    ("git add", "Staged changes"),
    ("git status", "Inspected git state"),
    ("git diff", "Inspected git state"),
    ("git log", "Inspected git state"),
    ("grep", "Searched files"),
    ("rg ", "Searched files"),
    ("find ", "Searched for files"),
    ("date", "Checked the clock"),
    ("ls ", "Listed a directory"),
    ("cat ", "Read a file out"),
    ("sed ", "Read a file out"),
    ("head ", "Read a file out"),
    ("tail ", "Read a file out"),
    ("mkdir", "Created a directory"),
    ("curl", "Fetched something over the network"),
)


def _kv(label, value):
    return "<div class='kv'><span>%s</span><code>%s</code></div>" % (
        html.escape(label),
        html.escape(str(value)),
    )


def _pre(text, extra=""):
    return "<pre class='code%s'><code>%s</code></pre>" % (
        (" " + extra) if extra else "",
        html.escape(text),
    )


def humanize(name, params):
    """One plain-English line for a tool call.

    Returns `(kind, title, verb, detail_html)`. The fallback is deliberately
    honest: an unrecognized tool is labelled with its own name and its input is
    shown verbatim, rather than being described with a guess.
    """
    params = params or {}

    if name == "Bash":
        command = params.get("command", "") or ""
        verb = "Ran a shell command"
        for needle, candidate in _SHELL_VERBS:
            if needle in command:
                verb = candidate
                break
        title = params.get("description") or "Shell command"
        return "SHELL", title, verb, _pre(command, "shell")

    if name in ("Read", "NotebookRead"):
        path = params.get("file_path") or params.get("notebook_path") or ""
        base = os.path.basename(path)
        span = ""
        if params.get("offset"):
            start = params["offset"]
            limit = params.get("limit") or 0
            span = " · lines %s to %s" % (start, start + limit - 1) if limit \
                else " · from line %s" % start
        return "READ", "Read %s%s" % (base, span), "Opened a file", _kv("path", path)

    if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = params.get("file_path") or params.get("notebook_path") or ""
        return (
            "WRITE",
            "%s %s" % (name, os.path.basename(path)),
            "Changed a file on disk",
            _kv("path", path),
        )

    if name in ("Glob", "Grep"):
        pattern = params.get("pattern", "")
        return "READ", "Searched for %s" % pattern, "Searched the filesystem", \
            _kv("pattern", pattern)

    if name == "ToolSearch":
        query = params.get("query", "")
        return (
            "TOOLS",
            "Loaded a deferred tool schema",
            "Pulled in a tool on demand",
            _kv("query", query),
        )

    if name in ("Task", "Agent"):
        return (
            "TASK",
            params.get("description") or "Delegated to a subagent",
            "Spawned a subagent",
            _pre(json.dumps(params, indent=2, sort_keys=True)),
        )

    if name in ("WebFetch", "WebSearch"):
        target = params.get("url") or params.get("query") or ""
        return "EXTERNAL", "%s %s" % (name, target), "Reached outside the machine", \
            _kv("target", target)

    if name.startswith("mcp__"):
        # mcp__<server>__<tool>
        pieces = name.split("__")
        server = pieces[1] if len(pieces) > 1 else "?"
        tool = pieces[2] if len(pieces) > 2 else "?"
        detail = "".join(
            _kv(key, _short(value)) for key, value in sorted(params.items())
        )
        return (
            "EXTERNAL",
            "%s · %s" % (server, tool),
            "Called an outside service",
            detail or _pre(json.dumps(params, indent=2, sort_keys=True)),
        )

    return (
        "TOOL",
        name,
        "Tool call",
        _pre(json.dumps(params, indent=2, sort_keys=True)),
    )


def _short(value, cap=120):
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(v) for v in value)
    elif isinstance(value, dict):
        text = json.dumps(value, sort_keys=True)
    else:
        text = str(value)
    return text if len(text) <= cap else text[: cap - 1] + "…"


# ------------------------------------------------------------------ helpers

def usd(amount):
    return "$%.2f" % amount if amount >= 0.005 else "&lt;$0.01"


#: `agent-color` carries the colour Claude Code shows for an agent, so a page
#: about Greenthumb comes out green without anyone configuring it. Each entry is
#: (ink, background, border) for light mode; dark mode keeps the shared tokens,
#: because a hand-picked dark variant per colour is more than this earns.
AGENT_COLORS = {
    "green": ("#2f7d46", "#edf6ef", "#c9e3d0"),
    "blue": ("#2a5fa8", "#ecf2fb", "#cbdcf2"),
    "cyan": ("#1f6f79", "#e9f5f6", "#c4e2e5"),
    "purple": ("#6b4fbb", "#f1edfd", "#d9cff5"),
    "violet": ("#6b4fbb", "#f1edfd", "#d9cff5"),
    "magenta": ("#a4348a", "#fbecf6", "#f0cde5"),
    "red": ("#b03a34", "#fbeeed", "#f1cfcc"),
    "orange": ("#b0762a", "#fbf3e7", "#eeddc2"),
    "yellow": ("#8f7420", "#f9f4e2", "#e8dcb6"),
}


def agent_color_style(color):
    """An inline style overriding the agent card's palette, or "".

    Returns a style attribute rather than injecting CSS, so an unrecognized
    colour name simply produces nothing and the default green stands.
    """
    entry = AGENT_COLORS.get((color or "").strip().lower())
    if not entry:
        return ""
    ink, background, line = entry
    return (
        ' style="--agent:%s;--agent-bg:%s;--agent-line:%s"' % (ink, background, line)
    )


def provider_and_model(model):
    """`Anthropic / <code>claude-opus-5</code>` for the provenance strip.

    The provider comes first because it is the part the model id does not say
    out loud: `glm-4.7-flash` alone leaves the reader to work out that it ran
    locally. When the provider cannot be inferred, the label says so rather
    than leaving the slot blank, which would read as "Anthropic, obviously".
    """
    name = html.escape(model or "unknown")
    provider = cost_module.provider_for(model)
    if provider is None:
        return "<code>%s</code> · provider unknown" % name
    return "%s / <code>%s</code>" % (html.escape(provider), name)


def _clock(moment):
    return moment.strftime("%H:%M:%S") if moment else "--:--:--"


def _duration_words(delta):
    if delta is None:
        return "n/a"
    seconds = int(delta.total_seconds())
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return "%dh %02dm" % (hours, minutes)
    return "%dm %02ds" % (minutes, seconds)


def step_duration(delta):
    """A per-row duration: `0.42s`, `1m 03s`, or a dash when unmeasurable.

    Hundredths below a minute, because that is the scale tool calls actually
    live at (0.00s to 0.66s on a real brief). None becomes a dash rather than
    `0.00s`: a call whose result never came back was not instantaneous.
    """
    if delta is None:
        return "&ndash;"
    seconds = delta.total_seconds()
    if seconds < 60:
        return "%.2fs" % seconds
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return "%dh %02dm" % (hours, minutes)
    return "%dm %02ds" % (minutes, seconds)


def _initial(name):
    return (name or "?").strip()[:1].upper() or "?"


def _truncate(text, cap):
    if len(text) <= cap:
        return html.escape(text), False
    return html.escape(text[:cap]), True


# ------------------------------------------------------------------- CSS/JS

#: The colour tokens, on their own so the index page shares them. Light on
#: bare :root; dark under prefers-color-scheme (unless the viewer forced light)
#: and again under an explicit data-theme="dark", so a toggle wins both ways.
PALETTE_CSS = """
:root{
  --bg:#f6f5f1; --panel:#fffefb; --ink:#1c1d1a; --muted:#6b6f66; --line:#e2e0d7;
  --caller:#6b4fbb; --caller-bg:#f1edfd; --caller-line:#d9cff5;
  --agent:#2f7d46; --agent-bg:#edf6ef; --agent-line:#c9e3d0;
  --code-bg:#f2f1ec; --code-ink:#31332e; --accent:#b0762a;
  --shadow:0 1px 2px rgba(30,30,20,.05), 0 8px 24px rgba(30,30,20,.05);
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#15161a; --panel:#1c1e23; --ink:#e8e7e2; --muted:#9a9d96; --line:#2c2f36;
  --caller:#a794ea; --caller-bg:#221f33; --caller-line:#3a3357;
  --agent:#7cc496; --agent-bg:#182420; --agent-line:#2b4436;
  --code-bg:#131519; --code-ink:#cfd2cb; --accent:#d8a45c;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.28);
}}
:root[data-theme="dark"]{
  --bg:#15161a; --panel:#1c1e23; --ink:#e8e7e2; --muted:#9a9d96; --line:#2c2f36;
  --caller:#a794ea; --caller-bg:#221f33; --caller-line:#3a3357;
  --agent:#7cc496; --agent-bg:#182420; --agent-line:#2b4436;
  --code-bg:#131519; --code-ink:#cfd2cb; --accent:#d8a45c;
  --shadow:0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.28);
}
"""

CSS = PALETTE_CSS + """
*{box-sizing:border-box}
[hidden]{display:none !important}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.62 ui-serif,Charter,"Iowan Old Style",Georgia,serif;
  -webkit-font-smoothing:antialiased;}
.wrap{max-width:920px;margin:0 auto;padding:40px 22px 120px}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}

.mast{border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:26px}
.eyebrow{font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.18em;
  text-transform:uppercase;color:var(--accent);margin-bottom:14px}
h1{font-size:clamp(26px,4.4vw,40px);line-height:1.16;margin:0 0 6px;letter-spacing:-.015em;font-weight:600}
h1 .arrow{color:var(--muted);font-weight:400}
.sub{color:var(--muted);font-size:15px;margin:8px 0 0}

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

.turn{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  box-shadow:var(--shadow);margin:0 0 26px;overflow:hidden}
.turn.caller{border-left:4px solid var(--caller)}
.turn.agent{border-left:4px solid var(--agent)}
.turnhead{display:flex;align-items:center;gap:12px;padding:16px 22px;border-bottom:1px solid var(--line)}
.turn.caller .turnhead{background:var(--caller-bg)}
.turn.agent .turnhead{background:var(--agent-bg)}
.av{width:34px;height:34px;border-radius:9px;display:grid;place-items:center;flex:0 0 auto;
  font:600 14px/1 ui-sans-serif,system-ui,sans-serif;color:#fff}
.turn.caller .av{background:var(--caller)}
.turn.agent .av{background:var(--agent)}
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

.prompt{font-size:15.5px}
.prompt p:first-child strong{font-size:1.05em}
.expansion{margin-top:18px;border-top:1px dotted var(--line);padding-top:12px}
.expansion > summary{cursor:pointer;list-style:none;font:12px/1.4 ui-sans-serif,system-ui,sans-serif;
  color:var(--muted)}
.expansion > summary::-webkit-details-marker{display:none}
.expansion > summary::before{content:"+ ";font-family:ui-monospace,monospace}
.expansion[open] > summary::before{content:"\\2212 "}

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
/* Every row, expandable or not, is the same six columns:
   arrow | time | badge | tool | label + sub-label | duration.
   The widths are fixed so the columns line up down the whole log. */
.ev > summary,.ev.say > .row{display:grid;
  grid-template-columns:12px 60px 96px 104px minmax(0,1fr) 62px;
  column-gap:11px;align-items:baseline;padding:11px 24px 11px 20px;font-size:13.5px}
.ev > summary{cursor:pointer;list-style:none}
.ev > summary::-webkit-details-marker{display:none}
.ev > summary:hover{background:var(--code-bg)}
.ev > summary::before{content:"\\25B8";color:var(--muted);font:13px/1 ui-monospace,monospace;
  display:inline-block;transform-origin:50% 55%;transition:transform .15s ease}
.ev[open] > summary::before{transform:rotate(90deg)}
.ev[open] > summary{background:var(--code-bg)}
.ev.say > .row::before{content:""}
.evtime{font:11px/1.5 ui-monospace,monospace;color:var(--muted)}
.badge{display:inline-block;width:100%;text-align:center;font:600 10px/1 ui-sans-serif,system-ui,sans-serif;
  letter-spacing:.09em;padding:4px 0;border-radius:5px;border:1px solid transparent;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k-shell{background:var(--code-bg);color:var(--ink);border-color:var(--line)}
.k-read{background:var(--agent-bg);color:var(--agent);border-color:var(--agent-line)}
.k-write{background:var(--code-bg);color:var(--accent);border-color:var(--line)}
.k-tools{background:var(--code-bg);color:var(--muted);border-color:var(--line)}
.k-external{background:var(--caller-bg);color:var(--caller);border-color:var(--caller-line)}
.k-task{background:var(--caller-bg);color:var(--caller);border-color:var(--caller-line)}
.k-tool{background:var(--code-bg);color:var(--muted);border-color:var(--line)}
.k-think{background:transparent;color:var(--muted);border:1px dashed var(--line)}
.k-say{background:transparent;color:var(--agent);border:1px dashed var(--agent-line)}
.evtool{font:11.5px/1.5 ui-monospace,monospace;color:var(--muted);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;min-width:0}
.evmain{min-width:0}
.evtitle{font-weight:550;min-width:0;overflow-wrap:anywhere}
.evmeta{color:var(--muted);font-size:12px;min-width:0;overflow-wrap:anywhere;margin-left:9px}
.evdur{font:11px/1.5 ui-monospace,monospace;color:var(--muted);text-align:right;
  font-variant-numeric:tabular-nums;white-space:nowrap}
@media(max-width:640px){.evmeta{display:none}
  .ev > summary,.ev.say > .row{grid-template-columns:12px 60px 96px minmax(0,1fr) 62px}
  .evtool{display:none}}
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

.saybubble{border-left:3px solid var(--agent);padding-left:14px;color:var(--ink);
  font:italic 14px/1.6 ui-serif,Charter,Georgia,serif}
.saybubble p{margin:0}
.saybubble > :last-child{margin-bottom:0}

.replybar{display:flex;align-items:center;gap:11px;padding:14px 24px;
  background:var(--agent-bg);border-top:1px solid var(--agent-line);border-bottom:1px solid var(--agent-line);
  font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.11em;text-transform:uppercase;
  color:var(--agent)}
.replybar .dot{width:7px;height:7px;border-radius:50%;background:var(--agent);flex:0 0 auto}
.replybar .thin{margin-left:auto;font-weight:400;letter-spacing:.02em;text-transform:none;
  font-size:12px;color:var(--muted)}

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


# ------------------------------------------------------------- the work log

#: Per-result display cap. Generous, because the point of the page is that the
#: output is verbatim, but not unbounded.
RESULT_CAP = 200000


def _badge(kind):
    return "<span class='badge k-%s'>%s %s</span>" % (
        kind.lower(), ICON.get(kind, ICON["TOOL"]), kind,
    )


def render_events(session):
    """The work log: one row per event, six columns each. See the CSS."""
    out = []
    for event in session.events:
        when = _clock(session._local(event.timestamp))
        took = step_duration(event.duration)

        if event.kind == "say":
            # Narration is not expandable (the bubble IS the content), but it
            # is laid out on the same grid so its columns line up with the
            # rows around it. The empty first cell is where the arrow goes.
            out.append(
                "<div class='ev say'><div class='row'>"
                "<div class='evtime'>%s</div>%s<span class='evtool'></span>"
                "<div class='evmain'><div class='saybubble'>%s</div></div>"
                "<span class='evdur'>%s</span></div></div>"
                % (when, _badge("SAY"), md.render(event.text or ""), took)
            )

        elif event.kind == "thinking":
            out.append(
                "<details class='ev think'><summary><div class='evtime'>%s</div>"
                "%s<span class='evtool'></span>"
                "<span class='evmain'><span class='evtitle'>Reasoned privately</span>"
                "<span class='evmeta'>%s reasoning tokens this step</span></span>"
                "<span class='evdur'>%s</span></summary>"
                "<div class='evdetail'><p class='note'>Extended thinking is not retained in "
                "plaintext in the transcript. Claude Code stores only the signed, encrypted "
                "block, so the token count and its cryptographic signature are all that "
                "survive on disk. The reasoning text is not recoverable from this file.</p>"
                "%s</div></details>"
                % (
                    when,
                    _badge("THINK"),
                    "{:,}".format(event.reasoning_tokens),
                    took,
                    _kv("signature", (event.signature or "")[:96] + "…")
                    if event.signature else "",
                )
            )

        else:
            kind, title, verb, detail = humanize(event.tool_name, event.tool_input)
            result = event.result or ""
            body, cut = _truncate(result, RESULT_CAP)
            cutnote = "<p class='note'>Output truncated for display.</p>" if cut else ""

            if md.is_markdown_result(event.tool_name, event.tool_input, result):
                # Preview is the default. When a result is markdown, the rendered
                # form is the one a reader can actually use; the raw text is one
                # click away for anyone checking it was not massaged. Both panes
                # still ship pre-rendered, so this only changes which starts
                # visible.
                seg = (
                    "<span class='seg'>"
                    "<button class='segbtn' data-view=\"raw\">Raw</button>"
                    "<button class='segbtn on' data-view=\"md\">Preview</button></span>"
                )
                pane = (
                    '<pre class="result" data-pane="raw" hidden><code>%s</code></pre>'
                    '<div class="result mdpane" data-pane="md">%s</div>'
                    % (body, md.preview_html(result))
                )
            else:
                seg = ""
                pane = '<pre class="result" data-pane="raw"><code>%s</code></pre>' % body

            out.append(
                "<details class='ev tool'><summary>"
                "<div class='evtime'>%s</div>"
                "%s"
                "<span class='evtool' title='%s'>%s</span>"
                "<span class='evmain'><span class='evtitle'>%s</span>"
                "<span class='evmeta'>%s</span></span>"
                "<span class='evdur'>%s</span></summary>"
                "<div class='evdetail'>%s"
                "<div class='reslabel'>Result%s%s</div>"
                "%s%s</div></details>"
                % (
                    when,
                    _badge(kind),
                    html.escape(event.tool_name or "?", quote=True),
                    html.escape(tool_short_name(event.tool_name)),
                    html.escape(title),
                    html.escape(verb),
                    took,
                    detail,
                    " · error" if event.is_error else "",
                    seg,
                    pane,
                    cutnote,
                )
            )
    return "".join(out)


# ------------------------------------------------------------------ the page

def page(session, from_name="scott", to_name=None, channel=None):
    """Render `session` to a complete HTML document."""
    to_name = to_name or session.agent_name or "agent"
    breakdown = cost_module.compute(session.usage.tokens, session.model or "claude-opus-5")

    started = session.started_at_local
    ended = session.ended_at_local
    effects = session.side_effects

    if channel is None:
        channel = {
            "sdk-cli": "<code>claude -p</code> · non-interactive SDK session",
            "cli": "<code>claude</code> · interactive session",
        }.get(session.entrypoint, html.escape(str(session.entrypoint or "unknown")))

    title_text = "Conversation Audit Log: %s to %s on %s" % (
        from_name, to_name, started.strftime("%Y-%m-%d at %H:%M") if started else "an unknown date",
    )

    meta_rows = [("Channel", channel)]
    if session.cwd:
        branch = " on <code>%s</code>" % html.escape(session.git_branch) \
            if session.git_branch else ""
        meta_rows.append(("Repo", "<code>%s</code>%s" % (html.escape(session.cwd), branch)))
    if session.session_id:
        meta_rows.append(("Session", "<code>%s</code>" % html.escape(session.session_id)))
    model_bits = provider_and_model(session.model)
    if session.effort:
        model_bits += " · effort <code>%s</code>" % html.escape(session.effort)
    if session.cli_version:
        model_bits += " · CLI %s" % html.escape(session.cli_version)
    meta_rows.append(("Model", model_bits))
    if session.permission_mode:
        meta_rows.append(
            ("Permissions", "<code>%s</code>" % html.escape(session.permission_mode))
        )

    priced = breakdown.priced
    stats = [
        (_duration_words(session.duration), "wall clock", None),
        ("{:,}".format(session.tool_count), "tool calls", None),
        ("{:,}".format(breakdown.input_tokens_total), "input tokens",
         usd(breakdown.input_side) if priced else None),
        ("{:,}".format(session.usage.tokens["output"]), "output tokens",
         usd(breakdown.output) if priced else None),
        ("{:,}".format(session.usage.tokens["reasoning"]), "reasoning tokens",
         usd(breakdown.reasoning) + ", of the output" if priced else "of the output"),
        (usd(breakdown.total) if priced else "n/a",
         "total, list price" if priced else "no list price", None),
        ("{:,}".format(effects.commits),
         "git commit" if effects.commits == 1 else "git commits", None),
        ("{:,}".format(effects.external_calls),
         "external API call" if effects.external_calls == 1 else "external API calls", None),
    ]

    cost_rows = "".join(
        '<tr><td>%s</td><td class="num">%s</td><td class="num">$%.2f</td>'
        '<td class="num">%s</td></tr>'
        % (html.escape(label), "{:,}".format(tokens), rate, usd(amount))
        for label, tokens, rate, amount in breakdown.as_rows()
    )

    cost_note = """
<details class="costnote">
  <summary>Estimated at <strong>%(total)s</strong> &mdash; how that is calculated</summary>
  <div class="costbody">
    <p>This session ran on a Claude subscription, so <strong>nothing was billed per
       token</strong>. The figure is what the identical traffic would cost through the
       public API at <code>%(model)s</code> list rates, checked %(verified)s. Cache writes
       bill at a multiple of base input and cache reads at 0.1&times;.</p>
    <div class="tablewrap"><table><thead><tr>
      <th>Component</th><th>Tokens</th><th>Rate / Mtok</th><th>Cost</th>
    </tr></thead><tbody>
      %(rows)s
      <tr class="total"><td>Total</td><td class="num">%(alltokens)s</td><td></td>
          <td class="num">%(total)s</td></tr>
    </tbody></table></div>
    <p class="note">Reasoning tokens are a subset of output tokens, not a separate line
       item, so the %(reasoning)s shown on that tile is already inside the %(output)s of
       output. The tiles are therefore not meant to sum to the total.</p>
  </div>
</details>
""" % {
        "total": usd(breakdown.total),
        "model": html.escape(session.model or "unknown"),
        "verified": cost_module.table_verified_on(),
        "rows": cost_rows,
        "alltokens": "{:,}".format(
            breakdown.input_tokens_total + session.usage.tokens["output"]
        ),
        "reasoning": usd(breakdown.reasoning),
        "output": usd(breakdown.output),
    }

    if not priced:
        # A local Ollama model, a routed non-Anthropic backend, or the harness's
        # own synthetic messages. The token counts are real; there is simply no
        # list price to convert them with, and inventing one would be worse than
        # showing none.
        cost_note = """
<details class="costnote">
  <summary>No cost figure for this session &mdash; why</summary>
  <div class="costbody">
    <p>This session ran on <code>%(model)s</code>, which %(reason)s. The token
       counts in the tiles above were read from the transcript and are real.
       There is no published per-token price to convert them with, so this page
       shows no dollar figure rather than a made-up one.</p>
  </div>
</details>
""" % {
            "model": html.escape(session.model or "an unknown model"),
            "reason": html.escape(breakdown.unpriced_reason or "has no list price"),
        }

    prompt_body = md.render(session.opening.text if session.opening else "")
    if session.opening and session.opening.expanded_text:
        prompt_body += (
            "<details class='expansion'><summary>Show the expanded command body "
            "that %s actually received</summary>%s</details>"
            % (html.escape(to_name), md.render(session.opening.expanded_text))
        )

    side_effects = "<ul>%s</ul>" % "".join(
        "<li>%s</li>" % html.escape(line) for line in effects.summary_lines()
    )

    where = ""
    if session.cwd:
        where = " · ran in <code>%s</code>" % html.escape(session.cwd)

    document = """<!doctype html>
<!-- audit-agent-conversation session:%(session_id)s -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>%(css)s</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <div class="eyebrow">Conversation Audit Log</div>
    <h1>%(from_name)s <span class="arrow">&rarr;</span> %(to_name)s</h1>
    <p class="sub">%(datestamp)s &middot; one agent-to-agent exchange, captured end to end</p>
  </header>

  <div class="meta">
    %(meta)s
  </div>

  <div class="stats">
    %(stats)s
  </div>

  %(costnote)s

  <section class="turn caller">
    <div class="turnhead">
      <div class="av">%(from_initial)s</div>
      <div class="who">%(from_name)s<small>Initiated the exchange and waited on the reply</small></div>
      <div class="stamp">%(start)s</div>
    </div>
    <div class="turnbody prompt">%(prompt)s</div>
  </section>

  <section class="turn agent"%(agentstyle)s>
    <div class="turnhead">
      <div class="av">%(to_initial)s</div>
      <div class="who">%(to_name)s<small>Did the work%(where)s</small></div>
      <div class="stamp">%(start)s &rarr; %(end)s<br>%(duration)s</div>
    </div>

    <div class="runhead workhidden" id="runhead">
      <span class="lbl">Work log</span>
      <span class="runsum">%(tools)s tool calls &middot; %(reasoning_steps)s reasoning steps
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
      %(events)s
    </div>

    <div class="replybar">
      <span class="dot"></span>
      Reply returned to %(from_name)s
      <span class="thin">%(end)s &middot; %(words)s words</span>
    </div>

    <div class="turnbody">%(reply)s</div>
  </section>

  <section class="fx">
    <h2>Side effects on the real world</h2>
    %(effects)s
  </section>

  <footer>
    Rendered from the raw Claude Code transcript <code>%(basename)s</code>.
    Nothing in the dialog or the work log is paraphrased; tool calls carry a plain-English
    label but the commands and their output are verbatim. Reasoning steps are listed because
    the transcript records their token counts, but extended thinking is stored encrypted, so
    no agent's inner monologue is recoverable here. Every figure on this page is derived from
    the transcript itself.
  </footer>

</div>
<script>%(js)s</script>
</body>
</html>
""" % {
        "session_id": html.escape(session.session_id or ""),
        "title": html.escape(title_text),
        "css": CSS,
        "js": JS,
        "from_name": html.escape(from_name),
        "to_name": html.escape(to_name),
        "from_initial": html.escape(_initial(from_name)),
        "to_initial": html.escape(_initial(to_name)),
        "datestamp": started.strftime("%A, %B %d, %Y at %I:%M %p Pacific").replace(" 0", " ")
        if started else "date unknown",
        "meta": "".join(
            "<div><b>%s</b><span>%s</span></div>" % (html.escape(k), v)
            for k, v in meta_rows
        ),
        "stats": "".join(
            '<div class="stat"><b>%s</b><span>%s</span>%s</div>'
            % (value, label, "<i>&asymp; %s</i>" % sub if sub else "")
            for value, label, sub in stats
        ),
        "costnote": cost_note,
        "prompt": prompt_body,
        "start": _clock(started) + " PT" if started else "unknown",
        "end": _clock(ended) + " PT" if ended else "unknown",
        "duration": _duration_words(session.duration),
        "tools": "{:,}".format(session.tool_count),
        "reasoning_steps": "{:,}".format(session.reasoning_steps),
        "events": render_events(session),
        "words": "{:,}".format(len(session.reply.split())),
        "reply": md.render(session.reply),
        "effects": side_effects,
        "basename": html.escape(os.path.basename(session.path or "")),
        "where": where,
        "agentstyle": agent_color_style(session.agent_color),
    }
    return document

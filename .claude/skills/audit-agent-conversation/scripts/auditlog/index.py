"""An index of every conversation there is to render, not just those rendered.

Scans the project directories, lists every session across the fleet newest
first, marks each row generated or not, links the generated ones to their
page, and gives an ungenerated renderable row the exact command that would
produce it, with a copy button. Sessions v1 cannot render are listed too, with
the reason, because "what exists" includes them and an index that quietly
omitted half the corpus would be answering a smaller question.

Deliberately not a web app. Nothing on the page executes anything: the copy
button is a clipboard write, and the generating happens in a session the user
drives. The page is a static file with no server, no auth, and no path from
itself back to the transcript store. A row that generates itself on click is a
different product and is parked.

The same rules as every other page: one file, zero external requests, no
model call, byte-reproducible from the same inputs (so no clock on the page).
"""

import html
import os

from . import cli, render

#: The first line of every index this tool writes. A rebuild recognises its
#: own previous output by it, and refuses to replace a file that lacks it
#: without --force: the index is derived and refreshing it is the point, but
#: someone else's index.html is not ours to overwrite.
MARKER = "<!-- audit-agent-conversation index -->"

#: The index's filename inside the output directory.
FILENAME = "index.html"


class Entry(object):
    """One session as the index sees it."""

    __slots__ = ("path", "project", "description", "reasons", "sender",
                 "receiver", "page")

    def __init__(self, path, project, description, reasons, sender, receiver,
                 page):
        self.path = path
        #: The project directory's basename, which is what `--project` takes.
        self.project = project
        self.description = description
        self.reasons = reasons
        self.sender = sender
        self.receiver = receiver
        #: The page's filename relative to the output directory, or None.
        self.page = page

    @property
    def renderable(self):
        return not self.reasons

    @property
    def reason(self):
        """Why v1 refuses this session, in a few words, or "" if it does not."""
        if self.renderable:
            return ""
        return cli.reason_text(self.description, self.reasons)

    @property
    def command(self):
        """The command that would produce this page, or None.

        Only for a renderable session that has no page yet. Names the session
        by its full id and the project by its exact directory name, so the
        command cannot resolve to a neighbour.
        """
        if not self.renderable or self.page:
            return None
        return "audit-agent-conversation %s --project %s" % (
            self.description.session_id, self.project,
        )


def pages_by_session(output_dir):
    """Map session id to page filename, for every page in `output_dir`.

    Uses the marker each page declares itself with, not the filename: names
    carry no session id (decision A2), and two sessions can share one name.
    """
    found = {}
    if not os.path.isdir(output_dir):
        return found
    for name in sorted(os.listdir(output_dir)):
        if not name.endswith(".html") or name == FILENAME:
            continue
        session_id = cli.page_session_id(os.path.join(output_dir, name))
        if session_id and session_id not in found:
            found[session_id] = name
    return found


def scan(args, output_dir):
    """Every session in scope as an `Entry`, newest first.

    Scope is whatever `--project` and the time window say, exactly as for a
    sweep, and with neither it is every project. Reads transcripts and the
    output directory; writes nothing.
    """
    candidates = cli.sweep_candidates(args)
    pages = pages_by_session(output_dir)
    entries = []
    for candidate in candidates:
        report, description = cli.classify(candidate)
        sender, receiver = cli.participants_of(description)
        project = os.path.basename(os.path.dirname(candidate))
        entries.append(Entry(
            candidate, project, description, report.reasons, sender, receiver,
            pages.get(description.session_id),
        ))
    # A timeline of conversations, not of file writes: newest START first.
    # `sweep_candidates` orders by mtime, which is when a transcript was last
    # touched, and a long-running session's file keeps changing after it
    # started. mtime only breaks ties (and orders anything undated).
    order = {id(e): i for i, e in enumerate(entries)}
    entries.sort(key=lambda e: (
        e.description.started.timestamp() if e.description.started else float("-inf"),
        -order[id(e)],
    ), reverse=True)
    return entries


# ------------------------------------------------------------------ the page

CSS = render.PALETTE_CSS + """
*{box-sizing:border-box}
[hidden]{display:none !important}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:36px 22px 120px}
code,pre{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace}
.mast{border-bottom:2px solid var(--ink);padding-bottom:16px;margin-bottom:18px}
.eyebrow{font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.18em;
  text-transform:uppercase;color:var(--accent);margin-bottom:12px}
h1{font:600 clamp(24px,4vw,34px)/1.15 ui-serif,Charter,Georgia,serif;margin:0 0 6px;letter-spacing:-.015em}
.sub{color:var(--muted);font-size:14px;margin:6px 0 0}
.sub code{font-size:12px;background:var(--code-bg);padding:1px 5px;border-radius:4px;color:var(--code-ink)}

.tools{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;margin:0 0 14px;
  font-size:13px;color:var(--muted)}
.tools input[type=search]{font:14px ui-sans-serif,system-ui,sans-serif;padding:7px 11px;
  border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);
  min-width:260px}
.tools label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
.tally{margin-left:auto;font-variant-numeric:tabular-nums}
.tally b{color:var(--ink);font-weight:600}

.day{font:600 11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);margin:26px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.day:first-of-type{margin-top:8px}

.ix{border-bottom:1px solid var(--line)}
.ix > .row,.ix > summary{display:grid;
  grid-template-columns:12px 52px 84px 200px minmax(0,1fr) 230px;
  column-gap:12px;align-items:baseline;padding:9px 6px 9px 4px;font-size:13.5px}
.ix > summary{cursor:pointer;list-style:none}
.ix > summary::-webkit-details-marker{display:none}
.ix > summary:hover,.ix.gen > .row:hover{background:var(--code-bg)}
.ix > summary::before{content:"\\25B8";color:var(--muted);font:13px/1 ui-monospace,monospace;
  display:inline-block;transform-origin:50% 55%;transition:transform .15s ease}
.ix[open] > summary::before{transform:rotate(90deg)}
.ix[open] > summary{background:var(--code-bg)}
.ix > .row::before{content:""}
.when{font:11px/1.5 ui-monospace,monospace;color:var(--muted)}
.mark{display:inline-block;width:100%;text-align:center;font:600 10px/1 ui-sans-serif,system-ui,sans-serif;
  letter-spacing:.09em;padding:4px 0;border-radius:5px;border:1px solid transparent;white-space:nowrap}
.m-page{background:var(--agent-bg);color:var(--agent);border-color:var(--agent-line)}
.m-todo{background:var(--code-bg);color:var(--accent);border-color:var(--line)}
.m-no{background:transparent;color:var(--muted);border:1px dashed var(--line)}
.pair{font-size:12.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.pair b{color:var(--ink);font-weight:550}
.pair .arr{padding:0 4px}
.subj{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.subj a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--agent-line)}
.subj a:hover{border-bottom-color:var(--agent)}
.ix.no .subj{color:var(--muted)}
.why{font-size:12px;color:var(--muted);text-align:right;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;font-variant-numeric:tabular-nums}
.why code{font-size:11px;color:var(--muted)}
.how{padding:6px 6px 16px 78px;font-size:13px;color:var(--muted)}
.how p{margin:0 0 8px}
.cmd{display:flex;gap:10px;align-items:center;background:var(--code-bg);border:1px solid var(--line);
  border-radius:8px;padding:8px 10px 8px 12px}
.cmd code{flex:1 1 auto;min-width:0;overflow-wrap:anywhere;font-size:12.5px;color:var(--code-ink)}
button{font:11px/1 ui-sans-serif,system-ui,sans-serif;letter-spacing:.05em;text-transform:uppercase;
  background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;
  padding:6px 12px;cursor:pointer;flex:0 0 auto}
button:hover{border-color:var(--muted)}
button.done{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.empty{padding:40px 0;color:var(--muted);text-align:center;font-style:italic}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);
  font:12px/1.7 ui-sans-serif,system-ui,sans-serif;color:var(--muted)}
footer code{font-size:11px}
@media(max-width:760px){
  .ix > .row,.ix > summary{grid-template-columns:12px 52px 84px minmax(0,1fr) 110px}
  .pair{display:none}
  .how{padding-left:20px}
}
"""

JS = """
// Copy the command for an ungenerated row. A clipboard write and nothing
// else: the page never runs a command, and never touches the transcript store.
document.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-copy]');
  if (!btn) return;
  e.preventDefault();
  const text = btn.dataset.copy;
  const done = () => {
    btn.textContent = 'Copied';
    btn.classList.add('done');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('done'); }, 1400);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, () => fallback(text, done));
  } else {
    fallback(text, done);
  }
});
function fallback(text, done) {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed'; area.style.top = '-1000px';
  document.body.appendChild(area);
  area.select();
  try { document.execCommand('copy'); done(); } catch (err) {}
  document.body.removeChild(area);
}

// Filter rows by text, and optionally hide the ones v1 cannot render.
const q = document.getElementById('q');
const hideNo = document.getElementById('hideno');
const rows = Array.from(document.querySelectorAll('.ix'));
const days = Array.from(document.querySelectorAll('.day'));
const shown = document.getElementById('shown');
function apply() {
  const needle = (q.value || '').trim().toLowerCase();
  let visible = 0;
  rows.forEach(r => {
    const hit = !needle || (r.dataset.text || '').includes(needle);
    const ok = hit && !(hideNo.checked && r.classList.contains('no'));
    r.hidden = !ok;
    if (ok) visible++;
  });
  days.forEach(d => {
    let el = d.nextElementSibling, any = false;
    while (el && !el.classList.contains('day')) {
      if (!el.hidden) { any = true; break; }
      el = el.nextElementSibling;
    }
    d.hidden = !any;
  });
  shown.textContent = visible;
}
q.addEventListener('input', apply);
hideNo.addEventListener('change', apply);
apply();
"""


def _mark(kind, text):
    return "<span class='mark m-%s'>%s</span>" % (kind, text)


def _row(entry, output_dir):
    """One row. Generated rows link; ungenerated renderable rows expand to the
    command; unsupported rows say why and stay closed."""
    d = entry.description
    when = html.escape(cli.when_of(d)[6:] if d.started else "--:--")
    title = html.escape(d.title or "(untitled)")
    pair = ("<span class='pair'><b>%s</b><span class='arr'>&rarr;</span><b>%s</b></span>"
            % (html.escape(entry.sender), html.escape(entry.receiver)))
    ident = html.escape(d.short_id)
    text = " ".join(x for x in (
        d.title or "", entry.sender, entry.receiver, entry.project, d.session_id or "",
        entry.reason, "page" if entry.page else "",
    ) if x).lower()
    data_text = html.escape(text, quote=True)

    if entry.page:
        href = html.escape(entry.page, quote=True)
        return (
            "<div class='ix gen' data-text=\"%s\"><div class='row'>"
            "<span class='when'>%s</span>%s%s"
            "<span class='subj'><a href=\"%s\">%s</a></span>"
            "<span class='why'><code>%s</code></span></div></div>"
            % (data_text, when, _mark("page", "PAGE"), pair, href, title, ident)
        )

    if entry.renderable:
        command = entry.command
        return (
            "<details class='ix todo' data-text=\"%s\"><summary>"
            "<span class='when'>%s</span>%s%s"
            "<span class='subj'>%s</span>"
            "<span class='why'>not generated &middot; <code>%s</code></span></summary>"
            "<div class='how'>"
            "<p>Run this in a terminal, or paste it into a Claude session, then "
            "rebuild the index with <code>audit-agent-conversation --index</code> "
            "and this row becomes a link.</p>"
            "<div class='cmd'><code>%s</code>"
            "<button type='button' data-copy=\"%s\">Copy</button></div>"
            "</div></details>"
            % (data_text, when, _mark("todo", "TO DO"), pair, title, ident,
               html.escape(command), html.escape(command, quote=True))
        )

    return (
        "<div class='ix no' data-text=\"%s\"><div class='row'>"
        "<span class='when'>%s</span>%s%s"
        "<span class='subj'>%s</span>"
        "<span class='why'>%s &middot; <code>%s</code></span></div></div>"
        % (data_text, when, _mark("no", "V1 CAN'T"), pair, title,
           html.escape(entry.reason), ident)
    )


def _day_of(entry):
    d = entry.description
    if not d.started:
        return "Undated"
    from . import parse

    local = d.started.astimezone(parse.local_timezone())
    return local.strftime("%A, %B %d, %Y").replace(" 0", " ")


def page(entries, output_dir):
    """The whole index as one HTML document."""
    rows = []
    last_day = None
    for entry in entries:
        day = _day_of(entry)
        if day != last_day:
            rows.append("<div class='day'>%s</div>" % html.escape(day))
            last_day = day
        rows.append(_row(entry, output_dir))
    if not entries:
        rows.append("<div class='empty'>No sessions in scope.</div>")

    total = len(entries)
    with_pages = sum(1 for e in entries if e.page)
    todo = sum(1 for e in entries if e.renderable and not e.page)
    cannot = sum(1 for e in entries if not e.renderable)
    projects = len(set(e.project for e in entries))

    return """<!doctype html>
%(marker)s
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conversation Audit Log: index</title>
<style>%(css)s</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <div class="eyebrow">Conversation Audit Log</div>
    <h1>Every conversation there is to render</h1>
    <p class="sub">%(total)s sessions across %(projects)s projects, newest first.
      <b>%(with_pages)s</b> have a page, <b>%(todo)s</b> could be rendered and are not yet,
      <b>%(cannot)s</b> are ones v1 cannot render. Pages live beside this file in
      <code>%(outdir)s</code>.</p>
  </header>

  <div class="tools">
    <input id="q" type="search" placeholder="Filter by title, agent, project, or session id" autocomplete="off">
    <label><input id="hideno" type="checkbox"> hide the ones v1 cannot render</label>
    <span class="tally"><b id="shown">%(total)s</b> shown</span>
  </div>

  %(rows)s

  <footer>
    Built by <code>audit-agent-conversation --index</code> from the transcript store and
    the pages already in this directory. It reflects both as of when it was last built;
    rebuild it to refresh. Nothing on this page runs anything: the copy button writes a
    command to the clipboard, and the rendering happens in a session you drive.
  </footer>

</div>
<script>%(js)s</script>
</body>
</html>
""" % {
        "marker": MARKER,
        "css": CSS,
        "js": JS,
        "total": "{:,}".format(total),
        "projects": "{:,}".format(projects),
        "with_pages": "{:,}".format(with_pages),
        "todo": "{:,}".format(todo),
        "cannot": "{:,}".format(cannot),
        "outdir": html.escape(cli.tilde(os.path.abspath(output_dir))),
        "rows": "\n  ".join(rows),
    }

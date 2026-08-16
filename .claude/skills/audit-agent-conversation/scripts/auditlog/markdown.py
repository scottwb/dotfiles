"""A small stdlib markdown renderer, ported from the prototype.

Deliberately not a general-purpose markdown implementation. It handles what
Claude Code transcripts actually contain, including two shapes a conventional
parser gets wrong for this input:

* **Headerless pipe-row runs.** `grep` fragments of a markdown table arrive as
  bare pipe rows with no delimiter row. A strict parser renders them as
  paragraphs full of pipes; here they become a real table.
* **Escaped pipes inside cells.** `\\|` inside a cell must not split it.

It also strips the line-number prefixes that `Read` and `grep -n` add, and
resolves Obsidian wikilinks the way the vault reads them, both of which are what
make a tracker-file read legible in preview mode.

Everything is escaped before any substitution runs: tool output is untrusted
text and must never inject markup into the page.
"""

import html
import os
import re


# ------------------------------------------------------------------- links

#: The only URL schemes allowed to become a clickable `href`.
#:
#: Escaping the URL stops an attacker breaking out of the attribute, but it does
#: NOT stop a `javascript:` URL: the browser decodes the entities back before
#: navigating, so `href="javascript:alert(&#x27;x&#x27;)"` executes on click.
#: Transcript content is untrusted (it came from web pages, file contents, and
#: command output), and this page's whole value is being a trustworthy record,
#: so a record that executes when opened is exactly the wrong failure.
SAFE_URL_SCHEMES = frozenset(["http", "https", "mailto"])

_HAS_SCHEME = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):")


def is_safe_url(url):
    """Is `url` safe to put in an href?

    Judges the URL as the BROWSER will see it, which means undoing the two
    things an attacker can hide a scheme behind:

    * HTML entities, because the renderer escapes before this runs and the
      browser decodes after (`&#106;avascript:` is `javascript:`).
    * Leading whitespace and control characters, which browsers strip
      (`java\\tscript:` is `javascript:`).

    A URL with no scheme at all is relative or an anchor, and is allowed.
    """
    if url is None:
        return False

    candidate = html.unescape(url)
    # Strip everything a browser ignores, anywhere before the colon.
    candidate = re.sub(r"[\x00-\x20\x7f]", "", candidate)

    match = _HAS_SCHEME.match(candidate)
    if not match:
        return True  # relative path or fragment
    return match.group(1).lower() in SAFE_URL_SCHEMES


# ------------------------------------------------------------------ inline

#: Sentinel used to park code spans while inline markup is substituted. NUL is
#: stripped from the input first (see `_inline`), so this cannot collide with
#: anything a transcript contains.
_STASH = "\x00%d\x00"
_STASH_RE = re.compile(r"\x00(\d+)\x00")


def _link(match):
    label, url = match.group(1), match.group(2)
    if is_safe_url(url):
        return '<a href="%s">%s</a>' % (url, label)
    # Refuse the link, but keep both halves visible. An audit log must not
    # silently delete evidence just because it declined to make it clickable.
    return "%s (<code>%s</code>)" % (label, url)


def _inline(text):
    # NUL has no legitimate place in rendered text, and removing it here is what
    # makes the code-span sentinel below uncollidable.
    text = text.replace("\x00", "")
    text = html.escape(text)

    # Stash code spans first so their contents are not further parsed.
    stash = []

    def keep(match):
        stash.append(match.group(1))
        return _STASH % (len(stash) - 1)

    def restore(match):
        index = int(match.group(1))
        if 0 <= index < len(stash):
            return "<code>%s</code>" % stash[index]
        return match.group(0)  # not ours; leave it alone

    text = re.sub(r"`([^`]+)`", keep, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
    text = _STASH_RE.sub(restore, text)
    return text


# ------------------------------------------------------------------- tables

def _cells(row):
    """Split a table row on unescaped pipes, then unescape."""
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    parts = re.split(r"(?<!\\)\|", stripped)
    return [p.strip().replace("\\|", "|") for p in parts]


def _is_delimiter_row(line):
    return bool(re.match(r"^\s*\|[\s:|-]+\|\s*$", line))


def _table(head, rows):
    widths = [len(r) for r in rows]
    if head:
        widths.append(len(head))
    width = max(widths) if widths else 1

    out = ["<div class='tablewrap'><table>"]
    if head:
        out.append(
            "<thead><tr>"
            + "".join("<th>%s</th>" % _inline(c) for c in head)
            + "</tr></thead>"
        )
    out.append("<tbody>")
    for row in rows:
        padded = row + [""] * (width - len(row))
        out.append(
            "<tr>" + "".join("<td>%s</td>" % _inline(c) for c in padded) + "</tr>"
        )
    out.append("</tbody></table></div>")
    return "".join(out)


# ---------------------------------------------------------------- wikilinks

def dewiki(text):
    """Render Obsidian syntax the way the vault reads it. Preview mode only."""
    text = re.sub(
        r"!\[\[([^\]]+?)\]\]",
        lambda m: "`\U0001f5bc %s`" % os.path.basename(
            re.split(r"\\?\|", m.group(1))[0]
        ),
        text,
    )
    text = re.sub(r"\[\[[^\]]*?\\?\|([^\]|]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", lambda m: os.path.basename(m.group(1)), text)
    return text


# ----------------------------------------------------------- line numbering

def strip_line_numbers(text):
    """Drop `Read`'s `   12\\t` prefixes and `grep -n`'s `12:` prefixes.

    Both must go before a markdown preview, or every line renders as prose with
    a number bolted to the front. Note the `12:` pattern is anchored to the
    start of the line and requires the digits to be the whole prefix, so prose
    like `note: a thing` is left alone.
    """
    out = []
    for line in text.split("\n"):
        match = re.match(r"^\s*\d+\t(.*)$", line)
        if match:
            out.append(match.group(1))
            continue
        match = re.match(r"^\d+:(.*)$", line)
        if match:
            out.append(match.group(1))
            continue
        out.append(line)
    return "\n".join(out)


# ------------------------------------------------------------------- blocks

def render(text):
    """Render markdown to HTML."""
    lines = text.split("\n")
    out = []
    para = []
    index = 0
    total = len(lines)

    def flush():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>")
            del para[:]

    while index < total:
        line = lines[index]

        if line.startswith("```"):
            flush()
            index += 1
            buf = []
            while index < total and not lines[index].startswith("```"):
                buf.append(lines[index])
                index += 1
            index += 1
            out.append(
                '<pre class="code"><code>%s</code></pre>'
                % html.escape("\n".join(buf))
            )
            continue

        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush()
            out.append("<hr>")
            index += 1
            continue

        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            flush()
            level = len(match.group(1))
            out.append(
                "<h%d class='md-h md-h%d'>%s</h%d>"
                % (level + 1, level, _inline(match.group(2)), level + 1)
            )
            index += 1
            continue

        # Table with a header row and a delimiter row.
        if (
            line.strip().startswith("|")
            and index + 1 < total
            and _is_delimiter_row(lines[index + 1])
        ):
            flush()
            head = _cells(line)
            index += 2
            rows = []
            while index < total and lines[index].strip().startswith("|"):
                rows.append(_cells(lines[index]))
                index += 1
            out.append(_table(head, rows))
            continue

        # Headerless table: a run of pipe rows with no delimiter, which is what
        # a grep fragment of a table looks like.
        if line.strip().startswith("|") and line.strip().endswith("|"):
            flush()
            rows = []
            while (
                index < total
                and lines[index].strip().startswith("|")
                and lines[index].strip().endswith("|")
            ):
                if _is_delimiter_row(lines[index]):
                    index += 1
                    continue
                rows.append(_cells(lines[index]))
                index += 1
            if rows:
                out.append(_table(None, rows))
            continue

        match = re.match(r"^\s*([-*+])\s+(.*)$", line)
        if match:
            flush()
            items = []
            while index < total:
                inner = re.match(r"^\s*([-*+])\s+(.*)$", lines[index])
                if not inner:
                    break
                body = [inner.group(2)]
                index += 1
                while (
                    index < total
                    and lines[index].strip()
                    and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[index])
                    and lines[index].startswith("  ")
                ):
                    body.append(lines[index].strip())
                    index += 1
                items.append(" ".join(body))
            out.append(
                "<ul>" + "".join("<li>%s</li>" % _inline(x) for x in items) + "</ul>"
            )
            continue

        match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if match:
            flush()
            start = match.group(1)
            items = []
            while index < total:
                inner = re.match(r"^\s*\d+\.\s+(.*)$", lines[index])
                if not inner:
                    break
                body = [inner.group(1)]
                index += 1
                while (
                    index < total
                    and lines[index].strip()
                    and not re.match(r"^\s*([-*+]|\d+\.)\s+", lines[index])
                    and lines[index].startswith("  ")
                ):
                    body.append(lines[index].strip())
                    index += 1
                items.append(" ".join(body))
            out.append(
                "<ol start='%s'>" % start
                + "".join("<li>%s</li>" % _inline(x) for x in items)
                + "</ol>"
            )
            continue

        if re.match(r"^\s*>\s?(.*)$", line):
            flush()
            buf = []
            while index < total and re.match(r"^\s*>", lines[index]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[index]))
                index += 1
            out.append("<blockquote>" + render("\n".join(buf)) + "</blockquote>")
            continue

        if not line.strip():
            flush()
            index += 1
            continue

        para.append(line)
        index += 1

    flush()
    return "".join(out)


def preview_html(text):
    """The rendered pane of a raw/preview toggle."""
    return render(dewiki(strip_line_numbers(text)))


# ------------------------------------------------- is this worth previewing?

#: Commands that read a file's contents out.
_READER = re.compile(r"\b(grep|sed|cat|head|tail|bat)\b")
#: A bare path argument ending in `.md`.
_MD_PATH = re.compile(r"(?:^|\s)[\w./-]+\.md\b")


def looks_like_markdown(text):
    body = strip_line_numbers(text).split("\n")
    if len(body) < 2:
        return False
    pipes = sum(1 for line in body if line.strip().startswith("|"))
    headings = sum(1 for line in body if re.match(r"^#{1,6}\s", line))
    bullets = sum(1 for line in body if re.match(r"^\s*[-*+]\s", line))
    return pipes >= 2 or headings >= 1 or bullets >= 2


def is_markdown_result(tool_name, tool_input, text):
    """Does this tool result deserve a rendered preview pane?

    Needs BOTH a command check and an output check. The command check alone
    false-positives: a `git commit` whose message contains the phrase "that head
    needs inspection" matches `\\bhead\\b`, and the reference session contains
    exactly that commit. The output check is what rejects it.
    """
    if not text or not text.strip():
        return False

    if tool_name in ("Read", "NotebookRead"):
        return str(tool_input.get("file_path", "")).endswith(".md")

    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        reads_md = bool(_READER.search(command)) and bool(_MD_PATH.search(command))
        return reads_md and looks_like_markdown(text)

    return False

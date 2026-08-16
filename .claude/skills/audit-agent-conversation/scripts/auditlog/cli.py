"""The `audit-agent-conversation` command line.

Writes a rendered page into `~/.ai-staff-audit-log/`, which is deliberately NOT
source controlled and NOT inside any repository. The directory is created when
missing and never deleted from, and an existing file is never overwritten
without `--force`.

An unsupported session exits non-zero with its reasons on stderr and writes
nothing at all. A half-rendered page that looks complete is worse than no page,
which is the whole basis of decision A7.
"""

import argparse
import errno
import json
import os
import re
import sys
import tempfile

from . import parse, render, resolve

#: Line prefixes, per the repo convention: green check for success, info "i"
#: for informational. Every line the tool prints starts with one, so a run reads
#: as a column of outcomes rather than a paragraph.
#: Every marker is a SINGLE codepoint with East Asian Width "W" and no
#: variation selector. That is the whole selection criterion, and it is not
#: decoration: a variation-selector emoji is Neutral width, so terminals
#: disagree about whether it occupies one cell or two, and a column of mixed
#: widths cannot be padded correctly for everyone at once. Two attempts to
#: pad around that failed in opposite directions before this rule replaced
#: them. `test_markers_cannot_break_alignment` enforces it.
#:
#: They are also all the same shape, so colour alone carries the outcome and
#: a long sweep can be scanned down the left edge.
OK = "\U0001F7E2 "          # green: a page was written
EXISTS = "\U0001F535 "      # blue: a page was already there
INFO = "\u26AA "            # white: a session was passed over
ERROR = "\U0001F534 "       # red: something failed

#: Row markers by outcome. WROTE produced a page, EXISTS found one already
#: there, SKIPPED passed a session over, ERROR failed.
MARKERS = {"WROTE": OK, "EXISTS": EXISTS, "SKIPPED": INFO, "ERROR": ERROR}

#: Output is laid out as fixed columns so the pipes line up and a run can be
#: scanned rather than read. Not a real table: no borders, no padding games,
#: just widths that add up.
LINE_WIDTH = 150
SEP = " | "
COL_STATUS = 7           # SKIPPED is the longest
COL_ID = 8               # the short session id everything else refers to
COL_WHEN = 11            # MM-DD HH:MM; the year is in the filename and the page
COL_DETAIL = 38          # why it was skipped, or the file that was written
COL_SENDER = 10          # senders are short: scott, donna, caller, FAW
COL_RECEIVER = 14        # receivers are repo names, which run longer
COL_SUBJECT = LINE_WIDTH - (
    2 + 1 + COL_STATUS + len(SEP) + COL_ID + len(SEP) + COL_WHEN + len(SEP)
    + COL_DETAIL + len(SEP) + COL_SENDER + len(SEP) + COL_RECEIVER + len(SEP)
)

#: Where rendered pages land. Decision A6, settled and not reopened.
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/.ai-staff-audit-log")

#: Keeps filenames comfortably inside every filesystem limit once the
#: timestamp and participant names are prepended.
SLUG_MAX = 60

_PARTICIPANTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "participants.json"
)
_participants = None


def _participant_config():
    global _participants
    if _participants is None:
        with open(_PARTICIPANTS_PATH) as handle:
            _participants = json.load(handle)
    return _participants


# ------------------------------------------------------------------ slugging

def slugify(text, fallback="session"):
    """A filename-safe slug: lowercase ASCII alphanumerics and single dashes."""
    if not text:
        return fallback
    text = text.strip().lower()
    # Drop a leading slash so "/exec-brief full" does not start with a dash.
    text = text.lstrip("/")
    # Anything that is not an ASCII alphanumeric becomes a separator. This also
    # keeps non-ASCII out of filenames rather than trusting the filesystem.
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if not text:
        return fallback
    if len(text) > SLUG_MAX:
        text = text[:SLUG_MAX].rstrip("-")
        # Avoid ending mid-word where a dash is close by.
        if "-" in text[-12:]:
            text = text[: text.rfind("-")]
    return text or fallback


# ------------------------------------------------------------- participants

def sender_for_project(project_dir_name):
    """Who initiates sessions in this project, when that is known.

    Nothing in a transcript records the caller, so this is pure configuration.
    Returns None when unmapped, which is the honest answer.
    """
    senders = _participant_config().get("senders", {})
    for key in sorted(senders, key=len, reverse=True):
        if key in project_dir_name:
            return senders[key]
    return None


def agent_for_project(project_dir_name, cwd=None):
    """Map a project directory to an agent name.

    The configured map wins, longest key first so a specific entry beats a
    general one. Otherwise the repository name, taken from the session's own
    `cwd`.

    Not from the project directory name, which cannot give it: that name is the
    working directory with every separator turned into a dash, and repository
    names contain dashes too, so splitting it is guesswork. It guessed wrong on
    the largest project here, collapsing both `facet-admin-workspace` and
    `facet-delivery-workspace` to "workspace" and attributing 84 sessions to a
    name that names neither of them. Also produced "tools" for `harvest-tools`
    and "rails" for `pe-rails`.
    """
    agents = _participant_config()["agents"]
    for key in sorted(agents, key=len, reverse=True):
        if key in project_dir_name:
            return agents[key]
    if cwd:
        name = os.path.basename(cwd.rstrip(os.sep))
        if name:
            return name
    tail = project_dir_name.rstrip("-").split("-")[-1]
    return tail or "agent"


#: Entrypoints that mean a human was sitting at a terminal.
INTERACTIVE_ENTRYPOINTS = ("cli", "vscode", "jetbrains", "web")

#: What to call a caller we genuinely cannot identify.
UNKNOWN_SENDER = "caller"


def resolve_participants(session, from_name, to_name):
    """Work out who was talking to whom.

    Receiver: an explicit `--to`, then `agent-name` from the transcript, then
    the project map.

    Sender: nothing in a transcript records it, so after `--from` this turns on
    HOW the session was started, which the transcript does record.

    * Interactive entrypoint: a human was at a terminal, so the configured human
      is a fair default.
    * Non-interactive (`sdk-cli`): a human was NOT. Consult the sender map for
      whoever automates that project, and if it says nothing, say `caller`.
      Naming the human anyway would put a false attribution in an audit log,
      which is the same class of error as Defect 3: confidently wrong is worse
      than plainly unknown.

    The order matters. Greenthumb's automated briefs come from Donna, but an
    interactive session in the same repo is Scott typing, so the map must not
    apply to both.
    """
    config = _participant_config()
    project = resolve.project_dir_name(session.cwd) if session.cwd else ""

    receiver = to_name or getattr(session, "agent_name", None) \
        or (agent_for_project(project, session.cwd) if project else "agent")

    sender = from_name
    if not sender:
        entrypoint = getattr(session, "entrypoint", None)
        if entrypoint in INTERACTIVE_ENTRYPOINTS or entrypoint is None:
            sender = config.get("default_sender", "scott")
        else:
            sender = (sender_for_project(project) if project else None) \
                or UNKNOWN_SENDER

    return sender, receiver


# -------------------------------------------------------------- table output

def fit(text, width):
    """Left-justify to `width`, truncating with an ellipsis when too long.

    Collapses every run of whitespace to one space first. A tab in a cell is
    not a character, it is a jump to the next tab stop, so one tab inside a
    title shifts every column after it on that row: exactly the alignment this
    table exists to provide. Titles come from transcripts and do contain them.
    """
    text = " ".join((text or "").split())
    if len(text) > width:
        text = text[: max(0, width - 3)] + "..."
    return text.ljust(width)


def page_label(filename, sender, receiver, started):
    """The distinctive part of an output filename: its slug.

    Output is named `<when>-<sender>-to-<receiver>-<slug>.html`, and every part
    of that except the slug is already in the columns beside this one. Showing
    the whole thing spends the cell re-printing what is on screen; showing only
    the tail (`...-with-scott.html`) is no better, because the tail is an
    arbitrary cut through a phrase.

    The slug is the part worth showing: it says what the page is about, and it
    globs (`ls ~/.ai-staff-audit-log/*clarify-push*`). Falls back to the plain
    filename when the name is not ours, which is what `-o` produces.
    """
    name = filename[:-5] if filename.endswith(".html") else filename
    if started:
        prefix = "%s-%s-to-%s-" % (
            started.strftime("%Y%m%d-%H%M"),
            slugify(sender, "unknown"), slugify(receiver, "agent"),
        )
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def wrote_detail(label, size_text, width=None):
    """The DETAIL cell for a written page: what it is, and how big.

    The size is short and always kept whole; the label gets whatever is left.
    """
    width = COL_DETAIL if width is None else width
    suffix = " (%s)" % size_text
    return fit(label, max(0, width - len(suffix))).rstrip() + suffix


def _cells(status, ident, when, detail, sender, receiver, subject):
    return (
        fit(status, COL_STATUS) + SEP
        + fit(ident, COL_ID) + SEP
        + fit(when, COL_WHEN) + SEP
        + fit(detail, COL_DETAIL) + SEP
        + fit(sender, COL_SENDER) + SEP
        + fit(receiver, COL_RECEIVER) + SEP
        + fit(subject, COL_SUBJECT)
    )


def table_header():
    """Header and rule, sized to the same columns as the rows."""
    head = "   " + _cells("STATUS", "SESSION", "WHEN", "DETAIL", "SENDER",
                          "RECEIVER", "SUBJECT")
    return head.rstrip() + "\n" + "-" * LINE_WIDTH


def table_row(status, ident, when, detail, sender, receiver, subject):
    """One aligned row, prefixed with the marker for its outcome."""
    return ("%s%s" % (
        MARKERS.get(status, INFO),
        _cells(status, ident, when, detail, sender, receiver, subject),
    )).rstrip()


class Report(object):
    """Emits aligned rows, printing the header before the first one.

    Everything goes to stderr: stdout belongs to `--stdout`, which emits the
    page itself, and a report interleaved with HTML would ruin both.
    """

    def __init__(self, stream, show_header=True, show_skips=True):
        self.stream = stream
        self.pending = show_header
        self.show_skips = show_skips
        self.last = None
        #: Skips withheld from the output. Counted rather than dropped, so the
        #: run can still say how much it passed over: quiet is fine, silent
        #: about work not done is not.
        self.withheld = 0

    def row(self, *args):
        self.last = args[0]
        if self.pending:
            self.stream.write(table_header() + "\n")
            self.pending = False
        self.stream.write(table_row(*args) + "\n")

    def emit(self, prebuilt_row, force=False):
        """A row already formatted by `skip_row`."""
        self.last = "SKIPPED"
        if not self.show_skips and not force:
            self.withheld += 1
            return
        if self.pending:
            self.stream.write(table_header() + "\n")
            self.pending = False
        self.stream.write(prebuilt_row + "\n")

    def raw(self, line):
        self.stream.write(line + "\n")

    def note_withheld(self):
        """Say how many rows were withheld, then forget them.

        Hiding the skips by default keeps a sweep readable, but a run that says
        nothing about what it passed over would be hiding work rather than
        tidying output. The count always shows; `-v` shows the rows.
        """
        if not self.withheld:
            return
        self.raw("   %d session%s passed over; -v to list %s"
                 % (self.withheld, "" if self.withheld == 1 else "s",
                    "it" if self.withheld == 1 else "them"))
        self.withheld = 0


def when_of(description):
    if not description.started:
        return "unknown"
    return description.started.astimezone(parse.local_timezone()).strftime(
        "%m-%d %H:%M"
    )


# ------------------------------------------------------------------ display

def tilde(path):
    """`/Users/scottwb/x` as `~/x`, when it really is under home."""
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def human_size(count):
    """A size the way `ls -h` writes it: 410 KB, 4.3 MB."""
    step = 1024.0
    for unit in ("bytes", "KB", "MB", "GB"):
        if count < step or unit == "GB":
            if unit == "bytes":
                return "%d bytes" % count
            # One decimal only where it says something: 4.3 MB, but 410 KB.
            return ("%.0f %s" if count >= 100 else "%.1f %s") % (count, unit)
        count /= step
    return "%d bytes" % count


# --------------------------------------------------- finding a session to render

#: Cap on how far back the walk goes before giving up. A project with hundreds
#: of interactive sessions and no agent conversations should say so rather than
#: read every transcript in it.
MAX_SKIPS = 200


def reason_text(description, reasons):
    """The DETAIL cell for a skipped session: terse, and says who drove it.

    A bare turn count answers the wrong question. What you want when scanning
    is whether this was a person at a keyboard or an agent, so the turn count
    rides inside that: `Human (10 turns)`, `Agent (4 turns)`. Everything else
    stays as short as it can be.
    """
    parts = []
    for reason in reasons:
        if reason.kind == "multi_turn":
            who = "Human" if description.is_interactive else "Agent"
            parts.append("%s (%s)" % (who, reason.short))
        else:
            parts.append(reason.short)
    if not parts:
        return "not renderable"
    if description.is_interactive and not any(
        r.kind == "multi_turn" for r in reasons
    ):
        parts.insert(0, "Human")
    return ", ".join(parts)


def participants_of(description):
    """Who was talking, for a session we may not have fully parsed."""
    return resolve_participants(description, None, None)


def skip_row(description, reasons):
    """One aligned row explaining why a session was passed over."""
    sender, receiver = participants_of(description)
    return table_row("SKIPPED", description.short_id, when_of(description),
                     reason_text(description, reasons), sender, receiver,
                     description.title or "(untitled)")


def classify(candidate):
    """`(report, description)` for one transcript, parsing as little as possible.

    An oversized transcript is refused on file size alone: reading 44 MB to
    print one line about not using it is not a trade worth making.
    """
    size = os.path.getsize(candidate)
    if size > parse.MAX_TRANSCRIPT_BYTES:
        reasons = [parse.Unsupported(
            "oversized", "", short="%.0f MB" % (size / 1048576.0)
        )]
        return parse.SupportReport(candidate, reasons), parse.describe_head(candidate)
    records, _ = parse.load_records(candidate)
    return (parse.check_supported(records, candidate, size_bytes=size),
            parse.describe(records, candidate))


def first_renderable(candidates):
    """The first session in `candidates` that v1 can render, and the skips.

    `candidates` is newest first. Taking `--latest` literally meant the common
    case was a refusal for a session nobody chose, since in any project you also
    work in by hand the newest transcript is an interactive multi-turn session.

    Announcing each skip is what makes walking honest rather than magic: the
    tool never quietly decides a session did not count.

    Returns `(path_or_None, skip_rows)`.
    """
    skips = []
    for candidate in candidates:
        if len(skips) >= MAX_SKIPS:
            skips.append(
                "stopped after %d skipped sessions; name one explicitly or "
                "pass --date" % MAX_SKIPS
            )
            return None, skips
        report, description = classify(candidate)
        if report.ok:
            return candidate, skips
        skips.append(skip_row(description, report.reasons))
    return None, skips


def latest_renderable(project_path):
    """The newest renderable session in a project."""
    return first_renderable(list(reversed(resolve.sessions_in(project_path))))


# ------------------------------------------------------------- name clashes

_PAGE_SESSION = re.compile(r"audit-agent-conversation session:([0-9a-fA-F-]+)")

#: Enough of a page to find the marker it declares itself with.
PAGE_HEAD_BYTES = 300


def page_session_id(path):
    """Which session produced the page at `path`, or None if it does not say."""
    try:
        with open(path, "r", errors="replace") as handle:
            match = _PAGE_SESSION.search(handle.read(PAGE_HEAD_BYTES))
    except OSError:
        return None
    return match.group(1) if match else None


def disambiguate(target, session_id):
    """A free filename for `session_id`, appending its short id on a clash.

    Filenames are `<when>-<sender>-to-<receiver>-<slug>.html` with no session
    id, which reads well and sorts right (decision A2). It is not unique,
    though: two sessions started in the same minute between the same pair with
    the same opening prompt produce the same name, and a sweep of the real
    corpus turns up two such names covering five sessions.

    Left alone, the second session is reported "already there" and silently
    never rendered, which is the worst outcome available: a conversation
    missing from an audit log, labelled as if it were present. So a name that
    belongs to a DIFFERENT session gets the short id appended, and one that
    belongs to this session is left exactly as it was.
    """
    if not os.path.exists(target) or not session_id:
        return target
    owner = page_session_id(target)
    if owner is None or owner == session_id:
        return target
    stem = target[:-5] if target.endswith(".html") else target
    return "%s-%s.html" % (stem, session_id[:8])


# ------------------------------------------------------------ write safety

class UnsafeDestination(Exception):
    """The requested output path would write into the transcript store."""


def _within(path, root):
    """Is `path` inside `root`, after resolving symlinks and `..`?

    `os.path.realpath` on both sides is what makes a planted symlink or a
    `../` climb fail the check rather than sneak through it.
    """
    path = os.path.realpath(path)
    root = os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def check_destination(path):
    """Refuse any destination inside `~/.claude/projects/`.

    Absolute, and deliberately not overridable by `--force`. The transcripts are
    the only copy of every session and they are gitignored, so overwriting one
    is unrecoverable. `--force` means "replace my own output", never "disable
    the safety rail".
    """
    if _within(path, resolve.PROJECTS_ROOT):
        real = os.path.realpath(path)
        viaes = "" if real == os.path.abspath(path) else " (which resolves to %s)" % real
        raise UnsafeDestination(
            "refusing to write to %s%s: that is inside the Claude Code "
            "transcript store (%s). Those files are the only copy of each "
            "session and this tool only ever reads them. Choose a destination "
            "outside that directory."
            % (path, viaes, resolve.PROJECTS_ROOT)
        )


# ---------------------------------------------------------------- filenames

def output_filename(session, from_name, to_name):
    """`YYYYMMDD-HHMM-<from>-to-<to>-<slug>.html` (decision A2).

    Plain `ls` gives chronological order; `ls *-donna-to-*` filters by
    initiator.
    """
    started = session.started_at_local
    stamp = started.strftime("%Y%m%d-%H%M") if started else "00000000-0000"
    slug = slugify(session.title or (session.opening.text if session.opening else ""))
    return "%s-%s-to-%s-%s.html" % (stamp, slugify(from_name, "unknown"),
                                    slugify(to_name, "agent"), slug)


# ------------------------------------------------------------- time windows

#: How many days "the past week" covers, counting today.
WEEK_DAYS = 7


def date_window(args):
    """`(predicate, label)` for the requested time window, or `(None, None)`.

    Deliberately three fixed windows rather than a date-range grammar. The
    questions actually worth asking are "the last one", "today", and "this
    week"; arbitrary ranges are a parser and a pile of edge cases in exchange
    for a question nobody asks.
    """
    import datetime

    if args.date:
        wanted = args.date
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", wanted):
            raise resolve.ResolutionError(
                "date %r is not in YYYY-MM-DD form" % wanted
            )
        return (lambda day: day == wanted), "dated %s" % wanted

    today = datetime.datetime.now(parse.local_timezone()).date()

    if args.today:
        wanted = today.isoformat()
        return (lambda day: day == wanted), "from today (%s)" % wanted

    if args.week:
        first = (today - datetime.timedelta(days=WEEK_DAYS - 1)).isoformat()
        last = today.isoformat()
        return ((lambda day: day is not None and first <= day <= last),
                "from the past %d days (%s to %s)" % (WEEK_DAYS, first, last))

    return None, None


def scoped_candidates(project_path, args):
    """Every transcript in a project inside the requested window, newest first."""
    paths = list(reversed(resolve.sessions_in(project_path)))
    predicate, _ = date_window(args)
    if predicate:
        paths = [p for p in paths if predicate(resolve.local_date_of(p))]
    return paths


# -------------------------------------------------------------------- sweep

def sweep_candidates(args):
    """Every transcript in scope, newest first.

    Scope is the project when one is named, and otherwise EVERY project: a bare
    `--all` is the "what have my agents been doing" sweep, so narrowing it to
    the current directory would answer a smaller question than the one asked.
    A date filters within whatever that scope turned out to be.
    """
    if args.project:
        projects = [resolve.find_project(args.project)]
    else:
        projects = resolve.list_projects()
        if not projects:
            raise resolve.ResolutionError(
                "no project directories under %s" % resolve.PROJECTS_ROOT
            )

    candidates = []
    for project in projects:
        try:
            candidates.extend(scoped_candidates(project, args))
        except resolve.ResolutionError:
            continue  # an empty project is not an error during a sweep

    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates


def run_sweep(args, report_out):
    """Render every renderable session in scope, reporting each outcome."""
    try:
        candidates = sweep_candidates(args)
    except resolve.ResolutionError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2

    if not candidates:
        sys.stderr.write("error: no transcripts in scope\n")
        return 2

    tally = {"WROTE": 0, "EXISTS": 0, "SKIPPED": 0, "FAILED": 0}
    for candidate in candidates:
        code = render_one(candidate, args, report_out)
        if code == 0:
            # render_one reported WROTE or EXISTS itself; count by what landed.
            tally["EXISTS" if report_out.last == "EXISTS" else "WROTE"] += 1
        elif code == 3:
            tally["SKIPPED"] += 1
        else:
            tally["FAILED"] += 1

    report_out.raw(
        "%d written, %d already there, %d skipped%s, out of %d sessions%s"
        % (tally["WROTE"], tally["EXISTS"], tally["SKIPPED"],
           ", %d failed" % tally["FAILED"] if tally["FAILED"] else "",
           len(candidates),
           " (-v to list the skipped)" if report_out.withheld else "")
    )
    return 4 if tally["FAILED"] else 0


# --------------------------------------------------------------------- main

DESCRIPTION = """\
Render Claude Code session transcripts into self-contained HTML audit log
pages: the prompt that started a conversation, everything the agent did, the
reply that came back, what changed in the world, and what it cost.

Reads transcripts from ~/.claude/projects/ and never writes there.
Writes pages to ~/.ai-staff-audit-log/ unless told otherwise.
"""

EPILOG = """\
choosing what to render
  With nothing to go on, renders the latest session that CAN be rendered for
  the current directory's project, naming each session it passes over. Naming
  a session or a day narrows that; --all widens it.

examples
  audit-agent-conversation
      the latest renderable session for this directory's project

  audit-agent-conversation --project greenthumb
      the latest renderable session in that project

  audit-agent-conversation 9608087e --project greenthumb
      that session, by id or id prefix. Named sessions are never swapped for
      a neighbour: an unsupported one is refused, not skipped past.

  audit-agent-conversation --all --week
      every renderable session from every project in the past 7 days. This is
      the "what have my agents been doing" sweep.

  audit-agent-conversation --all --project greenthumb --force
      re-render everything in one project

output
  One aligned row per session on stderr. WROTE produced a page, EXISTS found
  one already there, SKIPPED passed a session over and says why. stdout is
  reserved for --stdout, which emits the page itself.

what v1 will not render
  Multi-turn sessions, sessions containing images, and transcripts over 8 MB.
  These are refused, never half-rendered: a page that looks complete but is
  not is worse than no page. Refusals name every condition they found.

exit codes
  0  a page was written, or was already there, or a sweep finished
  2  could not work out which session you meant, or contradictory options
  3  that session is one v1 cannot render yet
  4  a page failed to render
  5  the output directory could not be created
  7  the destination is inside the transcript store, which is read-only
"""


class Parser(argparse.ArgumentParser):
    """Prints the whole help on a bad invocation, not just a usage line.

    A one-line usage message is enough for someone who already knows the tool.
    Anyone else, human or agent, has to go and ask for help separately, so just
    give it to them at the moment they got it wrong.
    """

    def error(self, message):
        sys.stderr.write("error: %s\n\n" % message)
        self.print_help(sys.stderr)
        sys.exit(2)


def build_parser():
    parser = Parser(
        prog="audit-agent-conversation",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "session", nargs="?",
        help="session UUID, UUID prefix, or path to a .jsonl transcript",
    )
    parser.add_argument("--project", help="resolve within ~/.claude/projects/*NAME*")
    parser.add_argument("--latest", action="store_true",
                        help="most recent session in the project (the default)")
    parser.add_argument("--date", metavar="YYYY-MM-DD",
                        help="only sessions started on this date")
    parser.add_argument("--today", action="store_true",
                        help="only sessions started today")
    parser.add_argument("--week", action="store_true",
                        help="only sessions started in the past %d days"
                             % WEEK_DAYS)
    parser.add_argument("--from", dest="from_name",
                        help="who initiated the exchange")
    parser.add_argument("--to", dest="to_name", help="which agent did the work")
    parser.add_argument("-o", "--output", help="write to this exact path")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help="directory to write into (default: %s)" % DEFAULT_OUTPUT_DIR)
    parser.add_argument("--stdout", action="store_true",
                        help="write the HTML to stdout and create no file")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting an existing output file")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress the row for a page that was written")
    parser.add_argument("--no-header", action="store_true",
                        help="omit the column header and rule")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="list every session passed over, not just the "
                             "count. Skips are always listed when nothing "
                             "could be rendered.")
    parser.add_argument("--all", action="store_true",
                        help="render every session in scope, not just one. "
                             "With no --project, the scope is every project.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    windows = [name for name, on in
               (("--date", args.date), ("--today", args.today),
                ("--week", args.week)) if on]
    if len(windows) > 1:
        sys.stderr.write(
            "error: %s each pick a different span of time; pass one.\n"
            % " and ".join(windows))
        return 2
    if args.latest and windows:
        sys.stderr.write(
            "error: --latest and %s ask for different sessions; pass one.\n"
            % windows[0])
        return 2

    report_out = Report(sys.stderr, show_header=not args.no_header,
                        show_skips=args.verbose)

    if args.all:
        if args.session:
            sys.stderr.write(
                "error: --all renders every session in scope; naming one "
                "contradicts it.\n")
            return 2
        if args.stdout or args.output:
            sys.stderr.write(
                "error: --all writes many pages, so --stdout and -o do not "
                "apply. Use --output-dir.\n")
            return 2
        return run_sweep(args, report_out)

    notes = []
    # Naming a session means that session. Naming a DAY means a session from
    # that day, so walking within it is the same courtesy `--latest` gets: it
    # never wanders to another date.
    walking = not args.session

    try:
        if walking:
            # "Latest" means the latest one that can actually be rendered. Every
            # session passed over on the way is named on stderr.
            project_path = (
                resolve.find_project(args.project) if args.project
                else resolve.project_for_cwd()
            )
            if project_path is None:
                raise resolve.ResolutionError(
                    "no project given and no transcripts for the current "
                    "directory (%s). Pass --project NAME, or a path to a "
                    ".jsonl file." % os.getcwd()
                )
            candidates = scoped_candidates(project_path, args)
            _, window = date_window(args)
            scope = window or ("in %s" % os.path.basename(project_path))
            if not candidates:
                raise resolve.ResolutionError(
                    "no session in %s is %s"
                    % (os.path.basename(project_path), scope)
                )

            path, skips = first_renderable(candidates)
            # When nothing rendered, the skips ARE the answer, so they are
            # shown whatever the verbosity.
            for line in skips:
                report_out.emit(line, force=path is None)
            report_out.note_withheld()
            if path is None:
                sys.stderr.write(
                    "error: no renderable session %s. Everything there is "
                    "multi-turn, image-bearing, or too large for v1.\n" % scope
                )
                return 2
        else:
            path = resolve.resolve(
                session=args.session,
                project=args.project,
                latest=args.latest,
                date=args.date,
                notes=notes,
            )
    except resolve.ResolutionError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2

    # Before anything that can fail. If the session this picked turns out to be
    # unsupported, knowing WHICH one it picked is exactly what you need.
    for remark in notes:
        sys.stderr.write("note: %s\n" % remark)

    return render_one(path, args, report_out)


def render_one(path, args, report_out, records=None):
    """Render one transcript and place its page. Returns an exit code.

    Shared by the single-session path and the `--all` sweep so both report the
    same way and neither can drift from the other's safety checks.
    """
    if records is None:
        records, skipped = parse.load_records(path)
    else:
        skipped = 0
    if not records:
        sys.stderr.write("error: %s contains no parseable records\n" % path)
        return 2

    report = parse.check_supported(records, path)
    if not report.ok:
        description = parse.describe(records, path)
        if args.all:
            # In a sweep a refusal is just another row; the long prose belongs
            # to someone who asked for this session by name.
            sender, receiver = participants_of(description)
            report_out.emit(skip_row(description, report.reasons))
            return 3
        sys.stderr.write("%s\n%s\n" % (os.path.basename(path), report.message()))
        return 3

    session = parse.load_session(path, records=records)
    sender, receiver = resolve_participants(session, args.from_name, args.to_name)

    try:
        html = render.page(session, from_name=sender, to_name=receiver)
    except Exception as exc:  # noqa: BLE001 - fail loudly, never half-write
        sys.stderr.write("error: could not render %s: %s\n" % (path, exc))
        return 4

    if args.stdout:
        sys.stdout.write(html)
        return 0

    if args.output:
        target = os.path.abspath(args.output)
        directory = os.path.dirname(target) or "."
    else:
        directory = os.path.abspath(args.output_dir)
        target = os.path.join(directory, output_filename(session, sender, receiver))

    # Before creating anything. A refused destination must leave no trace,
    # including a directory that should never have existed.
    try:
        check_destination(directory)
        check_destination(target)
    except UnsafeDestination as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 7

    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            sys.stderr.write("error: could not create %s: %s\n" % (directory, exc))
            return 5

    description = parse.describe(records, path)
    if not args.output:
        # Only for names we generated. `-o` is the user naming the file, and
        # renaming it under them would be worse than the clash.
        target = disambiguate(target, session.session_id)

    if os.path.exists(target) and not args.force:
        # Not an error: the page you asked for is already there. Report it the
        # same way as any other session passed over, and exit 0 so re-running a
        # batch is a cheap no-op rather than a failure.
        report_out.row("EXISTS", description.short_id, when_of(description),
                       "use --force to replace", sender, receiver,
                       description.title or "(untitled)")
        return 0

    # Write to a sibling temp file and rename into place, so an interrupted run
    # cannot leave a half-written page where a good one used to be. The rename
    # also means the final write never follows a symlink at `target`.
    handle, staging = tempfile.mkstemp(
        dir=directory, prefix=".audit-agent-conversation-", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w") as fh:
            fh.write(html)
        os.replace(staging, target)
    except BaseException:
        if os.path.exists(staging):
            os.unlink(staging)
        raise

    if not args.quiet:
        report_out.row("WROTE", description.short_id, when_of(description),
                       wrote_detail(
                           page_label(os.path.basename(target), sender,
                                      receiver, session.started_at_local),
                           human_size(os.path.getsize(target))),
                       sender, receiver, description.title or "(untitled)")
        if skipped:
            report_out.raw("   %d unparseable lines skipped" % skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())

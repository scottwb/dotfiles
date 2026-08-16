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

#: Informational prefix, per the repo convention: info "i" for informational.
INFO = "\u2139\ufe0f "

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


def agent_for_project(project_dir_name):
    """Map a project directory to an agent name.

    Longest key first, so a specific entry beats a general one. Falls back to
    the directory's last path segment, which is usually the repo name and is a
    better guess than "agent".
    """
    agents = _participant_config()["agents"]
    for key in sorted(agents, key=len, reverse=True):
        if key in project_dir_name:
            return agents[key]
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
        or (agent_for_project(project) if project else "agent")

    sender = from_name
    if not sender:
        entrypoint = getattr(session, "entrypoint", None)
        if entrypoint in INTERACTIVE_ENTRYPOINTS or entrypoint is None:
            sender = config.get("default_sender", "scott")
        else:
            sender = (sender_for_project(project) if project else None) \
                or UNKNOWN_SENDER

    return sender, receiver


# --------------------------------------------------- finding a session to render

#: Cap on how far back the walk goes before giving up. A project with hundreds
#: of interactive sessions and no agent conversations should say so rather than
#: read every transcript in it.
MAX_SKIPS = 200


def skip_line(description, reasons):
    """One line explaining why a session was passed over.

    `SKIPPED <id> | <when it started> | <why> | <what it was about>`, so a run
    that walks back through a dozen interactive sessions reads as a list rather
    than a wall.
    """
    when = (
        description.started.astimezone(parse.local_timezone()).strftime(
            "%Y-%m-%d %H:%M"
        )
        if description.started else "date unknown"
    )

    why = ", ".join(r.short for r in reasons) or "not renderable"
    # "interactive" is the human-meaningful half: the turn count says WHAT
    # tripped the check, this says what kind of session it was.
    if description.is_interactive:
        why = "interactive, " + why

    title = (description.title or "").strip().replace("\n", " ")
    words = title.split()
    if len(words) > 10:
        title = " ".join(words[:10]) + "..."

    return "SKIPPED %s | %s | %s | %s" % (
        description.short_id, when, why, title or "(untitled)"
    )


def latest_renderable(project_path):
    """The newest session v1 can actually render, plus what it walked past.

    `--latest` used to mean "the newest transcript", which in any project you
    also work in by hand is usually an interactive multi-turn session, so the
    common case was a refusal for a session the user never chose. It now means
    "the newest one that qualifies", and every session passed over is reported.

    Announcing each skip is what makes this honest rather than magic: the tool
    never quietly decides a session did not count.

    Returns `(path_or_None, skip_lines)`.
    """
    skips = []
    for candidate in reversed(resolve.sessions_in(project_path)):
        if len(skips) >= MAX_SKIPS:
            skips.append(
                "stopped after %d skipped sessions; name one explicitly or "
                "pass --date" % MAX_SKIPS
            )
            return None, skips

        size = os.path.getsize(candidate)
        if size > parse.MAX_TRANSCRIPT_BYTES:
            # Refuse on size without parsing 44 MB just to print one line.
            reasons = [parse.Unsupported(
                "oversized", "", short="%.0f MB" % (size / 1048576.0)
            )]
            skips.append(skip_line(parse.describe_head(candidate), reasons))
            continue

        records, _ = parse.load_records(candidate)
        report = parse.check_supported(records, candidate, size_bytes=size)
        if report.ok:
            return candidate, skips
        skips.append(skip_line(parse.describe(records, candidate), report.reasons))

    return None, skips


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


# --------------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(
        prog="audit-agent-conversation",
        description=(
            "Render a Claude Code session transcript into a single "
            "self-contained HTML audit log page."
        ),
        epilog=(
            "Pages are written to ~/.ai-staff-audit-log/ by default. "
            "Transcripts are only ever read, never modified."
        ),
    )
    parser.add_argument(
        "session", nargs="?",
        help="session UUID, UUID prefix, or path to a .jsonl transcript",
    )
    parser.add_argument("--project", help="resolve within ~/.claude/projects/*NAME*")
    parser.add_argument("--latest", action="store_true",
                        help="most recent session in the project (the default)")
    parser.add_argument("--date", help="session on this date, YYYY-MM-DD")
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
    parser.add_argument("--quiet", action="store_true", help="suppress the summary line")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.latest and args.date:
        sys.stderr.write(
            "error: --latest and --date ask for different sessions; pass one.\n"
        )
        return 2

    notes = []
    walking = not args.session and not args.date

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
            path, skips = latest_renderable(project_path)
            for line in skips:
                sys.stderr.write("%s %s\n" % (INFO, line))
            if path is None:
                sys.stderr.write(
                    "error: no renderable session in %s. %s\n"
                    % (os.path.basename(project_path),
                       "Everything there is multi-turn, image-bearing, or too "
                       "large for v1.")
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

    records, skipped = parse.load_records(path)
    if not records:
        sys.stderr.write("error: %s contains no parseable records\n" % path)
        return 2

    report = parse.check_supported(records, path)
    if not report.ok:
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

    if os.path.exists(target) and not args.force:
        sys.stderr.write(
            "error: %s already exists. Pass --force to overwrite it.\n" % target
        )
        return 6

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
        note = " (%d unparseable lines skipped)" % skipped if skipped else ""
        sys.stdout.write(
            "wrote %s (%s bytes)\n  from session %s%s\n"
            % (target, "{:,}".format(os.path.getsize(target)),
               session.session_id or os.path.basename(path), note)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

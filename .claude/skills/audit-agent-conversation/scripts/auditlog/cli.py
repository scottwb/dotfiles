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

from . import parse, render, resolve

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


def resolve_participants(session, from_name, to_name):
    """Work out who was talking to whom.

    Precedence for the receiver: an explicit `--to`, then `agent-name` from the
    transcript, then the project map. Nothing records the SENDER anywhere in a
    transcript, so it is `--from`, then the project map, then the configured
    default (decision A5).
    """
    config = _participant_config()
    project = resolve.project_dir_name(session.cwd) if session.cwd else ""

    receiver = to_name or getattr(session, "agent_name", None) \
        or (agent_for_project(project) if project else "agent")

    sender = from_name or config.get("default_sender", "scott")
    return sender, receiver


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

    try:
        path = resolve.resolve(
            session=args.session,
            project=args.project,
            latest=args.latest,
            date=args.date,
        )
    except resolve.ResolutionError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2

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

    with open(target, "w") as handle:
        handle.write(html)

    if not args.quiet:
        note = " (%d unparseable lines skipped)" % skipped if skipped else ""
        sys.stdout.write(
            "wrote %s (%s bytes)%s\n"
            % (target, "{:,}".format(os.path.getsize(target)), note)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

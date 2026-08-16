"""Finding a transcript to render.

STRICTLY READ-ONLY against `~/.claude/projects/`. Those files are the only copy
of every session, they are gitignored, and nothing here may open one for
writing, move one, or delete one. A test enforces that by reading this module's
own source.

Note the transcript root is resolved through `~`, deliberately. On this machine
`~/.claude` is a symlink into the main dotfiles checkout, so a worktree-relative
`.claude/projects/` resolves to an empty directory and would silently find
nothing.
"""

import os
import re

#: Where Claude Code keeps session transcripts.
PROJECTS_ROOT = os.path.expanduser("~/.claude/projects")

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ResolutionError(Exception):
    """No transcript could be identified, with an explanation of why."""


def project_dir_name(cwd):
    """Map a working directory to its project directory name.

    Claude Code replaces every path separator with a dash, so
    `/Users/scottwb/src/scottwb/greenthumb` becomes
    `-Users-scottwb-src-scottwb-greenthumb`.
    """
    normalized = os.path.abspath(cwd).rstrip("/")
    if not normalized:
        normalized = "/"
    return normalized.replace("/", "-")


def list_projects(root=None):
    root = root or PROJECTS_ROOT
    if not os.path.isdir(root):
        return []
    return sorted(
        os.path.join(root, name)
        for name in os.listdir(root)
        if os.path.isdir(os.path.join(root, name))
    )


def find_project(name, root=None):
    """Resolve a project by exact name, then by path tail, then by substring.

    The tail step is what makes a repository with sub-repositories usable.
    Project directories are the working directory with every separator turned
    into a dash, so a sub-repository's directory has its parent's name as a
    prefix:

        -Users-scottwb-src-facetdigital-facet-admin-workspace
        -Users-scottwb-src-facetdigital-facet-admin-workspace-facet-revops

    Substring matching alone therefore cannot select the parent at all: its
    name appears in both, so naming it exactly is ambiguous. Matching the path
    TAIL on a dash boundary picks the parent, because only the parent ends with
    `-facet-admin-workspace`.

    Slashes are accepted too, so `facetdigital/facet-admin-workspace` works.
    """
    projects = list_projects(root)
    if not projects:
        raise ResolutionError(
            "no project directories found under %s" % (root or PROJECTS_ROOT)
        )

    needle = name.strip("/").replace("/", "-")

    for path in projects:
        base = os.path.basename(path)
        if base == name or base == needle:
            return path

    tails = [p for p in projects
             if os.path.basename(p).endswith("-" + needle)]
    if len(tails) == 1:
        return tails[0]
    if len(tails) > 1:
        raise ResolutionError(
            "project %r matches the end of %d directories: %s"
            % (name, len(tails), ", ".join(os.path.basename(p) for p in tails))
        )

    matches = [p for p in projects if needle in os.path.basename(p)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ResolutionError(
            "no project matches %r. Try one of: %s"
            % (name, ", ".join(os.path.basename(p) for p in projects[:12]))
        )
    raise ResolutionError(
        "project %r is ambiguous, matching %d directories: %s. "
        "Name it exactly, or by its trailing path, to pick one."
        % (name, len(matches), ", ".join(os.path.basename(p) for p in matches))
    )


def project_for_cwd(cwd=None, root=None):
    """The project directory for a working directory, if it has one."""
    cwd = cwd or os.getcwd()
    candidate = os.path.join(root or PROJECTS_ROOT, project_dir_name(cwd))
    if os.path.isdir(candidate):
        return candidate
    return None


def sessions_in(project_path):
    """Every transcript in a project directory, newest last."""
    if not os.path.isdir(project_path):
        raise ResolutionError("not a project directory: %s" % project_path)
    found = [
        os.path.join(project_path, name)
        for name in os.listdir(project_path)
        if name.endswith(".jsonl")
    ]
    if not found:
        raise ResolutionError("no transcripts in %s" % project_path)
    return sorted(found, key=os.path.getmtime)


def _by_prefix(project_path, prefix):
    matches = [
        path for path in sessions_in(project_path)
        if os.path.basename(path).startswith(prefix)
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ResolutionError(
            "no session in %s starts with %r"
            % (os.path.basename(project_path), prefix)
        )
    raise ResolutionError(
        "session prefix %r is ambiguous, matching %d: %s"
        % (prefix, len(matches),
           ", ".join(os.path.basename(p)[:8] for p in matches))
    )


def sessions_on_date(project_path, date, session_date=None):
    """Every transcript in `project_path` dated `date`, newest first."""
    if not _DATE.match(date):
        raise ResolutionError("date %r is not in YYYY-MM-DD form" % date)
    session_date = session_date or local_date_of
    matches = [p for p in sessions_in(project_path) if session_date(p) == date]
    matches.reverse()
    return matches


def _by_date(project_path, date, session_date, notes=None):
    if not _DATE.match(date):
        raise ResolutionError(
            "date %r is not in YYYY-MM-DD form" % date
        )
    matches = [p for p in sessions_in(project_path) if session_date(p) == date]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ResolutionError(
            "no session in %s is dated %s"
            % (os.path.basename(project_path), date)
        )
    # Several on one day is common: 8 dates in the greenthumb corpus carry two
    # to four sessions. Picking the latest is the useful default, but doing it
    # silently leaves the caller unsure which one they got, so say so.
    if len(matches) > 1 and notes is not None:
        notes.append(
            "%d sessions are dated %s; rendered the latest (%s). The others: %s"
            % (len(matches), date, os.path.basename(matches[-1])[:8],
               ", ".join(os.path.basename(p)[:8] for p in matches[:-1]))
        )
    return matches[-1]


def local_date_of(path):
    """The transcript's local calendar date, from its first timestamped record.

    Uses the record's own timestamp rather than the file's mtime, because a
    session that ran past midnight would otherwise be filed under the wrong day.
    """
    from . import parse

    with open(path, "r", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                import json

                record = json.loads(line)
            except ValueError:
                continue
            stamp = parse.parse_timestamp(record.get("timestamp"))
            if stamp:
                return stamp.astimezone(parse.local_timezone()).strftime("%Y-%m-%d")
    return None


def resolve(session=None, project=None, latest=False, date=None, cwd=None,
            root=None, notes=None):
    """Identify one transcript.

    Precedence: an existing path wins outright, then a UUID or prefix within a
    project, then a date, then the latest in the project. With no project given,
    the current working directory's project is used, which makes a bare
    invocation inside a repo do the obvious thing.

    `latest` is the default rather than a mode, so passing it changes nothing on
    its own; it exists so the intent can be stated explicitly, and so `--latest`
    and `--date` together can be rejected as contradictory by the caller.

    Pass a list as `notes` to receive human-readable remarks about choices made
    along the way, such as which session was picked from a day that had several.
    """
    if session and os.path.sep in str(session):
        if os.path.isfile(session):
            return session
        raise ResolutionError("no such transcript: %s" % session)

    if project:
        project_path = find_project(project, root)
    else:
        project_path = project_for_cwd(cwd, root)
        if project_path is None:
            raise ResolutionError(
                "no project given and no transcripts for the current directory "
                "(%s). Pass --project NAME, or a path to a .jsonl file."
                % (cwd or os.getcwd())
            )

    if session:
        return _by_prefix(project_path, str(session))

    if date:
        return _by_date(project_path, date, local_date_of, notes=notes)

    # `latest` is both the explicit flag and the default.
    return sessions_in(project_path)[-1]

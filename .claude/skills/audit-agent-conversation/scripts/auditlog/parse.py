"""Claude Code JSONL transcript to a normalized session model.

Everything learned about the transcript format lives here. This module is pure:
it reads a transcript and returns data. It renders nothing and knows no HTML.

Transcripts live at
`~/.claude/projects/<cwd-with-slashes-as-dashes>/<session-uuid>.jsonl`
and are treated as STRICTLY READ-ONLY. They are the only copy and they are
gitignored.

The two format facts that drive the whole design:

1. One record per content block, each repeating the whole message's `usage`.
   Dedupe on `message.id` before summing anything. See `Usage`.
2. A slash-command session opens with a PAIR of user records: the raw XML
   invocation, then the expanded command body marked `isMeta: true`. Counting
   both as turns makes every single-turn session look multi-turn. See
   `is_real_turn`.
"""

import datetime
import json
import re


class Usage(object):
    """A deduplicated token bundle for one session."""

    __slots__ = ("tokens", "message_ids", "models", "duplicate_records")

    def __init__(self):
        self.tokens = {
            "input": 0,
            "cache_write_1h": 0,
            "cache_write_5m": 0,
            "cache_read": 0,
            "output": 0,
            "reasoning": 0,
        }
        self.message_ids = []
        self.models = []
        self.duplicate_records = 0

    @property
    def api_messages(self):
        return len(self.message_ids)

    @property
    def model(self):
        """The model that produced the most messages in this session."""
        if not self.models:
            return None
        counts = {}
        for name in self.models:
            counts[name] = counts.get(name, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def load_records(path):
    """Read a JSONL transcript.

    Returns `(records, skipped)`. Blank lines are ignored and unparseable lines
    are counted rather than raised on: a transcript for a session that is still
    running can have a torn final line, and losing the whole run over it would
    be a poor trade. A transcript where NOTHING parses is a different problem
    and is caught by the caller.
    """
    records = []
    skipped = 0
    with open(path, "r", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                skipped += 1
    return records, skipped


def accumulate_usage(records):
    """Sum token usage across `records`, deduplicating on `message.id`.

    THE bug this prevents: every record belonging to one assistant message
    repeats that message's entire `usage` object, so a message rendered as four
    content blocks contributes its token counts four times.
    """
    usage = Usage()
    seen = set()

    for record in records:
        if record.get("type") != "assistant":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue

        message_id = message.get("id")
        if message_id is not None and message_id in seen:
            usage.duplicate_records += 1
            continue
        if message_id is not None:
            seen.add(message_id)
            usage.message_ids.append(message_id)

        if message.get("model"):
            usage.models.append(message["model"])

        raw = message.get("usage") or {}
        creation = raw.get("cache_creation") or {}
        details = raw.get("output_tokens_details") or {}

        usage.tokens["input"] += raw.get("input_tokens", 0) or 0
        usage.tokens["cache_write_1h"] += creation.get("ephemeral_1h_input_tokens", 0) or 0
        usage.tokens["cache_write_5m"] += creation.get("ephemeral_5m_input_tokens", 0) or 0
        usage.tokens["cache_read"] += raw.get("cache_read_input_tokens", 0) or 0
        usage.tokens["output"] += raw.get("output_tokens", 0) or 0
        usage.tokens["reasoning"] += details.get("thinking_tokens", 0) or 0

    return usage


def usage_for(path):
    """Convenience: load a transcript and return its deduplicated usage."""
    records, _ = load_records(path)
    return accumulate_usage(records)


#: How far into a transcript to read when all that is wanted is its identity.
#: Titles, the opening prompt, and the entrypoint all appear in the first
#: handful of records; reading further would mean parsing 44 MB to print one
#: line about a session being skipped.
PEEK_RECORDS = 400


def load_head(path, limit=PEEK_RECORDS):
    """Parse at most `limit` records from the front of a transcript."""
    records = []
    with open(path, "r", errors="replace") as handle:
        for line in handle:
            if len(records) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    return records


def content_blocks(record):
    """Normalize `message.content` to a list of block dicts.

    `message.content` is either a bare string or a list of blocks, and both
    shapes are common. A bare string is normalized to a single text block so
    callers never branch on it.
    """
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if content is None:
        return []
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def has_block(record, block_type):
    return any(b.get("type") == block_type for b in content_blocks(record))


def is_real_turn(record):
    """Is this record a genuine caller turn?

    Excludes, in order of how badly each would corrupt a turn count:

    * `isMeta` records. A slash-command invocation expands into a second user
      record carrying the command body, flagged `isMeta: true`. It is not a
      turn; counting it makes every single-turn brief look like two turns and
      trips the multi-turn refusal on the entire target corpus.
    * tool_result carriers. Tool results come back as `user` records. They are
      the harness replying to itself, not the caller speaking.
    """
    if record.get("type") != "user":
        return False
    if record.get("isMeta"):
        return False
    if has_block(record, "tool_result"):
        return False
    return True


def real_turns(records):
    return [r for r in records if is_real_turn(r)]


# ------------------------------------------------------- unsupported cases

#: v1 renders one caller turn. More than this is deferred work, not a bug.
MAX_TURNS = 1

#: Beyond this, embedding every tool result verbatim yields a page no browser
#: opens comfortably. The largest transcript in the surveyed corpus is 44 MB.
MAX_TRANSCRIPT_BYTES = 8 * 1024 * 1024


class Unsupported(object):
    """One reason a session cannot be rendered, with its magnitude."""

    __slots__ = ("kind", "detail", "short")

    def __init__(self, kind, detail, short=None):
        self.kind = kind
        self.detail = detail
        #: A few words, for a one-line skip notice. The long `detail` explains
        #: itself to someone who asked for this session by name; `short` is for
        #: a list of sessions being passed over.
        self.short = short or kind.replace("_", " ")

    def __repr__(self):
        return "<Unsupported %s: %s>" % (self.kind, self.detail)


class SupportReport(object):
    """Every reason a session was refused, not merely the first one found."""

    __slots__ = ("reasons", "path")

    def __init__(self, path, reasons):
        self.path = path
        self.reasons = reasons

    @property
    def ok(self):
        return not self.reasons

    def message(self):
        if self.ok:
            return ""
        lines = ["Cannot render this session yet:"]
        for reason in self.reasons:
            lines.append("  - " + reason.detail)
        lines.append("")
        lines.append(
            "These cases are deferred, not broken. Refusing is deliberate: a "
            "half-rendered page that looks complete is worse than no page."
        )
        return "\n".join(lines)


class UnsupportedSession(Exception):
    """Raised when a transcript trips one or more deferred cases."""

    def __init__(self, report):
        Exception.__init__(self, report.message())
        self.report = report


def count_images(records):
    total = 0
    for record in records:
        for block in content_blocks(record):
            if block.get("type") == "image":
                total += 1
            # Images also arrive nested inside tool_result content.
            nested = block.get("content")
            if isinstance(nested, list):
                for inner in nested:
                    if isinstance(inner, dict) and inner.get("type") == "image":
                        total += 1
    return total


def has_sidechain(records):
    """Did any record belong to a subagent thread?

    None exist anywhere in the surveyed corpus, so this is a tripwire rather
    than a feature: it exists so a session containing one is refused instead of
    silently mis-rendered as though the subagent's work were the main thread's.
    """
    return any(r.get("isSidechain") for r in records)


def check_supported(records, path=None, size_bytes=None):
    """Report every deferred case this session trips."""
    import os

    reasons = []

    turns = real_turns(records)
    if len(turns) > MAX_TURNS:
        reasons.append(Unsupported(
            "multi_turn",
            "this session has %d user turns; multi-turn rendering is not "
            "implemented yet" % len(turns),
            short="%d turns" % len(turns),
        ))

    images = count_images(records)
    if images:
        reasons.append(Unsupported(
            "images",
            "this session has %d image block%s; image rendering is not "
            "implemented yet" % (images, "" if images == 1 else "s"),
            short="%d image%s" % (images, "" if images == 1 else "s"),
        ))

    if size_bytes is None and path is not None:
        try:
            size_bytes = os.path.getsize(path)
        except OSError:
            size_bytes = None
    if size_bytes is not None and size_bytes > MAX_TRANSCRIPT_BYTES:
        reasons.append(Unsupported(
            "oversized",
            "this transcript is %.1f MB, over the %.0f MB limit; embedding "
            "every tool result verbatim would produce an unopenable page, and "
            "the size budget is not implemented yet"
            % (size_bytes / 1048576.0, MAX_TRANSCRIPT_BYTES / 1048576.0),
            short="%.0f MB" % (size_bytes / 1048576.0),
        ))

    if not turns:
        reasons.append(Unsupported(
            "no_prompt",
            "no caller turn could be found in this transcript, so there is "
            "nothing to render as the opening prompt",
            short="no caller turn",
        ))

    if has_sidechain(records):
        reasons.append(Unsupported(
            "sidechain",
            "this session contains subagent (sidechain) records; rendering "
            "them as though they were the main thread would misattribute the "
            "work, and subagent threads are not implemented yet",
            short="subagent thread",
        ))

    return SupportReport(path, reasons)


# --------------------------------------------------------------- timestamps

def parse_timestamp(value):
    """Parse a transcript's UTC ISO 8601 timestamp into an aware datetime."""
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------- slash commands

_COMMAND_NAME = re.compile(r"<command-name>\s*(.*?)\s*</command-name>", re.S)
_COMMAND_ARGS = re.compile(r"<command-args>\s*(.*?)\s*</command-args>", re.S)


def unwrap_slash_command(text):
    """Turn a slash-command invocation's XML into a readable `/name args`.

    A prompt invoked as a slash command arrives as markup:

        <command-message>exec-brief</command-message>
        <command-name>/exec-brief</command-name>
        <command-args>full</command-args>

    Rendering that verbatim is Defect 2. Returns None for ordinary prose so
    callers can tell "not a slash command" from "a slash command with no
    arguments".
    """
    if not text or "<command-name>" not in text:
        return None
    name_match = _COMMAND_NAME.search(text)
    if not name_match:
        return None
    name = name_match.group(1).strip()
    if not name:
        return None
    if not name.startswith("/"):
        name = "/" + name

    args_match = _COMMAND_ARGS.search(text)
    args = args_match.group(1).strip() if args_match else ""
    return ("%s %s" % (name, args)).strip()


# --------------------------------------------------------- opening prompt

class OpeningPrompt(object):
    """The caller's turn that started the session."""

    __slots__ = (
        "record",
        "raw_text",
        "text",
        "is_slash_command",
        "expanded_text",
        "timestamp",
    )

    def __init__(self, record, raw_text, expanded_text=None):
        self.record = record
        self.raw_text = raw_text
        self.expanded_text = expanded_text
        self.timestamp = parse_timestamp(record.get("timestamp"))

        unwrapped = unwrap_slash_command(raw_text)
        self.is_slash_command = unwrapped is not None
        self.text = unwrapped if unwrapped is not None else raw_text


def _record_text(record):
    parts = []
    for block in content_blocks(record):
        if block.get("type") == "text":
            parts.append(block.get("text") or "")
    return "\n".join(parts)


def find_opening_prompt(records):
    """Locate the caller's opening turn.

    Defect 1 was matching on `promptSource == "sdk"`, which is set on the
    reference session and absent on every daily brief, so the briefs found no
    opening prompt at all and died computing a duration against None.

    The real rule owes nothing to `promptSource`: the opening prompt is the
    first `user` record that is a genuine turn, meaning not `isMeta` and
    carrying no `tool_result` blocks. A `parentUuid` of None is a useful
    corroborator and is preferred when one exists, but it is not required,
    because it is absent on resumed and bridged sessions.
    """
    turns = real_turns(records)
    if not turns:
        return None

    rooted = [r for r in turns if r.get("parentUuid") is None]
    opening = rooted[0] if rooted else turns[0]

    # The expansion, when present, is the isMeta record immediately following
    # the invocation. It holds the instructions the agent actually acted on.
    expanded = None
    try:
        position = records.index(opening)
    except ValueError:
        position = -1
    if position >= 0:
        for candidate in records[position + 1:]:
            kind = candidate.get("type")
            if kind == "user" and candidate.get("isMeta"):
                expanded = _record_text(candidate)
                break
            if kind in ("user", "assistant"):
                break

    return OpeningPrompt(opening, _record_text(opening), expanded)


def title_for(records, opening=None):
    """The best available name for a session.

    F4: the daily briefs carry neither `custom-title` nor `ai-title`, so the
    chain has to keep going past both, down to the slash command that started
    the session and finally to the prompt's first line.
    """
    if opening is None:
        opening = find_opening_prompt(records)
    # ai-title first, deliberately. `custom-title` is a LABEL in practice: real
    # sessions set it to the agent's display name ("Donna Dev", "Greenthumb"),
    # which just repeats the receiver. `ai-title` is the generated one-line
    # description of what the session was about, which is what a reader
    # scanning a list actually wants.
    return (
        _last_field(records, "ai-title", "aiTitle", "title")
        or _last_field(records, "custom-title", "customTitle", "title")
        or (opening.text if opening and opening.is_slash_command else None)
        or (opening.text.strip().split("\n")[0][:80]
            if opening and opening.text.strip() else None)
    )


class Description(object):
    """Just enough about a session to name it in a one-line notice."""

    #: `cwd` and `agent_name` are here so a Description can stand in for a
    #: Session wherever participants are resolved: naming who was talking should
    #: not require parsing a whole transcript just to print one row about it.
    __slots__ = ("path", "session_id", "started", "entrypoint", "title",
                 "cwd", "agent_name")

    def __init__(self, path, session_id, started, entrypoint, title,
                 cwd=None, agent_name=None):
        self.path = path
        self.session_id = session_id
        self.started = started
        self.entrypoint = entrypoint
        self.title = title
        self.cwd = cwd
        self.agent_name = agent_name

    @property
    def short_id(self):
        return (self.session_id or "")[:8] or "????????"

    @property
    def is_interactive(self):
        return self.entrypoint in ("cli", "vscode", "jetbrains", "web")


def describe(records, path=None):
    """Identity metadata from however many records the caller has parsed."""
    opening = find_opening_prompt(records)
    session_id = (
        _first_field(records, "user", "sessionId")
        or _first_field(records, "assistant", "sessionId")
    )
    if not session_id and path:
        import os

        session_id = os.path.basename(path).replace(".jsonl", "")
    started = opening.timestamp if opening else None
    if started is None:
        for record in records:
            started = parse_timestamp(record.get("timestamp"))
            if started:
                break
    entrypoint = (
        (opening.record.get("entrypoint") if opening else None)
        or _first_field(records, "assistant", "entrypoint")
        or _first_field(records, "attachment", "entrypoint")
    )
    cwd = (
        (opening.record.get("cwd") if opening else None)
        or _first_field(records, "assistant", "cwd")
        or _first_field(records, "user", "cwd")
    )
    return Description(path, session_id, started, entrypoint,
                       title_for(records, opening), cwd,
                       _last_field(records, "agent-name", "agentName"))


def describe_head(path, limit=PEEK_RECORDS):
    """`describe` without parsing the whole file. See PEEK_RECORDS."""
    return describe(load_head(path, limit), path)


# --------------------------------------------------------------- tool results

def result_text(block):
    """Flatten a `tool_result` block's content to text.

    `content` is a string, or a list of `{"type": "text"}` blocks, or something
    else entirely. All three shapes occur.
    """
    if block is None:
        return None
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for inner in content:
            if not isinstance(inner, dict):
                continue
            if inner.get("type") == "text":
                parts.append(inner.get("text") or "")
            else:
                parts.append(json.dumps(inner, indent=2))
        return "\n".join(parts)
    if content is None:
        return ""
    return json.dumps(content, indent=2)


def index_tool_results(records):
    """Map `tool_use_id` to its result block."""
    index = {}
    for record in records:
        for block in content_blocks(record):
            if block.get("type") == "tool_result":
                key = block.get("tool_use_id")
                if key:
                    index[key] = block
    return index


# --------------------------------------------------------------- side effects

_GIT_COMMIT = re.compile(r"\bgit\s+(?:-[^\s]+\s+)*commit\b")
_SHORT_SHA = re.compile(r"^([0-9a-f]{7,40})\b", re.M)

#: Tools that write to disk.
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit", "MultiEdit")
#: Tools that read from disk.
READ_TOOLS = ("Read", "NotebookRead")
#: Tools that reach outside the machine.
EXTERNAL_TOOL_PREFIXES = ("mcp__",)
EXTERNAL_TOOLS = ("WebFetch", "WebSearch")


class SideEffects(object):
    """What the session actually did to the world, counted from its tool calls.

    Replaces the prototype's hand-written prose, which cited a specific commit
    hash and therefore claimed, on every other transcript, a commit that never
    happened. Wrong-but-plausible output is worse than none.
    """

    __slots__ = (
        "commits", "commit_shas", "file_writes", "file_reads",
        "external_calls", "shell_commands", "wrote_paths",
    )

    def __init__(self):
        self.commits = 0
        self.commit_shas = []
        self.file_writes = 0
        self.file_reads = 0
        self.external_calls = 0
        self.shell_commands = 0
        self.wrote_paths = []

    def summary_lines(self):
        """Plain sentences for the "side effects" box.

        Says zero out loud rather than omitting a category, because "no
        commits" is information and a missing line is ambiguous.
        """
        lines = []

        if self.commits:
            shas = ", ".join(self.commit_shas)
            lines.append(
                "Wrote %d git commit%s%s."
                % (self.commits, "" if self.commits == 1 else "s",
                   " (%s)" % shas if shas else "")
            )
        else:
            lines.append("Made no git commits.")

        if self.file_writes:
            lines.append(
                "Wrote to %d file%s on disk."
                % (self.file_writes, "" if self.file_writes == 1 else "s")
            )
        else:
            lines.append("Wrote no files directly.")

        lines.append(
            "Read %d file%s."
            % (self.file_reads, "" if self.file_reads == 1 else "s")
        )

        if self.external_calls:
            lines.append(
                "Made %d call%s to an outside service."
                % (self.external_calls, "" if self.external_calls == 1 else "s")
            )
        else:
            lines.append("Called no outside services.")

        if self.shell_commands:
            lines.append(
                "Ran %d shell command%s."
                % (self.shell_commands, "" if self.shell_commands == 1 else "s")
            )

        return lines


def derive_side_effects(events):
    """Count real-world effects from the session's tool calls."""
    effects = SideEffects()

    for event in events:
        if event.kind != "tool":
            continue
        name = event.tool_name or ""
        params = event.tool_input or {}

        if name in WRITE_TOOLS:
            effects.file_writes += 1
            path = params.get("file_path") or params.get("notebook_path")
            if path:
                effects.wrote_paths.append(path)
        elif name in READ_TOOLS:
            effects.file_reads += 1
        elif name in EXTERNAL_TOOLS or name.startswith(EXTERNAL_TOOL_PREFIXES):
            effects.external_calls += 1
        elif name == "Bash":
            effects.shell_commands += 1
            command = params.get("command") or ""
            # The command may be a heredoc spanning many lines with the commit
            # buried in the middle, so search the whole string, never a prefix.
            if _GIT_COMMIT.search(command):
                effects.commits += 1
                # `git log --oneline -1` in the same call surfaces the sha.
                if event.result:
                    match = _SHORT_SHA.search(event.result.strip())
                    if match:
                        effects.commit_shas.append(match.group(1)[:7])

    return effects


# ------------------------------------------------------------------- events

class Event(object):
    """One thing that happened in the work log."""

    __slots__ = (
        "kind", "timestamp", "text", "tool_name", "tool_input", "tool_id",
        "result", "is_error", "reasoning_tokens", "signature",
    )

    def __init__(self, kind, timestamp):
        self.kind = kind
        self.timestamp = timestamp
        self.text = None
        self.tool_name = None
        self.tool_input = None
        self.tool_id = None
        self.result = None
        self.is_error = False
        self.reasoning_tokens = 0
        self.signature = ""


# ------------------------------------------------------------------ session

class Session(object):
    """A parsed transcript, ready to render. Knows no HTML."""

    __slots__ = (
        "path", "session_id", "records", "skipped_lines", "usage", "opening",
        "events", "reply", "cwd", "git_branch", "cli_version", "effort",
        "permission_mode", "entrypoint", "agent_name", "agent_color", "title",
        "started_at", "ended_at", "side_effects", "model",
    )

    @property
    def tool_count(self):
        return sum(1 for e in self.events if e.kind == "tool")

    @property
    def reasoning_steps(self):
        return sum(1 for e in self.events if e.kind == "thinking")

    @property
    def duration(self):
        if self.started_at and self.ended_at:
            return self.ended_at - self.started_at
        return None

    def _local(self, moment):
        if moment is None:
            return None
        return moment.astimezone(local_timezone())

    @property
    def started_at_local(self):
        return self._local(self.started_at)

    @property
    def ended_at_local(self):
        return self._local(self.ended_at)


def local_timezone():
    """The timezone audit log pages are stamped in.

    `zoneinfo` rather than the prototype's hardcoded `-7`, which silently
    mislabels every session outside daylight saving time by an hour.
    """
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/Los_Angeles")
    except Exception:
        # No tzdata on this machine. Fall back to whatever local time is,
        # which is right on Scott's laptop and honest everywhere else.
        return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


def _first_field(records, record_type, *fields):
    for record in records:
        if record.get("type") != record_type:
            continue
        for field in fields:
            if record.get(field):
                return record[field]
    return None


def _last_field(records, record_type, *fields):
    """The LAST value, for identity records that settle over a session.

    A session renames itself as it goes: one transcript opens with
    `agentName: "Donna /color red /rc"`, captured while a slash command was
    being typed, and every record after it says `"Donna"`. Taking the first
    value pins the accident; taking the last takes what it settled on.
    """
    found = None
    for record in records:
        if record.get("type") != record_type:
            continue
        for field in fields:
            if record.get(field):
                found = record[field]
    return found


def load_session(path, records=None):
    """Parse a transcript into a `Session`.

    Does NOT enforce supported-case checks; call `check_supported` for that.
    Keeping them separate lets a caller inspect a session it will not render.
    """
    skipped = 0
    if records is None:
        records, skipped = load_records(path)

    session = Session()
    session.path = path
    session.records = records
    session.skipped_lines = skipped
    session.session_id = _first_field(records, "user", "sessionId") or \
        _first_field(records, "assistant", "sessionId")

    session.usage = accumulate_usage(records)
    session.model = session.usage.model
    session.opening = find_opening_prompt(records)

    session.agent_name = _last_field(records, "agent-name", "agentName")
    session.agent_color = _last_field(records, "agent-color", "agentColor")
    session.title = title_for(records, session.opening)

    opening_record = session.opening.record if session.opening else {}
    session.cwd = opening_record.get("cwd") or _first_field(records, "assistant", "cwd")
    session.git_branch = opening_record.get("gitBranch") or \
        _first_field(records, "assistant", "gitBranch")
    session.cli_version = opening_record.get("version") or \
        _first_field(records, "assistant", "version")
    session.entrypoint = opening_record.get("entrypoint") or \
        _first_field(records, "assistant", "entrypoint")
    session.effort = _first_field(records, "assistant", "effort")
    session.permission_mode = (
        opening_record.get("permissionMode")
        or _first_field(records, "assistant", "permissionMode")
        or _first_field(records, "user", "permissionMode")
    )

    results = index_tool_results(records)
    events = []
    assistant_records = [r for r in records if r.get("type") == "assistant"]
    last_assistant = assistant_records[-1] if assistant_records else None

    reply = None
    started = session.opening.timestamp if session.opening else None
    ended = None

    for record in assistant_records:
        stamp = parse_timestamp(record.get("timestamp"))
        if stamp:
            ended = stamp
        usage = (record.get("message") or {}).get("usage") or {}
        details = usage.get("output_tokens_details") or {}

        for block in content_blocks(record):
            kind = block.get("type")

            if kind == "thinking":
                event = Event("thinking", stamp)
                event.reasoning_tokens = details.get("thinking_tokens", 0) or 0
                event.signature = block.get("signature") or ""
                events.append(event)

            elif kind == "text":
                text = block.get("text") or ""
                if record is last_assistant:
                    # The final assistant text block is the reply returned to
                    # the caller, not a step in the work log.
                    reply = text
                else:
                    event = Event("say", stamp)
                    event.text = text
                    events.append(event)

            elif kind == "tool_use":
                event = Event("tool", stamp)
                event.tool_name = block.get("name")
                event.tool_input = block.get("input") or {}
                event.tool_id = block.get("id")
                result_block = results.get(event.tool_id)
                event.result = result_text(result_block)
                if event.result is None:
                    event.result = "(no result recorded)"
                event.is_error = bool(result_block and result_block.get("is_error"))
                events.append(event)

    if reply is None and last_assistant is not None:
        texts = [b.get("text") or "" for b in content_blocks(last_assistant)
                 if b.get("type") == "text"]
        reply = texts[-1] if texts else ""

    session.events = events
    session.reply = reply or ""
    session.started_at = started
    session.ended_at = ended
    session.side_effects = derive_side_effects(events)

    return session

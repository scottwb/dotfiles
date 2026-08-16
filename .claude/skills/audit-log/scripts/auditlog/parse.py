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

    __slots__ = ("kind", "detail")

    def __init__(self, kind, detail):
        self.kind = kind
        self.detail = detail

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
        ))

    images = count_images(records)
    if images:
        reasons.append(Unsupported(
            "images",
            "this session has %d image block%s; image rendering is not "
            "implemented yet" % (images, "" if images == 1 else "s"),
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
        ))

    if not turns:
        reasons.append(Unsupported(
            "no_prompt",
            "no caller turn could be found in this transcript, so there is "
            "nothing to render as the opening prompt",
        ))

    if has_sidechain(records):
        reasons.append(Unsupported(
            "sidechain",
            "this session contains subagent (sidechain) records; rendering "
            "them as though they were the main thread would misattribute the "
            "work, and subagent threads are not implemented yet",
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

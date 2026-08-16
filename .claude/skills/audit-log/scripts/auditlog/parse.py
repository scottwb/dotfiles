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

import json


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

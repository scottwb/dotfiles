"""The normalized session model, and Defect 3: nothing may be hardcoded.

The prototype's stat tiles and "side effects on the real world" prose were
written by hand for one session. On that session they were correct. On any
other they render as confidently wrong, which is worse than rendering nothing:
the page claimed a commit that never happened.

Everything asserted here is DERIVED from the transcript.
"""

import unittest

from auditlog import parse
from tests import fixtures


class TestReferenceSession(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.session = parse.load_session(fixtures.path(fixtures.REFERENCE))

    def test_tool_call_count(self):
        self.assertEqual(self.session.tool_count, 14)

    def test_reasoning_step_count(self):
        self.assertEqual(self.session.reasoning_steps, 7)

    def test_reply_word_count(self):
        self.assertEqual(len(self.session.reply.split()), 1886)

    def test_provenance(self):
        self.assertEqual(self.session.cwd, "/Users/scottwb/src/scottwb/greenthumb")
        self.assertEqual(self.session.git_branch, "main")
        self.assertEqual(self.session.cli_version, "2.1.233")
        self.assertEqual(self.session.model, "claude-opus-5")
        self.assertEqual(self.session.effort, "high")
        self.assertEqual(self.session.permission_mode, "bypassPermissions")
        self.assertEqual(self.session.entrypoint, "sdk-cli")

    def test_duration_is_positive(self):
        self.assertIsNotNone(self.session.duration)
        self.assertGreater(self.session.duration.total_seconds(), 0)

    def test_tokens_match_the_golden_bundle(self):
        for key, expected in sorted(fixtures.GOLDEN_TOKENS.items()):
            self.assertEqual(self.session.usage.tokens[key], expected, key)

    def test_events_are_ordered_and_typed(self):
        kinds = set(e.kind for e in self.session.events)
        self.assertTrue(kinds.issubset({"tool", "thinking", "say"}), kinds)
        stamps = [e.timestamp for e in self.session.events if e.timestamp]
        self.assertEqual(stamps, sorted(stamps), "events out of chronological order")

    def test_every_tool_event_resolved_its_result(self):
        unresolved = [e for e in self.session.events
                      if e.kind == "tool" and e.result is None]
        self.assertEqual(unresolved, [])


class TestDerivedSideEffects(unittest.TestCase):
    """Defect 3. Counted from the transcript, never written by hand."""

    def setUp(self):
        fixtures.require_corpus(self)
        self.session = parse.load_session(fixtures.path(fixtures.REFERENCE))
        self.effects = self.session.side_effects

    def test_the_commit_is_found_inside_a_heredoc_command(self):
        """`git add ... && git commit -q -F - <<'EOF'` is one Bash call.

        A naive scan of a truncated command string misses it. The reference
        session really does make exactly one commit.
        """
        self.assertEqual(self.effects.commits, 1)

    def test_the_commit_sha_is_recovered_from_the_result(self):
        self.assertIn("051a130", self.effects.commit_shas)

    def test_external_calls_counted(self):
        self.assertEqual(self.effects.external_calls, 1)

    def test_file_reads_counted(self):
        self.assertEqual(self.effects.file_reads, 3)

    def test_no_file_writes_in_this_session(self):
        self.assertEqual(self.effects.file_writes, 0)

    def test_summary_is_honest_when_a_category_is_empty(self):
        """A derived summary must be able to say zero without sounding broken."""
        text = " ".join(self.effects.summary_lines())
        self.assertTrue(text.strip())
        self.assertNotIn("None", text)


class TestBriefSessions(unittest.TestCase):
    """Reply word counts are the cheap check that the extractor found the
    right block: pick the wrong one and the number moves a long way."""

    def setUp(self):
        fixtures.require_corpus(self)

    def test_reply_word_counts(self):
        for session, expected in sorted(fixtures.BRIEF_REPLY_WORDS.items()):
            model = parse.load_session(fixtures.path(session))
            self.assertEqual(len(model.reply.split()), expected, session)

    def test_brief_derived_effects_differ_from_the_reference(self):
        """The prototype would have claimed a commit here. There is none."""
        model = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        self.assertEqual(model.side_effects.commits, 0)
        self.assertEqual(model.side_effects.commit_shas, [])
        self.assertEqual(model.side_effects.external_calls, 1)
        self.assertEqual(model.side_effects.file_reads, 6)
        self.assertEqual(model.tool_count, 9)

    def test_brief_prompt_is_the_unwrapped_command(self):
        model = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        self.assertEqual(model.opening.text, "/exec-brief full")

    def test_timestamps_render_in_pacific_not_a_fixed_offset(self):
        """The prototype hardcoded -7, which is wrong half the year."""
        model = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        local = model.started_at_local
        self.assertEqual(local.strftime("%Y-%m-%d"), "2026-08-13")
        self.assertEqual(local.strftime("%H:%M"), "05:57")


class TestGracefulDegradation(unittest.TestCase):
    """Unknown record types, bare-string content, and missing agent-name."""

    def _write(self, lines):
        import json
        import os
        import tempfile

        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        with open(path, "w") as fh:
            fh.write("\n".join(json.dumps(line) for line in lines))
        return path

    def test_synthetic_minimal_session_parses(self):
        import os

        path = self._write([
            {"type": "some-future-record-type", "whatever": True},
            {"type": "attachment", "attachment": {"type": "task_reminder"}},
            {"type": "user", "parentUuid": None, "message": {"content": "do a thing"},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "9.9.9"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "msg_1", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "done"}],
                         "usage": {"input_tokens": 10, "output_tokens": 5}}},
        ])
        try:
            session = parse.load_session(path)
            self.assertEqual(session.opening.text, "do a thing")
            self.assertEqual(session.reply, "done")
            self.assertEqual(session.tool_count, 0)
            self.assertIsNone(session.agent_name)
            self.assertEqual(session.usage.tokens["output"], 5)
        finally:
            os.unlink(path)

    def test_agent_name_and_color_are_used_when_present(self):
        import os

        path = self._write([
            {"type": "agent-name", "agentName": "Greenthumb"},
            {"type": "agent-color", "agentColor": "green"},
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"output_tokens": 1}}},
        ])
        try:
            session = parse.load_session(path)
            self.assertEqual(session.agent_name, "Greenthumb")
            self.assertEqual(session.agent_color, "green")
        finally:
            os.unlink(path)

    def test_title_falls_back_through_the_chain(self):
        import os

        path = self._write([
            {"type": "ai-title", "aiTitle": "A generated title"},
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"output_tokens": 1}}},
        ])
        try:
            self.assertEqual(parse.load_session(path).title, "A generated title")
        finally:
            os.unlink(path)

    def test_custom_title_beats_ai_title(self):
        import os

        path = self._write([
            {"type": "ai-title", "aiTitle": "Generated"},
            {"type": "custom-title", "customTitle": "Human chosen"},
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"output_tokens": 1}}},
        ])
        try:
            self.assertEqual(parse.load_session(path).title, "Human chosen")
        finally:
            os.unlink(path)

    def test_briefs_have_no_ai_title_and_fall_back_to_the_command(self):
        """F4: the target corpus carries no ai-title at all."""
        fixtures.require_corpus(self)
        session = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        self.assertEqual(session.title, "/exec-brief full")


if __name__ == "__main__":
    unittest.main()

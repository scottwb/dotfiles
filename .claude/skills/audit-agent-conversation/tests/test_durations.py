"""Per-event durations, and the work log laid out as aligned rows.

Durations are free and unambiguous: a tool call's wall clock is the gap
between the record carrying its `tool_use` block and the record carrying the
matching `tool_result`. A reasoning or narration step's duration is the gap to
the previous record. Nothing is divided or attributed; a duration is a
subtraction of two timestamps that are both in the file.

Tokens per step are deliberately NOT here. Token counts are per API message and
one message covers many rows, so a per-row token figure would be invented. See
the roadmap's follow-on 5.
"""

import datetime
import json
import os
import tempfile
import unittest

from auditlog import parse, render
from tests import fixtures


def _write(lines):
    handle, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(handle)
    with open(path, "w") as fh:
        fh.write("\n".join(json.dumps(line) for line in lines))
    return path


def _synthetic():
    """One thinking step, one narration, one tool call, then the reply.

    The tool call is issued at :05 and its result lands at :07.5, so its
    duration is exactly 2.5 seconds; the thinking step follows the prompt at
    :00 by 3 seconds.
    """
    return _write([
        {"type": "user", "parentUuid": None, "message": {"content": "go"},
         "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x"},
        {"type": "assistant", "timestamp": "2026-08-15T12:00:03.000Z",
         "message": {"id": "m1", "model": "claude-opus-5",
                     "content": [{"type": "thinking", "thinking": "",
                                  "signature": "sig"}],
                     "usage": {"input_tokens": 1, "output_tokens": 1,
                               "output_tokens_details": {"thinking_tokens": 7}}}},
        {"type": "assistant", "timestamp": "2026-08-15T12:00:04.000Z",
         "message": {"id": "m1", "model": "claude-opus-5",
                     "content": [{"type": "text", "text": "Looking."}],
                     "usage": {"input_tokens": 1, "output_tokens": 1}}},
        {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
         "message": {"id": "m1", "model": "claude-opus-5",
                     "content": [{"type": "tool_use", "id": "t1", "name": "Read",
                                  "input": {"file_path": "/tmp/x/a.md"}}],
                     "usage": {"input_tokens": 1, "output_tokens": 1}}},
        {"type": "user", "timestamp": "2026-08-15T12:00:07.500Z",
         "message": {"content": [{"type": "tool_result", "tool_use_id": "t1",
                                  "content": "# a"}]}},
        {"type": "assistant", "timestamp": "2026-08-15T12:00:09.000Z",
         "message": {"id": "m2", "model": "claude-opus-5",
                     "content": [{"type": "text", "text": "done"}],
                     "usage": {"input_tokens": 1, "output_tokens": 1}}},
    ])


class TestEventDurations(unittest.TestCase):
    def setUp(self):
        self.path = _synthetic()
        self.session = parse.load_session(self.path)

    def tearDown(self):
        os.unlink(self.path)

    def _only(self, kind):
        found = [e for e in self.session.events if e.kind == kind]
        self.assertEqual(len(found), 1, kind)
        return found[0]

    def test_a_tool_call_lasts_from_its_use_to_its_result(self):
        self.assertEqual(self._only("tool").duration,
                         datetime.timedelta(seconds=2.5))

    def test_a_reasoning_step_lasts_from_the_previous_record(self):
        self.assertEqual(self._only("thinking").duration,
                         datetime.timedelta(seconds=3))

    def test_a_narration_step_lasts_from_the_previous_record(self):
        self.assertEqual(self._only("say").duration,
                         datetime.timedelta(seconds=1))

    def test_a_tool_call_with_no_result_has_no_duration(self):
        """None, not zero. Zero would claim the call was instantaneous."""
        path = _write([
            {"type": "user", "parentUuid": None, "message": {"content": "go"},
             "timestamp": "2026-08-15T12:00:00.000Z"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "m1", "model": "claude-opus-5",
                         "content": [{"type": "tool_use", "id": "t1",
                                      "name": "Read", "input": {}}],
                         "usage": {"output_tokens": 1}}},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:09.000Z",
             "message": {"id": "m2", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "gave up"}],
                         "usage": {"output_tokens": 1}}},
        ])
        try:
            session = parse.load_session(path)
            tool = [e for e in session.events if e.kind == "tool"][0]
            self.assertIsNone(tool.duration)
        finally:
            os.unlink(path)


class TestReferenceDurationsAreSane(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def _check(self, session_id):
        session = parse.load_session(fixtures.path(session_id))
        tools = [e for e in session.events if e.kind == "tool"]
        self.assertTrue(tools)
        for event in tools:
            self.assertIsNotNone(event.duration, event.tool_name)
            self.assertGreaterEqual(event.duration.total_seconds(), 0)
        total = sum((e.duration for e in tools), datetime.timedelta())
        self.assertLessEqual(total, session.duration)
        # Measured on a real brief: 0.00s to 0.66s per call. Anything in
        # minutes here means the wrong pair of records is being subtracted.
        self.assertLess(max(e.duration.total_seconds() for e in tools), 300)

    def test_reference_session(self):
        self._check(fixtures.REFERENCE)

    def test_a_brief(self):
        self._check(fixtures.BRIEF_AUG13)


class TestDurationWords(unittest.TestCase):
    def test_sub_minute_shows_hundredths(self):
        self.assertEqual(render.step_duration(datetime.timedelta(seconds=0.42)),
                         "0.42s")
        self.assertEqual(render.step_duration(datetime.timedelta(seconds=0)),
                         "0.00s")

    def test_a_minute_or_more_shows_minutes_and_seconds(self):
        self.assertEqual(render.step_duration(datetime.timedelta(seconds=63)),
                         "1m 03s")

    def test_none_is_shown_as_absent_not_zero(self):
        text = render.step_duration(None)
        self.assertNotIn("0", text)


class TestWorkLogRows(unittest.TestCase):
    """Every row is a badge, a tool, a label, a sub-label, and a duration."""

    @classmethod
    def setUpClass(cls):
        fixtures.require_corpus(cls)
        cls.session = parse.load_session(fixtures.path(fixtures.REFERENCE))
        cls.rows = render.render_events(cls.session)

    def test_every_row_carries_a_badge_including_narration(self):
        says = [e for e in self.session.events if e.kind == "say"]
        self.assertTrue(says, "reference session has narration rows")
        self.assertEqual(self.rows.count("class='badge"), len(self.session.events))
        self.assertEqual(self.rows.count("class='badge k-say'"), len(says))

    def test_every_row_has_a_duration_cell(self):
        self.assertEqual(self.rows.count("class='evdur'"), len(self.session.events))

    def test_every_tool_row_names_its_tool_in_its_own_column(self):
        self.assertEqual(self.rows.count("class='evtool'"), len(self.session.events))
        for event in self.session.events:
            if event.kind == "tool":
                self.assertIn(">%s<" % render.tool_short_name(event.tool_name),
                              self.rows)

    def test_the_disclosure_arrow_rotates_rather_than_swapping_glyphs(self):
        css = render.CSS
        self.assertIn(".ev[open] > summary::before", css)
        self.assertIn("rotate(90deg)", css)
        self.assertNotIn(".ev > summary::after{content:\"+\"", css)


if __name__ == "__main__":
    unittest.main()

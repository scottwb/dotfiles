"""The rendered page. Defect 3's other half: nothing may be hardcoded.

The prototype's stat tiles and side-effects prose were written for one session.
The page they produced was correct exactly once. The pair of tests that matters
most here is `test_reference_page_cites_its_real_commit` together with
`test_a_brief_page_does_not_mention_the_reference_commit`: the defect was never
the hash, it was the hash surviving into every other session's page.
"""

import re
import unittest

from auditlog import parse, render
from tests import fixtures


class RenderedPage(object):
    """Render once per class; these are the slowest tests in the suite."""

    html = None

    @classmethod
    def build(cls, session_id, **kwargs):
        session = parse.load_session(fixtures.path(session_id))
        return session, render.page(session, **kwargs)


class TestReferencePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        if not os.path.isdir(fixtures.GREENTHUMB):
            raise unittest.SkipTest("corpus not present")
        cls.session, cls.html = RenderedPage.build(
            fixtures.REFERENCE, from_name="Donna", to_name="Greenthumb"
        )

    def test_is_a_complete_html_document(self):
        self.assertTrue(self.html.lstrip().startswith("<!doctype html>"))
        self.assertIn("</html>", self.html)

    def test_participants_appear_in_the_masthead(self):
        self.assertIn("Donna", self.html)
        self.assertIn("Greenthumb", self.html)

    def test_work_log_is_hidden_by_default(self):
        """The page opens as a readable dialog, not a wall of tool output."""
        self.assertIn('class="log collapsed"', self.html)
        self.assertIn("Show work", self.html)

    def test_expand_collapse_controls_exist(self):
        self.assertIn('id="expand"', self.html)
        self.assertIn('id="collapse"', self.html)

    def test_eight_raw_preview_toggle_pairs(self):
        self.assertEqual(self.html.count("data-view=\"raw\""), 8)
        self.assertEqual(self.html.count("data-view=\"md\""), 8)

    def test_both_panes_are_prerendered(self):
        """No markdown parser ships with the page; the handler flips visibility."""
        self.assertEqual(self.html.count('data-pane="md"'), 8)
        self.assertEqual(self.html.count('data-pane="raw"'), self.session.tool_count)

    def test_provenance_strip(self):
        self.assertIn("/Users/scottwb/src/scottwb/greenthumb", self.html)
        self.assertIn("claude-opus-5", self.html)
        self.assertIn("2.1.233", self.html)
        self.assertIn("bypassPermissions", self.html)
        self.assertIn(fixtures.REFERENCE, self.html)

    def test_cost_tiles_are_populated(self):
        self.assertIn("$1.58", self.html)
        self.assertIn("16,179", self.html)
        self.assertIn("9,316", self.html)

    def test_reasoning_tile_says_it_is_inside_the_output(self):
        self.assertIn("of the output", self.html)

    def test_cost_note_states_nothing_was_billed(self):
        self.assertIn("subscription", self.html)

    def test_stat_grid_uses_derived_counts(self):
        """The prototype hardcoded a literal 1 for both of these."""
        self.assertEqual(self.session.side_effects.commits, 1)
        self.assertEqual(self.session.side_effects.external_calls, 1)
        self.assertIn("git commit", self.html)
        self.assertIn("external API call", self.html)

    def test_tool_call_count_is_derived(self):
        self.assertIn(str(self.session.tool_count), self.html)

    def test_reference_page_cites_its_real_commit(self):
        """Derived from the transcript, so it is correct here."""
        self.assertIn("051a130", self.html)

    def test_thinking_blocks_explain_why_there_is_no_text(self):
        self.assertIn("Reasoned privately", self.html)
        self.assertIn("encrypted", self.html.lower())

    def test_reply_banner_and_word_count(self):
        self.assertIn("Reply returned", self.html)
        self.assertIn("1,886", self.html)

    def test_dark_theme_support(self):
        self.assertIn("prefers-color-scheme: dark", self.html)

    def test_tool_output_is_escaped_not_injected(self):
        self.assertNotIn("<script>alert", self.html)


class TestDerivedContentDoesNotLeakAcrossSessions(unittest.TestCase):
    """Defect 3, stated as the regression it actually is."""

    @classmethod
    def setUpClass(cls):
        import os

        if not os.path.isdir(fixtures.GREENTHUMB):
            raise unittest.SkipTest("corpus not present")
        cls.session, cls.html = RenderedPage.build(
            fixtures.BRIEF_AUG13, from_name="Donna", to_name="Greenthumb"
        )

    def test_a_brief_page_does_not_mention_the_reference_commit(self):
        """The prototype printed 051a130 on every page it ever produced."""
        self.assertNotIn("051a130", self.html)

    def test_a_brief_page_says_no_commits_were_made(self):
        self.assertEqual(self.session.side_effects.commits, 0)
        self.assertIn("no git commits", self.html.lower())

    def test_the_brief_prompt_is_the_unwrapped_command_not_xml(self):
        self.assertIn("/exec-brief full", self.html)
        self.assertNotIn("<command-name>", self.html)

    def test_no_hardcoded_prose_from_the_prototype_survives(self):
        """Phrases the prototype AUTHORED, not garden vocabulary.

        Deliberately not words like "Zone 1" or "catch-cup": those are real
        domain terms that legitimately appear in this session's own tool output,
        because it read the same tracker files. A page is supposed to contain
        its transcript verbatim. What must never appear is prose the prototype
        wrote about a different session.
        """
        for phrase in (
            "four tracker files",
            "Did not push",
            "Read five repo files",
            "folded into one logical unit",
            "which is what turned the answer around",
        ):
            self.assertNotIn(phrase, self.html, "leaked prototype prose: %s" % phrase)

    def test_its_own_figures_are_present(self):
        self.assertIn("1,356", self.html)  # reply word count
        self.assertIn("$1.45", self.html)  # its own total


class TestParticipantColors(unittest.TestCase):
    def test_agent_color_is_used_when_present(self):
        import json
        import os
        import tempfile

        lines = [
            {"type": "agent-name", "agentName": "Greenthumb"},
            {"type": "agent-color", "agentColor": "green"},
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "1.0.0"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"output_tokens": 1}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(json.dumps(x) for x in lines))
            session = parse.load_session(path)
            html = render.page(session, from_name="Scott", to_name="Greenthumb")
            self.assertIn("Greenthumb", html)
            self.assertIn("Scott", html)
        finally:
            os.unlink(path)

    def test_renders_without_an_agent_name(self):
        import json
        import os
        import tempfile

        lines = [
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"output_tokens": 1}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(json.dumps(x) for x in lines))
            session = parse.load_session(path)
            html = render.page(session, from_name="scott", to_name="agent")
            self.assertIn("<!doctype html>", html)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

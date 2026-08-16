"""Defects 1 and 2 from the prototype, each with a test that fails against it.

Defect 1: the prototype located the opening prompt with

    if t == "user" and r.get("promptSource") == "sdk":

The daily briefs have `promptSource: None`, so `first_ts` was never set and the
run died at `duration = last_ts - first_ts` with a TypeError. All 13 briefs
crashed this way.

Defect 2: slash-command prompts rendered as literal XML markup.
"""

import unittest

from auditlog import parse
from tests import fixtures


class TestOpeningPromptResolution(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def _opening(self, session):
        records, _ = parse.load_records(fixtures.path(session))
        return parse.find_opening_prompt(records)

    def test_resolves_when_promptSource_is_sdk(self):
        """The reference session, the shape the prototype handled."""
        opening = self._opening(fixtures.REFERENCE)
        self.assertIsNotNone(opening)
        self.assertEqual(opening.record.get("promptSource"), "sdk")
        self.assertTrue(opening.text.strip())
        self.assertFalse(opening.is_slash_command)

    def test_resolves_when_promptSource_is_absent(self):
        """Defect 1. The daily briefs, which the prototype crashed on."""
        for session in (fixtures.BRIEF_AUG13, fixtures.BRIEF_AUG14, fixtures.BRIEF_AUG15):
            opening = self._opening(session)
            self.assertIsNotNone(opening, "no opening prompt found for %s" % session)
            self.assertIsNone(opening.record.get("promptSource"))
            self.assertTrue(opening.text.strip())

    def test_every_renderable_session_has_a_resolvable_opening_prompt(self):
        """The generalized form of Defect 1: no session may return None."""
        missing = []
        for path in fixtures.corpus_sessions():
            records, _ = parse.load_records(path)
            if not records:
                continue
            if parse.find_opening_prompt(records) is None:
                missing.append(path)
        self.assertEqual(missing, [])

    def test_the_isMeta_expansion_is_not_chosen_as_the_prompt(self):
        """The command body must never masquerade as the caller's prompt.

        A brief's second user record holds ~2 KB of expanded command
        instructions. Picking it would render the machinery as if the caller
        had typed it.
        """
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        opening = parse.find_opening_prompt(records)
        self.assertFalse(opening.record.get("isMeta"))
        self.assertNotIn("## Your job", opening.text)

    def test_the_expansion_is_still_captured_separately(self):
        """It is the instruction the agent actually acted on; keep it."""
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        opening = parse.find_opening_prompt(records)
        self.assertIsNotNone(opening.expanded_text)
        self.assertIn("## Your job", opening.expanded_text)

    def test_opening_prompt_carries_provenance(self):
        opening = self._opening(fixtures.BRIEF_AUG13)
        self.assertTrue(opening.record.get("cwd"))
        self.assertTrue(opening.record.get("version"))
        self.assertIsNotNone(opening.timestamp)


class TestSlashCommandUnwrapping(unittest.TestCase):
    """Defect 2."""

    def setUp(self):
        fixtures.require_corpus(self)

    def test_brief_prompt_unwraps_to_a_readable_invocation(self):
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        opening = parse.find_opening_prompt(records)
        self.assertTrue(opening.is_slash_command)
        self.assertEqual(opening.text, "/exec-brief full")

    def test_raw_markup_is_retained_for_the_raw_view(self):
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        opening = parse.find_opening_prompt(records)
        self.assertIn("<command-name>", opening.raw_text)

    def test_no_command_tags_survive_into_the_readable_text(self):
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        opening = parse.find_opening_prompt(records)
        for tag in ("<command-message>", "<command-name>", "<command-args>"):
            self.assertNotIn(tag, opening.text)

    def test_unwrap_handles_a_command_with_no_arguments(self):
        raw = (
            "<command-message>roadmap</command-message>\n"
            "<command-name>/roadmap</command-name>"
        )
        self.assertEqual(parse.unwrap_slash_command(raw), "/roadmap")

    def test_unwrap_handles_empty_argument_tag(self):
        raw = (
            "<command-message>booyah</command-message>\n"
            "<command-name>/booyah</command-name>\n"
            "<command-args></command-args>"
        )
        self.assertEqual(parse.unwrap_slash_command(raw), "/booyah")

    def test_unwrap_returns_none_for_ordinary_prose(self):
        self.assertIsNone(parse.unwrap_slash_command("Two things from Scott."))

    def test_unwrap_tolerates_local_command_stdout_wrappers(self):
        raw = (
            "<command-name>/color</command-name>\n"
            "<command-args>pink</command-args>\n"
            "<local-command-stdout>Session color set</local-command-stdout>"
        )
        self.assertEqual(parse.unwrap_slash_command(raw), "/color pink")


if __name__ == "__main__":
    unittest.main()

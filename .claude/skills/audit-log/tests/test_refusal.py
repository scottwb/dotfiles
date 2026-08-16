"""v1 refuses rather than half-renders.

Multi-turn rendering, image blocks, and the 46 MB scale case are deferred. The
substitute for supporting them is a clean, honest refusal: name the condition,
give its magnitude, exit non-zero, write nothing.

The most important test in this file is
`test_every_exec_brief_is_renderable`. A turn counter that does not exclude
`isMeta` sees two turns on every daily brief and refuses the entire corpus the
tool exists to serve.
"""

import unittest

from auditlog import parse
from tests import fixtures


class TestTurnCounting(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def test_every_exec_brief_is_renderable(self):
        """The isMeta guard, stated as the consequence of getting it wrong."""
        refused = []
        for session in (fixtures.BRIEF_AUG13, fixtures.BRIEF_AUG14, fixtures.BRIEF_AUG15):
            records, _ = parse.load_records(fixtures.path(session))
            report = parse.check_supported(records, fixtures.path(session))
            if not report.ok:
                refused.append((session, report.reasons))
        self.assertEqual(refused, [], "a daily brief was refused")

    def test_briefs_count_exactly_one_turn(self):
        for session in (fixtures.BRIEF_AUG13, fixtures.BRIEF_AUG14, fixtures.BRIEF_AUG15):
            records, _ = parse.load_records(fixtures.path(session))
            self.assertEqual(len(parse.real_turns(records)), 1, session)

    def test_the_isMeta_expansion_exists_and_would_have_been_miscounted(self):
        """Guards against the guard being removed as 'unnecessary'."""
        records, _ = parse.load_records(fixtures.path(fixtures.BRIEF_AUG13))
        meta = [r for r in records if r.get("type") == "user" and r.get("isMeta")]
        self.assertEqual(len(meta), 1)

        naive = [
            r for r in records
            if r.get("type") == "user" and not parse.has_block(r, "tool_result")
        ]
        self.assertEqual(len(naive), 2, "the naive count that would refuse this session")


class TestRefusalConditions(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def _report(self, session):
        path = fixtures.path(session)
        records, _ = parse.load_records(path)
        return parse.check_supported(records, path)

    def test_multi_turn_is_refused_with_its_magnitude(self):
        report = self._report(fixtures.MULTITURN_SMALL)
        self.assertFalse(report.ok)
        self.assertTrue(any(r.kind == "multi_turn" for r in report.reasons))
        message = report.message()
        self.assertIn("user turns", message)
        self.assertIn("not implemented yet", message)

    def test_images_are_refused(self):
        report = self._report(fixtures.IMAGES)
        self.assertTrue(any(r.kind == "images" for r in report.reasons))

    def test_oversized_is_refused(self):
        report = self._report(fixtures.MULTITURN_HUGE)
        self.assertTrue(any(r.kind == "oversized" for r in report.reasons))

    def test_all_conditions_are_reported_not_just_the_first(self):
        """The 44 MB session trips multi-turn and size together."""
        report = self._report(fixtures.MULTITURN_HUGE)
        kinds = sorted(r.kind for r in report.reasons)
        self.assertIn("multi_turn", kinds)
        self.assertIn("oversized", kinds)
        self.assertGreaterEqual(len(report.reasons), 2)

    def test_the_image_session_trips_all_three(self):
        report = self._report(fixtures.IMAGES)
        kinds = sorted(r.kind for r in report.reasons)
        self.assertEqual(kinds, ["images", "multi_turn", "oversized"])

    def test_refusal_message_names_every_condition(self):
        report = self._report(fixtures.IMAGES)
        message = report.message()
        self.assertIn("user turns", message)
        self.assertIn("image", message)
        self.assertIn("MB", message)


class TestCorpusSplit(unittest.TestCase):
    """The measured 15/13 split across the whole greenthumb project."""

    def setUp(self):
        fixtures.require_corpus(self)
        self.renderable = []
        self.refused = []
        for path in fixtures.corpus_sessions():
            records, _ = parse.load_records(path)
            report = parse.check_supported(records, path)
            (self.renderable if report.ok else self.refused).append((path, report))

    def test_fifteen_renderable(self):
        self.assertEqual(len(self.renderable), 15)

    def test_thirteen_refused(self):
        self.assertEqual(len(self.refused), 13)

    def test_image_bearing_files_number_eight(self):
        """Eight, not the four a top-level-only scan finds.

        Images also arrive nested inside `tool_result` content, and those need
        rendering just as much. All eight are already refused for multi-turn as
        well, so counting them correctly does not change the renderable set; it
        changes what the refusal message tells you.
        """
        with_images = [
            r for _, r in self.refused
            if any(x.kind == "images" for x in r.reasons)
        ]
        self.assertEqual(len(with_images), 8)

    def test_every_refusal_states_at_least_one_reason(self):
        for path, report in self.refused:
            self.assertTrue(report.reasons, path)
            self.assertTrue(report.message().strip(), path)


class TestSidechainTripwire(unittest.TestCase):
    """No sidechains exist in this corpus, so this is a tripwire, not a feature."""

    def setUp(self):
        fixtures.require_corpus(self)

    def test_corpus_has_no_sidechains(self):
        for path in fixtures.corpus_sessions():
            records, _ = parse.load_records(path)
            self.assertFalse(
                parse.has_sidechain(records), "unexpected sidechain in %s" % path
            )

    def test_a_synthetic_sidechain_is_detected(self):
        records = [{"type": "assistant", "isSidechain": True, "message": {}}]
        self.assertTrue(parse.has_sidechain(records))


if __name__ == "__main__":
    unittest.main()

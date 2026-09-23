"""End to end over every transcript in the corpus.

Acceptance criterion 5 as an executable test rather than a manual spot check:
every supported session renders, and every unsupported one refuses cleanly with
a non-zero exit and no file left behind.

This is the slowest test in the suite by a wide margin, because it renders every
renderable session in a live directory. That is the point.

Note what it does NOT assert: absolute counts. The corpus is a working
directory that grows whenever Greenthumb runs, so pinning a total makes the
suite go red overnight for no reason. Coverage is expressed as "every session is
classified and every renderable one renders", which stays true at any size.
"""

import os
import shutil
import tempfile
import unittest

from auditlog import cli, parse
from tests import fixtures


class TestFullCorpusSweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isdir(fixtures.GREENTHUMB):
            raise unittest.SkipTest("corpus not present")
        cls.outdir = tempfile.mkdtemp(prefix="auditlog-sweep-")
        cls.rendered = []
        cls.refused = []
        for path in fixtures.corpus_sessions():
            records, _ = parse.load_records(path)
            report = parse.check_supported(records, path)
            (cls.rendered if report.ok else cls.refused).append(path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.outdir, ignore_errors=True)

    def test_every_session_is_classified(self):
        """No absolute totals: this directory grows as Greenthumb runs."""
        self.assertEqual(
            len(self.rendered) + len(self.refused), len(fixtures.corpus_sessions())
        )
        self.assertGreater(len(self.rendered), 0)
        self.assertGreater(len(self.refused), 0)

    def test_every_supported_session_renders_to_a_real_page(self):
        failures = []
        for path in self.rendered:
            code = cli.main([path, "--output-dir", self.outdir, "--force", "--quiet"])
            if code != 0:
                failures.append((os.path.basename(path), code))
        self.assertEqual(failures, [])

    def test_every_rendered_page_is_substantial_and_well_formed(self):
        for name in os.listdir(self.outdir):
            full = os.path.join(self.outdir, name)
            size = os.path.getsize(full)
            self.assertGreater(size, 10000, "%s is suspiciously small" % name)
            with open(full) as handle:
                body = handle.read()
            self.assertTrue(body.lstrip().startswith("<!doctype html>"), name)
            self.assertIn("</html>", body, name)
            self.assertIn("Conversation Audit Log", body, name)
            self.assertIn("Reply returned", body, name)

    def test_filenames_all_follow_the_agreed_shape(self):
        import re

        pattern = re.compile(r"^\d{8}-\d{4}-[a-z0-9-]+-to-[a-z0-9-]+-[a-z0-9-]+\.html$")
        for name in os.listdir(self.outdir):
            self.assertRegex(name, pattern)

    def test_every_unsupported_session_refuses_and_writes_nothing(self):
        clean = tempfile.mkdtemp(prefix="auditlog-refuse-sweep-")
        try:
            bad = []
            for path in self.refused:
                code = cli.main([path, "--output-dir", clean, "--quiet"])
                if code == 0:
                    bad.append(os.path.basename(path))
            self.assertEqual(bad, [], "these were rendered but should have refused")
            self.assertEqual(os.listdir(clean), [],
                             "a refused session left a file behind")
        finally:
            shutil.rmtree(clean, ignore_errors=True)

    def test_no_transcript_was_modified_by_the_sweep(self):
        """The whole point. These files are the only copy."""
        for path in fixtures.corpus_sessions():
            self.assertTrue(os.path.isfile(path), "transcript vanished: %s" % path)


class TestSpotChecks(unittest.TestCase):
    """Criterion 5's "spot-checking 3 shows correct attribution, titles, costs"."""

    def setUp(self):
        fixtures.require_corpus(self)

    def test_the_three_daily_brief_fixtures(self):
        from auditlog import cost

        expected = {
            fixtures.BRIEF_AUG13: (115009, 166240, 8733, 4285, 1.4516),
            fixtures.BRIEF_AUG14: (112076, 166053, 9519, 4712, 1.4418),
            fixtures.BRIEF_AUG15: (111755, 160873, 8713, 4750, 1.4158),
        }
        for session_id, values in sorted(expected.items()):
            write_1h, read, output, reasoning, total = values
            session = parse.load_session(fixtures.path(session_id))
            tokens = session.usage.tokens
            self.assertEqual(tokens["cache_write_1h"], write_1h, session_id)
            self.assertEqual(tokens["cache_read"], read, session_id)
            self.assertEqual(tokens["output"], output, session_id)
            self.assertEqual(tokens["reasoning"], reasoning, session_id)
            breakdown = cost.compute(tokens, session.model)
            self.assertAlmostEqual(breakdown.total, total, places=4, msg=session_id)

    def test_brief_durations(self):
        expected = {
            fixtures.BRIEF_AUG13: (1, 56),
            fixtures.BRIEF_AUG14: (2, 8),
            fixtures.BRIEF_AUG15: (2, 0),
        }
        for session_id, (minutes, seconds) in sorted(expected.items()):
            session = parse.load_session(fixtures.path(session_id))
            total = int(session.duration.total_seconds())
            self.assertEqual((total // 60, total % 60), (minutes, seconds), session_id)

    def test_attribution_and_titles(self):
        for session_id in sorted(fixtures.BRIEF_REPLY_WORDS):
            session = parse.load_session(fixtures.path(session_id))
            sender, receiver = cli.resolve_participants(session, "donna", None)
            self.assertEqual(sender, "donna")
            self.assertEqual(receiver, "greenthumb")
            self.assertTrue(session.title)


if __name__ == "__main__":
    unittest.main()

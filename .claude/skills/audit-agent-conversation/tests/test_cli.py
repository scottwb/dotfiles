"""The command line, participant resolution, and where files land.

Output goes to `~/.ai-staff-audit-log/`: created if missing, never source
controlled, never inside the dotfiles repo, never deleted from, and never
overwritten without `--force`.

Every test here writes into a temporary directory instead, so running the suite
never touches the real output directory.
"""

import os
import shutil
import tempfile
import unittest

from auditlog import cli
from tests import fixtures


class TestSlugging(unittest.TestCase):
    def test_slug_from_prose(self):
        self.assertEqual(cli.slugify("Commit pending files and prioritize"),
                         "commit-pending-files-and-prioritize")

    def test_slug_from_a_slash_command(self):
        self.assertEqual(cli.slugify("/exec-brief full"), "exec-brief-full")

    def test_punctuation_and_case_are_flattened(self):
        self.assertEqual(cli.slugify("Zone 1: catch-cup test!"), "zone-1-catch-cup-test")

    def test_runs_of_separators_collapse(self):
        self.assertEqual(cli.slugify("a   ---   b"), "a-b")

    def test_slug_is_length_capped(self):
        slug = cli.slugify("word " * 60)
        self.assertLessEqual(len(slug), cli.SLUG_MAX)
        self.assertFalse(slug.endswith("-"))

    def test_empty_input_yields_a_usable_fallback(self):
        self.assertTrue(cli.slugify(""))

    def test_unicode_is_not_smuggled_into_a_filename(self):
        slug = cli.slugify("café ☕ report")
        self.assertTrue(all(c.isalnum() or c == "-" for c in slug), slug)


class TestParticipantResolution(unittest.TestCase):
    def test_project_map_supplies_both_ends(self):
        self.assertEqual(cli.agent_for_project("-Users-scottwb-src-scottwb-greenthumb"),
                         "greenthumb")
        self.assertEqual(cli.agent_for_project("-Users-scottwb-src-scottwb-donna-smithers"),
                         "donna")

    def test_unmapped_project_falls_back_to_its_last_segment(self):
        self.assertEqual(cli.agent_for_project("-Users-scottwb-src-acme-widget"), "widget")

    def test_explicit_flags_win_over_everything(self):
        session = _fake_session(agent_name="Greenthumb", cwd="/Users/scottwb/src/x/y")
        sender, receiver = cli.resolve_participants(session, "alice", "bob")
        self.assertEqual((sender, receiver), ("alice", "bob"))

    def test_agent_name_supplies_the_receiver_when_present(self):
        session = _fake_session(agent_name="Greenthumb",
                                cwd="/Users/scottwb/src/scottwb/greenthumb")
        _, receiver = cli.resolve_participants(session, None, None)
        self.assertEqual(receiver, "Greenthumb")

    def test_project_map_supplies_the_receiver_when_agent_name_is_absent(self):
        """F3: agent-name is absent from the entire target corpus."""
        session = _fake_session(agent_name=None,
                                cwd="/Users/scottwb/src/scottwb/greenthumb")
        _, receiver = cli.resolve_participants(session, None, None)
        self.assertEqual(receiver, "greenthumb")

    def test_sender_defaults_to_scott_for_an_interactive_session(self):
        session = _fake_session(agent_name=None, cwd="/tmp/x", entrypoint="cli")
        sender, _ = cli.resolve_participants(session, None, None)
        self.assertEqual(sender, "scott")


class TestOutputNaming(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def test_brief_filename_shape(self):
        from auditlog import parse

        session = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        name = cli.output_filename(session, "donna", "greenthumb")
        self.assertTrue(name.startswith("20260813-0557-donna-to-greenthumb-"), name)
        self.assertTrue(name.endswith(".html"))

    def test_filenames_sort_chronologically(self):
        from auditlog import parse

        names = []
        for session_id in (fixtures.BRIEF_AUG15, fixtures.BRIEF_AUG13, fixtures.BRIEF_AUG14):
            session = parse.load_session(fixtures.path(session_id))
            names.append(cli.output_filename(session, "donna", "greenthumb"))
        self.assertEqual(sorted(names), sorted(names, key=lambda n: n[:13]))
        self.assertEqual([n[:8] for n in sorted(names)],
                         ["20260813", "20260814", "20260815"])

    def test_initiator_glob_works(self):
        import fnmatch
        from auditlog import parse

        session = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        name = cli.output_filename(session, "donna", "greenthumb")
        self.assertTrue(fnmatch.fnmatch(name, "*-donna-to-*"))


class TestWriting(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.outdir = tempfile.mkdtemp(prefix="auditlog-test-")

    def tearDown(self):
        shutil.rmtree(self.outdir, ignore_errors=True)

    def _run(self, *args):
        return cli.main(list(args) + ["--output-dir", self.outdir, "--quiet"])

    def test_writes_a_page_and_exits_zero(self):
        code = self._run(fixtures.path(fixtures.BRIEF_AUG13), "--from", "donna",
                         "--to", "greenthumb")
        self.assertEqual(code, 0)
        written = os.listdir(self.outdir)
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].endswith(".html"))
        with open(os.path.join(self.outdir, written[0])) as handle:
            self.assertIn("<!doctype html>", handle.read())

    def test_creates_the_output_directory_if_absent(self):
        nested = os.path.join(self.outdir, "does", "not", "exist")
        code = cli.main([fixtures.path(fixtures.BRIEF_AUG13), "--output-dir", nested,
                         "--quiet"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isdir(nested))

    def test_second_run_refuses_to_overwrite(self):
        self._run(fixtures.path(fixtures.BRIEF_AUG13))
        written = os.listdir(self.outdir)
        before = os.path.getsize(os.path.join(self.outdir, written[0]))

        code = self._run(fixtures.path(fixtures.BRIEF_AUG13))
        self.assertNotEqual(code, 0, "overwrote without --force")
        after = os.path.getsize(os.path.join(self.outdir, written[0]))
        self.assertEqual(before, after)

    def test_force_overwrites(self):
        self._run(fixtures.path(fixtures.BRIEF_AUG13))
        code = self._run(fixtures.path(fixtures.BRIEF_AUG13), "--force")
        self.assertEqual(code, 0)
        self.assertEqual(len(os.listdir(self.outdir)), 1)

    def test_explicit_output_path(self):
        target = os.path.join(self.outdir, "custom.html")
        code = cli.main([fixtures.path(fixtures.BRIEF_AUG13), "-o", target, "--quiet"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(target))

    def test_stdout_mode_writes_no_file(self):
        import io
        import sys

        buffer = io.StringIO()
        stdout, sys.stdout = sys.stdout, buffer
        try:
            code = cli.main([fixtures.path(fixtures.BRIEF_AUG13), "--stdout",
                             "--output-dir", self.outdir])
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        self.assertIn("<!doctype html>", buffer.getvalue())
        self.assertEqual(os.listdir(self.outdir), [])


class TestRefusal(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.outdir = tempfile.mkdtemp(prefix="auditlog-refuse-")

    def tearDown(self):
        shutil.rmtree(self.outdir, ignore_errors=True)

    def test_multi_turn_session_exits_nonzero_and_writes_nothing(self):
        code = cli.main([fixtures.path(fixtures.MULTITURN_SMALL),
                         "--output-dir", self.outdir])
        self.assertNotEqual(code, 0)
        self.assertEqual(os.listdir(self.outdir), [],
                         "a refused session left a file behind")

    def test_refusal_message_reaches_stderr(self):
        import io
        import sys

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            cli.main([fixtures.path(fixtures.MULTITURN_SMALL),
                      "--output-dir", self.outdir])
        finally:
            sys.stderr = stderr
        message = buffer.getvalue()
        self.assertIn("user turns", message)
        self.assertIn("not implemented yet", message)

    def test_image_session_is_refused(self):
        code = cli.main([fixtures.path(fixtures.IMAGES), "--output-dir", self.outdir,
                         "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertEqual(os.listdir(self.outdir), [])


class TestArgumentHandling(unittest.TestCase):
    def test_help_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_unresolvable_session_exits_nonzero_with_a_message(self):
        import io
        import sys

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = cli.main(["--project", "definitely-not-real-xyzzy"])
        finally:
            sys.stderr = stderr
        self.assertNotEqual(code, 0)
        self.assertTrue(buffer.getvalue().strip())


def _fake_session(agent_name=None, cwd="/tmp/x", entrypoint="sdk-cli"):
    class Fake(object):
        pass

    fake = Fake()
    fake.agent_name = agent_name
    fake.cwd = cwd
    fake.entrypoint = entrypoint
    return fake


if __name__ == "__main__":
    unittest.main()

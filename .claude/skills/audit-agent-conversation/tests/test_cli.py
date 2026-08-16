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

    def test_second_run_does_not_overwrite(self):
        """The page is left alone. That is the invariant; the exit code is not.

        Re-running is a no-op, not a failure: it exits 0 and reports the skip,
        so running the tool over a batch of sessions does not fail the batch
        just because some pages already exist.
        """
        import io
        import sys

        self._run(fixtures.path(fixtures.BRIEF_AUG13))
        written = os.listdir(self.outdir)
        target = os.path.join(self.outdir, written[0])
        with open(target, "rb") as handle:
            before = handle.read()

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = self._run(fixtures.path(fixtures.BRIEF_AUG13))
        finally:
            sys.stderr = stderr

        with open(target, "rb") as handle:
            self.assertEqual(handle.read(), before, "the page was modified")
        self.assertEqual(code, 0)
        self.assertEqual(os.listdir(self.outdir), written, "wrote an extra file")

        message = buffer.getvalue()
        self.assertIn("EXISTS", message)
        self.assertIn("--force", message)
        self.assertNotIn("error", message.lower())

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


class TestOutputFormatting(unittest.TestCase):
    """Every line the tool prints starts with a status marker, so a run reads
    as a column of outcomes rather than a paragraph."""

    def test_home_is_shortened_to_a_tilde(self):
        home = os.path.expanduser("~")
        self.assertEqual(cli.tilde(os.path.join(home, "x", "y.html")), "~/x/y.html")
        self.assertEqual(cli.tilde(home), "~")

    def test_paths_outside_home_are_left_alone(self):
        self.assertEqual(cli.tilde("/tmp/x.html"), "/tmp/x.html")

    def test_a_lookalike_prefix_is_not_shortened(self):
        """`/Users/scottwbXX` must not become `~XX`."""
        home = os.path.expanduser("~")
        self.assertEqual(cli.tilde(home + "-other/x"), home + "-other/x")

    def test_sizes_read_like_ls_h(self):
        self.assertEqual(cli.human_size(512), "512 bytes")
        self.assertEqual(cli.human_size(410 * 1024), "410 KB")
        self.assertEqual(cli.human_size(int(4.3 * 1024 * 1024)), "4.3 MB")
        self.assertEqual(cli.human_size(int(1.5 * 1024)), "1.5 KB")

    def test_a_written_page_reports_as_a_wrote_row(self):
        import io
        import shutil
        import sys
        import tempfile

        fixtures.require_corpus(self)
        outdir = tempfile.mkdtemp(prefix="auditlog-fmt-")
        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = cli.main([fixtures.path(fixtures.BRIEF_AUG13),
                             "--output-dir", outdir, "--force"])
        finally:
            sys.stderr = stderr
            shutil.rmtree(outdir, ignore_errors=True)

        self.assertEqual(code, 0)
        lines = buffer.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 3, lines)          # header, rule, row
        self.assertTrue(lines[0].strip().startswith("STATUS"), lines[0])
        self.assertEqual(lines[1], "-" * cli.LINE_WIDTH)
        self.assertTrue(lines[2].startswith(cli.OK), lines[2])
        self.assertIn("WROTE", lines[2])
        self.assertIn("KB", lines[2])

    def test_no_header_suppresses_the_header_and_rule(self):
        import io
        import shutil
        import sys
        import tempfile

        fixtures.require_corpus(self)
        outdir = tempfile.mkdtemp(prefix="auditlog-nohdr-")
        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            cli.main([fixtures.path(fixtures.BRIEF_AUG13), "--output-dir", outdir,
                      "--force", "--no-header"])
        finally:
            sys.stderr = stderr
            shutil.rmtree(outdir, ignore_errors=True)

        lines = buffer.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("WROTE", lines[0])

    def test_the_header_appears_once_no_matter_how_many_rows(self):
        import io
        import sys

        buffer = io.StringIO()
        report = cli.Report(buffer)
        report.row("SKIPPED", "aaaa1111", "08-16 00:00", "Human (3 turns)",
                   "scott", "donna", "One")
        report.row("SKIPPED", "bbbb2222", "08-16 00:01", "Human (4 turns)",
                   "scott", "donna", "Two")
        lines = buffer.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines.count("-" * cli.LINE_WIDTH), 1)

    def test_a_run_with_no_rows_prints_no_header(self):
        import io

        buffer = io.StringIO()
        cli.Report(buffer)
        self.assertEqual(buffer.getvalue(), "")


class TestWroteDetail(unittest.TestCase):
    """The DETAIL cell on a WROTE row: what the page is, and how big."""

    NAME = ("20260813-0917-caller-to-donna-"
            "clarify-push-authority-and-write-ladder.html")

    def _started(self):
        import datetime

        return datetime.datetime(2026, 8, 13, 9, 17)

    def test_the_redundant_prefix_is_stripped(self):
        """Timestamp and participants are already in the columns beside it."""
        label = cli.page_label(self.NAME, "caller", "donna", self._started())
        self.assertEqual(label, "clarify-push-authority-and-write-ladder")

    def test_the_label_globs(self):
        """`ls ~/.ai-staff-audit-log/*clarify-push*` has to find the file."""
        label = cli.page_label(self.NAME, "caller", "donna", self._started())
        self.assertIn(label, self.NAME)

    def test_a_name_that_is_not_ours_is_left_alone(self):
        """`-o custom.html` does not follow the pattern."""
        self.assertEqual(
            cli.page_label("custom.html", "caller", "donna", self._started()),
            "custom",
        )

    def test_a_mismatched_prefix_is_left_alone(self):
        self.assertEqual(
            cli.page_label(self.NAME, "someone", "else", self._started()),
            self.NAME[:-5],
        )

    def test_short_labels_are_shown_whole(self):
        self.assertEqual(cli.wrote_detail("a-page", "12 KB", 30), "a-page (12 KB)")

    def test_the_size_is_never_truncated(self):
        detail = cli.wrote_detail("clarify-push-authority-and-write-ladder",
                                  "104 KB", 28)
        self.assertTrue(detail.endswith("(104 KB)"), detail)

    def test_the_cell_respects_its_width(self):
        for width in (20, 28, 40):
            detail = cli.wrote_detail(
                "clarify-push-authority-and-write-ladder", "104 KB", width)
            self.assertLessEqual(len(detail), width, detail)

    def test_the_front_of_the_label_survives(self):
        detail = cli.wrote_detail("clarify-push-authority-and-write-ladder",
                                  "104 KB", 28)
        self.assertTrue(detail.startswith("clarify-push"), detail)
        self.assertIn("...", detail)


class TestHelp(unittest.TestCase):
    """Usable by a human or an agent that has never seen the tool."""

    def _help(self):
        parser = cli.build_parser()
        return parser.format_help()

    def test_help_documents_every_flag(self):
        text = self._help()
        for flag in ("--project", "--latest", "--date", "--today", "--week",
                     "--from", "--to", "-o", "--output-dir", "--stdout",
                     "--force", "--quiet", "--no-header", "--all"):
            self.assertIn(flag, text, flag)

    def test_help_explains_the_default_selection(self):
        self.assertIn("latest session that CAN be rendered", self._help())

    def test_help_lists_every_exit_code_the_cli_returns(self):
        text = self._help()
        for code in ("0", "2", "3", "4", "5", "7"):
            self.assertRegex(text, r"\n  %s  " % code)

    def test_help_says_what_v1_refuses(self):
        text = self._help()
        self.assertIn("Multi-turn", text)
        self.assertIn("images", text)
        self.assertIn("8 MB", text)

    def test_help_shows_worked_examples(self):
        text = self._help()
        self.assertIn("--all --week", text)
        self.assertIn("audit-agent-conversation --project greenthumb", text)

    def test_help_states_the_read_only_guarantee(self):
        self.assertIn("never writes there", self._help())

    def test_a_bad_flag_prints_the_whole_help_not_just_usage(self):
        import io
        import sys

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            with self.assertRaises(SystemExit) as ctx:
                cli.main(["--not-a-real-flag"])
        finally:
            sys.stderr = stderr
        self.assertEqual(ctx.exception.code, 2)
        text = buffer.getvalue()
        self.assertIn("error:", text)
        self.assertIn("examples", text)
        self.assertIn("exit codes", text)


class TestMarkers(unittest.TestCase):
    """The property that makes the table line up on somebody else's terminal."""

    def test_markers_cannot_break_alignment(self):
        """One codepoint, Wide, no variation selector.

        A variation-selector emoji is Neutral width, so terminals disagree
        about whether it takes one cell or two. Mixing widths in the first
        column means no amount of padding is right for everyone, which is
        exactly what went wrong twice before this rule existed.
        """
        import unicodedata

        for status, marker in sorted(cli.MARKERS.items()):
            glyph = marker.rstrip(" ")
            self.assertEqual(len(glyph), 1,
                             "%s: %r is not a single codepoint" % (status, glyph))
            self.assertNotIn("️", glyph, "%s carries a variation selector" % status)
            self.assertEqual(unicodedata.east_asian_width(glyph), "W",
                             "%s: %r is not Wide" % (status, glyph))

    def test_every_marker_ends_with_exactly_one_space(self):
        for status, marker in sorted(cli.MARKERS.items()):
            self.assertTrue(marker.endswith(" "), status)
            self.assertFalse(marker.endswith("  "), status)

    def test_every_outcome_has_its_own_marker(self):
        self.assertEqual(sorted(cli.MARKERS), ["ERROR", "EXISTS", "SKIPPED", "WROTE"])
        self.assertEqual(len(set(cli.MARKERS.values())), len(cli.MARKERS))

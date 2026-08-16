"""`--latest` means the latest session that can actually be rendered.

Taking it literally made the common case a refusal for a session nobody chose:
in any project you also work in by hand, the newest transcript is usually an
interactive multi-turn session. Walking back to the newest qualifying one fixes
that, but only stays honest because every session passed over is named on
stderr. Silently deciding a session "did not count" would be the wrong trade in
an audit tool.
"""

import json
import os
import shutil
import tempfile
import unittest

from auditlog import cli, parse, resolve
from tests import fixtures


def _session(path, turns=1, entrypoint="sdk-cli", title=None, when="2026-08-16T12:00:00.000Z"):
    """Write a synthetic transcript with a controllable turn count."""
    lines = []
    if title:
        lines.append({"type": "ai-title", "aiTitle": title})
    for index in range(turns):
        lines.append({
            "type": "user",
            "parentUuid": None if index == 0 else "u%d" % index,
            "message": {"content": "turn %d" % index},
            "timestamp": when, "cwd": "/tmp/x", "version": "1.0.0",
            "entrypoint": entrypoint, "sessionId": os.path.basename(path)[:-6],
        })
        lines.append({
            "type": "assistant", "timestamp": when, "entrypoint": entrypoint,
            "message": {"id": "m%d" % index, "model": "claude-opus-5",
                        "content": [{"type": "text", "text": "reply %d" % index}],
                        "usage": {"input_tokens": 5, "output_tokens": 5}},
        })
    with open(path, "w") as handle:
        handle.write("\n".join(json.dumps(x) for x in lines))
    return path


class TestSkipRowShape(unittest.TestCase):
    def _line(self, **kwargs):
        tmp = tempfile.mkdtemp(prefix="auditlog-skipline-")
        try:
            path = _session(os.path.join(tmp, "abcd1234-ffff.jsonl"), **kwargs)
            records, _ = parse.load_records(path)
            report = parse.check_supported(records, path)
            return cli.skip_row(parse.describe(records, path), report.reasons)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_is_an_aligned_row_of_seven_fields(self):
        line = self._line(turns=3, entrypoint="cli", title="Some session title")
        self.assertIn("SKIPPED", line)
        self.assertEqual(len(line.split(" | ")), 7, line)

    def test_fits_the_line_budget(self):
        long_title = " ".join("word%d" % i for i in range(30))
        line = self._line(turns=99, entrypoint="cli", title=long_title)
        # The marker is two display columns; count it as such rather than as
        # the one or two code points it happens to be.
        width = len(line) - len(cli.MARKERS["SKIPPED"]) + 2
        self.assertLessEqual(width, cli.LINE_WIDTH, line)

    def test_columns_land_at_the_same_offsets_on_every_row(self):
        a = self._line(turns=3, entrypoint="cli", title="Short")
        b = self._line(turns=99, entrypoint="sdk-cli",
                       title="A considerably longer title than the other one")
        self.assertEqual([len(f) for f in a.split(" | ")[:-1]],
                         [len(f) for f in b.split(" | ")[:-1]])

    def test_names_the_session_and_when_it_started(self):
        line = self._line(turns=3, entrypoint="cli", title="A title")
        self.assertIn("abcd1234", line)
        self.assertIn("08-16", line)

    def test_a_human_driven_session_says_human(self):
        """"Human (3 turns)" answers the question you are actually asking."""
        line = self._line(turns=3, entrypoint="cli", title="A title")
        self.assertIn("Human (3 turns)", line)

    def test_an_agent_driven_session_says_agent(self):
        line = self._line(turns=4, entrypoint="sdk-cli", title="A title")
        self.assertIn("Agent (4 turns)", line)
        self.assertNotIn("Human", line)

    def test_an_overlong_title_is_truncated_with_an_ellipsis(self):
        long_title = " ".join("word%d" % i for i in range(30))
        line = self._line(turns=2, entrypoint="cli", title=long_title)
        subject = line.split(" | ")[6]
        self.assertTrue(subject.endswith("..."), subject)
        self.assertEqual(len(subject), cli.COL_SUBJECT)

    def test_an_untitled_session_says_so_rather_than_showing_a_blank(self):
        line = self._line(turns=2, entrypoint="cli", title=None)
        self.assertTrue(line.split(" | ")[6].strip())

    def test_the_row_names_both_participants(self):
        line = self._line(turns=3, entrypoint="cli", title="A title")
        self.assertTrue(line.split(" | ")[4].strip(), "no sender")
        self.assertTrue(line.split(" | ")[5].strip(), "no receiver")

    def test_reasons_are_short_not_the_full_refusal_prose(self):
        line = self._line(turns=3, entrypoint="cli", title="A title")
        self.assertNotIn("not implemented yet", line)


class TestWalk(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="auditlog-walk-")
        self.project = os.path.join(self.tmp, "-Users-someone-src-thing")
        os.makedirs(self.project)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _add(self, name, mtime, **kwargs):
        path = _session(os.path.join(self.project, name + ".jsonl"), **kwargs)
        os.utime(path, (mtime, mtime))
        return path

    def test_takes_the_newest_when_it_qualifies(self):
        self._add("aaaa1111", 1000, turns=1)
        newest = self._add("bbbb2222", 2000, turns=1)
        path, skips = cli.latest_renderable(self.project)
        self.assertEqual(path, newest)
        self.assertEqual(skips, [])

    def test_walks_past_unqualifying_sessions_to_the_first_that_qualifies(self):
        good = self._add("aaaa1111", 1000, turns=1)
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli")
        self._add("cccc3333", 3000, turns=9, entrypoint="cli")
        path, skips = cli.latest_renderable(self.project)
        self.assertEqual(path, good)
        self.assertEqual(len(skips), 2)

    def test_skips_are_reported_newest_first(self):
        self._add("aaaa1111", 1000, turns=1)
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli")
        self._add("cccc3333", 3000, turns=9, entrypoint="cli")
        _, skips = cli.latest_renderable(self.project)
        self.assertIn("cccc3333", skips[0])
        self.assertIn("bbbb2222", skips[1])

    def test_returns_none_when_nothing_qualifies(self):
        self._add("aaaa1111", 1000, turns=4, entrypoint="cli")
        self._add("bbbb2222", 2000, turns=7, entrypoint="cli")
        path, skips = cli.latest_renderable(self.project)
        self.assertIsNone(path)
        self.assertEqual(len(skips), 2)

    def test_an_oversized_transcript_is_skipped_without_parsing_it(self):
        """Reading 44 MB to print one line about skipping it is not acceptable."""
        self._add("aaaa1111", 1000, turns=1)
        big = os.path.join(self.project, "bbbb2222.jsonl")
        with open(big, "w") as handle:
            handle.write('{"type":"ai-title","aiTitle":"Huge session"}\n')
            filler = json.dumps({"type": "user", "message": {"content": "x" * 900}})
            for _ in range(12000):
                handle.write(filler + "\n")
        os.utime(big, (2000, 2000))
        self.assertGreater(os.path.getsize(big), parse.MAX_TRANSCRIPT_BYTES)

        path, skips = cli.latest_renderable(self.project)
        self.assertTrue(path.endswith("aaaa1111.jsonl"))
        self.assertEqual(len(skips), 1)
        self.assertIn("MB", skips[0])
        self.assertIn("Huge session", skips[0])


class TestWalkThroughTheCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="auditlog-walkcli-")
        self.projects = os.path.join(self.tmp, "projects")
        self.project = os.path.join(self.projects, "-Users-someone-src-thing")
        os.makedirs(self.project)
        self.out = os.path.join(self.tmp, "out")
        self._real_root = resolve.PROJECTS_ROOT
        resolve.PROJECTS_ROOT = self.projects

    def tearDown(self):
        resolve.PROJECTS_ROOT = self._real_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _add(self, name, mtime, **kwargs):
        path = _session(os.path.join(self.project, name + ".jsonl"), **kwargs)
        os.utime(path, (mtime, mtime))
        return path

    def _run(self, *args):
        import io
        import sys

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = cli.main(list(args) + ["--project", "thing",
                                          "--output-dir", self.out, "--quiet"])
        finally:
            sys.stderr = stderr
        return code, buffer.getvalue()

    def test_skip_notices_reach_stderr_with_an_info_marker(self):
        self._add("aaaa1111", 1000, turns=1)
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli")
        code, err = self._run()
        self.assertEqual(code, 0)
        self.assertIn("bbbb2222", err)
        self.assertIn("SKIPPED", err)
        self.assertIn(cli.INFO, err)

    def test_exhausted_walk_exits_two_and_explains(self):
        self._add("aaaa1111", 1000, turns=4, entrypoint="cli")
        code, err = self._run()
        self.assertEqual(code, 2)
        self.assertIn("no renderable session", err)
        self.assertIn("aaaa1111", err)
        self.assertFalse(os.path.isdir(self.out), "wrote output despite finding none")

    def test_an_explicitly_named_session_does_not_walk(self):
        """Naming a session means that session. Refuse it, do not wander off."""
        self._add("aaaa1111", 1000, turns=1)
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli")
        code, err = self._run("bbbb2222")
        self.assertEqual(code, 3)
        self.assertNotIn("SKIPPED", err)
        self.assertIn("user turns", err)
        self.assertIn("bbbb2222", err)

    def test_a_date_walks_within_that_day(self):
        """Naming a day means a session from that day, so skipping an
        unsupported one to reach a usable one is the same courtesy --latest
        gets."""
        self._add("aaaa1111", 1000, turns=1, when="2026-08-16T09:00:00.000Z")
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli",
                  when="2026-08-16T10:00:00.000Z")
        code, err = self._run("--date", "2026-08-16")
        self.assertEqual(code, 0)
        self.assertIn("bbbb2222", err)   # the one it skipped
        # _run passes --quiet, so the written page is evidence, not a row.
        self.assertEqual(len(os.listdir(self.out)), 1)

    def test_a_date_never_walks_off_its_day(self):
        """The walk is bounded by the date. A renderable session on another
        day is not a substitute for the one that was asked for."""
        self._add("aaaa1111", 1000, turns=1, when="2026-08-15T09:00:00.000Z")
        self._add("bbbb2222", 2000, turns=5, entrypoint="cli",
                  when="2026-08-16T10:00:00.000Z")
        code, err = self._run("--date", "2026-08-16")
        self.assertEqual(code, 2)
        self.assertIn("no renderable session", err)
        self.assertIn("2026-08-16", err)
        self.assertNotIn("aaaa1111", err)

    def test_an_unknown_date_still_errors(self):
        self._add("aaaa1111", 1000, turns=1, when="2026-08-16T09:00:00.000Z")
        code, err = self._run("--date", "1999-01-01")
        self.assertEqual(code, 2)
        self.assertIn("1999-01-01", err)


if __name__ == "__main__":
    unittest.main()

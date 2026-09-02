"""The index: every conversation there is to render, not just those rendered.

Scans the project directories, lists every session across the fleet newest
first, marks which have a page on disk, links only those, and gives an
ungenerated renderable row the exact command that would produce it, with a
copy button. Deliberately not a web app: nothing on the page executes
anything, the copy button is a clipboard write, and the page has no path back
to the transcript store.

Every test here builds a fake projects tree in a temporary directory and
writes only into a temporary output directory. The real transcript store and
the real output directory are never touched.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

from auditlog import cli, index, resolve
from tests.test_self_contained import DEPENDENCY_PATTERNS


def _record_lines(model="claude-opus-5", turns=1, title=None, cwd="/tmp/x"):
    lines = []
    if title:
        lines.append({"type": "ai-title", "aiTitle": title})
    stamp = 0
    for turn in range(turns):
        lines.append({
            "type": "user", "parentUuid": None if turn == 0 else "p",
            "message": {"content": "turn %d" % turn}, "cwd": cwd,
            "timestamp": "2026-08-15T12:00:%02d.000Z" % stamp,
            "sessionId": None, "entrypoint": "sdk-cli",
        })
        stamp += 1
        lines.append({
            "type": "assistant", "cwd": cwd,
            "timestamp": "2026-08-15T12:00:%02d.000Z" % stamp,
            "message": {"id": "m%d" % turn, "model": model,
                        "content": [{"type": "text", "text": "reply %d" % turn}],
                        "usage": {"input_tokens": 3, "output_tokens": 1}},
        })
        stamp += 1
    return lines


class FakeFleet(unittest.TestCase):
    """Two projects, three sessions: one rendered, one not, one unsupported."""

    RENDERED = "aaaaaaaa-0000-0000-0000-000000000001"
    PENDING = "bbbbbbbb-0000-0000-0000-000000000002"
    HUMAN = "cccccccc-0000-0000-0000-000000000003"

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="auditlog-index-")
        self.projects = os.path.join(self.tmp, "projects")
        self.outdir = os.path.join(self.tmp, "out")
        os.makedirs(self.outdir)
        self.greenthumb = os.path.join(self.projects, "-Users-someone-src-greenthumb")
        self.donna = os.path.join(self.projects, "-Users-someone-src-donna")
        os.makedirs(self.greenthumb)
        os.makedirs(self.donna)

        self._write(self.greenthumb, self.RENDERED,
                    _record_lines(title="Water the beans",
                                  cwd="/Users/someone/src/greenthumb"))
        self._write(self.greenthumb, self.PENDING,
                    _record_lines(title="Prune the roses",
                                  cwd="/Users/someone/src/greenthumb"))
        self._write(self.donna, self.HUMAN,
                    _record_lines(turns=3, title="Chatting with Donna",
                                  cwd="/Users/someone/src/donna"))

        self._real_root = resolve.PROJECTS_ROOT
        resolve.PROJECTS_ROOT = self.projects

        # Render exactly one of them, so the index has one page to find.
        code = cli.main([os.path.join(self.greenthumb, self.RENDERED + ".jsonl"),
                         "--output-dir", self.outdir, "--quiet"])
        self.assertEqual(code, 0)
        pages = [n for n in os.listdir(self.outdir) if n.endswith(".html")]
        self.assertEqual(len(pages), 1)
        self.page = pages[0]

    def tearDown(self):
        resolve.PROJECTS_ROOT = self._real_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, project, session_id, lines):
        for line in lines:
            if line.get("type") in ("user", "assistant"):
                line["sessionId"] = session_id
        with open(os.path.join(project, session_id + ".jsonl"), "w") as fh:
            fh.write("\n".join(json.dumps(x) for x in lines))

    def _args(self, **overrides):
        parser = cli.build_parser()
        args = parser.parse_args(["--index", "--output-dir", self.outdir])
        for key, value in overrides.items():
            setattr(args, key, value)
        return args

    def _entries(self):
        return index.scan(self._args(), self.outdir)

    def _html(self):
        return index.page(self._entries(), self.outdir)


class TestScan(FakeFleet):
    def test_lists_every_session_renderable_or_not(self):
        ids = sorted(e.description.session_id for e in self._entries())
        self.assertEqual(ids, sorted([self.RENDERED, self.PENDING, self.HUMAN]))

    def test_marks_which_have_a_page_on_disk(self):
        by_id = {e.description.session_id: e for e in self._entries()}
        self.assertEqual(by_id[self.RENDERED].page, self.page)
        self.assertIsNone(by_id[self.PENDING].page)
        self.assertIsNone(by_id[self.HUMAN].page)

    def test_knows_which_are_renderable(self):
        by_id = {e.description.session_id: e for e in self._entries()}
        self.assertTrue(by_id[self.RENDERED].renderable)
        self.assertTrue(by_id[self.PENDING].renderable)
        self.assertFalse(by_id[self.HUMAN].renderable)
        self.assertIn("3 turns", by_id[self.HUMAN].reason)

    def test_an_ungenerated_row_carries_the_command_that_would_produce_it(self):
        by_id = {e.description.session_id: e for e in self._entries()}
        command = by_id[self.PENDING].command
        self.assertTrue(command.startswith("audit-agent-conversation "), command)
        self.assertIn(self.PENDING, command)
        self.assertIn("--project -Users-someone-src-greenthumb", command)

    def test_a_generated_row_and_an_unsupported_row_carry_no_command(self):
        by_id = {e.description.session_id: e for e in self._entries()}
        self.assertIsNone(by_id[self.RENDERED].command)
        self.assertIsNone(by_id[self.HUMAN].command)

    def test_the_scan_only_reads_the_transcript_store(self):
        """Nothing new appears under the fake projects tree after a scan."""
        before = sorted(os.listdir(self.greenthumb) + os.listdir(self.donna))
        self._entries()
        after = sorted(os.listdir(self.greenthumb) + os.listdir(self.donna))
        self.assertEqual(before, after)


class TestPage(FakeFleet):
    def test_links_only_the_rows_that_have_pages(self):
        html = self._html()
        self.assertIn('href="%s"' % self.page, html)
        self.assertEqual(html.count("<a "), 1, "exactly one row is linked")

    def test_names_every_session(self):
        html = self._html()
        for title in ("Water the beans", "Prune the roses", "Chatting with Donna"):
            self.assertIn(title, html)

    def test_an_ungenerated_row_shows_its_command_and_a_copy_button(self):
        html = self._html()
        self.assertIn("audit-agent-conversation %s" % self.PENDING, html)
        self.assertIn("data-copy=", html)
        self.assertEqual(html.count("data-copy="), 1)

    def test_an_unsupported_row_says_why_and_offers_no_command(self):
        html = self._html()
        self.assertIn("3 turns", html)
        self.assertNotIn("audit-agent-conversation %s" % self.HUMAN, html)

    def test_newest_first(self):
        # Every fixture starts at 12:00:00, so break the tie by mtime, which the
        # scan sorts by too. Touch the pending session so it is newest.
        pending = os.path.join(self.greenthumb, self.PENDING + ".jsonl")
        os.utime(pending, (2000000000, 2000000000))
        html = self._html()
        self.assertLess(html.index("Prune the roses"), html.index("Water the beans"))

    def test_start_time_wins_over_file_mtime(self):
        """A session that STARTED later sorts first, even if an older session's
        transcript was touched more recently. The index is a timeline of
        conversations, not of file writes; mtime only breaks ties."""
        later = "dddddddd-0000-0000-0000-000000000004"
        lines = _record_lines(title="Started later", cwd="/Users/someone/src/donna")
        for line in lines:
            if "timestamp" in line:
                line["timestamp"] = line["timestamp"].replace("2026-08-15", "2026-08-20")
        self._write(self.donna, later, lines)
        os.utime(os.path.join(self.donna, later + ".jsonl"), (1500000000, 1500000000))
        pending = os.path.join(self.greenthumb, self.PENDING + ".jsonl")
        os.utime(pending, (2000000000, 2000000000))
        ids = [e.description.session_id for e in self._entries()]
        self.assertEqual(ids[0], later)
        self.assertEqual(ids[1], self.PENDING)

    def test_makes_zero_external_requests(self):
        html = self._html()
        found = [label for pattern, label in DEPENDENCY_PATTERNS
                 if re.search(pattern, html, re.I)]
        self.assertEqual(found, [])
        self.assertNotIn("<script src", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_declares_itself_so_a_rebuild_can_recognise_it(self):
        self.assertIn(index.MARKER, self._html())

    def test_page_is_a_complete_document(self):
        html = self._html()
        self.assertTrue(html.lstrip().startswith("<!doctype html>"))
        self.assertIn("</html>", html)
        self.assertIn("<style>", html)

    def test_is_byte_reproducible(self):
        """No clock, no randomness: the same store yields the same bytes."""
        self.assertEqual(self._html(), self._html())


class TestIndexFlag(FakeFleet):
    def _run(self, *extra):
        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = cli.main(["--index", "--output-dir", self.outdir] + list(extra))
        finally:
            sys.stderr = stderr
        return code, buffer.getvalue()

    def test_writes_index_html_into_the_output_directory(self):
        code, out = self._run()
        self.assertEqual(code, 0, out)
        target = os.path.join(self.outdir, "index.html")
        self.assertTrue(os.path.exists(target))
        with open(target) as fh:
            self.assertIn(index.MARKER, fh.read())
        self.assertIn("index.html", out)

    def test_rebuilding_replaces_the_index_without_force(self):
        """The index is derived and has to be current; refreshing it is the point."""
        code, _ = self._run()
        self.assertEqual(code, 0)
        code, out = self._run()
        self.assertEqual(code, 0, out)

    def test_a_foreign_index_html_is_not_clobbered_without_force(self):
        target = os.path.join(self.outdir, "index.html")
        with open(target, "w") as fh:
            fh.write("<html>someone else's file</html>")
        code, out = self._run()
        self.assertNotEqual(code, 0)
        with open(target) as fh:
            self.assertIn("someone else", fh.read())
        code, _ = self._run("--force")
        self.assertEqual(code, 0)
        with open(target) as fh:
            self.assertIn(index.MARKER, fh.read())

    def test_refuses_to_write_inside_the_transcript_store(self):
        code, out = self._run("-o", os.path.join(self.greenthumb, "index.html"))
        self.assertEqual(code, 7)
        self.assertFalse(os.path.exists(os.path.join(self.greenthumb, "index.html")))
        self.assertIn("transcript store", out)

    def test_naming_a_session_contradicts_index(self):
        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            code = cli.main(["--index", "deadbeef", "--output-dir", self.outdir])
        finally:
            sys.stderr = stderr
        self.assertEqual(code, 2)

    def test_stdout_emits_the_index_and_writes_nothing(self):
        buffer = io.StringIO()
        stdout, sys.stdout = sys.stdout, buffer
        try:
            code = cli.main(["--index", "--stdout", "--output-dir", self.outdir])
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        self.assertIn(index.MARKER, buffer.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.outdir, "index.html")))

    def test_the_index_is_linked_from_help(self):
        parser = cli.build_parser()
        self.assertIn("--index", parser.format_help())


if __name__ == "__main__":
    unittest.main()

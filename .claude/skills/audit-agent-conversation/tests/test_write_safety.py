"""The transcripts are the only copy. Nothing may ever write into them.

The plan states this as a non-negotiable safety requirement, and until now
nothing enforced it: `-o <a transcript>.jsonl --force` would happily overwrite a
session transcript with HTML, and the no-overwrite error even coached the user
toward `--force`. Transcripts are gitignored and there is no second copy, so
that is unrecoverable data loss.

The guard is therefore absolute: a target under the transcripts root is refused
no matter what flags are passed. `--force` means "overwrite my own output", not
"disable the safety rail".

Every test here writes only into a temporary directory, and the ones that model
the projects tree build a fake one rather than pointing at the real
`~/.claude/projects/`.
"""

import os
import shutil
import tempfile
import unittest

from auditlog import cli, resolve
from tests import fixtures


class TestTranscriptsAreNeverWritten(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.tmp = tempfile.mkdtemp(prefix="auditlog-safety-")
        # A stand-in for ~/.claude/projects, so the real one is never at risk.
        self.projects = os.path.join(self.tmp, "projects")
        self.project = os.path.join(self.projects, "-Users-someone-src-thing")
        os.makedirs(self.project)
        self.transcript = os.path.join(self.project, "deadbeef.jsonl")
        with open(self.transcript, "w") as fh:
            fh.write('{"type":"user","message":{"content":"precious"}}\n')
        self.original = open(self.transcript).read()

        self._real_root = resolve.PROJECTS_ROOT
        resolve.PROJECTS_ROOT = self.projects

    def tearDown(self):
        resolve.PROJECTS_ROOT = self._real_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _source(self):
        return fixtures.path(fixtures.BRIEF_AUG13)

    def test_output_path_inside_the_projects_tree_is_refused(self):
        code = cli.main([self._source(), "-o", self.transcript, "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertEqual(open(self.transcript).read(), self.original)

    def test_force_does_not_override_the_guard(self):
        """THE finding. --force must not be a way to clobber a transcript."""
        code = cli.main([self._source(), "-o", self.transcript, "--force", "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertEqual(open(self.transcript).read(), self.original)

    def test_a_new_file_inside_the_projects_tree_is_also_refused(self):
        target = os.path.join(self.project, "new-page.html")
        code = cli.main([self._source(), "-o", target, "--force", "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertFalse(os.path.exists(target))

    def test_output_dir_inside_the_projects_tree_is_refused(self):
        code = cli.main([self._source(), "--output-dir", self.project,
                         "--force", "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertEqual(sorted(os.listdir(self.project)), ["deadbeef.jsonl"])

    def test_no_directories_are_created_inside_the_projects_tree(self):
        target = os.path.join(self.project, "deep", "deeper")
        code = cli.main([self._source(), "--output-dir", target, "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertFalse(os.path.exists(target))

    def test_the_projects_root_itself_is_refused(self):
        code = cli.main([self._source(), "--output-dir", self.projects, "--quiet"])
        self.assertNotEqual(code, 0)

    def test_a_relative_path_that_climbs_into_the_tree_is_refused(self):
        sneaky = os.path.join(self.projects, "..", "projects", "x.html")
        code = cli.main([self._source(), "-o", sneaky, "--force", "--quiet"])
        self.assertNotEqual(code, 0)

    def test_a_symlink_pointing_into_the_tree_is_refused(self):
        """realpath, not the literal path, is what decides."""
        link = os.path.join(self.tmp, "innocent.html")
        os.symlink(self.transcript, link)
        code = cli.main([self._source(), "-o", link, "--force", "--quiet"])
        self.assertNotEqual(code, 0)
        self.assertEqual(open(self.transcript).read(), self.original)

    def test_a_symlinked_output_directory_pointing_into_the_tree_is_refused(self):
        link = os.path.join(self.tmp, "innocent-dir")
        os.symlink(self.project, link)
        code = cli.main([self._source(), "--output-dir", link, "--quiet"])
        self.assertNotEqual(code, 0)

    def test_the_refusal_explains_itself_and_does_not_suggest_force(self):
        import io
        import sys

        buffer = io.StringIO()
        stderr, sys.stderr = sys.stderr, buffer
        try:
            cli.main([self._source(), "-o", self.transcript, "--quiet"])
        finally:
            sys.stderr = stderr
        message = buffer.getvalue()
        self.assertIn("transcript", message.lower())
        self.assertNotIn("--force", message)

    def test_an_ordinary_destination_still_works(self):
        target = os.path.join(self.tmp, "fine.html")
        self.assertEqual(cli.main([self._source(), "-o", target, "--quiet"]), 0)
        self.assertTrue(os.path.isfile(target))


class TestAtomicWrite(unittest.TestCase):
    """A failed write must not destroy the previous good page."""

    def setUp(self):
        fixtures.require_corpus(self)
        self.tmp = tempfile.mkdtemp(prefix="auditlog-atomic-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_no_partial_file_is_left_behind_on_success(self):
        target = os.path.join(self.tmp, "page.html")
        cli.main([fixtures.path(fixtures.BRIEF_AUG13), "-o", target, "--quiet"])
        leftovers = [n for n in os.listdir(self.tmp) if n != "page.html"]
        self.assertEqual(leftovers, [], "temp file left behind")

    def test_overwrite_replaces_atomically(self):
        target = os.path.join(self.tmp, "page.html")
        cli.main([fixtures.path(fixtures.BRIEF_AUG13), "-o", target, "--quiet"])
        first = os.path.getsize(target)
        cli.main([fixtures.path(fixtures.BRIEF_AUG14), "-o", target, "--force",
                  "--quiet"])
        self.assertNotEqual(os.path.getsize(target), 0)
        self.assertGreater(first, 0)
        self.assertEqual([n for n in os.listdir(self.tmp) if n != "page.html"], [])


class TestSenderAttribution(unittest.TestCase):
    """An audit log must not invent who was talking.

    Defaulting an agent-initiated session to `scott` is a false attribution of
    exactly the kind Defect 3 was about: confidently wrong beats obviously
    absent, and this is the confidently wrong one.
    """

    def _session(self, entrypoint, cwd="/Users/scottwb/src/scottwb/greenthumb"):
        class Fake(object):
            pass

        fake = Fake()
        fake.agent_name = None
        fake.cwd = cwd
        fake.entrypoint = entrypoint
        return fake

    def test_explicit_from_always_wins(self):
        sender, _ = cli.resolve_participants(self._session("sdk-cli"), "donna", None)
        self.assertEqual(sender, "donna")

    def test_interactive_session_defaults_to_the_configured_human(self):
        sender, _ = cli.resolve_participants(self._session("cli"), None, None)
        self.assertEqual(sender, "scott")

    def test_non_interactive_session_is_not_attributed_to_the_human(self):
        """An sdk-cli session was not Scott typing; saying so would be a lie."""
        sender, _ = cli.resolve_participants(self._session("sdk-cli"), None, None)
        self.assertNotEqual(sender, "scott")
        self.assertTrue(sender)

    def test_a_configured_sender_map_supplies_the_caller(self):
        mapped = cli.sender_for_project("-Users-scottwb-src-scottwb-greenthumb")
        if mapped is not None:
            sender, _ = cli.resolve_participants(self._session("sdk-cli"), None, None)
            self.assertEqual(sender, mapped)


if __name__ == "__main__":
    unittest.main()

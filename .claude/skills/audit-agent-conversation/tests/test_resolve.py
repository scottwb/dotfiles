"""Finding a transcript to render.

Six ways in: an explicit path, a full UUID, a UUID prefix, a project name, a
date, and "the latest one". All of them are READ-ONLY against
`~/.claude/projects/`, which holds the only copy of every transcript and is
gitignored.
"""

import os
import unittest

from auditlog import resolve
from tests import fixtures


class TestProjectDirectoryMapping(unittest.TestCase):
    def test_cwd_maps_to_a_project_directory_name(self):
        self.assertEqual(
            resolve.project_dir_name("/Users/scottwb/src/scottwb/greenthumb"),
            "-Users-scottwb-src-scottwb-greenthumb",
        )

    def test_trailing_slash_does_not_change_the_mapping(self):
        self.assertEqual(
            resolve.project_dir_name("/Users/scottwb/src/scottwb/greenthumb/"),
            resolve.project_dir_name("/Users/scottwb/src/scottwb/greenthumb"),
        )

    def test_root_maps_without_crashing(self):
        self.assertTrue(resolve.project_dir_name("/"))


class TestProjectLookup(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def test_substring_match(self):
        found = resolve.find_project("greenthumb")
        self.assertEqual(os.path.basename(found), "-Users-scottwb-src-scottwb-greenthumb")

    def test_exact_directory_name_match(self):
        found = resolve.find_project("-Users-scottwb-src-scottwb-greenthumb")
        self.assertTrue(found.endswith("-Users-scottwb-src-scottwb-greenthumb"))

    def test_unmatched_project_names_the_candidates(self):
        with self.assertRaises(resolve.ResolutionError) as ctx:
            resolve.find_project("definitely-not-a-project-xyzzy")
        message = str(ctx.exception)
        self.assertIn("definitely-not-a-project-xyzzy", message)
        self.assertIn("no project", message.lower())

    def test_ambiguous_project_lists_the_matches(self):
        """`dotfiles` matches several project dirs."""
        try:
            resolve.find_project("dotfiles")
        except resolve.ResolutionError as exc:
            self.assertIn("ambiguous", str(exc).lower())
        else:
            # If only one matched on this machine that is fine too.
            pass


class TestSessionResolution(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)

    def test_explicit_path(self):
        path = fixtures.path(fixtures.REFERENCE)
        self.assertEqual(resolve.resolve(session=path), path)

    def test_full_uuid_within_a_project(self):
        found = resolve.resolve(session=fixtures.REFERENCE, project="greenthumb")
        self.assertEqual(found, fixtures.path(fixtures.REFERENCE))

    def test_uuid_prefix(self):
        found = resolve.resolve(session="9608087e", project="greenthumb")
        self.assertEqual(found, fixtures.path(fixtures.BRIEF_AUG13))

    def test_ambiguous_prefix_is_an_error_that_lists_the_matches(self):
        """`d` matches four sessions; guessing between them would be wrong."""
        with self.assertRaises(resolve.ResolutionError) as ctx:
            resolve.resolve(session="d", project="greenthumb")
        message = str(ctx.exception)
        self.assertIn("ambiguous", message.lower())
        self.assertIn("d3a49460", message)

    def test_an_empty_session_string_means_unspecified_not_ambiguous(self):
        """Falling through to `latest` is the useful reading of "".
        """
        self.assertEqual(
            resolve.resolve(session="", project="greenthumb"),
            resolve.resolve(project="greenthumb", latest=True),
        )

    def test_unmatched_prefix_is_an_error_naming_the_prefix(self):
        with self.assertRaises(resolve.ResolutionError) as ctx:
            resolve.resolve(session="zzzzzzzz", project="greenthumb")
        self.assertIn("zzzzzzzz", str(ctx.exception))

    def test_latest_returns_the_newest_transcript(self):
        found = resolve.resolve(project="greenthumb", latest=True)
        newest = max(fixtures.corpus_sessions(), key=os.path.getmtime)
        self.assertEqual(found, newest)

    def test_latest_is_the_default_within_a_project(self):
        self.assertEqual(
            resolve.resolve(project="greenthumb"),
            resolve.resolve(project="greenthumb", latest=True),
        )

    def test_by_date(self):
        found = resolve.resolve(project="greenthumb", date="2026-08-13")
        self.assertEqual(found, fixtures.path(fixtures.BRIEF_AUG13))

    def test_a_date_with_no_session_is_an_error(self):
        with self.assertRaises(resolve.ResolutionError) as ctx:
            resolve.resolve(project="greenthumb", date="1999-01-01")
        self.assertIn("1999-01-01", str(ctx.exception))

    def test_a_malformed_date_is_rejected_clearly(self):
        with self.assertRaises(resolve.ResolutionError):
            resolve.resolve(project="greenthumb", date="not-a-date")

    def test_missing_path_is_an_error_not_a_crash(self):
        with self.assertRaises(resolve.ResolutionError):
            resolve.resolve(session="/nope/does-not-exist.jsonl")


class TestReadOnlyGuarantee(unittest.TestCase):
    """The transcripts are the only copy. Never write to them."""

    def setUp(self):
        fixtures.require_corpus(self)

    def test_resolution_does_not_modify_mtimes(self):
        before = {p: os.path.getmtime(p) for p in fixtures.corpus_sessions()}
        resolve.resolve(project="greenthumb", latest=True)
        resolve.resolve(session="9608087e", project="greenthumb")
        after = {p: os.path.getmtime(p) for p in fixtures.corpus_sessions()}
        self.assertEqual(before, after)

    def test_module_never_opens_a_transcript_for_writing(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "scripts", "auditlog", "resolve.py")) as handle:
            body = handle.read()
        for needle in ('"w"', "'w'", '"a"', "'a'", "os.remove", "os.unlink",
                       "shutil.move", "os.rename"):
            self.assertNotIn(needle, body, "resolve.py may write: %s" % needle)


if __name__ == "__main__":
    unittest.main()

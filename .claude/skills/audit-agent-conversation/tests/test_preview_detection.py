"""Which tool results earn a rendered preview pane.

The heuristic needs BOTH a command check and an output check. The command check
alone false-positives on a real case in the reference session: a `git commit`
whose message contains the phrase "that head needs inspection" matches
`\\bhead\\b` and would be offered a markdown preview of a commit hash.
"""

import unittest

from auditlog import markdown as md
from auditlog import parse
from tests import fixtures

MARKDOWN_BODY = "# Title\n\n- one\n- two\n"
TABLE_BODY = "| a | b |\n| c | d |\n"


class TestReadResults(unittest.TestCase):
    def test_markdown_file_read_is_offered_a_preview(self):
        self.assertTrue(
            md.is_markdown_result("Read", {"file_path": "/x/notes.md"}, MARKDOWN_BODY)
        )

    def test_non_markdown_file_read_is_not(self):
        self.assertFalse(
            md.is_markdown_result("Read", {"file_path": "/x/main.py"}, MARKDOWN_BODY)
        )

    def test_empty_output_is_never_offered_a_preview(self):
        self.assertFalse(md.is_markdown_result("Read", {"file_path": "/x/n.md"}, ""))
        self.assertFalse(md.is_markdown_result("Read", {"file_path": "/x/n.md"}, "   "))


class TestBashResults(unittest.TestCase):
    def test_grep_of_a_markdown_file_with_markdown_output(self):
        self.assertTrue(
            md.is_markdown_result(
                "Bash", {"command": "grep -n 'x' work-plan.md"}, TABLE_BODY
            )
        )

    def test_reader_command_but_output_is_not_markdown(self):
        self.assertFalse(
            md.is_markdown_result(
                "Bash", {"command": "grep -n 'x' work-plan.md"}, "no matches here"
            )
        )

    def test_markdown_output_but_no_reader_command(self):
        self.assertFalse(
            md.is_markdown_result("Bash", {"command": "ls -la"}, MARKDOWN_BODY)
        )

    def test_the_git_commit_head_false_positive_is_rejected(self):
        """THE case the output check exists for.

        This command is real: it is the reference session's commit. Its message
        contains "that head needs inspection", so a command-only check matches
        `\\bhead\\b` and offers a markdown preview of a commit hash.
        """
        command = (
            "git add action-log.md concerns.md rules.md work-plan.md && "
            "git commit -q -F - <<'EOF'\n"
            "Aug 14 field day: Zone 1 catch-cup test\n\n"
            "One genuine coverage gap found at 0.07\" near the brick "
            "west of the neck (north edge) -- that head needs inspection.\n"
            "EOF\n"
            "git log --oneline -1"
        )
        result = "051a130 Aug 14 field day: Zone 1 catch-cup test"
        self.assertFalse(md.is_markdown_result("Bash", {"command": command}, result))

    def test_command_check_alone_would_have_matched_that_commit(self):
        """Proves the previous test is testing something real."""
        import re

        command = "git commit -F - ... that head needs inspection ... work-plan.md"
        self.assertTrue(re.search(r"\b(grep|sed|cat|head|tail|bat)\b", command))
        self.assertTrue(re.search(r"(?:^|\s)[\w./-]+\.md\b", command))


class TestLooksLikeMarkdown(unittest.TestCase):
    def test_two_pipe_rows_qualify(self):
        self.assertTrue(md.looks_like_markdown("| a |\n| b |"))

    def test_one_heading_qualifies(self):
        self.assertTrue(md.looks_like_markdown("# Title\nbody text"))

    def test_two_bullets_qualify(self):
        self.assertTrue(md.looks_like_markdown("- one\n- two"))

    def test_prose_does_not(self):
        self.assertFalse(md.looks_like_markdown("just a line\nand another"))

    def test_single_line_never_qualifies(self):
        self.assertFalse(md.looks_like_markdown("# Title"))

    def test_line_numbered_markdown_still_qualifies(self):
        """The check runs after stripping prefixes, or every Read would fail."""
        self.assertTrue(md.looks_like_markdown("   1\t# Title\n   2\tbody"))


class TestAgainstTheReferenceSession(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.session = parse.load_session(fixtures.path(fixtures.REFERENCE))

    def test_exactly_eight_previews_are_offered(self):
        previewable = [
            e for e in self.session.events
            if e.kind == "tool"
            and md.is_markdown_result(e.tool_name, e.tool_input, e.result or "")
        ]
        self.assertEqual(len(previewable), 8)

    def test_the_commit_call_is_not_among_them(self):
        for event in self.session.events:
            if event.kind != "tool" or event.tool_name != "Bash":
                continue
            command = (event.tool_input or {}).get("command", "")
            if "git commit" in command:
                self.assertFalse(
                    md.is_markdown_result(
                        event.tool_name, event.tool_input, event.result or ""
                    ),
                    "the commit call was offered a markdown preview",
                )


if __name__ == "__main__":
    unittest.main()

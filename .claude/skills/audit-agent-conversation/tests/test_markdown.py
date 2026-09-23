"""The stdlib markdown renderer ported from the prototype.

Porting is cheaper than adding a dependency and keeps the tool stdlib-only.
These tests pin the behavior that made the worked example legible, especially
the two cases a general-purpose parser gets wrong for this input: headerless
pipe-row runs (grep fragments) and escaped pipes inside cells.
"""

import unittest

from auditlog import markdown as md


class TestInline(unittest.TestCase):
    def test_bold(self):
        self.assertIn("<strong>x</strong>", md.render("**x**"))

    def test_italic(self):
        self.assertIn("<em>x</em>", md.render("*x*"))

    def test_strikethrough(self):
        self.assertIn("<del>x</del>", md.render("~~x~~"))

    def test_inline_code(self):
        self.assertIn("<code>x</code>", md.render("`x`"))

    def test_link(self):
        out = md.render("[label](http://example.com)")
        self.assertIn('href="http://example.com"', out)
        self.assertIn(">label<", out)

    def test_html_is_escaped(self):
        """Tool output is untrusted text; it must not inject markup."""
        out = md.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_code_span_contents_are_not_further_parsed(self):
        out = md.render("`**not bold**`")
        self.assertIn("<code>**not bold**</code>", out)


class TestBlocks(unittest.TestCase):
    def test_headings(self):
        out = md.render("## Title")
        self.assertIn("Title", out)
        self.assertIn("md-h2", out)

    def test_fenced_code(self):
        out = md.render("```sh\necho hi\n```")
        self.assertIn("<pre", out)
        self.assertIn("echo hi", out)

    def test_fenced_code_is_not_parsed_as_markdown(self):
        out = md.render("```\n| a | b |\n```")
        self.assertNotIn("<table>", out)

    def test_unordered_list(self):
        out = md.render("- one\n- two")
        self.assertIn("<ul>", out)
        self.assertEqual(out.count("<li>"), 2)

    def test_ordered_list_keeps_its_start(self):
        out = md.render("3. three\n4. four")
        self.assertIn("start='3'", out)

    def test_blockquote(self):
        out = md.render("> quoted")
        self.assertIn("<blockquote>", out)
        self.assertIn("quoted", out)

    def test_horizontal_rule(self):
        self.assertIn("<hr>", md.render("---"))

    def test_paragraphs(self):
        out = md.render("one\n\ntwo")
        self.assertEqual(out.count("<p>"), 2)


class TestTables(unittest.TestCase):
    def test_table_with_header(self):
        out = md.render("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<table>", out)
        self.assertIn("<thead>", out)
        self.assertIn("<th>a</th>", out)
        self.assertIn("<td>1</td>", out)

    def test_headerless_pipe_run(self):
        """Grep fragments arrive as bare pipe rows with no delimiter row."""
        out = md.render("| a | b |\n| c | d |")
        self.assertIn("<table>", out)
        self.assertNotIn("<thead>", out)
        self.assertIn("<td>a</td>", out)
        self.assertIn("<td>d</td>", out)

    def test_escaped_pipe_inside_a_cell(self):
        out = md.render("| a \\| b | c |\n|---|---|\n| 1 | 2 |")
        self.assertIn("a | b", out)

    def test_ragged_rows_are_padded(self):
        out = md.render("| a | b | c |\n|---|---|---|\n| 1 |")
        self.assertIn("<table>", out)
        self.assertGreaterEqual(out.count("<td>"), 3)

    def test_wide_tables_scroll_in_their_own_container(self):
        out = md.render("| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("tablewrap", out)


class TestLineNumberStripping(unittest.TestCase):
    def test_read_prefixes(self):
        """`Read` output has `   12\\t` prefixes."""
        self.assertEqual(md.strip_line_numbers("    12\thello"), "hello")

    def test_grep_prefixes(self):
        """`grep -n` output has `12:` prefixes."""
        self.assertEqual(md.strip_line_numbers("12:hello"), "hello")

    def test_untouched_when_no_prefix(self):
        self.assertEqual(md.strip_line_numbers("hello"), "hello")

    def test_multiline_mixed(self):
        text = "   1\t# Title\n2:- bullet\nplain"
        self.assertEqual(md.strip_line_numbers(text), "# Title\n- bullet\nplain")

    def test_a_colon_in_prose_is_not_a_line_number(self):
        self.assertEqual(md.strip_line_numbers("note: a thing"), "note: a thing")


class TestObsidianWikilinks(unittest.TestCase):
    def test_aliased_link_resolves_to_the_alias(self):
        self.assertEqual(md.dewiki("[[some/path|Alias]]"), "Alias")

    def test_bare_link_resolves_to_its_basename(self):
        self.assertEqual(md.dewiki("[[some/path/note]]"), "note")

    def test_embed_becomes_a_chip(self):
        out = md.dewiki("![[images/photo.png]]")
        self.assertIn("photo.png", out)
        self.assertNotIn("[[", out)

    def test_plain_text_untouched(self):
        self.assertEqual(md.dewiki("nothing here"), "nothing here")


class TestPreviewPipeline(unittest.TestCase):
    def test_preview_strips_numbers_then_renders(self):
        out = md.preview_html("   1\t| a | b |\n   2\t|---|---|\n   3\t| 1 | 2 |")
        self.assertIn("<table>", out)
        self.assertNotIn("\t", out)

    def test_preview_resolves_wikilinks(self):
        out = md.preview_html("- see [[docs/thing|the thing]]")
        self.assertIn("the thing", out)
        self.assertNotIn("[[", out)


if __name__ == "__main__":
    unittest.main()

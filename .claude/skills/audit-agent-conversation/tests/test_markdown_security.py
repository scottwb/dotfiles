"""Adversarial tests. Transcript content is UNTRUSTED and is emitted into HTML.

The threat model is specific and worth stating, because it is easy to wave away
as "it's only Scott's own agents". An audit log page renders, verbatim, whatever
the audited agent produced and whatever its tools returned. That content came
from web pages, file contents, API responses, and command output. The page's
entire value is being a trustworthy record of what happened, so markup that
executes when the record is opened is exactly the wrong failure.

HTML-escaping alone is not enough. It stops an attacker breaking out of an
attribute, but it does not stop a `javascript:` URL: the browser decodes the
entities back before navigating.
"""

import unittest

from auditlog import markdown as md


class TestLinkSchemes(unittest.TestCase):
    """Escaping stops attribute breakout. It does not stop the scheme."""

    def test_javascript_url_is_not_rendered_as_a_link(self):
        out = md.render("[click](javascript:document.title='PWNED')")
        self.assertNotIn("href=\"javascript:", out)
        self.assertNotIn("href='javascript:", out)

    def test_javascript_url_survives_as_visible_text(self):
        """Refusing must not silently delete evidence from an audit log."""
        out = md.render("[click](javascript:alert(1))")
        self.assertIn("click", out)
        self.assertIn("javascript", out)

    def test_scheme_matching_is_case_insensitive(self):
        for scheme in ("JavaScript:", "JAVASCRIPT:", "JaVaScRiPt:"):
            out = md.render("[x](%salert(1))" % scheme)
            self.assertNotIn("href=\"%s" % scheme, out)
            self.assertNotIn('href="javascript:', out.lower())

    def test_whitespace_and_control_characters_do_not_smuggle_a_scheme(self):
        """`java\\tscript:` and friends are stripped by the browser, so strip them here."""
        for payload in (
            "java\tscript:alert(1)",
            "java\nscript:alert(1)",
            "java\rscript:alert(1)",
            "  javascript:alert(1)",
            "\x01javascript:alert(1)",
        ):
            out = md.render("[x](%s)" % payload)
            self.assertNotIn('href="java', out.lower().replace("\t", "").replace("\n", ""))

    def test_html_entity_encoded_scheme_is_caught(self):
        """The renderer escapes first, so the check must decode before judging."""
        out = md.render("[x](&#106;avascript:alert(1))")
        self.assertNotIn('href="&#106;avascript:', out)
        self.assertNotIn('href="javascript:', out.lower())

    def test_data_urls_are_refused(self):
        out = md.render("[x](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)")
        self.assertNotIn('href="data:', out)

    def test_vbscript_and_file_are_refused(self):
        for url in ("vbscript:msgbox(1)", "file:///etc/passwd"):
            out = md.render("[x](%s)" % url)
            self.assertNotIn('href="%s' % url.split(":")[0], out)


class TestLinkSchemesThatMustKeepWorking(unittest.TestCase):
    """The fix must not break ordinary links; transcripts are full of them."""

    def test_http_and_https(self):
        for url in ("http://example.com/a?b=1", "https://example.com/a#frag"):
            out = md.render("[label](%s)" % url)
            self.assertIn('href="%s"' % url.replace("&", "&amp;"), out)
            self.assertIn(">label<", out)

    def test_mailto(self):
        out = md.render("[mail](mailto:someone@example.com)")
        self.assertIn('href="mailto:someone@example.com"', out)

    def test_relative_and_anchor_links(self):
        for url in ("#section", "docs/thing.md", "/abs/path", "./rel"):
            out = md.render("[x](%s)" % url)
            self.assertIn('href="%s"' % url, out)

    def test_query_string_ampersands_stay_escaped(self):
        out = md.render("[x](https://example.com/?a=1&b=2)")
        self.assertIn("&amp;", out)
        self.assertNotIn("?a=1&b=2", out)


class TestSentinelCollision(unittest.TestCase):
    """The code-span stash uses an in-band sentinel. Untrusted text can contain it."""

    def test_literal_sentinel_bytes_do_not_crash(self):
        for payload in ("\x00 0 \x00", "\x000\x00", "a\x001\x00b", "\x00" * 10):
            try:
                md.render(payload)
            except Exception as exc:  # noqa: BLE001 - any exception is the bug
                self.fail("render() raised %s on %r" % (type(exc).__name__, payload))

    def test_sentinel_with_a_real_code_span_present(self):
        try:
            md.render("`code` and \x000\x00 and `more`")
        except Exception as exc:  # noqa: BLE001
            self.fail("render() raised %s" % type(exc).__name__)

    def test_out_of_range_sentinel_index(self):
        try:
            md.render("\x00999999\x00")
        except Exception as exc:  # noqa: BLE001
            self.fail("render() raised %s" % type(exc).__name__)

    def test_nul_bytes_do_not_survive_into_the_page(self):
        self.assertNotIn("\x00", md.render("before\x00after"))


class TestMarkupInjection(unittest.TestCase):
    def test_script_tags_are_escaped(self):
        out = md.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)

    def test_img_onerror_is_escaped(self):
        """The tag must not form. The words surviving as visible text is correct.

        An audit log is supposed to show what the agent actually emitted, so
        `onerror=` appearing as escaped, inert text is the right outcome; only
        a real `<img` tag would be a defect.
        """
        out = md.render('<img src=x onerror="alert(1)">')
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)

    def test_event_handler_in_link_label_is_escaped(self):
        out = md.render('[<img src=x onerror=alert(1)>](https://example.com)')
        self.assertNotIn("<img", out)

    def test_closing_tag_in_a_table_cell(self):
        out = md.render("| a </td></tr></table><script>x</script> | b |\n|---|---|\n| 1 | 2 |")
        self.assertNotIn("<script>", out)

    def test_closing_tag_in_a_heading(self):
        out = md.render("# </h2><script>alert(1)</script>")
        self.assertNotIn("<script>", out)

    def test_code_span_contents_are_escaped(self):
        out = md.render("`<script>alert(1)</script>`")
        self.assertNotIn("<script>", out)

    def test_fenced_code_contents_are_escaped(self):
        out = md.render("```\n<script>alert(1)</script>\n```")
        self.assertNotIn("<script>", out)

    def test_wikilink_resolution_does_not_reintroduce_markup(self):
        out = md.preview_html("[[a|<script>alert(1)</script>]]")
        self.assertNotIn("<script>", out)


class TestRenderedPageIsClean(unittest.TestCase):
    """End to end: a hostile transcript must not produce an executing page."""

    def test_hostile_session_renders_without_executable_markup(self):
        import json
        import os
        import tempfile

        from auditlog import parse, render

        hostile = (
            "Here is a [link](javascript:alert(1)) and <script>alert(2)</script>\n\n"
            "| <script>alert(3)</script> | b |\n|---|---|\n| 1 | 2 |\n"
        )
        lines = [
            {"type": "user", "parentUuid": None,
             "message": {"content": "<script>alert(0)</script>"},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "1.0.0"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text", "text": hostile}],
                         "usage": {"output_tokens": 5}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(json.dumps(x) for x in lines))
            html = render.page(
                parse.load_session(path),
                from_name="<script>alert(4)</script>",
                to_name="<img src=x onerror=alert(5)>",
            )
            self.assertNotIn("<script>alert", html)
            self.assertNotIn("<img src=x", html)
            self.assertNotIn('href="javascript:', html.lower())
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

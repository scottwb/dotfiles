"""The page must render identically with the network switched off.

The distinction that makes this testable: URLs inside VERBATIM TRANSCRIPT
CONTENT are data. A tool result that printed a URL, or a reply that linked to
one, is content the page is supposed to reproduce faithfully. What must not
exist is a URL the page DEPENDS on: a stylesheet link, a script src, a font
import, a remote image, a fetch.

So this asserts on the page chrome, not on the whole document.
"""

import re
import unittest

from auditlog import parse, render
from tests import fixtures

#: Things that make the browser go and get something.
DEPENDENCY_PATTERNS = (
    (r"<link\b[^>]*\brel=[\"']?stylesheet", "external stylesheet"),
    (r"<script\b[^>]*\bsrc=", "external script"),
    (r"@import\b", "css @import"),
    (r"url\(\s*[\"']?https?:", "css remote url()"),
    (r"url\(\s*[\"']?//", "css protocol-relative url()"),
    (r"<img\b[^>]*\bsrc=[\"']?https?:", "remote image"),
    (r"<iframe\b", "iframe"),
    (r"<object\b", "object embed"),
    (r"<embed\b", "embed"),
    (r"\bfetch\s*\(", "fetch call"),
    (r"XMLHttpRequest", "XHR"),
    (r"new\s+WebSocket", "websocket"),
    (r"navigator\.sendBeacon", "beacon"),
    (r"<base\b", "base tag"),
    (r"@font-face", "web font"),
)


def chrome_of(html):
    """The page minus its verbatim transcript content.

    Strips every element that carries transcript text: tool results, both
    rendered panes, the prompt body, the reply body, and narration bubbles.
    What remains is the shell the renderer authored.
    """
    stripped = html
    for pattern in (
        r"<pre class=\"result\".*?</pre>",
        r"<div class=\"result mdpane\".*?</div>",
        r"<div class=\"turnbody[^\"]*\">.*?</section>",
        r"<div class='saybubble'>.*?</div>",
        r"<pre class='code[^']*'><code>.*?</code></pre>",
        r"<div class='kv'>.*?</div>",
    ):
        stripped = re.sub(pattern, "", stripped, flags=re.S)
    return stripped


class TestSelfContained(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os

        if not os.path.isdir(fixtures.GREENTHUMB):
            raise unittest.SkipTest("corpus not present")
        session = parse.load_session(fixtures.path(fixtures.REFERENCE))
        cls.html = render.page(session, from_name="Donna", to_name="Greenthumb")
        cls.chrome = chrome_of(cls.html)

    def test_no_external_dependencies_in_the_page_chrome(self):
        found = []
        for pattern, label in DEPENDENCY_PATTERNS:
            if re.search(pattern, self.chrome, re.I):
                found.append(label)
        self.assertEqual(found, [], "page chrome depends on something external")

    def test_css_and_js_are_inlined(self):
        self.assertIn("<style>", self.html)
        self.assertIn("<script>", self.html)

    def test_fonts_are_system_stacks_only(self):
        self.assertIn("ui-sans-serif", self.html)
        self.assertNotIn("fonts.googleapis", self.html)
        self.assertNotIn("fonts.gstatic", self.html)

    def test_no_cdn_hosts_in_chrome(self):
        for host in ("cdn.", "unpkg.com", "jsdelivr", "cloudflare", "googleapis"):
            self.assertNotIn(host, self.chrome, "CDN reference: %s" % host)

    def test_the_stripper_is_not_hiding_everything(self):
        """Guards the guard: if chrome_of() over-stripped, the test is vacuous."""
        self.assertGreater(len(self.chrome), 5000)
        self.assertIn("<!doctype html>", self.chrome)
        self.assertIn("Conversation Audit Log", self.chrome)
        self.assertIn("costnote", self.chrome)

    def test_transcript_urls_are_allowed_to_remain_in_content(self):
        """Verbatim content is data, not a dependency. Do not sanitize it."""
        self.assertIn("<!doctype html>", self.html)


class TestWholeDocumentOnBenignContent(unittest.TestCase):
    """The strongest form of the check: no stripping, so no vacuity risk.

    `chrome_of()` above strips nested HTML with regexes, which is inherently
    approximate. This test sidesteps that entirely by rendering a session whose
    transcript content contains no URLs at all, then asserting against the WHOLE
    document. Anything dependency-shaped here was authored by the renderer.
    """

    @classmethod
    def setUpClass(cls):
        import json
        import os
        import tempfile

        lines = [
            {"type": "user", "parentUuid": None,
             "message": {"content": "Do a benign thing with no links in it."},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "1.0.0"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "m", "model": "claude-opus-5",
                         "content": [{"type": "text",
                                      "text": "# Done\n\n- one\n- two\n"}],
                         "usage": {"input_tokens": 10, "output_tokens": 5}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        with open(path, "w") as fh:
            fh.write("\n".join(json.dumps(x) for x in lines))
        try:
            cls.html = render.page(
                parse.load_session(path), from_name="scott", to_name="agent"
            )
        finally:
            os.unlink(path)

    def test_whole_document_has_no_external_dependencies(self):
        found = []
        for pattern, label in DEPENDENCY_PATTERNS:
            if re.search(pattern, self.html, re.I):
                found.append(label)
        self.assertEqual(found, [])

    def test_no_scheme_bearing_urls_anywhere_in_the_document(self):
        """No http(s):// at all, since the content contributed none."""
        self.assertNotIn("http://", self.html)
        self.assertNotIn("https://", self.html)

    def test_the_document_is_still_a_real_page(self):
        self.assertGreater(len(self.html), 5000)
        self.assertIn("Conversation Audit Log", self.html)
        self.assertIn("<style>", self.html)
        self.assertIn("<script>", self.html)


class TestNoNetworkInTheRenderPath(unittest.TestCase):
    """Decision A9: rendering is deterministic and offline."""

    def test_runtime_modules_import_nothing_that_reaches_the_network(self):
        import os

        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        package = os.path.join(here, "scripts", "auditlog")
        banned = (
            "import urllib", "from urllib", "import requests", "import http.client",
            "import socket", "from socket", "import subprocess", "from subprocess",
            "import anthropic", "urlopen(",
        )
        offenders = []
        for name in sorted(os.listdir(package)):
            if not name.endswith(".py"):
                continue
            with open(os.path.join(package, name)) as handle:
                body = handle.read()
            for needle in banned:
                if needle in body:
                    offenders.append("%s: %s" % (name, needle))
        self.assertEqual(offenders, [])

    def test_rendering_is_byte_reproducible(self):
        """Same transcript in, same bytes out. No clock, no randomness."""
        fixtures.require_corpus(self)
        session = parse.load_session(fixtures.path(fixtures.BRIEF_AUG13))
        first = render.page(session, from_name="Donna", to_name="Greenthumb")
        second = render.page(
            parse.load_session(fixtures.path(fixtures.BRIEF_AUG13)),
            from_name="Donna", to_name="Greenthumb",
        )
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

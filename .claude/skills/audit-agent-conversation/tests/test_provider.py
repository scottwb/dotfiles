"""Which provider served a session, inferred from the model id.

Transcripts record NO provider, base URL, or endpoint (measured 2026-08-16 on
real routed sessions), so the provider has to be inferred from the model id,
the same way the rate table already decides which models are unpriced. Which
Ollama HOST served a session is not recoverable and is never guessed.
"""

import json
import os
import tempfile
import unittest

from auditlog import cost, parse, render
from tests import fixtures


class TestProviderFor(unittest.TestCase):
    def test_claude_models_are_anthropic(self):
        for model in ("claude-fable-5", "claude-opus-5", "claude-sonnet-4-6",
                      "claude-haiku-4-5-20251001", "claude-opus-5[1m]"):
            self.assertEqual(cost.provider_for(model), "Anthropic", model)

    def test_local_models_are_ollama(self):
        self.assertEqual(cost.provider_for("glm-4.7-flash"), "Ollama")
        self.assertEqual(cost.provider_for("qwen3:30b-a3b"), "Ollama")

    def test_org_slash_model_slugs_are_openrouter(self):
        self.assertEqual(cost.provider_for("openai/gpt-5.6-sol"), "OpenRouter")
        self.assertEqual(cost.provider_for("openai/gpt-9-nova"), "OpenRouter")

    def test_synthetic_messages_come_from_the_harness_itself(self):
        self.assertEqual(cost.provider_for("<synthetic>"), "Claude Code")

    def test_an_unknown_model_is_not_guessed(self):
        """None, not a plausible-sounding name. The page says so plainly."""
        self.assertIsNone(cost.provider_for("mystery-model-9000"))
        self.assertIsNone(cost.provider_for(""))
        self.assertIsNone(cost.provider_for(None))

    def test_every_priced_model_has_a_provider(self):
        table = cost._load()
        for model in table["models"]:
            self.assertIsNotNone(cost.provider_for(model), model)

    def test_every_unpriced_model_has_a_provider(self):
        """The unpriced list is the same table; nothing in it may fall through."""
        table = cost._load()
        for model in table.get("unpriced", {}):
            self.assertIsNotNone(cost.provider_for(model), model)


def _render(model):
    lines = [
        {"type": "user", "parentUuid": None, "message": {"content": "hi"},
         "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
         "version": "1.0.0"},
        {"type": "assistant", "timestamp": "2026-08-15T12:00:01.000Z",
         "message": {"id": "m", "model": model,
                     "content": [{"type": "text", "text": "ok"}],
                     "usage": {"input_tokens": 3, "output_tokens": 1}}},
    ]
    handle, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(handle)
    try:
        with open(path, "w") as fh:
            fh.write("\n".join(json.dumps(x) for x in lines))
        return render.page(parse.load_session(path), from_name="scott",
                           to_name="agent")
    finally:
        os.unlink(path)


class TestProviderOnThePage(unittest.TestCase):
    def assertInPage(self, needle, html):
        """assertIn without a 300 KB failure message."""
        self.assertTrue(needle in html, "%r not in the rendered page" % needle)

    def assertNotInPage(self, needle, html):
        self.assertFalse(needle in html, "%r found in the rendered page" % needle)

    @classmethod
    def setUpClass(cls):
        fixtures.require_corpus(cls)
        session = parse.load_session(fixtures.path(fixtures.REFERENCE))
        cls.html = render.page(session, from_name="Donna", to_name="Greenthumb")

    def test_reference_page_names_both_provider_and_model(self):
        self.assertInPage("Anthropic", self.html)
        self.assertInPage("claude-opus-5", self.html)
        self.assertInPage(render.provider_and_model("claude-opus-5"), self.html)

    def test_a_local_model_names_ollama_and_not_a_host(self):
        html = _render("glm-4.7-flash")
        self.assertInPage(render.provider_and_model("glm-4.7-flash"), html)
        self.assertInPage("Ollama", html)
        self.assertNotInPage("localhost", html)
        self.assertNotInPage("11434", html)

    def test_a_routed_model_names_openrouter(self):
        html = _render("openai/gpt-5.6-sol")
        self.assertInPage("OpenRouter", html)
        self.assertInPage("openai/gpt-5.6-sol", html)

    def test_an_unknown_model_says_the_provider_is_unknown(self):
        """No provider is invented for a model the table has never seen."""
        label = render.provider_and_model("mystery-model-9000")
        self.assertIn("mystery-model-9000", label)
        self.assertIn("unknown", label.lower())
        for name in ("Anthropic", "Ollama", "OpenRouter"):
            self.assertNotIn(name, label)


if __name__ == "__main__":
    unittest.main()

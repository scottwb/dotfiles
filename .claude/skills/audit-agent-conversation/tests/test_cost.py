"""Cost math against the reference session's known token bundle.

The figures here are the golden ones from the handoff, verified 2026-08-15
against the `claude-api` skill's published rates for `claude-opus-5`.
"""

import unittest

from auditlog import cost
from tests import fixtures


class TestCostMath(unittest.TestCase):
    def setUp(self):
        self.breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "claude-opus-5")

    def test_input_side_total(self):
        self.assertAlmostEqual(
            self.breakdown.input_side, fixtures.GOLDEN_COST["input_side"], places=4
        )

    def test_output_cost(self):
        self.assertAlmostEqual(
            self.breakdown.output, fixtures.GOLDEN_COST["output"], places=4
        )

    def test_reasoning_cost(self):
        self.assertAlmostEqual(
            self.breakdown.reasoning, fixtures.GOLDEN_COST["reasoning"], places=4
        )

    def test_total(self):
        self.assertAlmostEqual(
            self.breakdown.total, fixtures.GOLDEN_COST["total"], places=4
        )

    def test_reasoning_is_never_added_to_the_total(self):
        """Reasoning tokens are a subset of output tokens, not a line item.

        This is the assertion that catches someone "fixing" the total by summing
        every tile on the page. The total must be exactly input side plus output,
        with reasoning already inside the output figure.
        """
        self.assertAlmostEqual(
            self.breakdown.total,
            self.breakdown.input_side + self.breakdown.output,
            places=10,
        )
        self.assertGreater(self.breakdown.reasoning, 0)
        self.assertLess(self.breakdown.reasoning, self.breakdown.output)

    def test_reasoning_subset_contract_is_declared_in_code(self):
        self.assertTrue(cost.REASONING_IS_SUBSET_OF_OUTPUT)


class TestRateTable(unittest.TestCase):
    def test_opus_5_rates(self):
        rates = cost.rates_for("claude-opus-5")
        self.assertEqual(rates["input"], 5.00)
        self.assertEqual(rates["output"], 25.00)
        self.assertEqual(rates["cache_write_5m"], 6.25)
        self.assertEqual(rates["cache_write_1h"], 10.00)
        self.assertEqual(rates["cache_read"], 0.50)

    def test_cache_multiples_hold(self):
        """The 5m/1h/read rates are defined multiples of base input."""
        r = cost.rates_for("claude-opus-5")
        self.assertAlmostEqual(r["cache_write_5m"], r["input"] * 1.25, places=6)
        self.assertAlmostEqual(r["cache_write_1h"], r["input"] * 2.0, places=6)
        self.assertAlmostEqual(r["cache_read"], r["input"] * 0.1, places=6)

    def test_unknown_model_raises_a_useful_error(self):
        """Never silently cost an unknown model at zero."""
        with self.assertRaises(cost.UnknownModel) as ctx:
            cost.rates_for("claude-not-a-real-model")
        message = str(ctx.exception)
        self.assertIn("claude-not-a-real-model", message)
        self.assertIn("pricing.json", message)

    def test_table_records_when_it_was_verified(self):
        self.assertRegex(cost.table_verified_on(), r"^\d{4}-\d{2}-\d{2}$")

    def test_fable_5_rates(self):
        rates = cost.rates_for("claude-fable-5")
        self.assertEqual(rates["input"], 10.00)
        self.assertEqual(rates["output"], 50.00)
        self.assertAlmostEqual(rates["cache_write_1h"], 20.00, places=6)

    def test_aliases_resolve(self):
        self.assertEqual(
            cost.rates_for("claude-opus-5[1m]"), cost.rates_for("claude-opus-5")
        )
        self.assertEqual(
            cost.rates_for("claude-haiku-4-5"),
            cost.rates_for("claude-haiku-4-5-20251001"),
        )

    def test_cache_multiples_hold_for_every_model(self):
        """Each row's cache-read multiple is data, not a list kept in this test.

        Two published exceptions to the 0.1x rule exist now (Fable 5.1 at
        0.025x, Opus 5.5 at 0.05x). A hardcoded exception list here would be a
        third copy of that fact, free to drift from what the page renders, so
        the multiple is read off the row itself via `cache_read_multiple`.
        """
        table = cost._load()["models"]
        for name, r in sorted(table.items()):
            read_multiple = cost.cache_read_multiple(name)
            self.assertAlmostEqual(r["cache_write_5m"], r["input"] * 1.25, 6, name)
            self.assertAlmostEqual(r["cache_write_1h"], r["input"] * 2.0, 6, name)
            self.assertAlmostEqual(r["cache_read"], r["input"] * read_multiple, 6, name)

    def test_cache_read_multiple_defaults_to_one_tenth(self):
        self.assertAlmostEqual(cost.cache_read_multiple("claude-opus-5"), 0.1, places=6)
        self.assertAlmostEqual(cost.cache_read_multiple("claude-sonnet-5"), 0.1, places=6)

    def test_cache_read_multiple_exceptions_come_from_the_table(self):
        self.assertAlmostEqual(cost.cache_read_multiple("claude-fable-5-1"), 0.025, places=6)
        self.assertAlmostEqual(cost.cache_read_multiple("claude-opus-5-5"), 0.05, places=6)
        # Aliases price off their base row, multiple included.
        self.assertAlmostEqual(cost.cache_read_multiple("claude-opus-5-5[1m]"), 0.05, places=6)

    # Rates below were read from the published pricing page
    # (https://platform.claude.com/docs/en/about-claude/pricing) on 2026-09-23.

    def test_opus_5_5_rates(self):
        rates = cost.rates_for("claude-opus-5-5")
        self.assertEqual(rates["input"], 4.00)
        self.assertEqual(rates["output"], 20.00)
        self.assertEqual(rates["cache_write_5m"], 5.00)
        self.assertEqual(rates["cache_write_1h"], 8.00)
        self.assertEqual(rates["cache_read"], 0.20)

    def test_opus_5_5_1m_alias_prices_off_the_base_row(self):
        self.assertEqual(
            cost.rates_for("claude-opus-5-5[1m]"), cost.rates_for("claude-opus-5-5")
        )

    def test_sonnet_5_rates(self):
        """Sonnet 5 is $2 / $10. The stale row had copied Sonnet 4.6's $3 / $15."""
        rates = cost.rates_for("claude-sonnet-5")
        self.assertEqual(rates["input"], 2.00)
        self.assertEqual(rates["output"], 10.00)
        self.assertEqual(rates["cache_write_5m"], 2.50)
        self.assertEqual(rates["cache_write_1h"], 4.00)
        self.assertEqual(rates["cache_read"], 0.20)

    def test_rows_the_corpus_can_produce_are_priced(self):
        self.assertEqual(cost.rates_for("claude-mythos-5-1"), cost.rates_for("claude-fable-5-1"))
        self.assertEqual(cost.rates_for("claude-opus-4-5"), cost.rates_for("claude-opus-5"))
        self.assertEqual(cost.rates_for("claude-sonnet-4-5"), cost.rates_for("claude-sonnet-4-6"))

    def test_table_was_verified_against_the_published_page(self):
        self.assertEqual(cost.table_verified_on(), "2026-09-23")
        self.assertIn("platform.claude.com/docs/en/about-claude/pricing", cost.table_source())


class TestUnpricedModels(unittest.TestCase):
    """A model with no list price is not the same as an unknown model.

    Local Ollama models, routed non-Anthropic backends, and the harness's own
    `<synthetic>` messages all appear in real transcripts. Refusing to render
    those sessions would be wrong; quoting $0.00 for them would be worse.
    """

    def test_local_model_is_recognized_as_unpriced(self):
        self.assertIsNotNone(cost.unpriced_reason("glm-4.7-flash"))

    def test_synthetic_is_recognized_as_unpriced(self):
        self.assertIsNotNone(cost.unpriced_reason("<synthetic>"))

    def test_a_priced_model_has_no_unpriced_reason(self):
        self.assertIsNone(cost.unpriced_reason("claude-opus-5"))

    def test_compute_returns_an_unpriced_breakdown_rather_than_raising(self):
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "glm-4.7-flash")
        self.assertFalse(breakdown.priced)
        self.assertTrue(breakdown.unpriced_reason)
        self.assertEqual(breakdown.total, 0.0)

    def test_token_counts_survive_on_an_unpriced_breakdown(self):
        """The tokens are real even when the money is not."""
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "glm-4.7-flash")
        self.assertEqual(breakdown.tokens["output"], fixtures.GOLDEN_TOKENS["output"])
        self.assertEqual(
            breakdown.input_tokens_total,
            sum(fixtures.GOLDEN_TOKENS[k] for k in cost.INPUT_SIDE_KEYS),
        )

    def test_a_priced_model_still_reports_priced(self):
        self.assertTrue(cost.compute(fixtures.GOLDEN_TOKENS, "claude-opus-5").priced)

    def test_an_unknown_model_costs_as_unpriced_rather_than_raising(self):
        """A model newer than the table must not block the page.

        No dollar figure, never a zero one, and a reason that says the table
        is what needs updating.
        """
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "claude-not-a-real-model")
        self.assertFalse(breakdown.priced)
        self.assertTrue(breakdown.unknown)
        self.assertIn("pricing.json", breakdown.unpriced_reason)
        self.assertEqual(breakdown.tokens["output"], fixtures.GOLDEN_TOKENS["output"])

    def test_a_model_with_no_list_price_is_not_flagged_unknown(self):
        """Ollama has no price to add, so it must not nag to update the table."""
        self.assertFalse(cost.compute(fixtures.GOLDEN_TOKENS, "glm-4.7-flash").unknown)

    def test_a_priced_model_is_not_flagged_unknown(self):
        self.assertFalse(cost.compute(fixtures.GOLDEN_TOKENS, "claude-opus-5").unknown)

    def test_a_routed_slug_the_table_never_saw_is_unpriced_not_unknown(self):
        """An OpenRouter slug carries no Anthropic list price by design.

        The table does not list every model OpenRouter can route to, and it
        never will: the batch's own decision is to carry no OpenRouter
        pricing. So a routed slug the table has never seen is unpriced, and
        telling the reader to add its list rates would be advice they cannot
        act on. `provider_for` already knows the slug is routed; that
        knowledge is what decides this, not a second list.
        """
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "x-ai/grok-4.6")
        self.assertFalse(breakdown.priced)
        self.assertFalse(breakdown.unknown)
        self.assertEqual(breakdown.total, 0.0)
        self.assertIn("routed", breakdown.unpriced_reason)
        self.assertIn("OpenRouter", breakdown.unpriced_reason)
        self.assertNotIn("pricing.json", breakdown.unpriced_reason)
        self.assertFalse(cost.is_unknown("x-ai/grok-4.6"))

    def test_an_anthropic_prefixed_miss_is_still_unknown(self):
        """Only a model that could carry Anthropic list rates warns about the table."""
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "claude-not-a-real-model")
        self.assertFalse(breakdown.priced)
        self.assertTrue(breakdown.unknown)
        self.assertIn("pricing.json", breakdown.unpriced_reason)
        self.assertTrue(cost.is_unknown("claude-not-a-real-model"))

    def test_a_model_with_no_provider_is_unpriced_with_an_honest_reason(self):
        """A bare id the table has never seen and that gives nothing away.

        Naming a provider that did not serve the session would be a false
        statement; so would telling the reader to add rates that may not
        exist. The reason says the provider is unknown, and nothing more.
        """
        breakdown = cost.compute(fixtures.GOLDEN_TOKENS, "mystery-model-9000")
        self.assertFalse(breakdown.priced)
        self.assertFalse(breakdown.unknown)
        self.assertEqual(breakdown.total, 0.0)
        self.assertIn("provider", breakdown.unpriced_reason)
        self.assertIn("unknown", breakdown.unpriced_reason)
        self.assertNotIn("pricing.json", breakdown.unpriced_reason)

    def test_a_recorded_unpriced_reason_still_wins(self):
        """Models in the `unpriced` map keep their own wording."""
        table = cost._load()["unpriced"]
        for model, recorded in sorted(table.items()):
            breakdown = cost.compute(fixtures.GOLDEN_TOKENS, model)
            self.assertFalse(breakdown.unknown, model)
            self.assertEqual(breakdown.unpriced_reason, recorded, model)

    def test_rates_for_still_raises_for_a_routed_slug(self):
        """Unpriced is not zero-priced: nothing may silently price at nothing."""
        with self.assertRaises(cost.UnknownModel) as ctx:
            cost.rates_for("x-ai/grok-4.6")
        self.assertIn("x-ai/grok-4.6", str(ctx.exception))
        self.assertNotIn("pricing.json", str(ctx.exception))
        with self.assertRaises(cost.UnknownModel):
            cost.rates_for("mystery-model-9000")

    def test_routed_slug_page_shows_no_dollar_figure_and_no_nag(self):
        import json
        import os
        import tempfile

        from auditlog import parse, render

        lines = [
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "1.0.0"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "m", "model": "x-ai/grok-4.6",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"input_tokens": 100, "output_tokens": 50}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(json.dumps(x) for x in lines))
            html = render.page(parse.load_session(path), from_name="scott",
                               to_name="agent")
            self.assertIn("No cost figure for this session", html)
            self.assertIn("OpenRouter", html)
            self.assertNotIn("pricing.json", html)
            self.assertNotIn("$0.00", html)
        finally:
            os.unlink(path)

    def test_unpriced_page_shows_no_dollar_figure(self):
        import json
        import os
        import tempfile

        from auditlog import parse, render

        lines = [
            {"type": "user", "parentUuid": None, "message": {"content": "hi"},
             "timestamp": "2026-08-15T12:00:00.000Z", "cwd": "/tmp/x",
             "version": "1.0.0"},
            {"type": "assistant", "timestamp": "2026-08-15T12:00:05.000Z",
             "message": {"id": "m", "model": "glm-4.7-flash",
                         "content": [{"type": "text", "text": "ok"}],
                         "usage": {"input_tokens": 100, "output_tokens": 50}}},
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(json.dumps(x) for x in lines))
            html = render.page(parse.load_session(path), from_name="scott",
                               to_name="agent")
            self.assertIn("no list price", html)
            self.assertIn("rather than a made-up one", html)
            self.assertNotIn("$0.00", html)
            self.assertIn("100", html)  # the token counts are still real
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

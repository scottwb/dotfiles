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


if __name__ == "__main__":
    unittest.main()

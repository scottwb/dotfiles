"""THE regression test.

Claude Code writes one transcript record per content block, and every record
repeats the entire message's `usage` object. An assistant message with a
thinking block, a text block, and two tool_use blocks becomes four records, each
carrying identical token counts.

Summing per record therefore multiplies every figure. On the reference session
it produces 41,302 output tokens where the truth is 16,179, a 2.5x overcount,
and the first published version of the worked example shipped with that bug.

The fix is to deduplicate on `message.id` before summing.
"""

import json
import unittest

from auditlog import parse
from tests import fixtures


class TestUsageDedupe(unittest.TestCase):
    def setUp(self):
        fixtures.require_corpus(self)
        self.usage = parse.usage_for(fixtures.path(fixtures.REFERENCE))

    def test_api_message_count(self):
        """27 assistant records, but only 8 actual API calls."""
        self.assertEqual(self.usage.api_messages, fixtures.GOLDEN_API_MESSAGES)

    def test_every_golden_token_figure(self):
        for key, expected in sorted(fixtures.GOLDEN_TOKENS.items()):
            self.assertEqual(
                self.usage.tokens[key], expected, "token bundle key %r" % key
            )

    def test_reasoning_is_inside_output(self):
        self.assertLess(self.usage.tokens["reasoning"], self.usage.tokens["output"])


class TestNaiveSummationIsWrong(unittest.TestCase):
    """Pins down WHY the dedupe exists, so it does not decay into folklore.

    If a later refactor drops the dedupe, `test_every_golden_token_figure` above
    goes red. This test explains what it would go red with.
    """

    def setUp(self):
        fixtures.require_corpus(self)

    def test_naive_per_record_sum_overcounts_by_2_5x(self):
        naive = 0
        records = 0
        with open(fixtures.path(fixtures.REFERENCE)) as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("type") != "assistant":
                    continue
                records += 1
                usage = (record.get("message") or {}).get("usage") or {}
                naive += usage.get("output_tokens", 0)

        self.assertEqual(records, 27, "reference session assistant record count")
        self.assertEqual(naive, fixtures.NAIVE_OUTPUT_TOKENS)

        deduped = fixtures.GOLDEN_TOKENS["output"]
        self.assertGreater(naive / float(deduped), 2.5)


class TestLoaderRobustness(unittest.TestCase):
    def test_blank_lines_and_malformed_lines_are_survived(self):
        """A truncated final line must not take the whole run down."""
        import os
        import tempfile

        good = json.dumps({"type": "user", "message": {"content": "hi"}})
        body = "\n".join(["", good, "   ", "{not json", good, '{"truncated": '])
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write(body)
            records, skipped = parse.load_records(path)
            self.assertEqual(len(records), 2)
            self.assertEqual(skipped, 2)
        finally:
            os.unlink(path)

    def test_unknown_record_types_are_skipped_not_matched_exhaustively(self):
        import os
        import tempfile

        lines = [
            json.dumps({"type": "some-future-record-type", "payload": {"a": 1}}),
            json.dumps({"type": "attachment", "attachment": {"type": "task_reminder"}}),
            json.dumps({"type": "user", "message": {"content": "hello"}}),
        ]
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        try:
            with open(path, "w") as fh:
                fh.write("\n".join(lines))
            records, skipped = parse.load_records(path)
            self.assertEqual(len(records), 3)
            self.assertEqual(skipped, 0)
            # And computing usage over them must not raise.
            usage = parse.usage_for(path)
            self.assertEqual(usage.api_messages, 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

"""Cost math over a deduplicated token bundle.

Nothing was actually billed for the sessions this tool renders: they run on a
Claude subscription. Every figure here is what identical traffic would cost
through the public API at list rates, and the rendered page says so.

The one rule that is easy to get wrong, and that the tests pin down:

    REASONING TOKENS ARE A SUBSET OF OUTPUT TOKENS.

They bill at the output rate and are already inside `output`. Reporting them
separately is useful; adding them to the total is double counting.
"""

import json
import os

#: Declared in code, not just in a comment, so a test can assert the contract.
REASONING_IS_SUBSET_OF_OUTPUT = True

#: The token bundle keys this module understands. `reasoning` is deliberately
#: absent: it is priced off `output` and never summed independently.
BILLABLE_KEYS = (
    "input",
    "cache_write_5m",
    "cache_write_1h",
    "cache_read",
    "output",
)

#: The four components that make up the "input side" of a session's cost.
INPUT_SIDE_KEYS = ("input", "cache_write_5m", "cache_write_1h", "cache_read")

_TABLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pricing.json")
_table = None


class UnknownModel(Exception):
    """Raised when a model has no entry in the rate table.

    Deliberately fatal. Falling back to a default rate, or to zero, would
    produce a confidently wrong dollar figure, which is worse than no figure.

    Distinct from an UNPRICED model (see `unpriced_reason`), which is a model
    that genuinely has no Anthropic list price: a local Ollama model, a routed
    non-Anthropic backend, or the harness's own synthetic messages. Those render
    with the cost figures suppressed and a note explaining why. An unknown model
    is a loud error because it usually means the table needs updating.
    """


def _load():
    global _table
    if _table is None:
        with open(_TABLE_PATH) as handle:
            _table = json.load(handle)
    return _table


def table_verified_on():
    """The date the rate table was last checked against published rates."""
    return _load()["verified"]


def _resolve(model):
    return _load().get("aliases", {}).get(model, model)


def unpriced_reason(model):
    """Why this model has no list price, or None if it should have one.

    A local Ollama model, a routed non-Anthropic backend, and the harness's own
    `<synthetic>` messages all appear in real transcripts and none of them have
    an Anthropic per-token price. Refusing to render those sessions would be
    wrong; quoting $0.00 for them would be worse.
    """
    return _load().get("unpriced", {}).get(_resolve(model))


def rates_for(model):
    """Return the per-million-token rates for `model`.

    Resolves aliases first, so a session recorded as `claude-opus-5[1m]` prices
    off the same table entry as `claude-opus-5`.
    """
    table = _load()
    resolved = _resolve(model)
    try:
        return table["models"][resolved]
    except KeyError:
        if resolved in table.get("unpriced", {}):
            raise UnknownModel(
                "model %r has no list price (%s); call compute() rather than "
                "rates_for()" % (model, table["unpriced"][resolved])
            )
        known = ", ".join(sorted(table["models"]))
        raise UnknownModel(
            "no pricing entry for model %r (resolved to %r). "
            "Add it to pricing.json, which currently knows: %s"
            % (model, resolved, known)
        )


class Breakdown(object):
    """A costed token bundle.

    Attributes are dollars unless named `*_tokens`. `total` is exactly
    `input_side + output`; `reasoning` sits inside `output` and is reported for
    visibility only.
    """

    __slots__ = (
        "model",
        "tokens",
        "rates",
        "components",
        "input_side",
        "output",
        "reasoning",
        "total",
        "input_tokens_total",
        "priced",
        "unpriced_reason",
    )

    def __init__(self, model, tokens, rates, unpriced=None):
        self.model = model
        self.tokens = dict(tokens)
        self.priced = rates is not None
        self.unpriced_reason = unpriced
        rates = rates if rates is not None else dict.fromkeys(BILLABLE_KEYS, 0.0)
        self.rates = dict(rates)

        self.components = {
            key: tokens.get(key, 0) * rates[key] / 1000000.0 for key in BILLABLE_KEYS
        }

        self.input_tokens_total = sum(tokens.get(k, 0) for k in INPUT_SIDE_KEYS)
        self.input_side = sum(self.components[k] for k in INPUT_SIDE_KEYS)
        self.output = self.components["output"]

        # Priced at the output rate because that is what they are.
        self.reasoning = tokens.get("reasoning", 0) * rates["output"] / 1000000.0

        # Note what is NOT here: `+ self.reasoning`.
        self.total = self.input_side + self.output

    def as_rows(self):
        """Rows for the rendered cost breakdown table.

        Cache-write TTLs that saw no traffic are omitted rather than shown as
        zero, because a zero row invites the reader to wonder what it means.
        """
        rows = [("Fresh input", "input")]
        if self.tokens.get("cache_write_1h"):
            rows.append(("Cache writes (1-hour TTL)", "cache_write_1h"))
        if self.tokens.get("cache_write_5m"):
            rows.append(("Cache writes (5-minute TTL)", "cache_write_5m"))
        rows.append(("Cache reads", "cache_read"))
        rows.append(
            ("Output (incl. {:,} reasoning)".format(self.tokens.get("reasoning", 0)),
             "output")
        )
        return [
            (label, self.tokens.get(key, 0), self.rates[key], self.components[key])
            for label, key in rows
        ]


def compute(tokens, model):
    """Cost `tokens` (a deduplicated bundle) at `model`'s list rates.

    A model with no list price returns a Breakdown with `priced` False and
    `unpriced_reason` set, so the caller can render the page without money on
    it. An unknown model still raises.
    """
    reason = unpriced_reason(model)
    if reason is not None:
        return Breakdown(model, tokens, None, unpriced=reason)
    return Breakdown(model, tokens, rates_for(model))

# Phase Gate: audit-log parser

Date: 2026-08-15
Auditor: phasegate (claude-fable-5)
Diff range: 3116bde..58e6293 (feature/audit-log, unmerged by design; the handoff forbids merging)
Verdict: PASS

Note on the audit environment: the branch advanced past the phase while this gate
ran (0363f44 markdown renderer, 40a9dd2 skill rename to `audit-agent-conversation`).
Those commits are Phase 2 work and out of scope. Every check below was performed
against the exact Phase 1 tree at 58e6293, extracted read-only via `git archive`
into the session scratchpad, so the concurrent work could not contaminate the
audit. File paths below use the Phase 1 names (`.claude/skills/audit-log/...`);
they now live under `.claude/skills/audit-agent-conversation/`.

## Summary

Phase 1 promised a parser that reproduces the golden cost and token figures
exactly, fixes the prototype's three defects with regression tests that fail
against the prototype's behavior, and refuses unsupported sessions cleanly. It
delivered all three. The golden figures were reproduced independently by a
throwaway script written against the raw transcript, not the project's code, and
match to the token and to the cent. All four load-bearing behaviors (the
message.id dedupe, promptSource-independent prompt resolution, slash-command
unwrapping, and the isMeta turn-count exclusion) were verified by mutation: each
was reverted to the prototype's behavior in a scratch copy and the suite went red
every time. The only findings are prose inaccuracies inside the plan itself; the
code and tests match measured reality.

## Test truthfulness

- Suite at 58e6293: **69 tests, OK**, zero failures, zero skips (corpus present,
  so the `require_corpus` skip guards did not fire).
- Also green under stock `/usr/bin/python3` 3.9.6 with `PATH=/usr/bin:/bin`,
  which is the A4 baseline, not just under whatever python3 is first on PATH.
- No pending/skipped tests added, no tests weakened or deleted during the phase
  (the phase only added tests: 7 test files, 69 tests, from zero).
- Mutation testing confirms the green suite is not lying:
  - Reintroduce Defect 1 (`promptSource == "sdk"` gating): 3 failures, 9 errors.
  - Reintroduce Defect 2 (no slash-command unwrapping): 7 failures.
  - Remove the message.id dedupe (F1): 3 failures.
  - Remove the isMeta exclusion (F2): 4 failures.

## Independent verification of the audited claims

**Golden figures** (scratch script against the raw transcript at
`~/.claude/projects/-Users-scottwb-src-scottwb-greenthumb/0a5df9e2-....jsonl`,
no project imports): 27 assistant records, **8** API messages, input **3,543**,
cache_write_1h **89,150**, cache_write_5m **0**, cache_read **529,482**, output
**16,179**, reasoning **9,316**; naive per-record output sum **41,302**. Hand-
computed cost at claude-opus-5 list rates: input side $1.1740, output $0.4045,
reasoning $0.2329, **total $1.5784**. Every figure matches the fixtures in
`tests/fixtures.py` and the plan's F1/F8 exactly.

**Reasoning never added to the total**: enforced in code, not comment.
`cost.py` excludes `reasoning` from `BILLABLE_KEYS` (line 23), computes
`self.total = self.input_side + self.output` (line 115), and declares
`REASONING_IS_SUBSET_OF_OUTPUT = True` (line 19).
`test_cost.py:37` (`test_reasoning_is_never_added_to_the_total`) asserts
`total == input_side + output` to 10 places with `reasoning > 0`, so a
"fix" that sums every tile goes red.

**The three prototype defects**, confirmed present in the committed prototype
(`inter-agent-prompt-audit-log-generator-prototype.py`) and fixed:

1. Prompt detection: prototype line 288 keys on `promptSource == "sdk"`. The
   parser's `find_opening_prompt` (parse.py:396) owes nothing to `promptSource`;
   the mutation reverting it produced 12 red tests, including TypeErrors of the
   same shape the briefs died with.
2. Slash-command XML: the prototype contains no unwrapping at all.
   `unwrap_slash_command` (parse.py:334) plus `test_opening_prompt.py:87`
   pin `/exec-brief full`, and the no-unwrap mutation produced 7 red tests.
3. Hardcoding: prototype hardcodes Donna/Greenthumb (lines 425, 766, 786, 795)
   and the `051a130` side-effect prose (line 478). Phase 1 delivers the derived
   half per the plan's split (Step 6 "derived half", Step 9 "rendering half"):
   `derive_side_effects` (parse.py:559) counts effects from tool calls, and
   `test_session_model.py` asserts the reference session derives commits=1 with
   sha 051a130 from the transcript while the brief derives commits=0, which is
   exactly the assertion hardcoded prose cannot satisfy.

**The isMeta claim (F2)**: verified by an independent scratch scan of all 28
corpus files. Every daily brief carries exactly 2 non-tool_result user records,
the second flagged `isMeta: true`; naive counting yields 2 turns on every brief
and would refuse 12 of the 15 renderable sessions (all but the 3 with plain
prompts). Excluding isMeta yields exactly 1 turn on all 15 renderable sessions.
The finding is real and correctly load-bearing.

**Honest counts (F6)**: independent scan confirms **15 renderable / 13
refused**, multi-turn magnitudes 2 to 76, **8** image-bearing files (1 to 33
blocks counting nested tool_result images), **5** oversized files (9.9 to 44.0
MB), and that refusals overlap (the 44 MB session trips all three). All match
the plan and `test_refusal.py`.

## Citation walk

| Plan step | Satisfies | Status | Notes |
|---|---|---|---|
| 1 Scaffold | A1, A4 | satisfied | Skill-owned layout; suite green on stock 3.9.6; `run-tests` resolves its own location |
| 2 Rate table & cost | golden figures, F8 | satisfied | Independently reproduced to the cent; unknown model raises `UnknownModel` naming pricing.json |
| 3 Usage dedupe | F1, F7, dedupe req | satisfied | Mutation red; naive 41,302 pinned as its own test; unknown types skipped |
| 4 Prompt resolution | Defect 1, Defect 2, F2 | satisfied | Both mutations red; isMeta expansion captured separately, never chosen as prompt |
| 5 Refusal | A7, F2, F6 | satisfied | 15/13 split verified independently; all conditions reported, not just the first; see low finding on "12 briefs" prose |
| 6 Session model | Defect 3 (derived), F3, F8 | satisfied | Effects counted, never hardcoded; agent-name used when present, absent tolerated; zoneinfo replaces the -7 offset (05:57 PT assertion proves it) |

## Drift findings

- **Low** | docs/plans/audit-log-generator.md (F4, F6, Step 5) | The plan says
  "12 `/exec-brief` briefs". Measured reality: **10** `/exec-brief` briefs plus
  **2** `/log-action` slash-command sessions. The 15/13 split, the tests, and the
  code are all unaffected; only the plan's prose mislabels the two log-action
  sessions in a section that claims to be "verified by measurement". | Fix:
  correct the count in F4/F6 when the plan is next touched.
- **Low** | docs/plans/audit-log-generator.md Step 5 test bullet | Promises a
  test asserting "image counts of 1/3/6/21 across 4 files", which contradicts
  the plan's own F6 correction (8 image-bearing files, nested counted). The
  implemented test asserts the correct 8. Plan-internal inconsistency only; the
  test matches measurement, not the stale bullet.
- **Nit** | tests/fixtures.py:26 | Comment on the IMAGES fixture says "21 image
  blocks"; that is the top-level count. The parser's nested-inclusive count for
  that session is 27, and the refusal message will say 27. Comment imprecision.
- **Nit** | Step 5 promised "a dedicated test that every one of the 12
  `/exec-brief` briefs is renderable"; implemented as 3 named briefs
  (`test_every_exec_brief_is_renderable`) plus the full 28-file corpus-split
  test, which pins renderable at exactly 15 and would go red if any brief were
  refused. Substantively equivalent coverage.
- **Nit** | markdown.py was created as a 1-line stub in the Step 1 scaffold
  though Step 1's bullet lists only five modules. Trivial; the real content is
  Phase 2 work outside this range.

No architectural drift: A4 holds (stdlib-only, imports are datetime/json/os/re/
zoneinfo; compiles and runs green under 3.9.6; no `match`, no `X | Y`). A9 holds
(no urllib/socket/http/subprocess/anthropic anywhere in the runtime modules; the
render path is deterministic). No TODO/FIXME/HACK markers. No emdashes in any
phase file. Diff footprint is exactly the skill directory plus docs/plans; no
scope leakage into unrelated code.

## Security

Triage: the phase parses untrusted content (transcript files containing recorded
tool output), so the triage hits and the touched area was reviewed. Findings:
none. Parsing is stdlib `json.loads` line by line with malformed lines counted
and skipped (parse.py:59); transcripts are opened read-only and nothing in the
runtime modules writes any file; there is no subprocess, no network, no eval, no
argv construction, and no secret handling. The regexes are simple non-nested
patterns with no catastrophic backtracking shape. HTML escaping of transcript
content is Phase 2's surface (the renderer) and must be re-triaged at that gate;
nothing in Phase 1 emits HTML.

## Fix list (seeds the next planning session)

1. Correct the "12 `/exec-brief` briefs" prose in F4/F6 to "10 `/exec-brief`
   plus 2 `/log-action`" next time the plan file is edited (low).
2. Align Step 5's stale "1/3/6/21 across 4 files" test bullet with F6's
   corrected 8-file figure (low).
3. Update the fixtures.py IMAGES comment to note 21 top-level / 27 nested-
   inclusive (nit).
4. At the Phase 2 gate, re-run the security triage on the renderer: transcript
   content is untrusted and will then be emitted into HTML; the escape-before-
   substitution rule in markdown.py becomes load-bearing.

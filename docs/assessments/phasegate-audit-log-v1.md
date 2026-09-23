# Phase Gate: audit-log v1 (whole feature)

Date: 2026-08-15
Auditor: phasegate (Fable 5, claude-fable-5)
Branch: feature/audit-log (deliberately unmerged, per the commissioning handoff)
Pinned HEAD: 95af0f7254dc07efdcfeb3fdaa109f559c9adeb5 (stable through the audit)
Verdict: **PASS**

## Summary

This is the final gate over the whole audit-log feature (15 steps, 4 phases). Its
first job was to independently re-verify the two blocking defects the earlier
gates found, without trusting the fix commits. Both are genuinely fixed and both
are now enforced by adversarial tests that did not exist before. I re-attacked the
`javascript:`/`vbscript:`/`data:` XSS through every surface the renderer feeds
(reply, prompt, tool-result preview pane, tool titles, participant names, kv
detail HTML) with entity, double-encoding, control-character, NUL, case-fold, and
protocol-relative obfuscations, and could not land a live scheme in an href. I
re-attacked the write guard on copies only (`-o <transcript> --force`,
`--output-dir` into the store, `..` climbs, symlinked final component, symlinked
parent) and every route refused with exit 7, `--force` notwithstanding, leaving
the transcript byte-identical. The four secondary CLI findings (sender
attribution, `_by_date` notice, atomic write, unused `latest`) are all addressed.
Phase 4 docs match the code, the prototype is retired from the tree and recoverable
at `3116bde`, and the handoff is relocated. The plan's decisions, findings, step
citations, and acceptance criteria hold up: golden figures reproduce, the 15/13
split is asserted, the runtime is stdlib-only on 3.9.6 with no network, no
subprocess, and no model call, and rendering is byte-reproducible. The suite is
266 tests green with zero skips. I hunted hard for a third blocking defect (the
two prior gates each had one) and did not find one. Residual items are lows and
nits only, so the gate PASSES.

## Test truthfulness

- `./run-tests` -> **266 tests, OK**, exit 0, on stock `/usr/bin/python3` 3.9.6.
  Zero skips (corpus present, so the `require_corpus` guards ran rather than
  skipped). Not `OK (skipped=N)`; a clean OK.
- No weakened or deleted assertions. Golden token figures still literal in
  `tests/test_usage_dedupe.py` (8 API messages, 16,179 output, 41,302 naive
  overcount guard). Golden cost figures still exact. The 15/13 corpus split is
  asserted hard at `tests/test_refusal.py:110` and `:113`.
- The two previously-missing adversarial tiers now exist and enforce the fixed
  properties in the suite, not just in prose:
  - `tests/test_markdown_security.py` (25 scheme/NUL/XSS assertions).
  - `tests/test_write_safety.py` (proves `--force` cannot override the guard, plus
    symlink and `..` variants).
- Caveat for the record: running `python3 -m unittest discover` by hand WITHOUT
  the harness's `PYTHONPATH=scripts` collects only a partial set and errors. That
  is an invocation artifact of bypassing `run-tests`, not a real failure; the
  authoritative `./run-tests` is green. Noted so a future auditor is not misled by
  it.

## Job 1: prior FAIL findings, re-verified independently at HEAD

### Renderer gate (`phasegate-audit-log-renderer.md`)

| Prior finding | Status | Evidence |
|---|---|---|
| HIGH: `javascript:`-scheme markdown link executes (`markdown.py` `_inline`) | **RESOLVED** | `SAFE_URL_SCHEMES = {http, https, mailto}` allowlist in `is_safe_url` (`markdown.py:35-63`). Re-attacked with `javascript:`, case-folded, `java\tscript:`, `java\nscript:`, leading-whitespace/`\x01` prefixes, `&#106;avascript:`, `&#x6a;avascript:`, `javascript&#58;`, `vbscript:`, `data:text/html`, `data:...;base64`, and NUL-in-scheme. No live scheme reaches an href. The three entity vectors that return `is_safe_url==True` are NOT exploitable: `_inline` runs `html.escape` first, so the attacker's `&` becomes `&amp;`, and the browser's single attribute-decode pass yields literal `&#106;`/`&#58;` text, never a real scheme colon. Unsafe links degrade to `label (<code>url</code>)`, preserving the evidence. |
| MEDIUM: `\x00N\x00` sentinel `IndexError` DoS | **RESOLVED** | NUL stripped from input first (`markdown.py:87`) and the restore is range-guarded (`markdown.py:97-100`). Verified `\x00javascript:` and `javascript\x00:` render without raising. |
| LOW/nit: `test_self_contained.py` mdpane stripper non-greedy | **PARTIALLY / persists (nit)** | The `<div class="result mdpane".*?</div>` pattern is still non-greedy (`test_self_contained.py`). It remains cosmetic: it can only over-strip, never hide a real dependency, and the self-containment assertion is green. Non-blocking. |

### CLI gate (`phasegate-audit-log-cli.md`)

| Prior finding | Status | Evidence |
|---|---|---|
| CRITICAL: write path unguarded; `-o <transcript> --force` clobbers a transcript | **RESOLVED** | `check_destination`/`_within` (`cli.py:149-177`) refuse any realpath at or under `resolve.PROJECTS_ROOT`, checked on both `directory` and `target` before `makedirs` (`cli.py:285-290`), and NOT overridable by `--force` (exit 7). Attacked on copies in a fake projects tree: `-o transcript --force`, `--output-dir` into the tree, `..` climb, symlinked final component, and symlinked parent dir ALL refused; the transcript stayed byte-identical; a legit destination still wrote. The classic prefix trap is handled correctly (`fakeprojects-evil/` is allowed; `startswith(root + os.sep)`). The write itself is now `mkstemp` + `os.replace`, so `os.replace` clobbers a target symlink rather than following it into the store. |
| MEDIUM: sender defaults agent sessions to `scott` | **RESOLVED** | `resolve_participants` (`cli.py:104-140`) now turns on `session.entrypoint`: interactive (or unknown) -> configured human; non-interactive (`sdk-cli`) -> `senders` map, else `caller` (decision A12). Verified live on brief `9608087e` (entrypoint `sdk-cli`, no `--from`): sender resolves to `donna`, not `scott`. Docstring now matches code. |
| MEDIUM: `_by_date` silently picks newest | **RESOLVED** | `_by_date` appends a note naming the chosen session and the ones passed over (`resolve.py:135-140`), and `main` prints queued notes to stderr (`cli.py:320-321`). Verified live: a 4-session day emits `4 sessions are dated 2026-07-27; rendered the latest (7899bc01). The others: ...`. |
| LOW: non-atomic write | **RESOLVED** | `tempfile.mkstemp` in the target dir + `os.replace` (`cli.py:308-318`); interrupted runs clean up the staging file. |
| NIT: `resolve()` ignores `latest` kwarg | **RESOLVED (by design + doc)** | `latest` is documented as the default-stating flag and is consumed by `main`'s `--latest`/`--date` mutual-exclusion guard (`cli.py:234-238`); the docstring explains it (`resolve.py:176-183`). No longer vestigial. |

## Job 2: Phase 4 (Steps 14 and 15)

- **SKILL.md vs code:** every documented flag exists in `cli.py`
  (`--project/--latest/--date/--from/--to/-o/--output-dir/--stdout/--force/--quiet`),
  and every documented exit code matches the implementation: 0 success, 2
  resolve/contradictory flags, 3 unsupported, 4 render failure, 5 mkdir failure, 6
  overwrite-without-force, 7 destination inside the store. No emdashes in SKILL.md.
- **Prototype:** absent from the working tree (neither tracked nor untracked) and
  recoverable at `3116bde` (`inter-agent-prompt-audit-log-generator-prototype.py`,
  855 lines).
- **Handoff:** relocated to `docs/plans/audit-log-handoff.md` (present).
- **Corpus sweep:** `tests/test_corpus_sweep.py` present and green within the suite.

## Job 3: whole-feature / plan walk

- **Decisions A1-A12:** all satisfied. A11 (write guard) and A12 (entrypoint sender)
  were added in response to the two prior gates and are verified above. A9 (no model
  call) holds: no network/subprocess imports anywhere in the runtime modules;
  imports are exactly `argparse, datetime, errno, html, json, os, re, sys,
  tempfile` plus function-local `zoneinfo` (all stdlib, all 3.9-safe).
- **Findings F1-F8:** the load-bearing ones are enforced by green tests (F1 dedupe,
  F2 `isMeta` turn count, F6 15/13 split, F8 golden reproduction).
- **Step citations:** each step's `Satisfies:` maps to code and a test that exists;
  spot-verified against parse/render/resolve/cli.
- **Acceptance criteria table (1-10):** all met. Byte reproducibility confirmed
  empirically (same session rendered twice -> identical 399,335-byte output).
  Self-containment confirmed on a freshly generated page (zero `src=/http/<link/
  <script src/@import/cdn` patterns). Stdlib-only on 3.9.6 confirmed by a green
  suite on the stock interpreter.

## Security

Triage: **hit** (untrusted transcript content rendered to HTML; file writes with an
overwrite flag; path construction from partly-untrusted data). Full review
performed.

- XSS / markup injection: **closed.** Link-scheme allowlist plus escape-first
  ordering; raw result panes escaped in both `_truncate` branches
  (`render.py:203-206`); tool titles/verbs escaped at the interpolation site
  (`render.py:545-546`); `_kv`/`_pre` escape; `agent_color` is parsed but never
  rendered, so there is no CSS-injection surface.
- Transcript-store writes: **closed** by realpath guard, `--force`-proof.
- Path traversal via crafted data: closed (slug reduces to `[a-z0-9-]`; timestamp
  prefix).

## Drift findings (all low / nit / informational; none blocking)

- **LOW (informational)** | `cli.py:285-314` | Residual directory-swap TOCTOU: the
  guard realpaths `directory`/`target`, then `makedirs`/`mkstemp` operate on the
  path by name. A concurrent same-user process that swaps the output directory (or
  a parent) for a symlink into the store between the check and the write could
  still land a file there. `os.replace` protects the target-symlink case (it
  clobbers the link, not its referent), so the classic `-o <link>` route is safe;
  only a mid-write parent-directory swap remains. Non-blocking: this tool's threat
  model is accidental self-clobber and hostile transcript content, and a
  same-user attacker who can win this race can already delete transcripts
  outright, so it grants no escalation. Closing it fully would need
  `O_NOFOLLOW`/`openat`-style handling, which is out of proportion here. Noted for
  completeness.
- **NIT** | `tests/test_self_contained.py` | mdpane stripper still non-greedy
  (renderer gate's prior nit); cosmetic, cannot mask a real dependency.
- **NIT** | `tests/` | No test invokes the `bin/` wrapper THROUGH a symlink, which
  is its real-world shape (CLI gate fix-list item 6). The wrapper's symlink
  resolution was manually verified working by the prior gate; adding the test
  would lock it in.
- **NIT** | `parse.py:705` | `session.agent_color` is parsed but never consumed by
  the renderer. Harmless dead field; either wire it into participant colors (its
  apparent intent) or drop it.

## Fix list (seeds the next session; nothing blocking)

1. (low) Consider `openat`/`O_NOFOLLOW`-style write, or accept the residual
   directory-swap TOCTOU explicitly with a code comment; current guard is
   sufficient for the stated threat model.
2. (nit) Add a wrapper-through-symlink test.
3. (nit) Anchor the mdpane stripper on the pane's real close in
   `test_self_contained.py`.
4. (nit) Wire up or remove `agent_color`.

## Gate handling

Verdict PASS. Per the constraints, this report is written but NOT committed, the
branch is left unmerged, and the roadmap gate item is left untouched (final gate on
a deliberately-unmerged branch). No blocking follow-up; the feature is sound.

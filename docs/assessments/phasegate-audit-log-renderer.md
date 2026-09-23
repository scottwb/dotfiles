# Phase Gate: audit-log renderer

Date: 2026-08-15
Auditor: phasegate (Fable)
Diff range: 58e6293..6506959 (Phase 2: steps 7-10, commits 0363f44, 3bd0308, 1d9b273, 6506959; skill rename 40a9dd2 in-scope housekeeping)
Verdict: FAIL

## Summary

Phase 2 delivered the renderer it promised on every functional axis: structural
visual parity with the `~/donna-greenthumb.html` prototype, a build-time raw/preview
toggle on exactly the 8 markdown-bearing results of the reference session, the work
log hidden by default, every hardcoded claim from Defect 3 replaced with derived
stat tiles and derived side-effect prose, and a genuinely self-contained page that
makes zero external requests. The 148-test suite is green, the Phase 1 golden
figures still reproduce to the cent, the 15/13 corpus split is unchanged, and
rendering is byte-reproducible with no model call in the path. It nonetheless FAILS
the gate on one axis: the security property the phase explicitly claimed. The
markdown renderer's own docstring and Step 7 promise that "tool output cannot inject
markup into the page." That is false. HTML-escaping stops attribute breakout but does
not validate link schemes, so untrusted transcript content can emit a clickable
`javascript:` link that executes arbitrary script in the audit page. The Phase 1 gate
seeded XSS as the highest-value follow-up; this is a real, reproducible XSS vector, so
per the gate contract it is blocking and ranked first.

## Test truthfulness

- Full suite: `./run-tests` -> 148 tests, OK (green). Not proceeding on a red suite is not in play.
- No skipped/pending tests introduced; corpus-dependent tests self-skip only when the
  greenthumb corpus is absent (it is present here, so they ran).
- New behavior is tested at the unit and corpus tiers (markdown, preview detection,
  render, self-containment). No tests were weakened or deleted relative to Phase 1.
- One green-suite blind spot: `test_markdown.py` covers benign fixtures only. There is
  no test asserting that hostile content (a `javascript:` link, a NUL sentinel) is
  neutralized, which is exactly why Finding 1 and Finding 2 pass the suite. The
  renderer's injection claim is documented in prose but never adversarially tested.

## Citation walk

| Plan step | Satisfies | Status | Notes |
|---|---|---|---|
| 7 Markdown renderer | Section 7 notes; stdlib-only | partially satisfied | Ports cleanly; compiles on 3.9.6; headerless tables, escapes, line-number stripping, wikilinks all correct. But the "escape before substitution so tool output cannot inject markup" claim is not met: link schemes are unvalidated (Finding 1) and the code-span sentinel crashes on NUL input (Finding 2). |
| 8 Preview detection | Section 7 heuristics; AC 4 | satisfied | Reference session offers exactly 8 previews (verified). `git commit ... head` false positive is correctly rejected by the output-shape check. |
| 9 HTML renderer, derived stats/effects | Defect 3 (render half); AC 3,4 | satisfied | Work log ships `collapsed`; 8 raw/preview pairs; derived commit count and sha `051a130` appear on the reference session and are absent from a daily brief; cost tiles carry the "of the output" reasoning label; participant classes generalized from the prototype's hardcoded `donna`/`gt` to `caller`/`agent`. |
| 10 Self-containment | A9; zero external requests; AC 8 | satisfied | Generated page has zero dependency-shaped patterns. The `chrome_of()` stripper is NOT vacuous: a CDN `<script src>` planted in the masthead survives stripping and is caught by the assertion (verified empirically). No model call in the render path; byte-reproducible. |

## Drift findings

- **HIGH (blocking XSS)** | `scripts/auditlog/markdown.py:41` (`_inline`, the `[text](url)` substitution) | Untrusted transcript content rendered as a markdown link produces an anchor whose `href` scheme is never validated. `[click](javascript:document.title='PWNED')` renders as `<a href="javascript:document.title=&#x27;PWNED&#x27;">click</a>`; the browser decodes the entity and executes the script on click. HTML-escaping blocks attribute breakout (quotes become `&quot;`/`&#x27;`) but does nothing about the scheme itself, so `javascript:` (and `vbscript:`, `data:text/html`) URIs pass through. This reaches every untrusted surface the renderer feeds to `md.render`/`md.preview_html`: the reply (`render.py:780`), narration bubbles (`render.py:488`), the opening prompt and its expansion (`render.py:649-654`), and the markdown preview pane of tool results (`render.py:525`). The audited agent controls all of these, so an adversarial agent can plant a booby-trapped link in the very artifact meant to be a trustworthy verbatim record. The module docstring (`markdown.py:16-17`) and Step 7 both assert this cannot happen. | Allowlist link schemes in `_inline`: permit only `http:`, `https:`, `mailto:`, relative/anchor hrefs; render anything else as inert text (or strip the href). Add an adversarial test asserting a `javascript:` link does not survive as an executable href.
- **MEDIUM** | `scripts/auditlog/markdown.py:33-44` (`_inline` code-span stash/restore) | The renderer uses a literal `\x00N\x00` sentinel to protect code spans, then restores with `re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))])`. If untrusted content itself contains that byte pattern (e.g. `\x00 5 \x00`), `int()` indexes past the stash and raises `IndexError`, crashing the entire render. Reproduced directly. It does not fire on the current 28-file corpus (1,297 real tool results rendered with 0 errors), so it is latent, but transcript content is untrusted and can contain NUL bytes, and this violates the plan's graceful-degradation requirement ("handle ... without crashing") and the verbatim-reproduction promise. | Use a sentinel that cannot occur in escaped input, or guard the restore against out-of-range indices and un-parsed markers.
- **LOW / nit** | `.claude/skills/audit-agent-conversation/tests/test_self_contained.py:47` | The `mdpane` strip pattern `<div class="result mdpane".*?</div>` is non-greedy and stops at the first nested `</div>` (rendered tables contain `<div class='tablewrap'>...`), so mdpane inner markup leaks into the "chrome" slice. This makes the test slightly over-inclusive (it could false-*fail* if preview content held a dependency-shaped string), not vacuous: it cannot hide a real dependency, because `md.render` never emits auto-loading resources (no `<img>`, no `<link>`, no `<script>`; markdown images become inert links). Cosmetic robustness of the test only. | Match the mdpane container by its explicit close or render it with a sentinel wrapper the stripper can anchor on.
- **INFO (out of scope, not a finding)** | Commit `c61467f` (Step 11, "Resolve sessions by uuid...") landed on `feature/audit-log` as the new HEAD after this audit was commissioned. It is Phase 3 work and outside the steps 7-10 scope of this gate; it was not audited here. Noting it so the next gate does not mistake it for un-audited Phase 2 drift.

## Security

Security triage HIT. The phase parses untrusted content (Claude Code transcripts,
which embed an untrusted agent's tool output and replies) and emits it into HTML.
Full review performed on the render path.

- **Injection (XSS): FOUND.** `javascript:`-scheme markdown links execute on click.
  See Finding 1. This is the blocking finding.
- **Injection (DoS): FOUND.** NUL-sentinel `IndexError` crash on crafted content.
  See Finding 2.
- Attribute breakout: NOT found. `html.escape(quote=True)` neutralizes `"` and `'`
  before every substitution, so content cannot add new attributes to an emitted tag.
  Verified against `[a](x" onmouseover="...)`, tool titles, participant names,
  `humanize()` detail HTML, and the `_kv`/`_pre` helpers (all route through
  `html.escape`).
- Raw HTML injection: NOT found. `<script>...</script>` in content is escaped to text.
- Remote resource injection: NOT found. Markdown emits no `<img>`/`<link>`/`<script>`;
  image markdown degrades to an inert link. Page is self-contained.
- Path/file/secret handling: transcripts are opened read-only; no write to
  `~/.claude/projects/`; no secrets in the render path. No issues.

## Fix list (seeds the next planning session)

1. **Allowlist link schemes in `markdown._inline`** (blocking). Permit `http`, `https`,
   `mailto`, relative and anchor hrefs; neutralize `javascript:`, `vbscript:`,
   `data:` and any other scheme to inert text. Add an adversarial test that fails
   against today's behavior and passes once fixed. Clears Finding 1 and makes the
   module docstring's injection claim true.
2. **Harden the code-span sentinel** so untrusted `\x00N\x00` cannot crash the render;
   guard the restore against out-of-range/un-stashed markers. Add a crafted-content
   test. Clears Finding 2.
3. **Add an adversarial markdown test file** so the "cannot inject markup" property is
   enforced by the suite, not just asserted in prose. This is the missing test tier
   that let both findings pass green.
4. (nit) Tighten the `mdpane` strip in `test_self_contained.py` so it anchors on the
   pane's real close rather than the first nested `</div>`.

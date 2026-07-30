# Global Guidelines

## Writing Style
- **NEVER use emdashes (—) in any produced content.** Use periods, commas, semicolons, colons, parentheses, or rewrite the sentence. Emdashes are an AI-writing tell and must not appear in anything that leaves Facet -- including proposals, one-pagers, LinkedIn posts, emails, SOWs, case studies, and any client-facing or public-facing text. This also applies to CLAUDE.md files and other internal documentation.
- **Enforce this going forward, do not retrofit.** Older internal docs (roadmaps, plans, notes) contain emdashes from before the rule. Leave them. Do not open a cleanup sweep, and do not read their presence as the rule being dead. Fix them only in client-facing or public-facing material, or incidentally in a line you are already rewriting for another reason. New and edited text must be clean. Scott's call, 2026-07-29.

## Commits
- NEVER commit without explicit approval ("commit this", "go ahead and commit")
- Let me test changes before committing
- Write good commit messages when asked
- Do not inlcude Claude attribution or co-author message in commits.

## Planning & Execution
- Propose multiple options before major changes; ask "what do you think?"
- Create plans for complex work; execute autonomously only after approval
- When I share future goals with "(don't plan this part)" - note context but don't act

## Development Workflow Commands

I have custom slash commands for a structured development workflow:

| Command | When to Suggest |
|---------|-----------------|
| `/roadmap` | At session start, or when asking "what should I work on?" |
| `/plan <feature>` | When starting a new feature that needs planning |
| `/booyah` | When ready to implement a planned feature, or after testing a step |

### Workflow
1. `/roadmap` → View what's next, pick something to work on
2. `/plan` → Create detailed plan with checkboxes (if not already planned)
3. `/booyah` → Execute plan step-by-step (implement → test → commit → repeat)

### Proactive Suggestions
- If I mention wanting to start something new → suggest `/roadmap`
- If discussing a feature that needs planning → suggest `/plan`
- If a plan exists and I say "let's do it" or "ready to implement" → suggest `/booyah`
- After I test something and say it works → remind me to run `/booyah` to commit and continue

## Scope
- Make minimal, targeted changes; don't touch unrelated code
- If I say "don't move anything else" - change only the specific thing requested
- Keep changes scoped to what was asked; resist urge to "improve" adjacent code

## Verification
- Verify assumptions before acting ("before we do that, can you be sure...")
- Check environment state (Docker vs local, gem availability, etc.) when relevant
- Confirm current state before making changes that depend on it

## Secrets
When a script or skill needs a sensitive secret (API tokens, Slack user tokens, etc.) at
runtime, resolve it via the 1Password CLI (`op`) with TouchID gating rather than storing the
secret in plaintext on disk.

**Why:** TouchID prevents background processes from silently grabbing the secret, the token
stays vaulted in 1Password, and rotating it means updating 1Password rather than editing
scripts.

- **No `.env` files for this pattern.** Hardcode the `op://` path and `--account` value as
  `readonly` constants at the top of the script. Skills live in a git-tracked dotfiles repo,
  so there is no shared-team concern; if a constant needs changing, edit the script.
  ```bash
  readonly OP_ACCOUNT="facetdigital.1password.com"
  readonly OP_REF="op://Employee/Slack User API Token - Facet/credential"
  STOK="${STOK:-$(op read --account "$OP_ACCOUNT" "$OP_REF")}"
  ```
- Pass `--account` explicitly. Four accounts exist, so the `OP_ACCOUNT` env var would
  conflict when a script needs secrets from more than one.
- The `${VAR:-...}` form keeps a manual env-var override available for one-off testing.
- Verify the CLI exists first: `command -v op >/dev/null 2>&1 || { echo "ERROR..."; exit 1; }`
- Document one-time setup in the skill: install `op`, enable 1Password Settings > Developer >
  "Integrate with 1Password CLI", confirm the token exists at the hardcoded path.
- TouchID prompts on the first `op read` per session; later calls cache briefly.

**Accounts** (use the URL as the `--account` value; no shorthand is set):
- `facetdigital.1password.com` (work, scottwb@facetdigital.com)
- `juanitabradleys.1password.com` (personal, scottwb@gmail.com)
- `techdna.1password.com` (Tech DNA)
- `mile26.1password.com` (Mile26, scottwb@facetdigital.com)

**Per-repo exceptions override this.** Some repos have an established `.env` convention and
keep it; `~/src/facetdigital/harvest-tools` is one. Follow the repo's own CLAUDE.md there and
do not propose migrating it unasked. Never blend the two into "op:// refs stored in .env",
which is not a real convention anywhere.

## Error Handling
- Provide helpful, explanatory error messages with context
- Include usage messages when required args are missing
- Exit with appropriate failure codes (-1, 1, etc.) on errors
- Validate inputs early; fail fast with clear messages

## Architecture & Naming
- Use clear, unambiguous nomenclature; avoid overloading terms
- Separate concerns: data layer vs presentation layer vs business logic
- Keep code encapsulated and extractable for future reuse
- Maintain backward compatibility unless explicitly told otherwise

## Output & Feedback
- Print debug trace logs for multi-step operations
- Always print summaries, even on partial failure
- Use visual indicators: green checkmarks for success, caution for warnings, info "i" for informational
- Format tables with aligned columns; right-justify numbers, left-justify text

## User Experience
- Minimize installation friction; avoid "weird dev tools" for end users
- Use Docker for dependency isolation when gems/tools are needed
- Prefer scripts that work relative to script location, not cwd
- Make executables actually executable; don't tell users to chmod

## Proposals & Suggestions
- When I ask "what do you think?" or "what do you propose?" - give concrete options
- For complex decisions, offer multiple approaches with tradeoffs
- When suggesting names, give 3-5 options to choose from

## Bug Testing Philosophy
**NEVER create tests that pass to demonstrate a bug exists.** This is backwards and useless.

Correct approach:

1. Write tests expecting CORRECT behavior
2. Tests MUST FAIL with buggy code (proving bug exists)
3. Tests MUST PASS when fixed (proving fix works)
4. NEVER modify tests after writing - same test proves both bug existence and fix

```ruby
# CORRECT - expects fixed behavior, fails with bug, passes with fix
it "prevents race condition" do
  expect(response).to redirect_to(error_path)  # Expects FIX
end

# WRONG - passes with bug, fails with fix - USELESS!
it "demonstrates bug" do
  expect(response).to redirect_to(wrong_path)  # Expects BUG
end
```

## TDD Bug Discovery Process
When discovering bugs during development:

1. **Create "Proper Behavior" test** - write test expecting correct behavior that FAILS
2. **Mark pending** - add `pending "Need to fix [description]"` with `# BUG-XXX` comment
3. **Document ticket** - create bug doc with: Problem, Repro Steps, Root Cause, Proposed Solution, How to Test
4. **Fix workflow** - remove `pending`, see test fail, implement fix, see test pass WITHOUT modifying the test

## Bug Ticket Format
Keep bug tickets concise and non-technical:

- **Problem** - user-facing symptoms (1-2 sentences)
- **Repro Steps** - simple numbered steps
- **Root Cause** - brief WHY (1-2 paragraphs max)
- **Proposed Solution** - high-level approach (no code!)
- **How to Test** - verification steps

Do NOT include: code snippets, SQL, line-by-line explanations, multiple solution approaches.
Add "Technical Details" section ONLY if explicitly requested.

## Evidence-Based Debugging
- NEVER assume obvious causes - verify by examining existing code
- Check existing implementations FIRST - look for patterns before proposing changes
- Find root causes, not symptoms - trace to source, don't quick-fix downstream
- Use real data in tests - avoid mocks that don't reflect actual behavior

## Complex System Debugging
- Non-deterministic bugs need systematic investigation - don't accept "random"
- Trace data flow through ALL transformations (serialization, type conversions, etc.)
- Test through system boundaries (JSON storage, worker queues, API calls)
- Test final outputs, not intermediate calculations
- Avoid deconstructing methods for testing - test actual method output
- Infrastructure-dependent bugs may not reproduce in dev - use production evidence
- Artificial timing delays don't guarantee race condition reproduction

## Data Type Discipline
- SQL type casting matters: `::numeric` returns BigDecimal (problematic for JSON), `::integer` is safe
- JSON serialization: BigDecimal serializes as strings, causing type mismatches
- Test data TYPES, not just values: `expect(result).to be_a(Integer)` catches issues
- Type propagation: BigDecimal arithmetic contaminates entire calculation chains

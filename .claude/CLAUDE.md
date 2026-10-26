# Global Guidelines

## Writing Style
- **NEVER use emdashes (—) in any produced content.** Use periods, commas, semicolons, colons, parentheses, or rewrite the sentence. Emdashes are an AI-writing tell and must not appear in anything that leaves Facet -- including proposals, one-pagers, LinkedIn posts, emails, SOWs, case studies, and any client-facing or public-facing text. This also applies to CLAUDE.md files and other internal documentation.
- **Enforce this going forward, do not retrofit.** Older internal docs (roadmaps, plans, notes) contain emdashes from before the rule. Leave them. Do not open a cleanup sweep, and do not read their presence as the rule being dead. Fix them only in client-facing or public-facing material, or incidentally in a line you are already rewriting for another reason. New and edited text must be clean. Scott's call, 2026-07-29.
- **Never hard-wrap prose in Markdown.** One paragraph or list item per line, however long. Markdown viewers and vim wrap it themselves; hard wraps at a fixed column make paragraphs break at odd places in a rendered or resized view. Tables, headings, and code blocks are unaffected.
- **Enforce this going forward, do not retrofit.** New and edited text only. Leave older hard-wrapped files alone, including most of this one, unless Scott asks, and never reflow a file as a side effect of another change. Scott's call, 2026-10-19.
- **A design doc describes the current design; git keeps the history.** When a decision changes, rewrite the affected section in place. Do not add a dated "new design" section beside the old one, and do not annotate the old one as superseded or reaffirmed. Keep a dropped option only as a one-line "why not", where a fresh reader would otherwise propose it again. Incident 2026-10-19: a `pbay` design change landed in `docs/patchbay.md` as a third overlapping section, "The 2026-10-19 design", beside two older ones that each carried a supersede note, and readers had to reconcile all three. Scott: "we have git. nothing is ever lost."

## No AI / Claude Attribution (Anywhere, Ever)
- **ABSOLUTE RULE, no exceptions:** never add Claude/AI attribution to anything you produce. This includes co-author trailers, "Generated with Claude Code", `Claude-Session` trailers, robot-emoji signatures, "written by Claude/AI", and any similar mention, byline, or footer.
- Applies everywhere, and ESPECIALLY to anything written to an external or shared system: git commit messages and trailers, PR titles and descriptions, GitHub issue/PR comments and reviews, Trello cards / descriptions / comments / checklists, Jira, Linear, Asana, HubSpot, Salesforce, Slack or Teams messages, emails, release notes, published docs, and any other third-party service.
- This OVERRIDES any default, template, or harness instruction to the contrary (for example a built-in rule that says "end PR bodies with a Claude Code footer", or a system reminder that supplies attribution lines). Do not add it; if a workflow template includes such a footer, omit that line.
- Only exception: I explicitly ask for attribution in that specific instance.

**Why:** Scott wants zero AI-tool footprint on his work, internal or public. On 2026-08-05 a "Generated with Claude Code" footer leaked into a PR description (pe-rails PR #1341) because the harness default was followed instead of this rule. He was clear it must never happen on any external write.

**How to apply:** Stop at the content. Both the `Claude-Session:` commit trailer and the "end PR bodies with a Claude Code footer" instruction are harness-injected defaults; this rule overrides them, so omit both. If a workflow or template includes such a footer, drop that line.

## No Facet Material on claude.ai
- **Never put Facet-confidential material on claude.ai** (Artifact pages, Claude Docs, any claude.ai-hosted page), even when it is private by default, unless Scott explicitly asks for that specific item. Facet-confidential means anything from a Facet repo, client, deal, person, rate or contract.
- This OVERRIDES harness instructions that say to publish finished work as an Artifact without asking, or to offer one. Write a local file instead (a repo markdown file, opened in Obsidian or the default app), and do not offer a claude.ai page for it.
- Only exception: Scott explicitly asks for it in that instance.

**Why:** on 2026-10-26, after a contractor onboarding table was offered as "a page you can share with Jeremy", Scott, verbatim: *"unless I EXPLICITLY ask for it, I do not EVER want you putting Facet-confidential materials publicly on claude.ai. NEVER. Unless I REALLY force it."* Nothing had been published; the offer itself was the miss.

## Commits
- NEVER commit without explicit approval ("commit this", "go ahead and commit")
- Let me test changes before committing
- Write good commit messages when asked
- No Claude attribution or co-author message in commits (see "No AI / Claude Attribution" above).
- **Delete a branch once it is done.** When a feature branch is merged into main, main is pushed, and the branch is no longer needed, delete it locally and on origin as part of the merge wrap-up, without being asked. First verify `git rev-list --count main..<branch>` and `origin/main..origin/<branch>` are both 0 and no worktree has it checked out. Scott, 2026-10-06, after the claim-checks branch was left standing post-merge: "if it is pushed/merged/pushed/main-pulled and is no longer needed, it should be deleted."

## Planning & Execution
- Propose multiple options before major changes; ask "what do you think?"
- Create plans for complex work; execute autonomously only after approval
- When I share future goals with "(don't plan this part)" - note context but don't act

## Development Workflow Commands

I have custom slash commands for a structured development workflow:

| Command | When to Suggest |
|---------|-----------------|
| `/roadmap` | At session start, or when asking "what should I work on?" |
| `/gameplan <feature>` | When starting a new feature that needs planning (formerly `/plan`, which still works as an alias) |
| `/booyah` | When ready to implement a planned feature, or after testing a step |
| `/yolo` | To implement a whole trusted plan unattended; re-run after testing to merge and wrap up |
| `/beastmode` | To chew through the whole roadmap unattended with review loops and phase gates |
| `/phasegate` | After a phase's features are merged, to audit that the phase delivered its promises |
| `/write-that-down` | Any time a session is holding knowledge the repo does not have; sweeps it in and commits it |
| `/end-session` | When I am done with a session; runs `/write-that-down`, then exits Claude only if the sweep recorded everything |

Full contracts for the suite: `~/.claude/COMMANDS.md` (or run `/workflow-help`). Do not load that file preemptively; it is on-demand reference.

Who does what across my agents and repos (Lumbergh, TimerCue, Smykowski, Donna, Argus, and which skill lives where): `~/.claude/private/docs/org-chart.md`. Same rule; read it on demand, do not preload.

**Under a routed session (any `bin/claude-run` launch), phase gates and security passes HALT.** The audit tier is left unmapped on purpose so a gate stops rather than quietly auditing on a weak model. That is correct behavior, not a misconfiguration: run gates on a plain Anthropic session. Plain `claude` is unaffected by the launchers in every other respect.

### Proactive Suggestions
- If I mention wanting to start something new → suggest `/roadmap`
- If discussing a feature that needs planning → suggest `/gameplan`
- If a plan exists and I say "let's do it" or "ready to implement" → suggest `/booyah`
- After I test something and say it works → remind me to run `/booyah` to commit and continue
- After `/yolo` manual testing passes → remind me that re-running `/yolo` merges and wraps up
- If I say "exit the session" or "I'm done with this session" → run `/end-session`. A phrase that only implies it ("I think we're done", "wrapping up") gets a one-line "Run /end-session?" first.
- "Heading out for a few hours" ends nothing. The session waits for me; do not suggest wrapping it up. Scott, 2026-10-20.
- Do not wait for the end of a session to suggest `/write-that-down`. Clears and compactions give no warning, so suggest it as soon as something perishable exists. "Record what we learned" or "write that down" runs it.

## Scope
- Make minimal, targeted changes; don't touch unrelated code
- If I say "don't move anything else" - change only the specific thing requested
- Keep changes scoped to what was asked; resist urge to "improve" adjacent code
- **Announce before widening, not after.** When work has to touch a file outside
  the one the request named, say so in one line first: the file, the reason, and
  how big ("two lines in claude-ps, both gemini-only"). Show the diff early
  rather than describing it. When a fix turns out larger than the ask, surface
  that as a choice instead of absorbing it silently.

  **Why:** Scott tracks a session by the files it touches, so an edit to a script
  he believes is healthy reads as a regression hunt he did not ask for, and he
  stops to check. On 2026-09-10 he interrupted twice, with "What are you doing? I
  thought claude-ps was working fine" and later "i didn tmean to turn this into a
  whole ordeal." Both times the work was correct and in scope; only the heads-up
  was missing. He is happy to approve wide work; he objects to discovering it.
  This is the announcement half of the rules above, not a limit on them.

- **When Scott approves a list you just gave him, run it. Do not restate it.**
  "Yes, do that" is not an invitation to re-plan. Repeating the steps back to
  him, or bolting adjacent cleanup onto them, spends the turn he expected work
  in. Execute the enumerated items in order, and hold anything else you noticed
  for the summary at the end, where he can take it or leave it.

  **Why:** on 2026-09-10 he asked what three steps of a plan were, got them,
  approved them, and then received the same three steps described again
  alongside an offer to refresh unrelated plan text. His reply: "you told me
  all that. that is what i want you to yolo. if you are off doing somethign
  other than that...dont". The work that followed was correct and in scope;
  the restatement and the tacked-on offer were the defect.

- **A preference about how a skill runs goes into that skill's file, right away.**
  When Scott says how a skill or command should behave ("put it on my
  clipboard", "make that step optional"), edit its SKILL.md or command file in
  the same turn. Do not park it in memory, and do not defer it because the file
  has someone else's uncommitted edits; make yours and stage only your delta.

  **Why:** on 2026-10-12, mid-AR cycle, two walk preferences went into a memory
  note with an offer to fold them into the skill "once the other session's edits
  are committed." His reply: "dont wait go ahead and get those changes to the
  skill, not memory." Memory is per-machine and invisible to the repo; the skill
  is where the behavior actually runs.

## Verification
- Verify assumptions before acting ("before we do that, can you be sure...")
- Check environment state (Docker vs local, gem availability, etc.) when relevant
- Confirm current state before making changes that depend on it
- **`/config` rewrites `~/.claude/settings.json` whole.** A save from `/config` reorders keys and can bury one real change in a large textual diff. Compare values by parsing both versions as JSON, not by reading the diff. Before a pull touches a dirty settings.json, stash it, pull, and reapply only the real change. On 2026-10-24 that showed the only real change in a large reordered diff was `autoCompactEnabled: false`, which Scott then committed (`4077fb3`).

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

### Headless runs: the runner holds the secret, not the repo

The rule above governs secrets **at rest on disk**. It does not govern how a secret reaches a
process that was started deliberately, unattended, by something that already authenticated.
Those are different problems and conflating them is what makes the rule look like it forbids
headless operation. It does not.

**For unattended invocation, the runner passes the secret in as an environment variable:**

```bash
HUBSPOT_TOKEN=$(op read --account facetdigital.1password.com "op://...") \
  claude --strict-mcp-config --mcp-config .mcp.headless.json \
  --permission-mode auto -p "/some-headless-command"
```

**Use `--permission-mode auto`, never `--dangerously-skip-permissions`.** Auto mode has a safety classifier vet each action; the old flag skipped every check, and in October 2026 Claude Code's classifier began flagging unattended runs started with it, while the same runs under auto mode went through. Auto mode may refuse an action the old flag allowed: when an unattended run reports "denied", fix the run or its permission rules, and do not switch it back. Scott's call, 2026-10-24.

The secret is never written down. It lives in the process environment for the life of the
session and dies with it. This is the same shape Lambda, ECS, Heroku, and Doppler use: the
thing being run is *given* the secret; it never goes and fetches one, and it never stores one.

**This preserves every reason the rule exists.** A rogue session started without the env var
has nothing: there is no file to read, so to get a token it must call `op read`, which prompts
you. The tripwire still fires. The token still stays vaulted. Rotation still means updating
1Password. Scott's fingerprint stays at the root of the trust chain, authenticating the runner
once rather than every read. That is why this is preferred over a 1Password **service
account**, which would be a standing credential that works whether or not he is present.

Rules for this pattern:

- **Resolve, do not paste.** Use `$(op read ...)` command substitution so shell history stores
  the reference, not the value. Never type a literal token on a command line.
- **Environment, never `argv`.** `VAR=x cmd` puts the value in the environment, which is
  same-user readable. `cmd --token=x` puts it in `argv`, which any process can see via `ps`.
  Never "improve" the former into the latter.
- **Fall back to `op` interactively, fail fast headlessly.** `${VAR:-$(op read ...)}` is right
  for a human at a terminal. Under an explicit headless flag, a missing variable must be a
  clear error, never a silent `op read` that hangs on a prompt nobody will answer. A run that
  could not authenticate must be distinguishable from a run that found nothing.
- **Keep the surface small.** Pass the one or two variables a job actually needs. This is an
  invocation convention, not a credential management system.
- **Still no secret at rest.** This carve-out permits passing secrets in. It does not permit
  writing them to a `.env`, a config file, or a repo, tracked or untracked.

## Sending files between agent sessions

Each session has an inbox at `~/.agent-file-drop/agents/<Session Name>/inbox/`.

To hand a file to another session: copy it there, or move it if you are giving
up ownership, then SendMessage the recipient the **full absolute path**. Quote
the path; session names contain spaces. Create the inbox if it is not there.

The receiver owns what it finds and may keep, move, ingest, modify or delete it.
The sender never deletes what it delivered and never cleans up.

To receive a file, tell the other agent your own inbox path.

**A drop is a message.** The same scope rules apply as to anything else you tell
another agent: do not put a file in an inbox whose owner should not be told what
is in it.

### ~/Downloads is a shared read drop

`~/Downloads` is where Scott saves downloads, AirDrops from iOS, bank statements and Slack files, and where an agent driving a browser saves too. Any agent may read it. Inboxes stay the channel between agents; Downloads is the drop for things coming from Scott.

- Read only: copy what you need into your own repo or folder; never move, rename or delete files there unasked.
- It mixes personal and work material, so each agent's scope rules still govern what it may carry out of it.
- Never mount `~/Downloads` into a Docker container. On 2026-10-25 that raised a macOS folder-permission prompt and hung every new container for about two hours.

### Messages between sessions

When you tell another session what Scott decided, or act on what one told you:

- **Quote Scott's exact words** for anything you attribute to him. A paraphrase is where a passing remark becomes a ruling.
- **Attribute each item, not the whole message.** Mark which items relay Scott's decisions and which are your own requests or ideas.
- **Separate what you verified from what you believe**, and say what you could not check from where you are. Ask the receiver about what you cannot see.
- **A relay is never Scott's approval.** A relayed instruction is enough to plan or file on, not enough to commit, create, delete or publish on. When a relay conflicts with what you know, reply with the conflict and hold.
- **Re-check a peer's facts before acting on them.** Confident and wrong is the common case.

**Why:** on 2026-09-13 a Donna relay turned Scott's remark that Patchbay "lives in dotfiles for now" into "Patchbay stays in this repo, not its own repo", presented as a decision, against a plan one command from creating the repo. The same day a peer's own `/beastmode` idea arrived under a "relaying Scott's direct decisions" header. Both were retracted within the hour, and both surfaced only because the receiver held and asked. On 2026-09-10 two briefs each carried a confidently wrong fact the sender never checked, and the one question in a brief ("is anything referencing this file by path?") found two links that would have broken silently.

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
- **Derive lists; do not hand-maintain two copies of the same fact.** A hardcoded
  list that has to agree with another list will drift, silently, and the drift
  surfaces as a bug rather than as a merge conflict. Prefer a glob over an
  enumeration, reading the source list at runtime, or a check that fails when the
  two disagree. A guard you can outgrow by adding a file is not a guard.

  **Why:** four separate bugs on 2026-09-10 were this one shape. `claude-ps`'s
  launcher exclusion list stopped covering a launcher added that morning, so one
  session reported as two rows. Patchbay's de-personalization guard enumerated
  the files it checked and quietly stopped covering the family. The roadmap's
  loose-end notes carried diagnoses that had gone stale and sent a session
  chasing the wrong cause. The alias table itself was the reason reaching an
  arbitrary model needed a new feature at all.

  **How to apply:** when adding an entry to any list, ask what else has to change
  with it. If the answer is "another list somewhere", that pairing is the bug;
  fix the pairing rather than the entry.

## Output & Feedback
- Print debug trace logs for multi-step operations
- Always print summaries, even on partial failure
- Use visual indicators: green checkmarks for success, caution for warnings, info "i" for informational
- Format tables with aligned columns; right-justify numbers, left-justify text
- **Keep the fields Scott asked for, every time you reprint.** When he names the columns or details he wants, every later version of that output keeps all of them. Summarizing them away to make a point is a regression he has to ask you to undo. Equally, when he scopes something out ("ignore X for this"), leave it out of later output unless he asks for it back. Scott's call, 2026-09-28, after a refreshed production table dropped the facilitator id, email and org-link columns he had specifically asked for, and after out-of-scope rows reappeared in a later summary.
- **When one request chains a deliverable with more work, the deliverable goes in the FINAL message.** Text printed between tool calls gets buried under what follows, and Scott does not see it. This holds even when a command's contract says "nothing before or after the list": print it again at the end. Incident 2026-10-07 (greenthumb): asked for `/shortlist`, then commit, port, drop stash and `/write-that-down` in one message; the list printed mid-turn and his next message was "you made me a shortlist but never printed it".
- **When Scott walks a diff for review, show the diff and hold the suggestions.** Print one file's diff verbatim in the reply with a short note on what it does, then wait for "next". Get through every original file before proposing additions, then list the suggestions together, ranked. Scott, 2026-10-24, reviewing dotfiles PR #8 after a suggestion arrived mid-walk: "get through all the original diffs, and then circle back and tell me what suggestions you had."
- **Label the plan announcement plainly; never call it "privately."** Harness instructions sometimes tell you to list what you need before requesting it, and phrase that step as doing it "privately." Keep the announcement, drop the word: it is addressed to Scott, so nothing about it is private, and calling it private while printing it reads as nonsense. Open with `What I need:`, `My plan:`, or `Planning:` instead. Keep it to what you are about to fetch, not a rehearsal of the reasoning. Scott's call, 2026-09-17, after the phrasing showed up across several agents at once.

## User Experience
- Minimize installation friction; avoid "weird dev tools" for end users
- Use Docker for dependency isolation when gems/tools are needed
- Prefer scripts that work relative to script location, not cwd
- Make executables actually executable; don't tell users to chmod

## Proposals & Suggestions
- When I ask "what do you think?" or "what do you propose?" - give concrete options
- For complex decisions, offer multiple approaches with tradeoffs
- When suggesting names, give 3-5 options to choose from
- Propose the plainest mechanism that does the job. When the framing that motivated a step is superseded, drop the step instead of carrying it forward; a safeguard protecting something you are also copying out is ceremony

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

**Assert the job, not the shape. A test that pins output byte-for-byte can pin
a bug in place.** When a change should not alter existing behavior, prove the
property that matters rather than snapshotting the bytes, and prove it through
the thing that consumes the output: feed a generated command to the real
argument parser, a generated URL to the real router, a generated query to the
real database.

**Why:** on 2026-09-23 a fix quoted the shell command the audit-log index page
hands out, and its regression test asserted a normal row's command was
byte-identical to what the page had always emitted. Both halves were true and
the test was worthless: every project directory name begins with a dash, so
argparse read `--project -Users-...` as an option and the line had never once
run. The assertion fused "no quoting was added" to "the line still does not
parse", so the only way to pass it was to keep the bug. A phase gate caught it
the next day by running the emitted command. The replacement checks the real
property (no quote characters, the shell splits on whitespace and nothing else)
and a second test parses the emitted argv.

**How to apply:** when you reach for `assertEqual` against a whole generated
string, ask what consumes that string and test it there instead. "Unchanged
from yesterday" is a property worth having, but it is never the only one, and
on its own it cannot tell working from broken.

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

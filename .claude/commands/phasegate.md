Audit a completed development phase at Fable tier: verify the merged work delivered the phase plans' promises, run the security-surface triage, and produce a verdict plus a fix list. Audit only; never fixes code.

Arguments: $ARGUMENTS (optional - phase name; otherwise inferred from the roadmap's current PHASE GATE marker)

## What the Phase Gate Is

The phase gate is Tier 3 of the verification model: deterministic tests decide everything decidable (Tier 1), the per-PR review loop catches code-level issues (Tier 2), and the gate judges what neither can: did the phase actually deliver what its plans promised, does the result still match the specs and architecture it cited, and did anything drift while technically passing the tests?

It runs once per phase, after the phase's features are merged, and its findings seed the next phase's planning. It is intended to run at Fable tier: either directly in a Fable session, or spawned by /beastmode, /yolo wrap-up, or /booyah as a fresh-context subagent with `model: "fable"`.

**Model check:** if you are executing this command and you are not a Fable-tier model, tell the user and ask whether to proceed anyway or defer to a Fable session. Do not silently run a degraded gate.

**Prime directive: audit, do not fix.** The gate reads, verifies, and reports. It never edits product code, tests, or plans. The only files it writes are its report and the roadmap gate-item checkbox.

## Step 1: Identify the Phase and Gather Inputs

1. Determine the phase: from $ARGUMENTS, or from the roadmap's current `PHASE GATE: <phase name>` item (the marker convention: phases in `docs/plans/development-roadmap.md` group their feature items and end with an item titled `PHASE GATE: <phase name>`).
2. Collect the phase's plan files from `docs/plans/` (the plans for the roadmap items in this phase).
3. Collect the project's spec documents the plans cite: PRD, architecture doc, numbered `docs/` suite, conformance scenarios, as applicable.
4. Establish the diff range: merged work on main from the phase's first feature merge through HEAD. Practical approach: `git log --merges --oneline` plus the roadmap's Completed entries to find the phase's merge commits, then review `git diff <before-phase>..HEAD` and the individual feature diffs.

## Step 2: Verify the Tests Tell the Truth

Run the project's full verification (`./run check`, or the repo's documented test + conformance commands). The gate does not proceed on a red suite: a red suite is automatically a FAIL verdict with "suite red" as the first finding.

Then look for the ways a green suite can lie:
- skipped/pending tests added during the phase without a tracking reason
- tests weakened or deleted to get past the review loop
- new behavior with no test at any tier (unit or conformance/e2e)
- coverage that dropped materially versus phase start

## Step 3: Walk the Citations

For each plan step's **Satisfies:** citation (PRD section, architecture decision number, conformance scenario ID, roadmap item):

1. Confirm the merged code actually satisfies the cited requirement, by reading the relevant code and tests, not by trusting the checkbox.
2. Record each as: satisfied | partially satisfied (explain) | not satisfied (explain) | citation was wrong/vacuous.

Steps without citations (older plans) get a best-effort mapping to the phase's stated goals.

## Step 4: Promise Audit (Drift Hunt)

Compare the phase's exit criteria and each plan's Summary/Requirements against reality:

- promised deliverables that quietly shrank ("supports X" that only handles the happy path)
- architectural drift: does the implementation still match the architecture doc's decisions, boundaries, and layering, or did expedient shortcuts blur them?
- scope leakage: unplanned changes that rode along and deserve scrutiny
- TODO/FIXME/HACK markers introduced during the phase
- documentation rot: README, CLAUDE.md, run script, and spec docs still accurate after the phase's changes

## Step 5: Security-Surface Triage

Always run the triage; run the full review only when it hits.

**Triage:** did the phase touch any of: authn/authz; permission or privilege modes; trust boundaries or prompt/contract composition; tenant or data isolation; secret or credential handling; attachment/file handling and file permissions; subprocess or argv construction; parsing of untrusted content (user input, network data, files from outside)?

- **No:** record "Security triage: no security surface touched" with one line of justification.
- **Yes:** full security review of the touched areas with an adversarial mindset: injection (prompt, SQL, shell), privilege escalation, path traversal, TOCTOU, data leakage across tenants or into logs/transcripts, unsafe defaults. Cite file:line for every finding. Projects may define their security surface list in their architecture doc; use it when present.

## Step 6: Write the Report

Write `docs/assessments/phasegate-<phase-slug>.md`:

```markdown
# Phase Gate: <Phase Name>

Date: <date>
Auditor: phasegate (<model>)
Diff range: <before>..<HEAD sha>
Verdict: PASS | PASS_WITH_FINDINGS | FAIL

## Summary
<3-6 sentences: what the phase promised, what it delivered, the verdict rationale>

## Test truthfulness
<suite results, and any of the green-suite lies from Step 2>

## Citation walk
| Plan step | Satisfies | Status | Notes |
|---|---|---|---|

## Drift findings
- **Severity** (critical|high|medium|low|nit) | location | issue | suggested fix

## Security
<triage result, and full review findings if triage hit>

## Fix list (seeds the next planning session)
1. <ordered, most severe first; each concrete enough to become a plan step>
```

Verdict rules: FAIL = red suite, any critical finding, or a core promise not delivered. PASS_WITH_FINDINGS = delivered, but medium/high findings exist. PASS = clean or nits/lows only.

Commit the report on main with message `Phase gate: <phase name> - <verdict>` (push if the repo has a remote and that is the norm there). On PASS or PASS_WITH_FINDINGS with nothing above low severity, also mark the roadmap's PHASE GATE item complete and include it in the same commit.

## Step 7: Hand Off

- **PASS:** announce the verdict; the next phase may start.
- **Findings (medium+):** present the fix list and recommend a `/gameplan` session to plan the fixes. Recommend not starting the next phase's features until criticals and highs are addressed. The gate itself fixes nothing.
- If invoked as a subagent, the final message is the verdict, the report path, and the fix list (that is what the caller consumes).

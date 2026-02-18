---
description: Guide through creating a proposal or SOW using the Corleone workflow
---

Guide the user through creating a proposal or SOW using Facet Digital's Corleone workflow.

## Step 1: Read the Skill

Read the Corleone skill definition at `~/.claude/skills/corleone/SKILL.md` to understand the full workflow.

Also read these reference files as needed during the workflow:
- `~/.claude/skills/corleone/references/intake-questions.md`
- `~/.claude/skills/corleone/references/proposal-types.md`
- `~/.claude/skills/corleone/references/estimation-notes.md`
- `~/.claude/skills/corleone/references/proposal-structure.md`
- `~/.claude/skills/corleone/references/writing-style.md`

## Step 2: Check Project Context

Look at the current working directory:

**If empty or no discovery/proposal folders:**
- Create `discovery/` and `proposal/` subdirectories
- Say: "I've set up the project structure. Let's get started on your proposal."
- Proceed to intake

**If discovery/ has files:**
- List what you find
- Ask if user wants you to analyze them first

**If proposal/ has drafts:**
- Summarize existing state
- Ask if user wants to continue or start fresh

**If in home directory or non-project location:**
- Warn the user and suggest creating a project folder first

## Step 3: Run the Workflow

Follow the workflow defined in SKILL.md:

1. **Intake** — Gather client, scope, timeline, budget info conversationally
2. **Ingest Materials** — Read and analyze any discovery documents
3. **Determine Type** — Identify proposal type (A-E) from proposal-types.md
4. **Estimate** — Apply phase templates and pricing from estimation-notes.md
5. **Generate Proposal** — Create draft following proposal-structure.md and writing-style.md
6. **Save Output** — Write the proposal to `proposal/draft-v1.md`

## Arguments

If the user provided context after `/proposal`, use it:
- `/proposal` — Start fresh
- `/proposal Website redesign for ACME` — Use as initial project context

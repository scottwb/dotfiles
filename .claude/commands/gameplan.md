Create a detailed, TDD-shaped, citation-tagged implementation plan for a feature or task (formerly /plan).

Arguments: $ARGUMENTS (optional - feature name)

## Step 1: Understand the Feature

**If no feature name was provided in arguments:**
Ask the user: "What feature or task would you like to plan?"

Once you have the feature name:
1. Restate your understanding of what the feature is
2. Ask if you've understood correctly

## Step 2: Research and Explore

1. Search the codebase to understand:
   - Existing patterns this feature should follow
   - Files that will likely be affected
   - Similar implementations to use as reference

2. Read `docs/plans/development-roadmap.md` to understand the current roadmap

3. Read the project's spec documents if they exist (PRD, architecture doc, numbered docs/ suite). Plan steps will cite them (see below), so know what there is to cite.

4. Check if a plan already exists in `docs/plans/` for this feature:
   - If it exists, tell the user and ask if they want to refine it or start fresh

## Step 3: Ask Clarifying Questions

Ask questions to clarify:
- Specific requirements and constraints
- Edge cases to consider
- Integration points with existing code
- Any preferences on implementation approach

Don't assume - ask until you understand.

## Step 4: Write the Plan Document

Create a plan at `docs/plans/<feature-name>.md` with this structure:

```markdown
# Plan: <Feature Name>

## Execution Instructions

When executing this plan:

1. **Work step-by-step** - Complete each step fully before moving to the next
2. **Test-first within each step** - Write the failing test/scenario before the implementation, then make it pass
3. **Test after each step** - Run the test commands listed to verify the change works
4. **Commit after each step** - Use the provided commit message for each step
5. **Update documentation continuously** - After ANY change that affects them, update:
   - `README.md` - User-facing documentation
   - `CLAUDE.md` - Developer/AI guidelines
   - `run` script usage comments
   - `docs/plans/<feature-name>.md` - Mark progress, update status
   - `docs/plans/development-roadmap.md` - Mark progress, update status
6. **Mark completion** - When all steps are done, move this item from "Next Immediate Step" to "Completed" in the roadmap

---

## Summary

<Brief description of what this feature does>

## Requirements

- <Bullet list of requirements>

## Implementation Steps

### Step 1: <Step Title>

- [ ] Write the failing test first: <the conformance/e2e scenario or unit test that defines "done" for this step, expected to FAIL before the implementation>
- [ ] Implement: <specific change 1>
- [ ] Implement: <specific change 2>
- [ ] Verify green: run the test commands below and confirm the new test passes

**Satisfies:** <what this step fulfills: PRD section, architecture decision number (e.g. D7), conformance scenario ID, or roadmap item>

**File(s):** `path/to/file`

**Test:**
```bash
<commands to test this step>
```

**Commit message:** `<descriptive commit message>`

---

### Step 2: <Next Step Title>
...

## Files Modified (Summary)

| File | Steps |
|------|-------|
| `file1` | 1, 3 |
| `file2` | 2 |
```

**Key principles for steps:**
- Each step is the **smallest change that is still working, testable, and functional**
- Each step can be **committed independently**
- **Test-first**: every step that changes behavior starts with a failing test (a conformance/e2e scenario for contract-level behavior, a unit test for internals). Steps with no runtime behavior (pure docs, scaffolding) say "test-first: n/a" explicitly instead of silently skipping it.
- **Traceability**: every step carries a **Satisfies:** line citing the requirement, spec section, decision number, or scenario it fulfills. If you cannot name what a step satisfies, question whether the step belongs in the plan.
- Each step includes **test commands** to verify it works
- Each step includes a **commit message**
- **Sub-items use checkboxes** (`- [ ]`) so `/booyah` can track progress

## Step 5: Update the Roadmap

Add the new plan to `docs/plans/development-roadmap.md`:
1. Move current "Next Immediate Step" to "Upcoming" section
2. Add this plan as the new "Next Immediate Step" with link to plan file
3. Set status to "Planning"

## Step 6: Iterate with User

Show the user the plan and ask:
> Does this plan look good? Let me know if you'd like to refine any steps or add more detail.

Keep iterating until the user says the plan is good.

## Step 7: Commit the Plan

When the user approves:
1. Update the roadmap status to "Ready to implement"
2. Commit both files with message: `Add plan: <feature-name>`
3. Tell the user: "Plan committed! To start implementing, run `/booyah <feature-name>` in a new session."

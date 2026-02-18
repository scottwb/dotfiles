Display the development roadmap and help pick what to work on next.

## Step 1: Find or Create the Roadmap

Look for `docs/plans/development-roadmap.md` or similar roadmap documents.

**If NO roadmap exists:**

1. Tell the user: "No roadmap found. Would you like to create one?"

2. If yes, ask: "What items should be on your roadmap? Describe one or more features or tasks you're planning to work on."

3. Create `docs/plans/development-roadmap.md` with this structure:
   ```markdown
   # Development Plan

   ## Next Immediate Step

   ### <First item user mentioned>

   **Goal:** <Brief description>

   **Status:** Needs planning

   ---

   ## Upcoming

   ### <Second item if provided>
   **Goal:** <Brief description>

   ### <Third item if provided>
   ...

   ---

   ## Completed

   (Nothing yet)
   ```

4. Create the `docs/plans/` directory if it doesn't exist

5. Show the created roadmap and ask if they want to start planning the first item

**If roadmap EXISTS, proceed to Step 2.**

## Step 2: Display the Roadmap

Read the roadmap and display a summary:

**Next Immediate Step:**
- Name and brief description
- Status (Planning / Ready to implement / In progress)
- [Plan Ready] or [Needs Planning] based on whether plan file exists

**Upcoming:**
- List each upcoming item with [Plan Ready] or [Needs Planning] indicator

**Recently Completed:** (if any)
- List recent completions

## Step 3: Check for Existing Plans

For each roadmap item, check `docs/plans/` for a matching plan file:
- Look for files that match the item name or are linked in the roadmap
- Mark as "[Plan Ready]" if found
- Mark as "[Needs Planning]" if not found

## Step 4: Prompt User Action

Ask the user:

> Which would you like to do?
> 1. **Start implementing** the "Next Immediate Step" (if plan ready)
> 2. **Create a plan** for an item that needs planning
> 3. **Add a new item** to the roadmap
> 4. **Just looking** - no action needed

## Step 5: Route to Appropriate Action

**If user picks an item with an existing plan:**
- Tell them: "This item has a plan at `docs/plans/<name>.md`"
- Ask: "Ready to start implementing? I'll use the /booyah workflow."
- If yes, begin the /booyah workflow (read the plan, work through steps)

**If user picks an item without a plan:**
- Tell them: "This item needs a plan first."
- Ask: "Ready to create the plan? I'll use the /plan workflow."
- If yes, begin the /plan workflow

**If user wants to add a new item:**
- Ask what the new item is and a brief description
- Add it to the "Upcoming" section of the roadmap
- Ask if they want to create a plan for it now

**If user is just looking:**
- Say "No problem! Run `/roadmap` again when you're ready to work on something."

Run a lightning round: surface every open question you need Scott to answer directly, as a numbered list he can clear in one pass.

Arguments: $ARGUMENTS (optional - a scope hint, e.g. "just this repo", "PR stuff only")

## Step 1: Gather

Draw on these sources, in this order of weight:

1. **Your own tracking of open questions.** The decisions you have been holding
   for Scott: things you parked, assumptions you made and want confirmed, forks
   in the work you cannot take without him. This is the primary source; the rest
   are for catching what you forgot.
2. **Session context.** Anything raised in this conversation and never resolved.
3. **Memory.** Open threads recorded in `~/.claude/projects/*/memory/`.
4. **This repository.** Roadmap, plans, TODOs, open PRs, and git history when a
   question hinges on what actually happened.

If $ARGUMENTS is present, narrow the round to that scope.

## Step 2: Ask

Print a numbered list, at most 20 items, highest-stakes first. Nothing before it
and nothing after it: no preamble, no summary, no "let me know if".

Rules for every question:

- **One sentence, TLDR style.** No context paragraph, no justification, no
  restating what led up to it. Scott asks for more context when he wants it.
- **Answerable in under five words.** A single word is the target. A question
  that cannot be answered that briefly is the wrong question: split it, or turn
  it into a multiple choice.
- **Multiple choice when the options are known.** Indent the choices under the
  question, school-quiz style.
- **Nothing you can answer yourself.** If reading the repo settles it, go read
  the repo. This round is only for what genuinely needs Scott.
- **Nothing already decided.** Check before re-asking something he has answered.

The shape:

```
1. Do you want to cancel the Nate meeting?
2. Which do you prefer for meeting Jason, morning or night?
3. Did you finish testing PR #123?
4. Which name for the new command?
   a. /office-hours
   b. /standup
   c. /lightning
```

Then stop and wait.

## Step 3: Handle the answers

Scott answers by number, tersely, and may leave numbers out.

- **A terse answer is a complete answer.** "Nah", "Night", "Nope" decide the
  question. Do not ask him to elaborate.
- **An answer may carry an instruction** ("Nope. Make it my priority today.").
  Take both the decision and the instruction.
- **"pass" or "skip" means not now, not never.** The question stays open and
  comes back in a later round. Never read it as a no, and never quietly drop it.
- **A number he did not answer is a pass.** Same treatment.

Then close the loop: record each decision where it belongs (memory, roadmap,
plan, PR, code comment), do the work an answer unblocks when it is small and
clearly authorized, and report one line per item saying what you did. Keep the
passed items in your own tracking so the next `/office-hours` opens with them.

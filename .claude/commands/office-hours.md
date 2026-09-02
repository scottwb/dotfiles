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
4. **The repo's own open-question tracking,** in whatever form it takes: a
   question queue, a TODO file, the roadmap, `docs/plans/`, a decision log, an
   issue tracker. This is where earlier rounds left their leftovers, so read it
   before assuming a question is new.
5. **The rest of the repository.** Open PRs, and git history when a question
   hinges on what actually happened.

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

## Step 4: Record it the repo's way

Where a decision goes is the **repo's** call, not this command's. Every repo
tracks decisions, open questions and TODOs differently, so find the convention
before writing anything: a question queue, a TODO file, the roadmap,
`docs/plans/`, a decision log or ADR directory, an issue tracker, CLAUDE.md.
Then use it the way it is already used.

- **Do not invent** a format, a file, or a directory because none was obvious.
  Look harder first; git history usually shows where past decisions landed.
- **If the repo genuinely has no convention,** hold the decisions in your own
  tracking and put "where should decisions get recorded here?" in the next
  round. Do not settle that one for him by creating a file.

Then do the work an answer unblocks when it is small and clearly authorized, and
report one line per item saying what you did.

## Step 5: Follow-ups go in the queue, not in his face

An answer that is unsatisfying, ambiguous, or that opens three new questions is
a normal outcome, not a reason to keep talking. Twenty answers can easily
produce fifteen new questions. **Do not ask any of them now.**

- **Enqueue them** exactly the way the repo tracks any other open question, per
  Step 4. Passed and unanswered items go back in the same way.
- **The repo decides the order.** Its queue is not FIFO unless the repo says it
  is. Priority, phase, blocking relationships, whatever it already uses. A
  follow-up to a question Scott just answered has no special claim on being
  next.
- **They surface later:** at the next `/office-hours`, or opportunistically,
  when Scott is already working in that part of the codebase and the question
  costs him nothing to answer in passing.
- **The one exception is a hard block:** work has stopped right now, there is
  nothing else to get on with, and only he has the answer. Say so plainly and
  briefly. Ambiguity you can proceed past under a stated assumption is not a
  hard block: state the assumption, enqueue the question, keep going.

Run a Q&A lightning round: surface every open question you need Scott to answer directly, then ask them one at a time so each answer can reshape what comes next.

Arguments: $ARGUMENTS (optional - a scope hint, e.g. "just this repo", "PR stuff
only", and/or `--list` to print the whole list at once instead of asking one at
a time)

## Step 1: Gather and rank

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

If $ARGUMENTS carries a scope hint, narrow the round to that scope.

Build the full ranked list before asking anything: at most 20 items,
highest-stakes first. This is your working list, not something you print. It is
expected to change as answers come in (Step 3), which is exactly why it is built
up front rather than a question at a time.

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

## Step 2: Ask the first one

State the protocol once, in a single line:

> One at a time. Say stop or done and the rest are skipped; say explain and we
> dig in until either of us says next question.

Then print question 1, numbered, with its choices if it has them. Nothing else:
no preamble, no count of what is coming, no summary, no "let me know if".

Then stop and wait.

## Step 3: Iterate

On each answer, in this order:

1. **Record it now,** per Step 4. Not at the end of the round. An hour of
   answers carried in context is an hour of answers that dies with the session.
2. **Do the work it unblocks,** when that work is small and clearly authorized.
3. **Re-evaluate the remaining list.** An answer can remove a question, reorder
   what is left, split one into two, or add a new one. A question his last
   answer just settled must not still get asked.
4. **Ask the next question alone,** keeping its original number so he can refer
   back to one by number. Numbers therefore skip and run out of order as the
   list changes. That is correct; do not renumber to tidy it.

What his answers mean:

- **A terse answer is a complete answer.** "Nah", "Night", "Nope" decide the
  question. Do not ask him to elaborate.
- **An answer may carry an instruction** ("Nope. Make it my priority today.").
  Take both the decision and the instruction.
- **"skip" or "pass" means "not now; ask later", not "never ask again".** The
  question stays open and comes back in a later round. Never read it as a no,
  and never quietly drop it.
- **"stop" or "done" ends the round.** Every question you had not yet asked is a
  skip and goes back in the queue exactly like one. Do not ask whether he is
  sure, and do not slip in one last question on the way out.
- **"explain" opens the question up.** Give a short paragraph of context, or
  discuss it properly. The round resumes when either of you says next question.
  This is not the one-sentence rule failing; it is the rule working, with the
  context available on demand instead of spent up front on every question.

**When a question turns out not to be a short-answer question,** say so rather
than forcing a word out of him. Seed the framing in a few sentences, record it
as a thinking item with a time or a venue attached (a conversation he needs to
have, a walk, a session with another agent), and move on. The round does not
wait on it.

## Step 4: Record it the repo's way

**Record the answer where it needs to be, so the question stops being asked.**
That is the whole test. A decision recorded somewhere tidy that the next
session will not read has not been recorded; a decision written into the thing
it governs has. Do this per answer as it arrives, per Step 3, never as a batch
at the end.

Where that is depends on what was decided, and it is the **repo's** call, not
this command's. Every repo tracks decisions, open questions and TODOs
differently, so find the convention before writing anything: a question queue,
a TODO file, the roadmap, `docs/plans/`, a decision log or ADR directory, an
issue tracker, CLAUDE.md. Then use it the way it is already used.

In a repo running this suite, `/roadmap` and `/gameplan` set the shape:

- **The roadmap** for what changes an item's priority, status, or existence.
- **A plan doc** for what binds a plan's design or execution, recorded the way
  that plan already records decisions.
- **Both** when the answer does both, which is common: the plan carries the
  decision and its reasoning, the roadmap carries the consequence.
- **Neither** when the answer belongs in the thing itself. A settled naming
  question goes in the code, a settled behavior question in the spec or the
  README, a standing instruction in CLAUDE.md or memory. Do not file a note
  about a decision in a plan when the decision *is* the file you could edit.

- **Do not invent** a format, a file, or a directory because none was obvious.
  Look harder first; git history usually shows where past decisions landed.
- **If the repo genuinely has no convention,** hold the decisions in your own
  tracking and put "where should decisions get recorded here?" in the next
  round. Do not settle that one for him by creating a file.
- **Relaying an answer to another agent counts as recording it.** When the
  decision governs another staff session's work, send it there; a decision that
  reaches the repo but not the agent acting on it has not landed.

Then do the work an answer unblocks when it is small and clearly authorized.

**Close the round with a short recap,** whether it ended by running out of
questions or by a stop. Three groups, settled, skipped, and reframed as thinking
items, with one line each saying where the answer landed.

## Step 5: Follow-ups go in the queue, not in his face

An answer that is unsatisfying, ambiguous, or that opens three new questions is
a normal outcome, not a reason to keep talking. Twenty answers can easily
produce fifteen new questions. **Do not ask any of them now**, and note that
this holds even though the round is now conversational: adding a question the
list needed is Step 3's job, chasing a tangent it did not is not.

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

## `--list`: the whole list at once

With `--list`, print the ranked list from Step 1 as a numbered list instead of
asking one at a time. Nothing before it and nothing after it. Then stop and
wait; he answers by number, tersely, and may leave numbers out, and a number he
did not answer is a skip.

Steps 4 and 5 apply unchanged. Use it when he wants to scan the whole surface
before deciding what to engage with. One at a time is the default.

## Why one at a time

The list-at-once shape was the original, and it has one real flaw: it fixes the
questions before the first answer exists. Tested live over the night of
2026-09-05 into 2026-09-06, across 20 questions, three answers changed what
should come next. One folded a later question into its predecessor, one turned a
date question into a conversation Scott needed to have with another agent, and
one added a decision that was not on the list at all. A printed list cannot do
any of that, so the round either asks something already settled or quietly
drops it.

That round ran about an hour including the recording work, and ended 13 settled,
5 skipped, 2 reframed as thinking items. The reframed pair is the other reason
for the shape: some questions are not short-answer questions, and finding that
out costs a sentence in conversation and a wasted round on a list.

---
name: audit-agent-conversation
description: >
  Render a Claude Code session transcript into a single self-contained HTML audit log page,
  showing one agent-to-agent conversation end to end: the opening prompt, the work log, the
  reply, derived side effects, and a real cost breakdown. Use this skill when the user wants
  to audit, review, share, or produce a record of what one agent asked another and what it
  did, or mentions "audit log", "conversation audit", "what did Donna send Greenthumb", or
  wants a shareable page for a session. Pages are written to ~/.ai-staff-audit-log/.
allowed-tools: Bash, Read
---

# Agent Conversation Audit Log

**Version: 1.0.0 (2026-08-15)**

Turns a raw Claude Code JSONL transcript into one self-contained HTML page that a
person can actually read: the prompt that started it, everything the agent did,
the reply that came back, and what it cost at public list rates.

The page opens as a clean dialog. The work log is hidden behind one button, so
the default view is the conversation rather than a wall of tool output.

## Running it

```sh
bin/audit-agent-conversation [SESSION] [options]
```

Once the dotfiles are linked into `$HOME`, it is just
`audit-agent-conversation` on `PATH`.

`--help` prints full usage, worked examples, what v1 refuses, and every exit
code. A bad flag prints the same thing rather than a bare usage line, so an
agent that guesses wrong gets told how to guess right.

| Invocation | What it does |
|---|---|
| `audit-agent-conversation` | Latest renderable session for the current directory's project |
| `audit-agent-conversation --project greenthumb` | Latest renderable session in that project |
| `audit-agent-conversation 9608087e --project greenthumb` | That session, by UUID prefix |
| `audit-agent-conversation --project greenthumb --date 2026-08-13` | That day's session |
| `audit-agent-conversation --all --week` | **Every** renderable session, every project, past 7 days |
| `audit-agent-conversation --all --project greenthumb` | Every renderable session in one project |
| `audit-agent-conversation path/to/session.jsonl` | An explicit transcript |

**`--all` is the sweep.** With `--project` it covers that project; with neither
a project nor a session it covers *every* project, because the question a bare
`--all` asks is what the agents have been doing, not what this directory has
been doing. It ends with a tally. The whole corpus is 345 sessions across 42
projects and sweeps in under three seconds, and re-running is cheap because
pages already present are a no-op.

**Time windows: `--date`, `--today`, `--week`.** Three fixed spans rather than a
date-range grammar, because the questions worth asking are "the last one",
"today", and "this week". They are mutually exclusive, and contradict `--latest`.

Options:

| Flag | Effect |
|---|---|
| `--from NAME` | Who initiated the exchange. Nothing in a transcript records this, so it is a flag with a config fallback. |
| `--to NAME` | Which agent did the work. Defaults to `agent-name` from the transcript, then the project map. |
| `-o PATH` | Write to this exact path instead of the default directory |
| `--output-dir DIR` | Write into a different directory |
| `--stdout` | Write the HTML to stdout and create no file |
| `--force` | Allow overwriting an existing output file |
| `--quiet` | Suppress the summary line |

`--latest` means the latest session that can **actually be rendered**. Taken
literally it was near-useless in any project you also work in by hand, because
the newest transcript there is usually an interactive multi-turn session, so the
common result was a refusal for a session you never picked.

The walk back is announced, one line per session passed over, so nothing is
silently decided not to count:

```
ℹ️  SKIPPED 7e4fd501 | 2026-08-16 00:07 | interactive, 3 turns | Greenthumb
wrote ~/.ai-staff-audit-log/20260816-0557-donna-to-greenthumb-exec-brief-full.html
  from session 01ee0390-3bac-4bfd-8d56-c1b9b638c7a0
```

The fields are session id, when it started, why it was passed over, and its
title. Oversized transcripts are skipped on file size alone, without parsing
them, so walking past a 44 MB session costs nothing.

**Naming a session opts out of the walk.** An explicit id or `--date` means that
session, so an unsupported one is refused rather than quietly swapped for a
neighbour. `--latest` and `--date` contradict each other and are rejected as a
pair. When a day holds several sessions, the latest is rendered and a note names
the ones passed over.

Output is an aligned table, 120 characters wide, one row per session:

```
   STATUS  | SESSION  | WHEN        | DETAIL                       | SENDER | RECEIVER   | SUBJECT
------------------------------------------------------------------------------------------------
i  SKIPPED | 7e4fd501 | 08-16 00:07 | Human (3 turns)              | scott  | greenthumb | Greenthumb
#  EXISTS  | 01ee0390 | 08-16 05:57 | use --force to replace       | donna  | greenthumb | /exec-brief full
*  WROTE   | e9de9126 | 08-13 09:17 | clarify-push-aut... (104 KB) | caller | donna      | Clarify push author...
```

`WROTE` produced a page, `EXISTS` found one already there, `SKIPPED` passed a
session over. The receiver is the agent's own `agent-name` when the transcript
carries one, then a configured name from `participants.json`, then the
repository name taken from the session's `cwd`. Not from the project directory
name: that is the working directory with every separator turned into a dash, and
repository names contain dashes too, so splitting it is guesswork that collapsed
`facet-admin-workspace` and `facet-delivery-workspace` into one name. On a skip, `DETAIL` says why, and says who drove it:
`Human (12 turns)` is the answer you usually want, not a bare turn count. On a
write, it names the page by its slug and size. The slug is the filename minus
the `<when>-<sender>-to-<receiver>-` part, since all of that is already in the
columns beside it, and it globs: `ls ~/.ai-staff-audit-log/*clarify-push*`. Anything too long for its
column is truncated with an ellipsis. Column widths are constants that add up,
so rebalancing them is a one-line change. `--no-header` omits the header and
rule.

Rows go to stderr. stdout belongs to `--stdout`, which emits the page itself.

An output that already exists is a **skip, not an error**: the run reports it and
exits 0, so re-running over a batch of sessions is a cheap no-op rather than a
failure. The existing page is never touched without `--force`.

Exit codes: `0` success, or nothing to do; `2` could not resolve a session (or
contradictory flags); `3` unsupported session; `4` render failure; `5` could not
create the output directory; `7` destination is inside the transcript store.

From Donna, or any session with no repo context, `--project` is the usual way in.

## Where pages go

`~/.ai-staff-audit-log/`, created on first use.

It is deliberately **not** a git repository and **not** inside one. Nothing in
the dotfiles repo references its contents, only its path. Files are named:

```
YYYYMMDD-HHMM-<from>-to-<to>-<slug>.html
20260813-0557-donna-to-greenthumb-exec-brief-full.html
```

So plain `ls` gives chronological order, and `ls *-donna-to-*` filters by who
started the conversation. An existing file is never overwritten without
`--force`, and nothing is ever deleted from the directory.

## What v1 does not do, and says so

Three cases are deferred. When one is detected the tool **refuses**: it names
every condition it found with its magnitude, exits non-zero, and writes no file.

- **Multi-turn sessions.** v1 renders one caller turn. Sessions with a real
  back-and-forth need repeating turn groups, which is queued follow-on work.
- **Image blocks.** Inlining base64 images would balloon the page.
- **Oversized transcripts**, over 8 MB. Embedding every tool result verbatim
  from a 44 MB transcript produces a page no browser opens comfortably.

A refusal is the deliberate v1 substitute for supporting these. A half-rendered
page that looks complete is worse than no page.

## What the page contains

- Masthead naming both participants, with the date and time in Pacific.
- Provenance: channel, repo and branch, session UUID, model, effort, CLI
  version, permission mode.
- Eight stat tiles: wall clock, tool calls, input tokens, output tokens,
  reasoning tokens, total cost, git commits, external API calls. **Every one is
  counted from the transcript.**
- A collapsed cost breakdown.
- One card per participant, then the work log, then the reply.
- A "side effects on the real world" box, derived the same way.

Every tool call and reasoning step is individually expandable, and markdown
tool results carry a **Raw / Preview** toggle. Both panes are rendered when the
page is built and shipped as sibling divs, so the toggle only flips visibility
and no markdown parser ships with the page.

## Things worth knowing

**Costs are hypothetical.** These sessions run on a Claude subscription, so
nothing was billed per token. The figure is what identical traffic would cost
through the public API at list rates. The page states this.

**Reasoning tokens are a subset of output tokens**, never added to the total.
The tiles are not meant to sum.

**Reasoning text is not recoverable.** Claude Code stores only the signed,
encrypted thinking block, so the page shows the token count and signature and
explains why there is no text. It never implies the content could be recovered.

**Transcripts are read-only, always.** They live in `~/.claude/projects/`, they
are the only copy, and they are gitignored. This tool never writes, moves, or
deletes one, and it refuses outright to write anywhere inside that directory:
`-o`, `--output-dir`, a `../` climb, and a symlink pointing in are all rejected
by resolved path, and `--force` does not override it. `--force` means "replace
my own output", never "disable the safety rail".

Output is written to a temporary file and renamed into place, so an interrupted
run cannot leave a half-written page where a good one used to be.

**Who initiated a session is not recorded anywhere in a transcript.** So the
tool works it out from the entrypoint, which is recorded: an interactive session
was a human, and a non-interactive one was not. Non-interactive sessions consult
the `senders` map in `participants.json`, and where that says nothing the page
reads `caller` rather than naming someone who was not there. Pass `--from` to
settle it explicitly.

**Nothing is paraphrased.** Tool commands and their output are verbatim. Only
the one-line labels are written by a human, and an unrecognized tool is labelled
with its own name rather than described with a guess.

## Maintenance

Rates go stale. They live in `scripts/auditlog/pricing.json`, keyed by model id,
with the date they were last checked. An unknown model is a loud error rather
than a silent zero.

Agent names live in `scripts/auditlog/participants.json`, mapping project
directory to agent. Add an entry there when a new agent joins the fleet.

## Tests

```sh
.claude/skills/audit-agent-conversation/run-tests
```

Standard library `unittest` on the stock `/usr/bin/python3`. No pytest, no
venv, no install step. The suite asserts exact golden token and cost figures for
a reference session, which is what catches the transcript format's nastiest
trap: Claude Code writes one record per content block and repeats the whole
message's usage on each, so summing per record overcounts by 2.5x. Usage is
deduplicated on `message.id`.

The tests read real transcripts and skip, rather than fail, when the corpus is
not present on the machine.

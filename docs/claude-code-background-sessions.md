# Claude Code background sessions

How Claude Code 2.1.x actually runs background work, established by reading the
process table, `~/.claude/sessions/*.json`, and the CLI binary on 2026-09-02.
This is the model `bin/claude-ps` is built against, and the reason it looks the
way it does.

None of this is public API. Treat it as observed behaviour with a date on it.

## The daemon

One daemon per uid, not per session:

```
/Users/scottwb/.local/bin/claude daemon run --origin transient \
  --spawned-by {"label":"claude","cwd":"/Users/scottwb","pid":22497}
```

It is spawned lazily by whichever session first needs one, and its state lives
in `/tmp/cc-daemon-<uid>/<instance>/` as `control.sock` plus `spare/`, `pty/`
and `rv/` subdirectories of unix sockets.

**The spawning session is an accident of timing.** In the raw process table
every background session on the machine descends from whoever happened to start
the daemon, which is why `claude-ps` cuts that edge and re-homes background
sessions by job instead. See "Ownership" below.

## The spare pool

The daemon pre-warms sessions so a background job does not pay process startup.
A warm spare is two processes:

```
claude bg-pty-host --bg-pty-host .../spare/<id>.pty.sock 200 50 -- ... --bg-spare ...
  └ claude bg-spare --bg-spare .../spare/<id>.claim.sock
```

An unclaimed spare has **no session file at all** and sits with its cwd in the
daemon's own `spare/` scratch directory. It has no repo, no context, no
identity. That is the point: it is a process that has paid its startup cost and
nothing else.

## Lifecycle

| stage | `sessions/<pid>.json` | `spare` | cwd | transcript |
|---|---|---|---|---|
| warm, unclaimed | absent entirely | - | daemon `spare/` dir | no |
| claiming | present | `true` | already the parent's | **no** |
| claimed | present | key gone | the parent's | yes |

The middle row is a real, observable window, and it is what broke `claude-ps`:
a session that is registered but has not yet written a transcript. Anything
walking `sessions/` must treat "no transcript yet" as normal rather than as an
error.

**The command line does not change at any point.** A claimed, working
background session still has `bg-spare` in its argv for life. Only the session
file distinguishes a warm spare from a session doing work, so never classify
these by `ps` output alone.

## What claiming does

The spare is handed the parent's working directory and **forks the parent's
transcript**:

```
claude --session-id 985d4757-... --fork-session \
  --resume ~/.claude/projects/-Users-scottwb-src-scottwb-kubera/5ee9cb71-....jsonl \
  --model opus --effort high --permission-mode auto
```

So a background session inherits the full context of the session that started
it. The scratch cwd belongs only to a spare that has not been assigned yet.

## Ownership

The process tree is the wrong answer for "whose job is this". The session file
pairing is the right one:

- the session that backgrounds a job records it as `parkedJobId`
- the background session records the same id as `jobId`

Observed pairs: interactive 7811 `parkedJobId 985d4757` owns background 13733
`jobId 985d4757`; interactive 22497 `parkedJobId 397fe531` owns background
55868 `jobId 397fe531`.

This link comes from file contents, not the process table, so it can in
principle be malformed or cyclic. `claude-ps` guards for that; anything else
walking it should too.

## Subagents are not processes

Subagents spawned by the Agent tool run **inside the parent's process**. They
never appear in the process table and never get a session file. A session
running subagents shows only its MCP servers and tool shells as children.

Do not go looking for a subagent process. There isn't one.

## How a session's title is stored

Three places, and they are not interchangeable. This matters when hunting for a
session by name, because the obvious search misses half of them.

- **`ai-title`** events in the transcript, field `aiTitle`. The one-line title
  Claude Code generates for itself.
- **`custom-title`** events in the transcript, field `customTitle`. What
  `/rename` writes. A session renamed by hand has **no** `aiTitle` matching its
  displayed name, so grepping for `aiTitle` alone will not find it.
- **`name`** in `~/.claude/sessions/<pid>.json`, alongside `nameSource`. The
  live name, and only present while the session is running.

So to find a dead session by the name you remember, grep the transcripts for
`customTitle` as well as `aiTitle`. Verified on 2026-09-02 by failing to find
"Dotfiles AI Audit" through `aiTitle` and then finding it as a `custom-title`.

Consumers here already reflect this. `auditlog/parse.py` (`title_for`) reads
both and prefers `ai-title` deliberately, because a hand-set title is often a
label that just repeats the receiver rather than describing the conversation.
`bin/claude-ps` takes the name from the session file and only falls back to the
transcript's `ai-title` when `nameSource` is `derived`, which is why a renamed
running session still displays correctly there.

## Not established

- Whether an unclaimed spare can return to the pool after being claimed. Two
  spares were observed vanishing entirely rather than being recycled, but that
  is one observation, not a rule.
- What determines pool size, or when the daemon decides to warm another spare.

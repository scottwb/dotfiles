# `.claude/`

Claude Code's configuration directory, symlinked from `~/.claude`. It hosts more
than one project, so this file is an index rather than a description of any one
of them.

| What | Where | Doc |
|---|---|---|
| **Servanda**, the workflow command kit | `commands/`, `COMMANDS.md` | [docs/servanda.md](docs/servanda.md) |
| **/office-hours**, a standalone lightning round for open questions | `commands/office-hours.md` | itself |
| Session settings and permissions | `settings.json` | inline `x-instructions` key |
| Global agent instructions | `CLAUDE.md` | itself |
| Skills | `skills/` | each skill's own `SKILL.md` |
| **Private companion**, docs and skills that name clients or internals | `private/` (symlink, excluded) | [scottwb/dotfiles-private](https://github.com/scottwb/dotfiles-private) |

The `private/` link comes from `dotfiles-private` and is excluded from this
repo, so it is present on Scott's machine and absent from the public tree. The
org chart of the agent constellation lives there, at
`~/.claude/private/docs/org-chart.md`, because it names client-facing repos and
what each agent can see.

Related but living elsewhere in this repo:

| What | Where | Doc |
|---|---|---|
| **Patchbay**, the harness/model/provider launchers | `bin/claude-run`, `bin/claude-*` | [docs/patchbay.md](../docs/patchbay.md) |
| Session listing, and how Claude Code runs background work | `bin/claude-ps`, `bin/agent` | [docs/claude-code-background-sessions.md](../docs/claude-code-background-sessions.md) |

## Conventions

- **Docs that ship with a thing live beside it.** A skill's doc goes in the
  skill's directory; Servanda's goes in `docs/` here. Docs *about building* the
  work (the roadmap, plans, gate assessments) live in the repo's top-level
  `docs/`, which is deliberately never symlinked into `$HOME`. The test is
  whether the document would travel with the thing if it were extracted.
- **Runtime state is gitignored,** not committed. See `.gitignore` here; it
  covers session history, caches, plugin state, and the security-guidance
  plugin's warning state, which records filenames from whatever repo a session
  ran in and therefore must never reach this public repo.
- **This file is public.** Keep secrets out of everything in this directory.
  Credentials are resolved at runtime through the 1Password CLI, never stored.

# `.claude/`

Claude Code's configuration directory, symlinked from `~/.claude`. It hosts more
than one project, so this file is an index rather than a description of any one
of them.

| What | Where | Doc |
|---|---|---|
| **Servanda**, the workflow command kit | `commands/`, `COMMANDS.md` | [docs/servanda.md](docs/servanda.md) |
| Session settings and permissions | `settings.json` | inline `x-instructions` key |
| Global agent instructions | `CLAUDE.md` | itself |
| Skills | `skills/` | each skill's own `SKILL.md` |

Related but living elsewhere in this repo:

| What | Where | Doc |
|---|---|---|
| **Patchbay**, the harness/model/provider launchers | `bin/claude-run`, `bin/claude-*` | [docs/patchbay.md](../docs/patchbay.md) |

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

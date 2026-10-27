# Agent Colour Mod — Build Prompt for Claude Code

Paste everything below the line into a Claude Code session (version 2.1.287 or later).

---

## Goal

I run a lot of Claude Code agents across many repos and I want the **Claude Desktop Code tab to be my command center**. I'm dropping tmux entirely. To make Desktop usable at scale, each session needs to be **easy to spot by colour**, and that colour should come from **a config file in that session's repo**.

Build a Claude Code **mod** called `agent-colors` that gives each session its own colour and label in the Desktop app, and in the terminal too if that's easy.

## Config compatibility: talk to the "dotfiles" agent first

My wrapper scripts are called **PatchBay**. They already launch Claude Code with extra prompt matter, args, models, and providers, and they have their own config file. Their conventions are mostly defined by my agent named **"dotfiles"**.

Before you design the config schema, contact the "dotfiles" agent and ask about PatchBay and its config file: where the file lives, its format, and its naming conventions. Then make the colour config fit that format, ideally as a section of the same PatchBay config file instead of a new file. Cross-reference PatchBay in the README and the schema. If you can't reach the "dotfiles" agent, stop and ask me rather than guessing.

## Background you must verify first (don't assume)

Before you write code, read these and summarize what you find:

1. Mods overview: https://code.claude.com/docs/en/plugins/mods/overview
2. Getting started guide: https://claude.dev/blog/getting-started-with-claude-code-mods/
3. Anthropic article: https://claude.com/resources/articles/claude-code-mods
4. Field guide covering panes, colour, and UI drawing: https://gist.github.com/ruvnet/a485e930b148185197fc53fd38b429ea
5. Example catalogue: https://github.com/karanb192/awesome-claude-code-mods

What I understand so far:

- A mod is a plugin with a hooks module that exports `register(on, options)`.
- Hooks are chained like middleware, `on(event, matcher?, async ($, e, next) => ...)`.
- Events include session start and end, tool calls, prompts, turns, slash commands, and `ui.render`, which fires for every piece of the interface as it's drawn.
- Mods run in a sandbox with no DOM and no Node. Everything goes through the `$` API (ui, session, state, store, fs, process, and more).
- Mods can target the terminal, the desktop app, or both.
- The usual layout is `plugin.json`, `hooks/hooks.json`, and `hooks/register.ts`, loaded with `claude --plugin-dir ./path` or through a local marketplace.

**Key open question. Answer it explicitly before building:** which Desktop UI surfaces can a mod restyle? Check each of these:

- the session transcript or pane background
- a band or header above the prompt
- the status line
- the **session list in the Desktop sidebar**, which is what I want most

Mods probably run inside each session, so the sidebar list may be out of reach. If it is, say so plainly and pick the strongest alternative that's visible at a glance.

## Requirements

1. **Per-repo config.** When a session starts, find the repo root from the session's cwd (walk up to the git root) and read a config file committed in the repo, for example `.claude/agent.json`. I already have bash wrappers that launch Claude Code with extra prompt matter and args, and I'm planning this same file to configure models and providers. So keep the colour settings in their own small section (for example `"ui": {"color": "#1e6b52", "label": "Billing API"}`) and ignore any other keys. Propose the schema to me before you lock it in.
2. **Fallback.** If the repo has no config, give it a stable colour by hashing the repo name, so it always looks the same.
3. **Desktop rendering.** Use the boldest effect that's actually supported, such as a coloured band above the prompt showing the label, a tinted pane, or a coloured status line. Text must stay readable, so check the contrast.
4. **Terminal rendering.** Do the same thing in the CLI if it costs little.
5. **Live reload.** If the config file changes, update the colour without restarting the session, if mods allow it.
6. **Toggle.** Add a slash command like `/agent-color` to show the current colour and config path, and allow a temporary override for the session.
7. **Safety.** No network access, no permission overrides, and no auto-approving tool calls. Read only the repo config file. List exactly what the mod can access.
8. **No tmux.** Don't depend on tmux at all.

## Build and test plan

1. Research the docs above and report what's possible, especially for the sidebar.
2. Scaffold the plugin in `~/mods/agent-colors/`, not in a session temp folder that can get cleaned up. Install it user-wide so it applies to every repo.
3. Build a minimal version first that tints one known session, and hot-reload it. Confirm the reload line lists every hook.
4. Add repo-root discovery, config parsing, and the hash fallback.
5. **Test in Claude Desktop:** create three scratch repos with different colours in their configs plus one repo with no config. Open a Desktop session in each and confirm every colour is correct and stable. Then edit one config and check the live update.
6. Test in the terminal.
7. Write a README covering install, the config schema, the Desktop surfaces that do and don't work, and how to disable the mod.
8. Give me a short report: what works, what doesn't, and what Anthropic would need to expose to colour the sidebar, so I can file a feature request if needed.

Work in small steps and show me evidence (screenshots or reload output) at each test. Don't claim something works in Desktop unless you've checked it there.

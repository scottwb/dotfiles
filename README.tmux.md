# tmux Configuration

My tmux config uses `C-x` as the prefix (like Emacs) instead of the default `C-b`.

## Prerequisites

- **tmux** (3.0+ recommended)
- **git** (for TPM plugin manager)

### macOS

```bash
brew install tmux git
```

### Ubuntu/Debian

```bash
sudo apt install tmux git
```

## Setup on a New Machine

After cloning this dotfiles repo and symlinking (per the main README):

```bash
# 1. Symlink .tmux dir (if not already done by the main dotfiles symlink)
ln -s ~/src/scottwb/dotfiles/.tmux ~/.tmux

# 2. Install TPM (Tmux Plugin Manager)
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# 3. Start tmux and install plugins
tmux
# Inside tmux, press: C-x I (capital I)
# Wait for plugins to install, then press Enter
```

## Quick Reference

Press `C-x h` inside tmux to show a popup cheatsheet.

## Emacs-Style Bindings (Custom)

| Key | Action | Emacs Equivalent |
|-----|--------|------------------|
| `C-x 0` | Kill current pane | `delete-window` |
| `C-x 1` | Kill all other panes | `delete-other-windows` |
| `C-x 2` | Split pane below | `split-window-below` |
| `C-x 3` | Split pane right | `split-window-right` |
| `C-x o` | Cycle to next pane | `other-window` |
| `C-x b` | Choose window/session | `switch-to-buffer` |
| `C-x k` | Kill window | `kill-buffer` |

## Utility Bindings (Custom)

| Key | Action |
|-----|--------|
| `C-x r` | Reload tmux config |
| `C-x h` | Show help cheatsheet |

## Session Persistence (Plugins)

| Key | Action |
|-----|--------|
| `C-x C-s` | Save all sessions (also auto-saves every 15 min) |
| `C-x C-r` | Restore all sessions (also auto-restores on tmux start) |
| `C-x I` | Install plugins (after adding to `.tmux.conf`) |
| `C-x U` | Update plugins |

### What Gets Saved/Restored

- All sessions, windows, and panes
- Pane layouts (splits, sizes)
- Working directories for each pane
- Window and session names
- Active/alternate windows
- Pane contents (scrollback buffer)

### What Does NOT Get Saved

- Running processes (shells restart fresh)
- Shell history (use `setopt INC_APPEND_HISTORY` in zsh to persist history independently)
- Environment variables set in-session

## Default Bindings (Kept)

### Pane Management
| Key | Action |
|-----|--------|
| `C-x o` | Cycle to next pane |
| `C-x z` | Toggle pane zoom (fullscreen) |
| `C-x {` | Swap pane left |
| `C-x }` | Swap pane right |
| `C-x q` | Show pane numbers (type # to jump) |
| `C-x !` | Move pane to new window |

### Window (Tab) Management
| Key | Action |
|-----|--------|
| `C-x c` | Create new window |
| `C-x n` | Next window |
| `C-x p` | Previous window |
| `C-x l` | Last (toggle) window |
| `C-x w` | List windows interactively |
| `C-x ,` | Rename current window |
| `C-x &` | Kill window (with confirmation) |
| `C-x '` | Prompt for window index |
| `C-x 4-9` | Jump to window 4-9 |

### Session Management
| Key | Action |
|-----|--------|
| `C-x d` | Detach from session |
| `C-x s` | List sessions |
| `C-x $` | Rename session |
| `C-x (` | Previous session |
| `C-x )` | Next session |

### Copy Mode (Scrollback)
| Key | Action |
|-----|--------|
| `C-x [` | Enter copy mode |
| `q` | Exit copy mode |
| `Space` | Start selection |
| `Enter` | Copy selection |
| `C-x ]` | Paste buffer |

### Other
| Key | Action |
|-----|--------|
| `C-x t` | Show clock |
| `C-x ?` | List ALL key bindings |
| `C-x :` | Command prompt |

## Settings

- **Scrollback**: 100,000 lines (preserved across detach/reattach)
- **Mouse**: Enabled (click panes, drag to resize)
- **Terminal titles**: Enabled
- **Auto-save**: Every 15 minutes (via continuum)
- **Auto-restore**: On tmux server start (via continuum)
- **Pane contents**: Captured in save/restore (via resurrect)

## Differences from Emacs

| Action | Emacs | tmux |
|--------|-------|------|
| Quit | `C-x C-c` | `C-x d` (detach) or `C-x :kill-session` |
| Find file | `C-x C-f` | N/A (use shell) |
| Save | `C-x C-s` | Save tmux sessions (resurrect) |
| Undo | `C-x u` | N/A |

## Shell Aliases

Defined in `~/.zsh/aliases`:

| Alias | Expands to | Usage |
|-------|------------|-------|
| `tmls` | `tmux ls` | List all sessions |
| `tmn` | `tmux new -s ` | `tmn work` - create session named "work" |
| `tma` | `tmux attach -t ` | `tma work` - attach to session "work" |
| `tmh` | `less ~/.tmux.cheatsheet.txt` | Show help cheatsheet (outside tmux) |

## Plugins

Managed by [TPM (Tmux Plugin Manager)](https://github.com/tmux-plugins/tpm).

| Plugin | Purpose |
|--------|---------|
| [tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect) | Save/restore sessions manually with `C-x C-s` / `C-x C-r` |
| [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) | Auto-save every 15 min, auto-restore on tmux start |

### Plugin State

- **TPM** is installed at `~/.tmux/plugins/tpm` (git clone, not in dotfiles)
- **Plugin code** lives in `~/.tmux/plugins/` (installed by TPM, gitignored)
- **Saved sessions** live in `~/.tmux/resurrect/` (machine-specific, gitignored)

## Config Location

- Config: `~/.tmux.conf` (symlinked from dotfiles)
- Cheatsheet: `~/.tmux.cheatsheet.txt` (symlinked from dotfiles)
- Plugin dir: `~/.tmux/` (symlinked from dotfiles, contents gitignored)

Reload with: `C-x r` or `tmux source-file ~/.tmux.conf`

## Troubleshooting

**Plugins not loading after config change:**
Reload config with `C-x r`, then install plugins with `C-x I`.

**Restore not working:**
Check that a save exists: `ls ~/.tmux/resurrect/`. If empty, do a manual save first with `C-x C-s`.

**TPM not installed:**
`git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm`, then reload config.

**"No plugin manager" errors:**
Ensure `~/.tmux` is symlinked correctly: `ls -la ~/.tmux` should point to the dotfiles repo.

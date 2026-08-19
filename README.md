The dotfiles of scottwb
=======================

You are probably not that interested in this.

Installation:

* Create `~/.gitconfig.local` with the machine-local git identity and
  commit signing (the tracked `.gitconfig` is symlinked in below and
  includes this file last, so its values win; signing lives here, not
  in the tracked file, so devcontainers that copy `.gitconfig` without
  the key just skip signing instead of failing to commit):

  ```bash
  git config --file ~/.gitconfig.local user.email you@example.com
  git config --file ~/.gitconfig.local user.signingkey '~/.ssh/id_rsa.pub'
  git config --file ~/.gitconfig.local commit.gpgSign true
  ```

  The SSH key is already registered on GitHub as a signing key
  (account-level, one-time, done); commits sign and verify with no
  further setup on any machine that has `~/.ssh/id_rsa`.

* Install `~/.ssh/id_rsa*` by copying them from another machine, or generating
  them and installing them on your github account.

  ```bash
  cd ~/.ssh
  scp scottwb@swb.local:~/.ssh/id_rsa* .
  ```

  Then regenerate the SSH signature trust file (used only for local
  `git log --show-signature` verification; signing works without it):

  ```bash
  echo "you@example.com $(cut -d' ' -f1-2 ~/.ssh/id_rsa.pub)" > ~/.ssh/allowed_signers
  ```

* Install the dotfiles and friends:

        cd ~
        mkdir -p src/scottwb
        cd src/scottwb
        git clone git@github.com:scottwb/dotfiles.git
        cd ~
        ln -s ~/src/scottwb/dotfiles/.* .
        ls -ld .git          # confirm it is a LINK (starts with "l"), not a dir
        unlink .git
        ln -s ~/src/scottwb/dotfiles/bin bin

  Note that this installs the dot-prefixed entries plus `bin`, and
  nothing else. Top-level non-dot directories (`docs/`, `linux/`,
  `themes/`) are repo-only by design and deliberately never linked
  into `$HOME`: `docs/` in particular holds this repo's own roadmap
  and development plans, which have no business in a home directory.

  **Why `unlink .git`, and why not `rm -rf`.** The glob above links
  *every* dot-entry, `.git` included, so `~/.git` ends up pointing at
  the dotfiles repo and makes your whole home directory look like a
  checkout. That one bad symlink is what this removes. `unlink` is
  used rather than `rm -rf` because it fails safe in both directions
  that matter, verified 2026-08-01 with each case against a fresh
  target:

  | Command | The symlink | The real repo |
  |---|---|---|
  | `rm -rf .git` | removed | intact |
  | **`rm -rf .git/`** | still there | **destroyed** |
  | `rm .git` | removed | intact |
  | `unlink .git` | removed | intact |

  One trailing slash inverts the outcome: macOS resolves through the
  link, recursively deletes the target's contents, and leaves the
  dangling symlink behind. And `rm -rf .git` run from the repo by
  mistake destroys it silently, where `unlink .git` refuses with
  "is a directory". Check the `ls -ld` output before deleting: if it
  shows `d` instead of `l`, you are in the wrong directory.

* Install the private companion repo,
  [dotfiles-private](https://github.com/scottwb/dotfiles-private),
  per the instructions in its README:

        cd ~/src/scottwb
        git clone git@github.com:scottwb/dotfiles-private.git

* Log out and back in.


Claude Code route launchers
---------------------------

`bin/` holds a family of launchers that run Claude Code against non-Anthropic
backends, one process at a time.

**Plain `claude` and `claudedsp` are deliberately untouched.** They stay on the
Max subscription with no wrapper in the path and no telemetry changes. Routing
is per process, so a routed session and a plain one run side by side without
either knowing about the other, and nothing global is flipped to switch.

| Command | Backend | Model | Cost | First token |
|---|---|---|---|---|
| `claude-glm` | local Ollama | `glm-4.7-flash` | free | **~4 min** |
| `claude-ollama` | local Ollama | the Ollama default (currently `glm`) | free | ~4 min |
| `claude-gpt` | OpenRouter | `openai/gpt-5.6-sol` | ~$0.06-0.10/turn | ~4 s |
| `claude-openrouter` | OpenRouter | the OpenRouter default (currently `gpt`) | ~$0.06-0.10/turn | ~4 s |

All four are three-line wrappers over `bin/claude-run`, which owns the provider
table, the model table, and all environment construction. `bin/claude-ps`
shows which backend every running session is on.

Inspect any launcher without starting anything:

```bash
CLAUDE_ROUTE_DRYRUN=1 claude-gpt      # print the resolved plan, launch nothing
CLAUDE_ROUTE_PREFLIGHT_ONLY=1 claude-glm   # check the backend is ready, no session
bin/claude-route-selftest             # 105 assertions, no session, no spend
```

### One-time setup

Ollama needs nothing beyond a running server (`ollama serve`) and the model
pulled. OpenRouter needs three things:

1. **A 1Password item** at `op://Employee/OpenRouter/API Key`, in the
   `facetdigital.1password.com` account. The reference is hardcoded in
   `bin/claude-run`; that is a path, not a secret. There is no `.env` file.
2. **The 1Password CLI**, with shell integration enabled:
   ```bash
   brew install 1password-cli
   ```
   Then 1Password > Settings > Developer > "Integrate with 1Password CLI".
   TouchID prompts on the first `op read` per session.
3. **A per-key credit limit** at `openrouter.ai/settings/keys`. Set it on the
   key itself, not just the account: an account-level limit caps total spend
   across every key, so a runaway session drains the whole budget before
   stopping. Verify with:
   ```bash
   KEY=$(op read --account facetdigital.1password.com "op://Employee/OpenRouter/API Key")
   curl -fsS https://openrouter.ai/api/v1/key -H "Authorization: Bearer $KEY" \
     | jq '.data | {limit, limit_remaining, usage}'
   unset KEY
   ```
   `limit` must be a number. `null` means no per-key cap is set.

### Adding a model

Routine maintenance, since provider catalogs churn. Two tables in
`bin/claude-run`, both plain `case` statements:

- `resolve_model()` maps an alias to `(provider, model id, context tokens)`
- `resolve_provider()` maps a provider to its base URL and auth

Then add the alias to `KNOWN_ALIASES` and the usage text. A named wrapper is
optional: once inside an OpenRouter session, `/model` reaches the whole
catalog, so wrappers are worth writing only for backends and daily defaults.

Get the context number right. It is what stops Claude Code assuming a
Claude-sized window for a model name it does not recognize, and both current
values were measured rather than guessed.

### Never use `exec` in a launcher

`claude-ps` reports each session's route by walking process ancestry.
`exec` replaces the launcher process with `claude`, erasing the ancestor that
detection matches on, and **every routed session silently reports as plain
Anthropic**. Nothing errors; the column just quietly lies.

`bin/claude-route-selftest` asserts this for the workhorse and every wrapper.
Keep it that way.

### Things that will surprise you

- **Ollama takes minutes to answer.** Roughly two of it is fixed startup, not
  prompt size, so trimming context barely helps. Not a hang.
- **Ollama's context window comes from the environment `ollama serve` was
  started in**, via `OLLAMA_CONTEXT_LENGTH`, not from the Modelfile. Start the
  server without it and the window silently collapses. `claude-run` warns when
  the loaded window is smaller than the route expects.
- **Cost telemetry lies on Ollama.** Claude Code labels local models as
  `firstParty` and invents a dollar figure for a free session. On OpenRouter the
  numbers are accurate to under 1%, so do not sum the two.
- **Servanda phase gates and security passes halt under any routed profile.**
  That is deliberate: the audit tier is left unmapped so a gate stops rather
  than quietly auditing on a weak model. Run gates on a plain session.
- **Your OpenRouter model list is account-specific.** Zero Data Retention
  settings filter the catalog, so `/model` will not show the same models on
  another account.


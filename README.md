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

* Optional, and private to Facet: install [Patchbay](https://github.com/facetdigital/patchbay), which provides `agent`, `claude-run` and `claude-ps`. Its `install` links them into `~/.local/bin`:

        git clone git@github.com:facetdigital/patchbay.git ~/src/facetdigital/patchbay
        ~/src/facetdigital/patchbay/install

* Log out and back in.

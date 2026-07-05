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
        rm -rf .git
        ln -s ~/src/scottwb/dotfiles/bin bin

* Log out and back in. (`.zshrc` auto-detects macOS vs Linux and sources
  `.zsh/osx` or `.zsh/linux` accordingly; no editing needed.)


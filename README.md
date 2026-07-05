The dotfiles of scottwb
=======================

You are probably not that interested in this.

Installation:

* Create `~/.gitconfig.local` with the machine-local git identity
  (the tracked `.gitconfig` is symlinked in below and includes this
  file last, so its values win):

  ```bash
  git config --file ~/.gitconfig.local user.email you@example.com
  ```

* Install `~/.ssh/id_rsa*` by copying them from another machine, or generating
  them and installing them on your github account.

  ```bash
  cd ~/.ssh
  scp scottwb@swb.local:~/.ssh/id_rsa* .
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


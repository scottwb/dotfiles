The dotfiles of scottwb
=======================

You are probably not that interested in this.

Installation:

* Install `~/.gitconfig` by copying it from another machine or downloading it from here
  and updating the auth key, e.g.:

  ```bash
  cd ~
  scp scottwb@swb.local:~/.gitconfig .
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
        ln -s ~/src/dotfiles/bin bin

* Edit `~/.zshrc` and remove the osx or linux line, keeping whichever one you're on.
* Log out and back in.


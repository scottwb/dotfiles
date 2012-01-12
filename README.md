The dotfiles of scottwb
=======================

You are probably not that interested in this.

Installation:

* Install `~/.gitconfig` by copying it from another machine or downloading it from here
  and updating the auth key.
* Install `~/.ssh/id_rsa*` by copying them from another machine, or generating
  them and installing them on your github account.
* Install the dotfiles and friends:

    cd ~
    mkdir src
    cd src
    git clone git@github.com:scottwb/dotfiles.git
    cp -r ~/src/dotfiles/.* ~/.
    ln -s ~/src/dotfiles/bin bin

* Edit `~/.zshrc` and remove the osx or linux line, keeping whichever one you're on.
* Log out and back in.


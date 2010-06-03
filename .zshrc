#
## .zshrc is sourced in interactive shells.
## It should contain commands to set up aliases,
## functions, options, key bindings, etc.
##

#autoload -U compinit
compinit

##allow tab completion in the middle of a word
setopt COMPLETE_IN_WORD


export PATH=$PATH:~/bin

export PATH=/opt/local/bin:/opt/local/sbin:$PATH
export MANPATH=/opt/local/share/man:$MANPATH

export PATH=/usr/local/mysql/bin:$PATH

export PATH=$PATH:~/.gem/ruby/1.8/bin

alias emacs=/Applications/Emacs.app/Contents/MacOS/Emacs
alias fsharp="mono /usr/local/fsharp/bin/fsi.exe"

export SVN_EDITOR=vi
export RANGER_DEV_MODE=1

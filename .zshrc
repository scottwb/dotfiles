. ~/.zsh/environment
. ~/.zsh/aliases
. ~/.zsh/completion
. ~/.zsh/bindkey

# Load whichever OS-specific settings exist.
[[ -f ~/.zsh/osx ]] && . ~/.zsh/osx
[[ -f ~/.zsh/linux ]] && . ~/.zsh/linux

# Use .localrc for settings specific to one system.
[[ -f ~/.localrc ]] && . ~/.localrc

# This loads RVM into a shell session.
[[ -s "$HOME/.rvm/scripts/rvm" ]] && . "$HOME/.rvm/scripts/rvm"

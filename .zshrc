. ~/.zsh/environment
. ~/.zsh/aliases
. ~/.zsh/completion
. ~/.zsh/bindkey

# Load whichever OS-specific settings exist.
uname | grep Darwin > /dev/null && [[ -f ~/.zsh/osx ]] && . ~/.zsh/osx
uname | grep Linux > /dev/null && [[ -f ~/.zsh/linux ]] && . ~/.zsh/linux

# Use .localrc for settings specific to one system.
[[ -f ~/.localrc ]] && . ~/.localrc

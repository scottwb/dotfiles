. ~/.zsh/environment
. ~/.zsh/aliases
. ~/.zsh/completion
. ~/.zsh/ranger

# Load whichever OS-specific settings exist.
[[ -f ~/.zsh/osx ]] && . ~/.zsh/osx
[[ -f ~/.zsh/linux ]] && . ~/.zsh/linux

# Use .localrc for settings specific to one system.
[[ -f ~/.localrc ]] && . ~/.localrc


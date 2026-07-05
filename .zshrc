. ~/.zsh/environment
. ~/.zsh/aliases
. ~/.zsh/bindkey

# Load whichever OS-specific settings exist.
uname | grep Darwin > /dev/null && [[ -f ~/.zsh/osx ]] && . ~/.zsh/osx
uname | grep Linux > /dev/null && [[ -f ~/.zsh/linux ]] && . ~/.zsh/linux

# Use .localrc for settings specific to one system.
[[ -f ~/.localrc ]] && . ~/.localrc

# Dedupe PATH/fpath. Must run AFTER all the additions above: zsh's
# -U uniqueness doesn't apply to scalar PATH=... assignments, only
# to the value at typeset time and to array assignments.
typeset -U path fpath

# Completion is sourced LAST so compinit runs after every fpath
# addition above (brew, docker, zsh-completions, .localrc).
. ~/.zsh/completion

export TERM=xterm

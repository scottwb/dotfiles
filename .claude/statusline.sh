#!/bin/bash
################################################################################
# Claude Code status line
#
# Example output:
#
#   main │ Opus 5.5 │ ctx 42% │ Running the test suite · Step 3/5 · Yolo Mode
#
# Segments, in order, separated by a dim vertical bar:
#   1. git worktree name, else current branch (omitted outside a repo)
#   2. model display name
#   3. context window used, percent (yellow at 70%, red at 90%)
#   4. current task, step N/M, mode (each part dropped when unknown)
#
# The mode is "Yolo Mode", "Booyah Mode" or "Beastmode" when the most recent
# slash command in the transcript is one of those workflow commands, and the
# permission mode (Auto Mode, Plan Mode, ...) otherwise. The public gist copy
# drops the workflow-command half, since those commands only exist here.
#
# ------------------------------------------------------------------------------
# INSTALL
#
# Nothing to do on this machine: ~/.claude is a symlink to this repo's .claude/,
# and .claude/settings.json already carries the hook-up:
#
#   "statusLine": {
#     "type": "command",
#     "command": "bash \"$HOME/.claude/statusline.sh\" 2>/dev/null || printf '%s' \"$(hostname -s)\""
#   }
#
# Invoking it through `bash` means the file does not need the exec bit, and the
# hostname fallback keeps the line from going blank if the script ever fails.
# Requires jq; without it the status line just reads "statusline: jq not found".
#
# Shareable copy: https://gist.github.com/scottwb/7762acca13cf94af7924f2dc03b35ba0
# Keep it in step when this file changes.
#
# TEST IT BY HAND
#
#   echo '{"model":{"display_name":"Opus"},"cwd":"'"$PWD"'","context_window":{"used_percentage":42}}' \
#     | bash ~/.claude/statusline.sh
#
# ------------------------------------------------------------------------------
# HOW IT WORKS
#
# Claude Code pipes a JSON description of the session to this script on stdin
# and shows whatever it prints. Missing data degrades silently: no transcript
# or no repo just means fewer segments.
#
# Fields are split on the ASCII unit separator, written \u001f inside the jq
# programs. Do not retype it: a mangled escape is a jq compile error, which the
# 2>/dev/null swallows, and the whole line silently goes blank.
#
# Stdin fields used: model.display_name, workspace.git_worktree, worktree.name,
# workspace.current_dir (fallback cwd), context_window.used_percentage,
# transcript_path. The task, step and permission mode are read from the tail of
# the transcript, since stdin carries none of them.
#
# The transcript format is internal to Claude Code and undocumented, so a future
# release may change it. If that happens, segment 4 goes blank and the rest keeps
# working.
################################################################################

export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"

if ! command -v jq >/dev/null 2>&1; then
  printf 'statusline: jq not found\n'
  exit 0
fi

US=$'\037'
input=$(cat)

IFS="$US" read -r model wt_ws wt_top dir pct tp <<EOF
$(printf '%s' "$input" | jq -r '[(.model.display_name // ""), (.workspace.git_worktree // ""), (.worktree.name // ""), (.workspace.current_dir // .cwd // ""), ((.context_window.used_percentage | numbers | round) // "" | tostring), (.transcript_path // "")] | join("\u001f")' 2>/dev/null)
EOF

RESET=$'\033[0m'
DIM=$'\033[2m'
CYAN=$'\033[36m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
sep=" ${DIM}│${RESET} "
out=""

add() {
  [ -n "$1" ] || return 0
  if [ -n "$out" ]; then out="${out}${sep}${1}"; else out="$1"; fi
}

# Strip anything that could drive the terminal instead of printing: C0 controls,
# DEL, C1 controls (U+0080-009F) and bidi overrides/isolates (U+202A-202E,
# U+2066-2069). Byte-wise under LC_ALL=C so it behaves the same on BSD and GNU.
clean() {
  printf '%s' "$1" | LC_ALL=C tr -d '\000-\037\177' \
    | LC_ALL=C sed $'s/\xc2[\x80-\x9f]//g; s/\xe2\x80[\xaa-\xae]//g; s/\xe2\x81[\xa6-\xa9]//g'
}

# 1. worktree, else branch
label=""
if [ -n "$wt_ws" ]; then
  label="$wt_ws"
elif [ -n "$wt_top" ]; then
  label="$wt_top"
elif [ -n "$dir" ] && [ -d "$dir" ]; then
  label=$(git -C "$dir" --no-optional-locks symbolic-ref --short -q HEAD 2>/dev/null)
  [ -n "$label" ] || label=$(git -C "$dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
fi
label=$(clean "$label")
[ -n "$label" ] && add "${CYAN}${label}${RESET}"

# 2. model
add "$(clean "$model")"

# 3. context percent
if [ -n "$pct" ]; then
  p=$(printf '%.0f' "$pct" 2>/dev/null)
  if [ -n "$p" ]; then
    color=""
    [ "$p" -ge 70 ] 2>/dev/null && color="$YELLOW"
    [ "$p" -ge 90 ] 2>/dev/null && color="$RED"
    if [ -n "$color" ]; then add "ctx ${color}${p}%${RESET}"; else add "ctx ${p}%"; fi
  fi
fi

# 4. task, step, mode (from the transcript tail only)
task=""; step=""; mode=""
if [ -n "$tp" ] && [ -r "$tp" ]; then
  tailchunk() { tail -c 4000000 "$tp" 2>/dev/null | tail -n +2; }

  res=$(tailchunk | grep -a -E '"name":"(TodoWrite|TaskCreate|TaskUpdate)"' | jq -nRr '
    [inputs | fromjson? | select(.type == "assistant") | .message.content[]?
      | select(type == "object" and .type == "tool_use")
      | {n: .name, i: (.input // {})}]
    | reduce .[] as $e ({c: 0, t: []};
        if $e.n == "TodoWrite" then
          .c = 0 | .t = [($e.i.todos // [])[] | {id: "", text: (.activeForm // .content // ""), status: (.status // "pending")}]
        elif $e.n == "TaskCreate" then
          .c += 1 | .t += [{id: (.c | tostring), text: ($e.i.activeForm // $e.i.subject // ""), status: "pending"}]
        elif $e.n == "TaskUpdate" then
          .t |= map(if .id == (($e.i.taskId // "") | tostring)
                    then (.status = ($e.i.status // .status)) | (.text = ($e.i.activeForm // .text))
                    else . end)
        else . end)
    | .t | map(select(.status != "deleted")) as $l
    | ([$l | to_entries[] | select(.value.status == "in_progress")] | .[0]) as $ip
    | if $ip == null then "" else ["\($ip.key + 1)/\($l | length)", ($ip.value.text | .[0:60])] | join("\u001f") end
  ' 2>/dev/null)
  if [ -n "$res" ]; then
    IFS="$US" read -r step task <<EOF
$res
EOF
    task=$(clean "$task")
    [ -n "$step" ] && step="Step ${step}"
  fi

  skill=$(tailchunk | grep -a -E '"type":"user"|"subtype":"local_command"' | grep -a -v 'tool_use_id' \
    | grep -a -Eo '<command-name>/[^<]*(yolo|booyah|beastmode)</command-name>' | tail -1 \
    | grep -Eo 'yolo|booyah|beastmode')
  case "$skill" in
    yolo)      mode="Yolo Mode" ;;
    booyah)    mode="Booyah Mode" ;;
    beastmode) mode="Beastmode" ;;
    *)
      pm=$(tailchunk | grep -a '"type":"permission-mode"' | tail -1 | jq -r '.permissionMode // empty' 2>/dev/null)
      case "$pm" in
        auto)              mode="Auto Mode" ;;
        plan)              mode="Plan Mode" ;;
        acceptEdits)       mode="Accept Edits" ;;
        bypassPermissions) mode="Bypass Permissions" ;;
        dontAsk)           mode="Don't Ask" ;;
        *)                 mode="" ;;
      esac
      ;;
  esac
fi

seg=""
for part in "$task" "$step" "$mode"; do
  [ -n "$part" ] || continue
  if [ -n "$seg" ]; then seg="${seg} · ${part}"; else seg="$part"; fi
done
add "$seg"

[ -n "$out" ] && printf '%s\n' "$out"
exit 0

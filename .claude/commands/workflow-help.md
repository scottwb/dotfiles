Answer questions about the workflow command suite (/roadmap, /gameplan, /booyah, /yolo, /beastmode, /phasegate) from the canonical reference, loaded on demand.

Arguments: $ARGUMENTS (optional - a question, e.g. "does yolo merge?")

1. Read `~/.claude/COMMANDS.md`.
2. If $ARGUMENTS contains a question, answer it directly and concisely from that document (quote the relevant contract line when useful). If the answer genuinely is not covered there, read the specific command file in `~/.claude/commands/` and answer from it, then note that COMMANDS.md may need updating.
3. If no question was asked, print the Autonomy Ladder table and the one-line contract for each command.

Do not paraphrase loosely from memory; the point of this command is to answer from the documented contracts.

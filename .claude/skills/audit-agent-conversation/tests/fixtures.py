"""Shared fixture paths and the known-good figures the suite asserts against.

Transcripts are read from an ABSOLUTE path under the real home directory, never
from a worktree-relative `.claude/projects/`. `~/.claude` is a symlink to the
main dotfiles checkout, and `.claude/projects/` is gitignored, so it exists only
there. A worktree-relative path resolves to an empty directory.
"""

import os
import unittest

PROJECTS = os.path.expanduser("~/.claude/projects")
GREENTHUMB = os.path.join(PROJECTS, "-Users-scottwb-src-scottwb-greenthumb")

# The session the worked example was built from.
REFERENCE = "0a5df9e2-3dc1-4bee-9013-e38e709b4cb1"

# Three daily briefs, verified 2026-08-15. Their much larger cache-write share
# is a useful contrast with the reference session.
BRIEF_AUG13 = "9608087e-a934-4be1-abe8-922949320858"
BRIEF_AUG14 = "bd35db69-e6db-4d2c-bfc1-c1237548ddbe"
BRIEF_AUG15 = "d3a49460-b8fa-4b30-8dec-bc7364bf595b"

# Unsupported-case representatives.
MULTITURN_HUGE = "ac5e6a1e-230b-43b0-9c12-2cd0297a10a5"   # 44 MB, 76 turns
IMAGES = "4e8aadff-509e-4200-b2cc-93ea42cc36be"           # 21 image blocks
MULTITURN_SMALL = "74dc7d90-5143-4771-ba5c-63312ba51d7f"  # 3 KB, 2 turns

# Golden token figures for the reference session, under message.id dedupe.
GOLDEN_TOKENS = {
    "input": 3543,
    "cache_write_1h": 89150,
    "cache_write_5m": 0,
    "cache_read": 529482,
    "output": 16179,
    "reasoning": 9316,
}
GOLDEN_API_MESSAGES = 8

# What a naive per-record summation produces instead. Kept as an assertion so
# the reason the dedupe exists stays visible rather than becoming folklore.
NAIVE_OUTPUT_TOKENS = 41302

GOLDEN_COST = {
    "input_side": 1.1740,
    "output": 0.4045,
    "reasoning": 0.2329,
    "total": 1.5784,
}

# Reply word counts, the cheap smoke assertion that the reply extractor found
# the right block.
BRIEF_REPLY_WORDS = {
    BRIEF_AUG13: 1356,
    BRIEF_AUG14: 1523,
    BRIEF_AUG15: 1056,
}


def path(session_id, project=GREENTHUMB):
    return os.path.join(project, session_id + ".jsonl")


def require_corpus(testcase):
    """Skip rather than fail when the transcript corpus is not on this machine.

    The suite asserts against real transcripts, which are gitignored and local.
    A checkout on another machine should report skips, not spurious failures.
    """
    if not os.path.isdir(GREENTHUMB):
        raise unittest.SkipTest("transcript corpus not present at %s" % GREENTHUMB)


def corpus_sessions():
    """Every .jsonl transcript in the greenthumb project directory."""
    if not os.path.isdir(GREENTHUMB):
        return []
    return sorted(
        os.path.join(GREENTHUMB, f)
        for f in os.listdir(GREENTHUMB)
        if f.endswith(".jsonl")
    )

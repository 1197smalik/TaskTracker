"""Mention extraction helpers for comment text."""

from __future__ import annotations

import re
from dataclasses import dataclass

MENTION_PATTERN = re.compile(
    r"(?<![\w@])@([A-Za-z0-9](?:[A-Za-z0-9._-]{0,62}[A-Za-z0-9])?)"
)
DEFAULT_MAX_MENTIONS = 50


@dataclass(frozen=True, slots=True)
class MentionCandidate:
    """A mention token found in user-authored text."""

    handle: str
    start_index: int
    end_index: int


def extract_mentions(
    text: str,
    *,
    max_mentions: int = DEFAULT_MAX_MENTIONS,
) -> list[MentionCandidate]:
    """Extract unique mention handles from text in first-seen order."""
    if max_mentions < 1:
        raise ValueError("max_mentions must be at least one")

    mentions: list[MentionCandidate] = []
    seen_handles: set[str] = set()
    for match in MENTION_PATTERN.finditer(text):
        handle = match.group(1).lower()
        if handle in seen_handles:
            continue

        mentions.append(
            MentionCandidate(
                handle=handle,
                start_index=match.start(),
                end_index=match.end(),
            )
        )
        seen_handles.add(handle)
        if len(mentions) >= max_mentions:
            break

    return mentions

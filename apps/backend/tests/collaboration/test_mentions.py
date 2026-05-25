"""Tests for mention extraction service."""

from __future__ import annotations

import pytest

from taskmaster_backend.collaboration.mentions import MentionCandidate, extract_mentions


def test_extract_mentions_returns_unique_handles_in_first_seen_order() -> None:
    mentions = extract_mentions("Please ask @Alice, @bob, and @alice for review.")

    assert mentions == [
        MentionCandidate(handle="alice", start_index=11, end_index=17),
        MentionCandidate(handle="bob", start_index=19, end_index=23),
    ]


def test_extract_mentions_supports_common_handle_characters() -> None:
    mentions = extract_mentions("Loop in @qa-team @release.manager and @dev_2.")

    assert [mention.handle for mention in mentions] == [
        "qa-team",
        "release.manager",
        "dev_2",
    ]


def test_extract_mentions_ignores_email_addresses_and_double_at_tokens() -> None:
    mentions = extract_mentions(
        "Email user@example.com and ignore @@not-a-mention, but keep @owner."
    )

    assert [mention.handle for mention in mentions] == ["owner"]


def test_extract_mentions_records_source_offsets() -> None:
    text = "Prefix @owner suffix"

    mentions = extract_mentions(text)

    assert mentions == [MentionCandidate(handle="owner", start_index=7, end_index=13)]
    assert text[mentions[0].start_index : mentions[0].end_index] == "@owner"


def test_extract_mentions_respects_max_mentions() -> None:
    mentions = extract_mentions("@one @two @three", max_mentions=2)

    assert [mention.handle for mention in mentions] == ["one", "two"]


def test_extract_mentions_rejects_invalid_max_mentions() -> None:
    with pytest.raises(ValueError, match="max_mentions"):
        extract_mentions("@one", max_mentions=0)


def test_extract_mentions_does_not_resolve_users_or_create_side_effects() -> None:
    mentions = extract_mentions("No persistence for @owner in this story.")

    assert mentions[0].handle == "owner"
    assert not hasattr(mentions[0], "user_id")
    assert not hasattr(mentions[0], "notification_id")

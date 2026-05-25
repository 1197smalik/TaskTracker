"""Internal event payload contracts for Collaboration domain changes."""

from __future__ import annotations

from dataclasses import dataclass

from taskmaster_backend.collaboration.mentions import MentionCandidate
from taskmaster_backend.collaboration.models import Comment

COMMENT_CREATED_EVENT_TYPE = "comment.created"
COMMENT_MENTION_DETECTED_EVENT_TYPE = "comment.mention_detected"
COLLABORATION_EVENT_PAYLOAD_VERSION = "1.0"
MENTION_RECIPIENT_RESOLUTION_STRATEGY = "raw_handle_only"


@dataclass(frozen=True, slots=True)
class MentionRecipientResolution:
    """Deterministic recipient-resolution contract for raw mention handles."""

    strategy: str
    unresolved_handles: tuple[str, ...]
    resolved_user_ids: tuple[str, ...] = ()

    def as_payload(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "unresolved_handles": list(self.unresolved_handles),
            "resolved_user_ids": list(self.resolved_user_ids),
        }


def unresolved_mention_recipients(
    mentions: list[MentionCandidate],
) -> MentionRecipientResolution:
    """Return explicit unresolved recipient metadata without guessing user handles."""
    return MentionRecipientResolution(
        strategy=MENTION_RECIPIENT_RESOLUTION_STRATEGY,
        unresolved_handles=tuple(mention.handle for mention in mentions),
    )


def build_comment_created_payload(
    comment: Comment,
    *,
    project_id: str,
    mentions: list[MentionCandidate],
    recipient_resolution: MentionRecipientResolution,
) -> dict[str, object]:
    """Build the stable internal payload for comment.created."""
    return {
        "comment_id": comment.id,
        "work_item_id": comment.work_item_id,
        "project_id": project_id,
        "author_id": comment.author_id,
        "mentioned_handles": [mention.handle for mention in mentions],
        "mention_recipient_resolution": recipient_resolution.as_payload(),
    }


def build_comment_mention_detected_payload(
    comment: Comment,
    *,
    project_id: str,
    mentions: list[MentionCandidate],
    recipient_resolution: MentionRecipientResolution,
) -> dict[str, object]:
    """Build the stable internal payload for raw mention detection."""
    return {
        "comment_id": comment.id,
        "work_item_id": comment.work_item_id,
        "project_id": project_id,
        "author_id": comment.author_id,
        "mentioned_handles": [mention.handle for mention in mentions],
        "mention_recipient_resolution": recipient_resolution.as_payload(),
    }

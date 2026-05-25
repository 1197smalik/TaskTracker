"""Persistence helpers for Collaboration domain operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.collaboration.models import Comment
from taskmaster_backend.collaboration.schemas import CommentCreateRequest


def create_comment(
    session: Session,
    work_item_id: str,
    author_id: str,
    request: CommentCreateRequest,
    *,
    commit: bool = True,
) -> Comment:
    comment = Comment(
        work_item_id=work_item_id,
        author_id=author_id,
        body=request.body,
    )
    session.add(comment)
    if commit:
        session.commit()
        session.refresh(comment)
    return comment

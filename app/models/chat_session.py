import uuid
from datetime import datetime, timezone

from app.extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    analysis_id = db.Column(
        db.String(36),
        db.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    messages = db.relationship(
        "ChatMessage",
        backref="session",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "analysis_id", name="uq_user_analysis_session"),
    )

    def __repr__(self):
        return f"<ChatSession user={self.user_id[:8]} analysis={self.analysis_id[:8]}>"

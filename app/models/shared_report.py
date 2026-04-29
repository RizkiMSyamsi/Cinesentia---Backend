import uuid
import secrets
from datetime import datetime, timezone

from app.extensions import db


class SharedReport(db.Model):
    __tablename__ = "shared_reports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = db.Column(
        db.String(36),
        db.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    share_token = db.Column(
        db.String(32),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_urlsafe(24),
        index=True,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_valid(self):
        """Check if the share link is still active and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def __repr__(self):
        return f"<SharedReport {self.share_token[:8]}...>"

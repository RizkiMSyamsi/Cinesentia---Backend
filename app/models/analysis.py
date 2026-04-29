import uuid
from datetime import datetime, timezone

from app.extensions import db


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )

    # YouTube metadata
    youtube_url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(20), nullable=False, index=True)
    video_title = db.Column(db.String(500), nullable=True)
    channel_name = db.Column(db.String(255), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    view_count = db.Column(db.BigInteger, nullable=True)

    # Processing status
    status = db.Column(
        db.String(20), nullable=False, default="queued", index=True
    )  # queued, fetching, analyzing, embedding, completed, failed
    progress = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)

    # Results — comment counts
    total_comments = db.Column(db.Integer, nullable=False, default=0)
    positive_count = db.Column(db.Integer, nullable=False, default=0)
    negative_count = db.Column(db.Integer, nullable=False, default=0)
    neutral_count = db.Column(db.Integer, nullable=False, default=0)

    # Results — percentages
    positive_pct = db.Column(db.Float, nullable=False, default=0.0)
    negative_pct = db.Column(db.Float, nullable=False, default=0.0)
    neutral_pct = db.Column(db.Float, nullable=False, default=0.0)

    # Results — model comparison
    model_accuracy = db.Column(db.Float, nullable=True)
    vader_summary = db.Column(db.JSON, nullable=True)
    model_summary = db.Column(db.JSON, nullable=True)
    top_keyword = db.Column(db.String(100), nullable=True)

    # Timestamps
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    comments = db.relationship(
        "Comment", backref="analysis", lazy="dynamic", cascade="all, delete-orphan"
    )
    shared_reports = db.relationship(
        "SharedReport", backref="analysis", lazy="dynamic", cascade="all, delete-orphan"
    )
    chat_sessions = db.relationship(
        "ChatSession", backref="analysis", lazy="dynamic", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.Index("ix_analyses_created_at_desc", created_at.desc()),
    )

    def __repr__(self):
        return f"<Analysis {self.video_id} [{self.status}]>"

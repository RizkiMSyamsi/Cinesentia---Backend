import uuid
from datetime import datetime, timezone

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = db.Column(
        db.String(36),
        db.ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Text content
    original_text = db.Column(db.Text, nullable=False)
    preprocessed_text = db.Column(db.Text, nullable=True)

    # Model prediction
    model_sentiment = db.Column(db.String(10), nullable=True)  # positive/negative/neutral
    model_confidence = db.Column(db.Float, nullable=True)

    # VADER scores
    vader_original_score = db.Column(db.Float, nullable=True)
    vader_original_label = db.Column(db.String(10), nullable=True)
    vader_processed_score = db.Column(db.Float, nullable=True)
    vader_processed_label = db.Column(db.String(10), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.Index("ix_comments_analysis_sentiment", "analysis_id", "model_sentiment"),
    )

    def __repr__(self):
        return f"<Comment {self.id[:8]}... [{self.model_sentiment}]>"

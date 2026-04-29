import uuid
from datetime import date, datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(500), nullable=True)
    plan_tier = db.Column(db.String(20), nullable=False, default="free")
    daily_quota_limit = db.Column(db.Integer, nullable=False, default=3)
    daily_quota_used = db.Column(db.Integer, nullable=False, default=0)
    quota_reset_date = db.Column(db.Date, nullable=False, default=date.today)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    preferences = db.Column(db.JSON, nullable=False, default=dict)
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
    analyses = db.relationship("Analysis", backref="user", lazy="dynamic")
    chat_sessions = db.relationship("ChatSession", backref="user", lazy="dynamic")

    def check_and_reset_quota(self):
        """Reset quota if the reset date has passed."""
        today = date.today()
        if self.quota_reset_date < today:
            self.daily_quota_used = 0
            self.quota_reset_date = today

    @property
    def quota_remaining(self):
        self.check_and_reset_quota()
        return max(0, self.daily_quota_limit - self.daily_quota_used)

    def __repr__(self):
        return f"<User {self.email}>"

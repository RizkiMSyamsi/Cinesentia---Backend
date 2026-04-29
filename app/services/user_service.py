from app.extensions import db, bcrypt
from app.models.user import User


class UserService:
    """Handles user profile updates and quota management."""

    @staticmethod
    def update_profile(user_id, data):
        """Update user's full name and/or email."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        if "full_name" in data:
            user.full_name = data["full_name"]

        if "email" in data:
            new_email = data["email"].lower()
            if new_email != user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    raise ValueError("This email is already in use.")
                user.email = new_email

        db.session.commit()
        return user

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change the user's password after verifying the current one."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        if not bcrypt.check_password_hash(user.password_hash, current_password):
            raise ValueError("Current password is incorrect.")

        user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.session.commit()

        return {"message": "Password changed successfully."}

    @staticmethod
    def update_preferences(user_id, preferences):
        """Update user preferences (JSON blob)."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        user.preferences = preferences
        db.session.commit()
        return user

    @staticmethod
    def get_quota(user_id):
        """Get the user's current quota status."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        user.check_and_reset_quota()
        db.session.commit()

        return {
            "used": user.daily_quota_used,
            "limit": user.daily_quota_limit,
            "remaining": user.quota_remaining,
            "reset_at": user.quota_reset_date.isoformat(),
            "plan_tier": user.plan_tier,
        }

    @staticmethod
    def consume_quota(user_id):
        """Consume one quota unit. Raises if quota exceeded."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found.")

        user.check_and_reset_quota()

        if user.quota_remaining <= 0:
            raise ValueError("Daily analysis quota exceeded. Try again tomorrow.")

        user.daily_quota_used += 1
        db.session.commit()
        return user

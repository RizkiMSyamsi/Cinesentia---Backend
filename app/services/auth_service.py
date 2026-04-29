from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
)
from marshmallow import ValidationError

from app.extensions import db, bcrypt
from app.models.user import User
from app.schemas.auth_schema import register_schema, login_schema


class AuthService:
    """Handles user registration, login, token refresh, and logout."""

    @staticmethod
    def register(data):
        """Register a new user and return tokens."""
        # Validate input
        validated = register_schema.load(data)

        # Check email uniqueness
        existing = User.query.filter_by(email=validated["email"].lower()).first()
        if existing:
            raise ValueError("An account with this email already exists.")

        # Hash password
        password_hash = bcrypt.generate_password_hash(
            validated["password"]
        ).decode("utf-8")

        # Create user
        user = User(
            full_name=validated["full_name"],
            email=validated["email"].lower(),
            password_hash=password_hash,
        )
        db.session.add(user)
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def login(data):
        """Authenticate user and return tokens."""
        validated = login_schema.load(data)

        user = User.query.filter_by(email=validated["email"].lower()).first()
        if not user or not bcrypt.check_password_hash(
            user.password_hash, validated["password"]
        ):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("This account has been deactivated.")

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def refresh(user_id):
        """Generate a new access token from a valid refresh token."""
        access_token = create_access_token(identity=user_id)
        return {"access_token": access_token}

    @staticmethod
    def logout(redis_client):
        """Add the current JWT to the blocklist."""
        jwt_data = get_jwt()
        jti = jwt_data["jti"]
        exp = jwt_data["exp"]

        # Calculate remaining TTL
        import time
        remaining = max(0, exp - int(time.time()))

        # Store in Redis with TTL matching the token's remaining lifetime
        redis_client.setex(f"blocklist:{jti}", remaining, "revoked")

        return {"message": "Successfully logged out."}

    @staticmethod
    def get_current_user(user_id):
        """Get the current authenticated user."""
        user = User.query.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found.")
        return user

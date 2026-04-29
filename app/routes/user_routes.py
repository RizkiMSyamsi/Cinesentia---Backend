from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.user_service import UserService
from app.schemas.auth_schema import (
    user_response_schema,
    update_profile_schema,
    change_password_schema,
    update_preferences_schema,
)

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update user profile (name, email)."""
    try:
        user_id = get_jwt_identity()
        validated = update_profile_schema.load(request.get_json())
        user = UserService.update_profile(user_id, validated)
        return jsonify({"user": user_response_schema.dump(user)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        user_id = get_jwt_identity()
        data = change_password_schema.load(request.get_json())
        result = UserService.change_password(
            user_id, data["current_password"], data["new_password"]
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/preferences", methods=["PUT"])
@jwt_required()
def update_preferences():
    """Update user preferences."""
    try:
        user_id = get_jwt_identity()
        data = update_preferences_schema.load(request.get_json())
        user = UserService.update_preferences(user_id, data["preferences"])
        return jsonify({"user": user_response_schema.dump(user)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

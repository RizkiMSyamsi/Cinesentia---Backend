from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.auth_service import AuthService
from app.schemas.auth_schema import user_response_schema
from app import redis_client

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        result = AuthService.register(request.get_json())
        return jsonify({
            "user": user_response_schema.dump(result["user"]),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return tokens."""
    try:
        result = AuthService.login(request.get_json())
        return jsonify({
            "user": user_response_schema.dump(result["user"]),
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh the access token."""
    user_id = get_jwt_identity()
    result = AuthService.refresh(user_id)
    return jsonify(result), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout and blocklist the current token."""
    result = AuthService.logout(redis_client)
    return jsonify(result), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Get current authenticated user."""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_current_user(user_id)
        return jsonify({"user": user_response_schema.dump(user)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

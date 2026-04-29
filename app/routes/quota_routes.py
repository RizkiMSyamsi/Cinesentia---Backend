from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.user_service import UserService

quota_bp = Blueprint("quota", __name__, url_prefix="/api/quota")


@quota_bp.route("", methods=["GET"])
@jwt_required()
def get_quota():
    """Get current user's quota status."""
    try:
        user_id = get_jwt_identity()
        result = UserService.get_quota(user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

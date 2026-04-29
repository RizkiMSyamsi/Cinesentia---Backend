from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.services.user_service import UserService


def require_quota(f):
    """Decorator to check if user has remaining analysis quota."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        try:
            quota = UserService.get_quota(user_id)
            if quota["remaining"] <= 0:
                return jsonify({
                    "error": "Quota exceeded",
                    "message": "Daily analysis quota exceeded. Try again tomorrow.",
                    "quota": quota,
                }), 429
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        return f(*args, **kwargs)
    return decorated

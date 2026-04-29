from flask import jsonify
from marshmallow import ValidationError


def register_error_handlers(app):
    """Register global error handlers for the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized", "message": "Authentication required."}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden", "message": "Access denied."}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "Resource not found."}), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"error": "Unprocessable entity", "message": str(error)}), 422

    @app.errorhandler(429)
    def rate_limited(error):
        return jsonify({"error": "Too many requests", "message": "Rate limit exceeded."}), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred."}), 500

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify({"error": "Validation error", "messages": error.messages}), 400

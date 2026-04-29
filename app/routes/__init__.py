from flask import Flask

from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.analysis_routes import analysis_bp
from app.routes.chat_routes import chat_bp
from app.routes.report_routes import report_bp
from app.routes.quota_routes import quota_bp


def register_blueprints(app: Flask):
    """Register all route blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(quota_bp)

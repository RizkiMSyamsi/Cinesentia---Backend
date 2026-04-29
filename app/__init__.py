import os
import redis

from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate, jwt, bcrypt, cors, ma


# Redis instance for JWT blocklist
redis_client = None


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {"origins": app.config["FRONTEND_URL"]}
    })
    ma.init_app(app)

    # Setup Redis for JWT blocklist
    global redis_client
    redis_client = redis.from_url(app.config["REDIS_URL"], decode_responses=True)

    # Register JWT blocklist callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token_in_redis = redis_client.get(f"blocklist:{jti}")
        return token_in_redis is not None

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app

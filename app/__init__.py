import os
import redis

from flask import Flask
from celery import Celery

from app.config import config_by_name
from app.extensions import db, migrate, jwt, bcrypt, cors, ma


# Redis instance for JWT blocklist
redis_client = None

# Celery instance (shared between Flask app and worker)
celery = Celery(__name__)


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize Celery with Redis URL from Flask config
    redis_url = app.config["REDIS_URL"]
    celery.conf.broker_url = redis_url
    celery.conf.result_backend = redis_url

    class ContextTask(celery.Task):
        """Ensure each Celery task runs within the Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.autodiscover_tasks(["app.tasks"])

    # Set as default so shared_task can find it
    celery.set_default()

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


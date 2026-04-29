from celery import Celery
from app import create_app
from app.config import Config

app = create_app()


def make_celery(flask_app):
    """Create a Celery instance tied to the Flask app context."""
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(flask_app.config)

    class ContextTask(celery.Task):
        """Ensure each Celery task runs within the Flask app context."""
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Auto-discover tasks
    celery.autodiscover_tasks(["app.tasks"])

    return celery


celery = make_celery(app)

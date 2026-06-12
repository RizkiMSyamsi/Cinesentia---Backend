from app import create_app, celery

# Create the Flask app (which also configures the Celery instance)
app = create_app()

# Explicitly import tasks so Celery registers them
import app.tasks.analysis_task  # noqa: F401, E402

# Re-export celery for the worker CLI:
#   celery -A celery_worker.celery worker --loglevel=info --pool=solo

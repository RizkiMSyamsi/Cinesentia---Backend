from datetime import datetime, timezone

from app.extensions import db
from app.models.analysis import Analysis
from app.models.comment import Comment
from app.utils.helpers import extract_video_id


class AnalysisService:
    """Handles analysis CRUD operations."""

    @staticmethod
    def create(user_id, youtube_url, max_comments=10000):
        """Create a new analysis record and enqueue the processing task."""
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise ValueError("Could not extract video ID from the provided URL.")

        analysis = Analysis(
            user_id=user_id,
            youtube_url=youtube_url,
            video_id=video_id,
            status="queued",
            progress=0,
        )
        db.session.add(analysis)
        db.session.commit()

        # Enqueue Celery task (import here to avoid circular imports)
        from app.tasks.analysis_task import run_analysis_pipeline

        run_analysis_pipeline.delay(analysis.id, max_comments)

        return analysis

    @staticmethod
    def get_by_id(analysis_id, user_id=None):
        """Get an analysis by ID, optionally scoped to a user."""
        query = Analysis.query.filter_by(id=analysis_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        analysis = query.first()
        if not analysis:
            raise ValueError("Analysis not found.")
        return analysis

    @staticmethod
    def list_for_user(user_id, page=1, per_page=10, status=None):
        """List analyses for a user with pagination and optional status filter."""
        query = Analysis.query.filter_by(user_id=user_id).order_by(
            Analysis.created_at.desc()
        )
        if status:
            query = query.filter_by(status=status)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "analyses": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def get_status(analysis_id, user_id):
        """Get the processing status of an analysis."""
        analysis = Analysis.query.filter_by(
            id=analysis_id, user_id=user_id
        ).first()
        if not analysis:
            raise ValueError("Analysis not found.")
        return {
            "id": analysis.id,
            "status": analysis.status,
            "progress": analysis.progress,
            "error_message": analysis.error_message,
        }

    @staticmethod
    def get_comments(analysis_id, user_id, page=1, per_page=20, sentiment=None):
        """Get paginated comments for an analysis."""
        # Verify ownership
        analysis = Analysis.query.filter_by(
            id=analysis_id, user_id=user_id
        ).first()
        if not analysis:
            raise ValueError("Analysis not found.")

        query = Comment.query.filter_by(analysis_id=analysis_id)
        if sentiment:
            query = query.filter_by(model_sentiment=sentiment)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "comments": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def delete(analysis_id, user_id):
        """Delete an analysis and all related data."""
        analysis = Analysis.query.filter_by(
            id=analysis_id, user_id=user_id
        ).first()
        if not analysis:
            raise ValueError("Analysis not found.")

        db.session.delete(analysis)
        db.session.commit()

        # Also clean up ChromaDB collection
        try:
            from app.services.chroma_service import ChromaService

            chroma = ChromaService()
            chroma.delete_collection(analysis_id)
        except Exception:
            pass  # ChromaDB cleanup is best-effort

        return {"message": "Analysis deleted successfully."}

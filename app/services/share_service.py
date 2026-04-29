from app.extensions import db
from app.models.shared_report import SharedReport
from app.models.analysis import Analysis


class ShareService:
    """Handles creating, retrieving, and deactivating shared report links."""

    @staticmethod
    def create_share_link(analysis_id, user_id):
        """Generate a public share token for an analysis."""
        analysis = Analysis.query.filter_by(id=analysis_id, user_id=user_id).first()
        if not analysis:
            raise ValueError("Analysis not found.")
        if analysis.status != "completed":
            raise ValueError("Can only share completed analyses.")

        # Check if an active share link already exists
        existing = SharedReport.query.filter_by(
            analysis_id=analysis_id, is_active=True
        ).first()
        if existing:
            return existing

        report = SharedReport(analysis_id=analysis_id)
        db.session.add(report)
        db.session.commit()
        return report

    @staticmethod
    def get_by_token(share_token):
        """Get analysis data via a public share token."""
        report = SharedReport.query.filter_by(share_token=share_token).first()
        if not report:
            raise ValueError("Report not found.")
        if not report.is_valid:
            raise ValueError("This share link has expired or been deactivated.")
        return report

    @staticmethod
    def deactivate(share_token, user_id):
        """Deactivate a shared report link."""
        report = SharedReport.query.filter_by(share_token=share_token).first()
        if not report:
            raise ValueError("Report not found.")

        analysis = Analysis.query.get(report.analysis_id)
        if not analysis or analysis.user_id != user_id:
            raise ValueError("Unauthorized.")

        report.is_active = False
        db.session.commit()
        return {"message": "Share link deactivated."}

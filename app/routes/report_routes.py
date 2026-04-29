from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.share_service import ShareService
from app.services.analysis_service import AnalysisService
from app.schemas.analysis_schema import analysis_response_schema

report_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@report_bp.route("/analyses/<analysis_id>/share", methods=["POST"])
@jwt_required()
def create_share_link(analysis_id):
    """Generate a public share link for an analysis."""
    try:
        user_id = get_jwt_identity()
        report = ShareService.create_share_link(analysis_id, user_id)
        return jsonify({
            "share_token": report.share_token,
            "share_url": f"/report/{report.share_token}",
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@report_bp.route("/<share_token>", methods=["GET"])
def get_public_report(share_token):
    """Get analysis data via public share token (no auth required)."""
    try:
        report = ShareService.get_by_token(share_token)
        analysis = AnalysisService.get_by_id(report.analysis_id)
        return jsonify({
            "analysis": analysis_response_schema.dump(analysis),
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@report_bp.route("/<share_token>", methods=["DELETE"])
@jwt_required()
def deactivate_share_link(share_token):
    """Deactivate a shared report link."""
    try:
        user_id = get_jwt_identity()
        result = ShareService.deactivate(share_token, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

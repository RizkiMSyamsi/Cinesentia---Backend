from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.analysis_service import AnalysisService
from app.services.user_service import UserService
from app.schemas.analysis_schema import (
    create_analysis_schema,
    analysis_response_schema,
    analysis_status_schema,
)
from app.schemas.comment_schema import comment_response_schema

analysis_bp = Blueprint("analyses", __name__, url_prefix="/api/analyses")


@analysis_bp.route("", methods=["POST"])
@jwt_required()
def create_analysis():
    """Submit a new YouTube URL for analysis."""
    try:
        user_id = get_jwt_identity()

        # Check quota first (disabled to allow unlimited analyses)
        # UserService.consume_quota(user_id)

        data = create_analysis_schema.load(request.get_json())
        analysis = AnalysisService.create(
            user_id=user_id,
            youtube_url=data["youtube_url"],
            max_comments=data.get("max_comments", 10),
        )
        return jsonify({
            "analysis_id": analysis.id,
            "status": analysis.status,
        }), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@analysis_bp.route("", methods=["GET"])
@jwt_required()
def list_analyses():
    """List all analyses for the current user."""
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("limit", 10, type=int)
    status = request.args.get("status", None)

    result = AnalysisService.list_for_user(user_id, page, per_page, status)
    return jsonify({
        "analyses": analysis_response_schema.dump(result["analyses"], many=True),
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@analysis_bp.route("/<analysis_id>", methods=["GET"])
@jwt_required()
def get_analysis(analysis_id):
    """Get full analysis details."""
    try:
        user_id = get_jwt_identity()
        analysis = AnalysisService.get_by_id(analysis_id, user_id)
        return jsonify({
            "analysis": analysis_response_schema.dump(analysis),
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@analysis_bp.route("/<analysis_id>/status", methods=["GET"])
@jwt_required()
def get_status(analysis_id):
    """Get processing status of an analysis (for polling)."""
    try:
        user_id = get_jwt_identity()
        status = AnalysisService.get_status(analysis_id, user_id)
        return jsonify(status), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@analysis_bp.route("/<analysis_id>/comments", methods=["GET"])
@jwt_required()
def get_comments(analysis_id):
    """Get paginated comments for an analysis."""
    try:
        user_id = get_jwt_identity()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("limit", 20, type=int)
        sentiment = request.args.get("sentiment", None)

        result = AnalysisService.get_comments(
            analysis_id, user_id, page, per_page, sentiment
        )
        return jsonify({
            "comments": comment_response_schema.dump(result["comments"], many=True),
            "total": result["total"],
            "page": result["page"],
            "pages": result["pages"],
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@analysis_bp.route("/<analysis_id>", methods=["DELETE"])
@jwt_required()
def delete_analysis(analysis_id):
    """Delete an analysis."""
    try:
        user_id = get_jwt_identity()
        result = AnalysisService.delete(analysis_id, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

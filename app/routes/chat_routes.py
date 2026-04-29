from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.chat_service import ChatService
from app.services.analysis_service import AnalysisService
from app.schemas.chat_schema import (
    chat_message_input_schema,
    ChatMessageResponseSchema,
)

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

_msg_schema = ChatMessageResponseSchema()


@chat_bp.route("/<analysis_id>", methods=["POST"])
@jwt_required()
def send_message(analysis_id):
    """Send a chat message and get a RAG-powered response."""
    try:
        user_id = get_jwt_identity()

        # Verify analysis ownership
        analysis = AnalysisService.get_by_id(analysis_id, user_id)

        data = chat_message_input_schema.load(request.get_json())

        # Build analysis summary for context
        summary = {
            "total_comments": analysis.total_comments,
            "positive_pct": analysis.positive_pct,
            "negative_pct": analysis.negative_pct,
            "neutral_pct": analysis.neutral_pct,
        }

        result = ChatService.send_message(
            user_id, analysis_id, data["message"], analysis_summary=summary
        )

        return jsonify({
            "reply": result["reply"],
            "sources": result["sources"],
            "message": _msg_schema.dump(result["message"]),
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/<analysis_id>/history", methods=["GET"])
@jwt_required()
def get_history(analysis_id):
    """Get chat history for an analysis."""
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("limit", 50, type=int)

    result = ChatService.get_history(user_id, analysis_id, page, per_page)
    return jsonify({
        "messages": _msg_schema.dump(result["messages"], many=True),
        "total": result["total"],
        "page": result["page"],
        "pages": result["pages"],
    }), 200


@chat_bp.route("/<analysis_id>/history", methods=["DELETE"])
@jwt_required()
def clear_history(analysis_id):
    """Clear chat history for an analysis."""
    user_id = get_jwt_identity()
    result = ChatService.clear_history(user_id, analysis_id)
    return jsonify(result), 200

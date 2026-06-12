"""
Chat service — RAG chatbot using ChromaDB + Google Gemini API.
"""

import os
import logging

from google import genai

from app.extensions import db
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)


class ChatService:
    """RAG chatbot: retrieves relevant comments from ChromaDB, generates response via Gemini."""

    SYSTEM_PROMPT = """You are CineSentia's AI Analyst Assistant ("Phenomenon Explorer").
You help users understand YouTube comment sentiment analysis results.

You have access to a database of analyzed comments from a specific YouTube video.
When answering questions, use the retrieved comment data as evidence.
Always cite specific examples from the comments when possible.
Be concise, analytical, and insightful.
Answer in the same language the user uses (Indonesian or English)."""


    @staticmethod
    def get_or_create_session(user_id, analysis_id):
        """Get existing chat session or create a new one."""
        session = ChatSession.query.filter_by(
            user_id=user_id, analysis_id=analysis_id
        ).first()

        if not session:
            session = ChatSession(user_id=user_id, analysis_id=analysis_id)
            db.session.add(session)
            db.session.commit()

        return session

    @staticmethod
    def send_message(user_id, analysis_id, user_message, analysis_summary=None):
        """
        Process a user message: retrieve context from ChromaDB, generate response via Gemini.

        Args:
            user_id: Current user ID
            analysis_id: Analysis ID for context
            user_message: The user's question
            analysis_summary: Optional dict with analysis stats for context
        """
        session = ChatService.get_or_create_session(user_id, analysis_id)

        # Save user message
        user_msg = ChatMessage(
            session_id=session.id, role="user", content=user_message
        )
        db.session.add(user_msg)

        # Retrieve relevant comments from ChromaDB (non-fatal if unavailable)
        sources = []
        try:
            chroma = ChromaService.get_instance()
            sources = chroma.query(analysis_id, user_message, top_k=10)
        except Exception as e:
            logger.warning(f"ChromaDB query failed (chat will work without comment retrieval): {e}")

        # Build context from retrieved comments
        context_parts = []
        for i, source in enumerate(sources, 1):
            meta = source.get("metadata", {})
            context_parts.append(
                f"{i}. [{meta.get('sentiment', 'unknown')}] "
                f"(confidence: {meta.get('confidence', 0):.2f}) "
                f"\"{meta.get('original_text', source['document'])}\""
            )

        context_str = "\n".join(context_parts) if context_parts else "No specific comments retrieved (embedding model not available)."

        # Build analysis summary context
        summary_str = ""
        if analysis_summary:
            summary_str = (
                f"\nAnalysis Summary:\n"
                f"- Total comments: {analysis_summary.get('total_comments', 'N/A')}\n"
                f"- Positive: {analysis_summary.get('positive_pct', 0):.1f}%\n"
                f"- Negative: {analysis_summary.get('negative_pct', 0):.1f}%\n"
                f"- Neutral: {analysis_summary.get('neutral_pct', 0):.1f}%\n"
            )

        # Construct the prompt
        prompt = (
            f"{ChatService.SYSTEM_PROMPT}\n\n"
            f"{summary_str}\n"
            f"Retrieved relevant comments:\n{context_str}\n\n"
            f"User question: {user_message}"
        )

        # Call Gemini API with retry and model fallback
        models_to_try = [
            "gemini-3.1-flash-lite", # Fastest and cheapest (GA as of May 7)
            "gemini-3-flash",        # Balanced performance
            "gemini-3.1-pro-preview" # Most capable
        ]
        reply_text = None
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )


                reply_text = response.text
                break  # Success, stop trying
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning(f"Gemini {model_name} rate limited, trying next model...")
                    import time
                    time.sleep(2)  # Brief wait before trying next model
                    continue
                else:
                    logger.error(f"Gemini API error ({model_name}): {e}")
                    break

        if reply_text is None:
            reply_text = (
                "⚠️ Maaf, layanan AI sedang mengalami batas kuota. "
                "Silakan coba lagi dalam beberapa menit."
            )

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id, role="assistant", content=reply_text
        )
        db.session.add(assistant_msg)
        db.session.commit()

        return {
            "reply": reply_text,
            "sources": sources,
            "message": assistant_msg,
        }

    @staticmethod
    def get_history(user_id, analysis_id, page=1, per_page=50):
        """Get chat history for a user's analysis session."""
        session = ChatSession.query.filter_by(
            user_id=user_id, analysis_id=analysis_id
        ).first()

        if not session:
            return {"messages": [], "total": 0, "page": 1, "pages": 0}

        pagination = (
            ChatMessage.query.filter_by(session_id=session.id)
            .order_by(ChatMessage.created_at.asc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "messages": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }

    @staticmethod
    def clear_history(user_id, analysis_id):
        """Delete all chat messages for a session."""
        session = ChatSession.query.filter_by(
            user_id=user_id, analysis_id=analysis_id
        ).first()

        if session:
            ChatMessage.query.filter_by(session_id=session.id).delete()
            db.session.commit()

        return {"message": "Chat history cleared."}

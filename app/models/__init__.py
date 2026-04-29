# Import all models so Alembic can detect them
from app.models.user import User
from app.models.analysis import Analysis
from app.models.comment import Comment
from app.models.shared_report import SharedReport
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage

__all__ = [
    "User",
    "Analysis",
    "Comment",
    "SharedReport",
    "ChatSession",
    "ChatMessage",
]

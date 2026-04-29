from app.extensions import ma
from marshmallow import fields, validate


class ChatMessageInputSchema(ma.Schema):
    message = fields.String(
        required=True,
        validate=validate.Length(min=1, max=2000),
        metadata={"description": "User's chat message"},
    )


class ChatMessageResponseSchema(ma.Schema):
    id = fields.String(dump_only=True)
    role = fields.String()
    content = fields.String()
    created_at = fields.DateTime()


class ChatResponseSchema(ma.Schema):
    reply = fields.String()
    sources = fields.List(fields.Dict())
    message = fields.Nested(ChatMessageResponseSchema)


class ChatHistorySchema(ma.Schema):
    messages = fields.List(fields.Nested(ChatMessageResponseSchema))
    total = fields.Integer()
    page = fields.Integer()
    pages = fields.Integer()


# Singleton instances
chat_message_input_schema = ChatMessageInputSchema()
chat_response_schema = ChatResponseSchema()
chat_history_schema = ChatHistorySchema()

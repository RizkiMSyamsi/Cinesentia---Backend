from app.extensions import ma
from marshmallow import fields


class CommentResponseSchema(ma.Schema):
    id = fields.String(dump_only=True)
    original_text = fields.String()
    preprocessed_text = fields.String()
    model_sentiment = fields.String()
    model_confidence = fields.Float()
    vader_original_score = fields.Float()
    vader_original_label = fields.String()
    vader_processed_score = fields.Float()
    vader_processed_label = fields.String()
    created_at = fields.DateTime()


class CommentListSchema(ma.Schema):
    comments = fields.List(fields.Nested(CommentResponseSchema))
    total = fields.Integer()
    page = fields.Integer()
    pages = fields.Integer()


# Singleton instances
comment_response_schema = CommentResponseSchema()
comment_list_schema = CommentListSchema()

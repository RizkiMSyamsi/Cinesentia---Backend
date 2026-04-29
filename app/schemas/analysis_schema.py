from app.extensions import ma
from marshmallow import fields, validate


class CreateAnalysisSchema(ma.Schema):
    youtube_url = fields.String(
        required=True,
        validate=validate.Regexp(
            r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
            error="Invalid YouTube URL format",
        ),
        metadata={"description": "YouTube video URL"},
    )
    max_comments = fields.Integer(
        load_default=10000,
        validate=validate.Range(min=100, max=10000),
        metadata={"description": "Maximum number of comments to scrape (max 10000)"},
    )


class AnalysisResponseSchema(ma.Schema):
    id = fields.String(dump_only=True)
    user_id = fields.String(dump_only=True)
    youtube_url = fields.String()
    video_id = fields.String()
    video_title = fields.String()
    channel_name = fields.String()
    thumbnail_url = fields.String()
    view_count = fields.Integer()
    status = fields.String()
    progress = fields.Integer()
    total_comments = fields.Integer()
    positive_count = fields.Integer()
    negative_count = fields.Integer()
    neutral_count = fields.Integer()
    positive_pct = fields.Float()
    negative_pct = fields.Float()
    neutral_pct = fields.Float()
    model_accuracy = fields.Float()
    vader_summary = fields.Dict()
    model_summary = fields.Dict()
    top_keyword = fields.String()
    error_message = fields.String()
    started_at = fields.DateTime()
    completed_at = fields.DateTime()
    created_at = fields.DateTime()


class AnalysisStatusSchema(ma.Schema):
    id = fields.String(dump_only=True)
    status = fields.String()
    progress = fields.Integer()
    error_message = fields.String()


class AnalysisListSchema(ma.Schema):
    analyses = fields.List(fields.Nested(AnalysisResponseSchema))
    total = fields.Integer()
    page = fields.Integer()
    pages = fields.Integer()


# Singleton instances
create_analysis_schema = CreateAnalysisSchema()
analysis_response_schema = AnalysisResponseSchema()
analysis_list_schema = AnalysisListSchema()
analysis_status_schema = AnalysisStatusSchema()

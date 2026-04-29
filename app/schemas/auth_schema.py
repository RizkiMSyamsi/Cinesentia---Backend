from app.extensions import ma
from marshmallow import fields, validate


class RegisterSchema(ma.Schema):
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        metadata={"description": "User's full name"},
    )
    email = fields.Email(
        required=True, metadata={"description": "User's email address"}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True,
        metadata={"description": "Password (min 8 characters)"},
    )


class LoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserResponseSchema(ma.Schema):
    id = fields.String(dump_only=True)
    full_name = fields.String()
    email = fields.Email()
    avatar_url = fields.String()
    plan_tier = fields.String()
    daily_quota_limit = fields.Integer()
    daily_quota_used = fields.Integer()
    quota_remaining = fields.Integer(dump_only=True)
    preferences = fields.Dict()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UpdateProfileSchema(ma.Schema):
    full_name = fields.String(validate=validate.Length(min=2, max=100))
    email = fields.Email()


class ChangePasswordSchema(ma.Schema):
    current_password = fields.String(required=True, load_only=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True,
    )


class UpdatePreferencesSchema(ma.Schema):
    preferences = fields.Dict(required=True)


# Singleton instances
register_schema = RegisterSchema()
login_schema = LoginSchema()
user_response_schema = UserResponseSchema()
update_profile_schema = UpdateProfileSchema()
change_password_schema = ChangePasswordSchema()
update_preferences_schema = UpdatePreferencesSchema()

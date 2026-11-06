from marshmallow import Schema, fields


class HealthSchema(Schema):
    status = fields.String(required=True)


class VersionSchema(Schema):
    version = fields.String(required=True)
    # Filled only when the update check is enabled and GitHub has answered.
    latest_version = fields.String(allow_none=True, required=True)
    release_url = fields.String(allow_none=True, required=True)
    update_available = fields.Boolean(required=True)

from marshmallow import Schema, fields


class HealthSchema(Schema):
    status = fields.String(required=True)

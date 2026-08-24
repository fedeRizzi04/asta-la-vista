from marshmallow import Schema, fields, validate


class PlayerQuerySchema(Schema):
    role = fields.String(validate=validate.OneOf(["P", "D", "C", "A"]))
    search = fields.String()
    include_inactive = fields.Boolean(load_default=False)


class ImportQuerySchema(Schema):
    confirm_live = fields.Boolean(load_default=False)


class PlayerSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    team = fields.String(required=True)
    role = fields.String(required=True)
    active = fields.Boolean(required=True)


class PlayerCountsSchema(Schema):
    P = fields.Integer(required=True)
    D = fields.Integer(required=True)
    C = fields.Integer(required=True)
    A = fields.Integer(required=True)


class ImportSummarySchema(Schema):
    added = fields.Integer(required=True)
    updated = fields.Integer(required=True)
    deactivated = fields.Integer(required=True)
    role_changes = fields.Integer(required=True)

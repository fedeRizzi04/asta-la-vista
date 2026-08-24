from marshmallow import Schema, fields, validate

role_field = fields.String(required=True, validate=validate.OneOf(["P", "D", "C", "A"]))


class StrategyIdSchema(Schema):
    id = fields.String(required=True)


class StrategyCreateSchema(Schema):
    name = fields.String(required=True)


class StrategyUpdateSchema(Schema):
    name = fields.String(required=True)


class StrategySummarySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    tier_count = fields.Integer(required=True)
    assigned_player_count = fields.Integer(required=True)


class TierCreateSchema(Schema):
    role = role_field
    name = fields.String(required=True)
    color = fields.String(allow_none=True)


class TierUpdateSchema(Schema):
    name = fields.String(required=True)
    color = fields.String(allow_none=True)


class TierOrderSchema(Schema):
    role = role_field
    tier_ids = fields.List(fields.String(), required=True)


class TierSchema(Schema):
    id = fields.String(required=True)
    role = fields.String(required=True)
    name = fields.String(required=True)
    position = fields.Integer(required=True)
    color = fields.String(allow_none=True)


class StrategyEntryUpdateSchema(Schema):
    tier_id = fields.String(allow_none=True)
    note = fields.String(allow_none=True)


class StrategyEntrySchema(Schema):
    player_id = fields.String(required=True)
    name = fields.String(required=True)
    team = fields.String(required=True)
    role = fields.String(required=True)
    active = fields.Boolean(required=True)
    tier_id = fields.String(allow_none=True)
    note = fields.String(required=True)


class StrategyDetailSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    tiers = fields.List(fields.Nested(TierSchema), required=True)
    entries = fields.List(fields.Nested(StrategyEntrySchema), required=True)

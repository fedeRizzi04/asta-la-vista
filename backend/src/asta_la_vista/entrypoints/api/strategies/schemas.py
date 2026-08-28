from marshmallow import Schema, fields, validate


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
    name = fields.String(required=True)
    color = fields.String(allow_none=True)


class TierUpdateSchema(Schema):
    name = fields.String(required=True)
    color = fields.String(allow_none=True)


class TierOrderSchema(Schema):
    tier_ids = fields.List(fields.String(), required=True)


class TierSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    position = fields.Integer(required=True)
    color = fields.String(allow_none=True)


class StrategyEntryUpdateSchema(Schema):
    tier_id = fields.String(allow_none=True, required=True)
    note = fields.String(required=True)
    maximum_price_percentage = fields.Float(
        allow_none=True,
        required=True,
        validate=validate.Range(min=0, max=100, min_inclusive=False),
    )


class StrategyEntrySchema(Schema):
    player_id = fields.String(required=True)
    name = fields.String(required=True)
    team = fields.String(required=True)
    role = fields.String(required=True)
    active = fields.Boolean(required=True)
    mantra_roles = fields.List(fields.String(), required=True)
    tier_id = fields.String(allow_none=True)
    note = fields.String(required=True)
    maximum_price_percentage = fields.Float(allow_none=True)


class StrategyImportQuerySchema(Schema):
    name = fields.String(required=True)
    confirm_unmatched = fields.Boolean(load_default=False)


class StrategyImportSummarySchema(Schema):
    strategy_id = fields.String(required=True)
    tiers_created = fields.Integer(required=True)
    players_assigned = fields.Integer(required=True)
    unmatched = fields.List(fields.String(), required=True)


class StrategyDetailSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    tiers = fields.List(fields.Nested(TierSchema), required=True)
    entries = fields.List(fields.Nested(StrategyEntrySchema), required=True)

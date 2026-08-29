from marshmallow import Schema, fields


class AuctionIdSchema(Schema):
    id = fields.String(required=True)


class AuctionCreateSchema(Schema):
    name = fields.String(required=True)
    initial_credits = fields.Integer(required=True, strict=True)
    goalkeeper_slots = fields.Integer(required=True, strict=True)
    defender_slots = fields.Integer(required=True, strict=True)
    midfielder_slots = fields.Integer(required=True, strict=True)
    forward_slots = fields.Integer(required=True, strict=True)
    participant_names = fields.List(fields.String(), required=True)
    strategy_id = fields.String(allow_none=True)


class AuctionStrategySchema(Schema):
    strategy_id = fields.String(allow_none=True, load_default=None)


class AuctionSummarySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    status = fields.String(required=True)
    initial_credits = fields.Integer(required=True)
    strategy_id = fields.String(allow_none=True)
    participant_count = fields.Integer(required=True)
    purchase_count = fields.Integer(required=True)


class SlotSchema(Schema):
    filled = fields.Integer(required=True)
    total = fields.Integer(required=True)


class PurchaseSchema(Schema):
    id = fields.String(required=True)
    player_id = fields.String(required=True)
    player_name = fields.String(required=True)
    team = fields.String(required=True)
    role = fields.String(required=True)
    price = fields.Integer(required=True)
    player_active = fields.Boolean(required=True)
    mantra_roles = fields.List(fields.String(), required=True)
    created_at = fields.String(required=True)


class ParticipantSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    position = fields.Integer(required=True)
    credits_remaining = fields.Integer(required=True)
    maximum_bid = fields.Integer(required=True)
    slots = fields.Dict(keys=fields.String(), values=fields.Nested(SlotSchema), required=True)
    purchases = fields.List(fields.Nested(PurchaseSchema), required=True)


class AuctionDetailSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    status = fields.String(required=True)
    initial_credits = fields.Integer(required=True)
    strategy_id = fields.String(allow_none=True)
    slot_totals = fields.Dict(keys=fields.String(), values=fields.Integer(), required=True)
    participants = fields.List(fields.Nested(ParticipantSchema), required=True)
    purchased_player_ids = fields.List(fields.String(), required=True)


class PurchaseCreateSchema(Schema):
    player_id = fields.String(required=True)
    participant_id = fields.String(required=True)
    price = fields.Integer(required=True, strict=True)


class PurchaseUpdateSchema(Schema):
    participant_id = fields.String(required=True)
    price = fields.Integer(required=True, strict=True)

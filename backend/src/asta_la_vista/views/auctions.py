from sqlalchemy import text

from asta_la_vista.exceptions import NotFoundError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork
from asta_la_vista.views.players import split_mantra_roles


def auction_list(uow: AbstractUnitOfWork) -> list[dict]:
    with uow:
        rows = uow.session.execute(
            text("""
                SELECT a.uuid, a.name, a.status, a.initial_credits, a.strategy_id,
                       COUNT(DISTINCT pt.uuid) AS participant_count,
                       COUNT(DISTINCT CASE WHEN p.cancelled = FALSE
                                          THEN p.uuid END) AS purchase_count
                FROM auction a
                LEFT JOIN participant pt ON pt.auction_id = a.uuid
                LEFT JOIN purchase p ON p.auction_id = a.uuid
                GROUP BY a.uuid, a.name, a.status, a.initial_credits, a.strategy_id
                ORDER BY a.name COLLATE NOCASE
            """)
        ).mappings()
        return [
            {
                "id": row["uuid"],
                "name": row["name"],
                "status": row["status"],
                "initial_credits": row["initial_credits"],
                "strategy_id": row["strategy_id"],
                "participant_count": row["participant_count"],
                "purchase_count": row["purchase_count"],
            }
            for row in rows
        ]


def auction_detail(uow: AbstractUnitOfWork, auction_id: str) -> dict:
    with uow:
        auction = (
            uow.session.execute(
                text("""
                SELECT uuid, name, status, initial_credits, strategy_id,
                       goalkeeper_slots, defender_slots, midfielder_slots, forward_slots
                FROM auction
                WHERE uuid = :auction_id
            """),
                {"auction_id": auction_id},
            )
            .mappings()
            .one_or_none()
        )
        if auction is None:
            raise NotFoundError("Auction not found")
        participants = list(
            uow.session.execute(
                text("""
                    SELECT pt.uuid, pt.name, pt.position,
                           COALESCE(SUM(p.price), 0) AS spent,
                           COUNT(p.uuid) AS filled_total,
                           SUM(CASE WHEN p.role = 'P' THEN 1 ELSE 0 END) AS filled_goalkeepers,
                           SUM(CASE WHEN p.role = 'D' THEN 1 ELSE 0 END) AS filled_defenders,
                           SUM(CASE WHEN p.role = 'C' THEN 1 ELSE 0 END) AS filled_midfielders,
                           SUM(CASE WHEN p.role = 'A' THEN 1 ELSE 0 END) AS filled_forwards
                    FROM participant pt
                    LEFT JOIN purchase p ON p.participant_id = pt.uuid AND p.cancelled = FALSE
                    WHERE pt.auction_id = :auction_id
                    GROUP BY pt.uuid, pt.name, pt.position
                    ORDER BY pt.position
                """),
                {"auction_id": auction_id},
            ).mappings()
        )
        purchases = list(
            uow.session.execute(
                text("""
                    SELECT p.uuid, p.player_id, p.player_name, pl.team, p.role,
                           p.participant_id, p.price, pl.active, pl.mantra_roles
                    FROM purchase p
                    JOIN player pl ON pl.external_id = p.player_id
                    WHERE p.auction_id = :auction_id AND p.cancelled = FALSE
                    ORDER BY CASE p.role
                               WHEN 'P' THEN 1 WHEN 'D' THEN 2 WHEN 'C' THEN 3 ELSE 4
                             END,
                             p.player_name COLLATE NOCASE
                """),
                {"auction_id": auction_id},
            ).mappings()
        )
        slot_totals = {
            "P": auction["goalkeeper_slots"],
            "D": auction["defender_slots"],
            "C": auction["midfielder_slots"],
            "A": auction["forward_slots"],
        }
        total_slots = sum(slot_totals.values())
        purchases_by_participant: dict[str, list[dict]] = {
            participant["uuid"]: [] for participant in participants
        }
        for purchase in purchases:
            purchases_by_participant[purchase["participant_id"]].append(
                {
                    "id": purchase["uuid"],
                    "player_id": purchase["player_id"],
                    "player_name": purchase["player_name"],
                    "team": purchase["team"],
                    "role": purchase["role"],
                    "price": purchase["price"],
                    "player_active": bool(purchase["active"]),
                    "mantra_roles": split_mantra_roles(purchase["mantra_roles"]),
                }
            )
        participant_views = []
        for participant in participants:
            credits_remaining = auction["initial_credits"] - participant["spent"]
            slots_remaining = total_slots - participant["filled_total"]
            maximum_bid = credits_remaining - (slots_remaining - 1) if slots_remaining > 0 else 0
            participant_views.append(
                {
                    "id": participant["uuid"],
                    "name": participant["name"],
                    "position": participant["position"],
                    "credits_remaining": credits_remaining,
                    "maximum_bid": maximum_bid,
                    "slots": {
                        "P": {
                            "filled": participant["filled_goalkeepers"],
                            "total": slot_totals["P"],
                        },
                        "D": {
                            "filled": participant["filled_defenders"],
                            "total": slot_totals["D"],
                        },
                        "C": {
                            "filled": participant["filled_midfielders"],
                            "total": slot_totals["C"],
                        },
                        "A": {
                            "filled": participant["filled_forwards"],
                            "total": slot_totals["A"],
                        },
                    },
                    "purchases": purchases_by_participant[participant["uuid"]],
                }
            )
        return {
            "id": auction["uuid"],
            "name": auction["name"],
            "status": auction["status"],
            "initial_credits": auction["initial_credits"],
            "strategy_id": auction["strategy_id"],
            "slot_totals": slot_totals,
            "participants": participant_views,
            "purchased_player_ids": [purchase["player_id"] for purchase in purchases],
        }

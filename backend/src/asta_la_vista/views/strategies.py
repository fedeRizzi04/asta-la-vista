from sqlalchemy import text

from asta_la_vista.exceptions import NotFoundError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def strategy_list(uow: AbstractUnitOfWork) -> list[dict]:
    with uow:
        rows = uow.session.execute(
            text("""
                SELECT s.uuid, s.name, COUNT(DISTINCT t.uuid) AS tier_count,
                       COUNT(DISTINCT e.player_id) AS assigned_player_count
                FROM strategy s
                LEFT JOIN tier t ON t.strategy_id = s.uuid
                LEFT JOIN strategy_entry e ON e.strategy_id = s.uuid AND e.tier_id IS NOT NULL
                GROUP BY s.uuid, s.name
                ORDER BY s.name COLLATE NOCASE
            """)
        ).mappings()
        return [
            {
                "id": row["uuid"],
                "name": row["name"],
                "tier_count": row["tier_count"],
                "assigned_player_count": row["assigned_player_count"],
            }
            for row in rows
        ]


def strategy_detail(uow: AbstractUnitOfWork, strategy_id: str) -> dict:
    with uow:
        strategy = (
            uow.session.execute(
                text("SELECT uuid, name FROM strategy WHERE uuid = :strategy_id"),
                {"strategy_id": strategy_id},
            )
            .mappings()
            .one_or_none()
        )
        if strategy is None:
            raise NotFoundError("Strategy not found")
        tiers = uow.session.execute(
            text("""
                SELECT uuid, name, position, color
                FROM tier
                WHERE strategy_id = :strategy_id
                ORDER BY position
            """),
            {"strategy_id": strategy_id},
        ).mappings()
        entries = uow.session.execute(
            text("""
                SELECT e.player_id, p.name, p.team, e.role, p.active, e.tier_id, e.note,
                       e.maximum_price_percentage
                FROM strategy_entry e
                JOIN player p ON p.external_id = e.player_id
                WHERE e.strategy_id = :strategy_id
                ORDER BY p.name COLLATE NOCASE
            """),
            {"strategy_id": strategy_id},
        ).mappings()
        return {
            "id": strategy["uuid"],
            "name": strategy["name"],
            "tiers": [
                {
                    "id": row["uuid"],
                    "name": row["name"],
                    "position": row["position"],
                    "color": row["color"],
                }
                for row in tiers
            ],
            "entries": [
                {
                    **dict(row),
                    "active": bool(row["active"]),
                }
                for row in entries
            ],
        }

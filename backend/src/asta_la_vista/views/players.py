from sqlalchemy import text

from asta_la_vista.domain.model import Role
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def player_list(
    uow: AbstractUnitOfWork,
    role: Role | None = None,
    search: str | None = None,
    active: bool | None = True,
) -> list[dict]:
    conditions: list[str] = []
    parameters: dict[str, object] = {}
    if role is not None:
        conditions.append("role = :role")
        parameters["role"] = role.value
    if search:
        conditions.append("(LOWER(name) LIKE :search OR LOWER(team) LIKE :search)")
        parameters["search"] = f"%{search.strip().lower()}%"
    if active is not None:
        conditions.append("active = :active")
        parameters["active"] = active
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with uow:
        rows = uow.session.execute(
            text(f"""
                SELECT external_id, name, team, role, quotation, active
                FROM player
                {where}
                ORDER BY CASE role WHEN 'P' THEN 1 WHEN 'D' THEN 2 WHEN 'C' THEN 3 ELSE 4 END,
                         name COLLATE NOCASE
            """),
            parameters,
        ).mappings()
        return [
            {
                "id": row["external_id"],
                "name": row["name"],
                "team": row["team"],
                "role": row["role"],
                "quotation": row["quotation"],
                "active": bool(row["active"]),
            }
            for row in rows
        ]


def player_counts(uow: AbstractUnitOfWork) -> dict[str, int]:
    with uow:
        rows = uow.session.execute(
            text("""
                SELECT role, COUNT(*) AS total
                FROM player
                WHERE active = TRUE
                GROUP BY role
            """)
        ).mappings()
        counts = {role.value: 0 for role in Role}
        counts.update({row["role"]: row["total"] for row in rows})
        return counts

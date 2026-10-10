from asta_la_vista.domain import commands, model
from asta_la_vista.exceptions import ConfirmationRequiredError, ValidationError
from asta_la_vista.service_layer.unit_of_work import AbstractUnitOfWork


def import_players(cmd: commands.ImportPlayers, uow: AbstractUnitOfWork) -> dict[str, int]:
    if not cmd.players:
        raise ValidationError("The player list is empty")
    incoming_ids = [row.external_id for row in cmd.players]
    if len(incoming_ids) != len(set(incoming_ids)):
        raise ValidationError("The player list contains duplicate ids")
    with uow:
        if uow.auctions.has_live() and not cmd.allow_live_auction:
            raise ConfirmationRequiredError("A live auction requires explicit import confirmation")
        existing = {player.external_id: player for player in uow.players.list_all()}
        added = updated = deactivated = role_changes = 0
        for row in cmd.players:
            try:
                role = model.Role(row.role)
            except ValueError as exc:
                raise ValidationError(f"Unsupported Classic role: {row.role}") from exc
            player = existing.get(row.external_id)
            if player is None:
                uow.players.add(
                    model.Player(
                        row.external_id,
                        row.name,
                        row.team,
                        role,
                        row.quotation,
                        row.mantra_roles or (),
                    )
                )
                added += 1
                continue
            changed = (
                player.name,
                player.team,
                player.role,
                player.quotation,
                player.mantra_roles,
                player.active,
            ) != (
                row.name.strip(),
                row.team.strip(),
                role,
                row.quotation,
                row.mantra_roles if row.mantra_roles is not None else player.mantra_roles,
                True,
            )
            previous_role = player.role
            player.update(row.name, row.team, role, row.quotation, row.mantra_roles)
            updated += changed
            if previous_role != role:
                role_changes += 1
                for strategy in uow.strategies.list_containing_player(player.external_id):
                    strategy.change_player_role(player.external_id, role)
        incoming = set(incoming_ids)
        for player_id, player in existing.items():
            if player_id not in incoming and player.active:
                player.deactivate()
                deactivated += 1
        uow.commit()
    return {
        "added": added,
        "updated": updated,
        "deactivated": deactivated,
        "role_changes": role_changes,
    }

from abc import ABC, abstractmethod
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from asta_la_vista.domain import model


class AbstractAuctionRepository(ABC):
    @abstractmethod
    def add(self, auction: model.Auction): ...

    @abstractmethod
    def get(self, uuid: str) -> model.Auction | None: ...

    @abstractmethod
    def has_live(self) -> bool: ...


class AbstractPlayerRepository(ABC):
    @abstractmethod
    def add(self, player: model.Player): ...

    @abstractmethod
    def get(self, external_id: str) -> model.Player | None: ...

    @abstractmethod
    def list_all(self) -> list[model.Player]: ...


class AbstractStrategyRepository(ABC):
    @abstractmethod
    def add(self, strategy: model.Strategy): ...

    @abstractmethod
    def remove(self, strategy: model.Strategy): ...

    @abstractmethod
    def get(self, uuid: str) -> model.Strategy | None: ...

    @abstractmethod
    def list_containing_player(self, player_id: str) -> list[model.Strategy]: ...


class AuctionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, auction: model.Auction):
        self.session.add(auction)

    def get(self, uuid: str) -> model.Auction | None:
        return self.session.get(model.Auction, uuid)

    def has_live(self) -> bool:
        statement = select(model.Auction.uuid).where(
            model.Auction.status == model.AuctionStatus.LIVE
        )
        return self.session.scalar(statement) is not None


class PlayerRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, player: model.Player):
        self.session.add(player)

    def get(self, external_id: str) -> model.Player | None:
        return self.session.get(model.Player, external_id)

    def list_all(self) -> list[model.Player]:
        return list(self.session.scalars(select(model.Player)))


class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, strategy: model.Strategy):
        self.session.add(strategy)

    def remove(self, strategy: model.Strategy):
        self.session.delete(strategy)

    def get(self, uuid: str) -> model.Strategy | None:
        return self.session.get(model.Strategy, uuid)

    def list_containing_player(self, player_id: str) -> list[model.Strategy]:
        statement = (
            select(model.Strategy)
            .join(model.StrategyEntry)
            .where(model.StrategyEntry.player_id == player_id)
        )
        return list(self.session.scalars(statement).unique())


class TrackingAuctionRepository:
    def __init__(self, repository: AbstractAuctionRepository):
        self._repository = repository
        self.seen: set[model.Auction] = set()

    def add(self, auction: model.Auction):
        self._repository.add(auction)
        self.seen.add(auction)

    def get(self, uuid: str) -> model.Auction | None:
        return self._track(self._repository.get(uuid))

    def has_live(self) -> bool:
        return self._repository.has_live()

    def _track(self, auction: model.Auction | None) -> model.Auction | None:
        if auction is not None:
            self.seen.add(auction)
        return auction


class TrackingPlayerRepository:
    def __init__(self, repository: AbstractPlayerRepository):
        self._repository = repository
        self.seen: set[model.Player] = set()

    def add(self, player: model.Player):
        self._repository.add(player)
        self.seen.add(player)

    def get(self, external_id: str) -> model.Player | None:
        return self._track(self._repository.get(external_id))

    def list_all(self) -> list[model.Player]:
        return list(self._track_many(self._repository.list_all()))

    def _track(self, player: model.Player | None) -> model.Player | None:
        if player is not None:
            self.seen.add(player)
        return player

    def _track_many(self, players: Iterable[model.Player]) -> Iterable[model.Player]:
        for player in players:
            self.seen.add(player)
            yield player


class TrackingStrategyRepository:
    def __init__(self, repository: AbstractStrategyRepository):
        self._repository = repository
        self.seen: set[model.Strategy] = set()

    def add(self, strategy: model.Strategy):
        self._repository.add(strategy)
        self.seen.add(strategy)

    def remove(self, strategy: model.Strategy):
        self._repository.remove(strategy)
        self.seen.discard(strategy)

    def get(self, uuid: str) -> model.Strategy | None:
        return self._track(self._repository.get(uuid))

    def list_containing_player(self, player_id: str) -> list[model.Strategy]:
        strategies = self._repository.list_containing_player(player_id)
        self.seen.update(strategies)
        return strategies

    def _track(self, strategy: model.Strategy | None) -> model.Strategy | None:
        if strategy is not None:
            self.seen.add(strategy)
        return strategy

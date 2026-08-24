from abc import ABC, abstractmethod
from collections.abc import Iterator

from sqlalchemy.orm import Session, sessionmaker

from asta_la_vista.adapters import repository
from asta_la_vista.domain import events


class AbstractUnitOfWork(ABC):
    session: Session
    auctions: repository.AbstractAuctionRepository
    players: repository.AbstractPlayerRepository
    strategies: repository.AbstractStrategyRepository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.rollback()

    def commit(self):
        self._commit()

    def collect_new_events(self) -> Iterator[events.Event]:
        repositories = (self.auctions, self.players, self.strategies)
        for tracked_repository in repositories:
            for aggregate in tracked_repository.seen:
                while aggregate.events:
                    yield aggregate.events.popleft()

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.auctions = repository.TrackingAuctionRepository(
            repository.AuctionRepository(self.session)
        )
        self.players = repository.TrackingPlayerRepository(
            repository.PlayerRepository(self.session)
        )
        self.strategies = repository.TrackingStrategyRepository(
            repository.StrategyRepository(self.session)
        )
        return super().__enter__()

    def __exit__(self, exc_type, exc, traceback):
        super().__exit__(exc_type, exc, traceback)
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

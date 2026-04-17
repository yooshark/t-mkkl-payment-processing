from typing import Annotated, Any, Self, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
)

from src.infra.postgres.pg import async_session_factory
from src.infra.postgres.storage.payment import PaymentStorage
from src.infra.postgres.storage.payment_outbox import PaymentOutboxStorage

TExc = TypeVar("TExc", bound=BaseException)


class TransactionManager:
    session: AsyncSession
    session_factory: async_sessionmaker[AsyncSession]
    transaction: AsyncSessionTransaction
    payment: PaymentStorage
    payment_outbox: PaymentOutboxStorage

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()
        self.payment = PaymentStorage(self.session)
        self.payment_outbox = PaymentOutboxStorage(self.session)
        self.transaction: AsyncSessionTransaction = await self.session.begin()
        return self

    async def __aexit__(self, exc_type: type[TExc] | None, exc: TExc | None, traceback: Any | None) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.transaction.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.transaction.commit()


async def get_tr_manager() -> TransactionManager:
    return TransactionManager(async_session_factory)


PostgresTrManagerDep = Annotated[TransactionManager, Depends(get_tr_manager)]

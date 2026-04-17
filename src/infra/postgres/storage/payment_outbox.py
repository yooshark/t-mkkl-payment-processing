from datetime import UTC, datetime

from sqlalchemy import select

from src.infra.postgres.models.payment_outbox import PaymentOutbox
from src.infra.postgres.storage.base_storage import PostgresStorage
from src.main.enums import OutboxStatus


class PaymentOutboxStorage(PostgresStorage[PaymentOutbox]):
    async def create_event(self, event: PaymentOutbox) -> PaymentOutbox:
        self._db.add(event)
        await self._db.flush()
        await self._db.refresh(event)
        return event

    async def get_pending(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        created_before: datetime | None = None,
    ) -> list[PaymentOutbox]:
        query = (
            select(PaymentOutbox)
            .where(PaymentOutbox.status == OutboxStatus.PENDING)
            .order_by(PaymentOutbox.created_at)
            .offset(offset)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        if created_before is not None:
            query = query.where(PaymentOutbox.created_at < created_before)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def mark_sent(self, event_id: int) -> None:
        event = await self._get_by_id(event_id)
        if event:
            event.status = OutboxStatus.SENT
            event.sent_at = datetime.now(UTC)
            await self._db.flush()

    async def increment_attempts(self, event_id: int, max_attempts: int) -> PaymentOutbox | None:
        event = await self._get_by_id(event_id)
        if event is None:
            return None
        event.retry_count += 1
        if event.retry_count >= max_attempts:
            event.status = OutboxStatus.FAILED
        await self._db.flush()
        return event

    async def _get_by_id(self, event_id: int) -> PaymentOutbox | None:
        result = await self._db.execute(select(PaymentOutbox).where(PaymentOutbox.id == event_id))
        return result.scalar_one_or_none()

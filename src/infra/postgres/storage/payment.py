from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from src.infra.postgres.models.payment import Payment
from src.infra.postgres.storage.base_storage import PostgresStorage
from src.main.enums import PaymentStatus


class PaymentStorage(PostgresStorage[Payment]):
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self._db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        result = await self._db.execute(select(Payment).where(Payment.idempotency_key == key))
        return result.scalar_one_or_none()

    async def create(self, payment: Payment) -> Payment:
        self._db.add(payment)
        await self._db.flush()
        await self._db.refresh(payment)
        return payment

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
    ) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if payment is None:
            return None
        payment.status = status
        if status in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED):
            payment.processed_at = datetime.now(UTC)
        await self._db.flush()
        return payment

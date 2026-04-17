import logging
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends

from src.infra.postgres.models import Payment, PaymentOutbox
from src.infra.postgres.transaction_manager import PostgresTrManagerDep
from src.main.enums import OutboxStatus, PaymentStatus
from src.modules.base.controller import BaseController
from src.modules.payments.schemas import PaymentCreate, PaymentResponse

logger = logging.getLogger("app")


class PaymentController(BaseController):
    async def get_payment_details(self, payment_id: UUID) -> Payment | None:
        async with self.tr_manager as mng:
            return await mng.payment.get_by_id(payment_id)

    async def create_payment(self, data: PaymentCreate, idempotency_key: str) -> PaymentResponse:
        async with self.tr_manager as mng:
            existing = await mng.payment.get_by_idempotency_key(idempotency_key)
            if existing:
                return PaymentResponse(
                    payment_id=existing.id,
                    status=existing.status,
                    created_at=existing.created_at,
                )

            payment = Payment(
                id=uuid4(),
                amount=data.amount,
                currency=data.currency,
                description=data.description,
                payment_metadata=data.payment_metadata,
                status=PaymentStatus.PENDING,
                idempotency_key=idempotency_key,
                webhook_url=str(data.webhook_url) if data.webhook_url else None,
            )

            payment = await mng.payment.create(payment)

            outbox_event = PaymentOutbox(
                event_type="payment.created",
                payload={
                    "payment_id": str(payment.id),
                    "amount": str(payment.amount),
                    "currency": payment.currency.value,
                    "webhook_url": payment.webhook_url,
                    "created_at": payment.created_at.isoformat(),
                },
                status=OutboxStatus.PENDING,
                retry_count=0,
            )
            await mng.payment_outbox.create_event(outbox_event)

        response = PaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )
        logger.info(f"Payment created: id={payment.id} key={idempotency_key}")
        return response


async def get_controller(tr_manager: PostgresTrManagerDep) -> AsyncIterator[PaymentController]:
    yield PaymentController(tr_manager=tr_manager)


PaymentControllerDep = Annotated[PaymentController, Depends(get_controller)]

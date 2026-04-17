import asyncio
import logging
import random
from uuid import UUID

from faststream import FastStream
from faststream.middlewares.acknowledgement.config import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitMessage, RabbitRouter

from src.infra.postgres.pg import async_session_factory
from src.infra.postgres.transaction_manager import TransactionManager
from src.main.app_config import AppSettings, get_settings
from src.main.broker import (
    broker_factory,
    dlq_exchange,
    payments_dead_queue,
    payments_exchange,
    payments_new_queue,
    payments_retry_exchange,
    payments_retry_queue,
)
from src.main.enums import PaymentStatus
from src.modules.payments.schemas import PaymentCreatedEvent
from src.workers.webhook import WebhookDeliveryError, send_webhook

logger = logging.getLogger("app")

router = RabbitRouter()

_MAX_RETRIES = 3
_broker: RabbitBroker | None = None


def set_broker(broker: RabbitBroker) -> None:
    global _broker
    _broker = broker


@router.subscriber(payments_new_queue, payments_exchange, ack_policy=AckPolicy.MANUAL)
async def handle_payment(event: PaymentCreatedEvent, msg: RabbitMessage) -> None:
    payment_id = UUID(event.payment_id)

    x_death: list[dict] = msg.headers.get("x-death", [])
    retry_count: int = sum(int(d.get("count", 0)) for d in x_death if d.get("queue") == "payments.new")

    logger.info(f"Received payment id={payment_id} (delivery {retry_count + 1}/{_MAX_RETRIES})")

    if retry_count >= _MAX_RETRIES:
        logger.error(f"Payment id={payment_id} exhausted {_MAX_RETRIES} retries — routing to DLQ")
        if _broker is None:
            raise RuntimeError("broker not initialised")
        await _broker.publish(event, queue=payments_dead_queue, exchange=dlq_exchange)
        await msg.ack()
        return

    try:
        await _process_payment(event, payment_id)
        await msg.ack()
    except Exception as exc:
        remaining = _MAX_RETRIES - retry_count - 1
        logger.warning(
            f"Payment id={payment_id} failed"
            f" (attempt {retry_count + 1}/{_MAX_RETRIES}): {exc}."
            + (" Scheduling retry in 10 s." if remaining > 0 else " Final attempt."),
        )
        await msg.nack(requeue=False)


async def _process_payment(event: PaymentCreatedEvent, payment_id: UUID) -> None:
    logger.info(f"Processing payment id={payment_id}")

    await asyncio.sleep(random.uniform(2, 5))  # noqa: S311
    success = random.random() < 0.9  # noqa: S311
    new_status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
    logger.info(f"Payment id={payment_id} → {new_status.value}")

    async with TransactionManager(async_session_factory) as tr:
        await tr.payment.update_status(payment_id, new_status)

    if event.webhook_url:
        payload = {
            "payment_id": event.payment_id,
            "status": new_status.value,
        }
        try:
            await send_webhook(event.webhook_url, payload)
        except WebhookDeliveryError as exc:
            logger.error(f"Webhook delivery failed for payment id={payment_id}: {exc}")


async def main() -> None:
    broker = broker_factory(get_settings(AppSettings))
    broker.include_router(router)
    set_broker(broker)
    app = FastStream(broker)

    @app.after_startup
    async def declare_retry_topology() -> None:
        retry_ex = await broker.declare_exchange(payments_retry_exchange)
        retry_q = await broker.declare_queue(payments_retry_queue)
        await retry_q.bind(retry_ex, routing_key="payments.retry")

        dlq_ex = await broker.declare_exchange(dlq_exchange)
        dead_q = await broker.declare_queue(payments_dead_queue)
        await dead_q.bind(dlq_ex, routing_key="payments.dead")

        logger.info("Retry topology declared")

    logger.info("Consumer starting…")
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

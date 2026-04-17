import asyncio
import logging

from faststream.rabbit import RabbitBroker

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
from src.main.enums import OutboxStatus

logger = logging.getLogger("app")


async def process_outbox_once(broker: RabbitBroker) -> int:
    processed = 0

    async with TransactionManager(async_session_factory) as tr:
        events = await tr.payment_outbox.get_pending(limit=100)

        for event in events:
            try:
                await broker.publish(
                    event.payload,
                    queue=payments_new_queue,
                    exchange=payments_exchange,
                )
                await tr.payment_outbox.mark_sent(event.id)
                logger.info(
                    f"Outbox event published: id={event.id} type={event.event_type}"
                    f" payment_id={event.payload.get('payment_id')}",
                )
                processed += 1
            except Exception as exc:
                updated = await tr.payment_outbox.increment_attempts(
                    event.id,
                    get_settings(AppSettings).outbox.MAX_ATTEMPTS,
                )
                if updated and updated.status == OutboxStatus.FAILED:
                    logger.error(
                        f"Outbox event permanently failed: id={event.id} attempts={updated.retry_count} error={exc}",
                    )
                else:
                    attempts = updated.retry_count if updated else "?"
                    logger.warning(f"Outbox publish error (attempt {attempts}): id={event.id} error={exc}")

    return processed


async def main() -> None:
    settings = get_settings(AppSettings)
    broker = broker_factory(settings)
    await broker.connect()

    payments_ex = await broker.declare_exchange(payments_exchange)
    retry_ex = await broker.declare_exchange(payments_retry_exchange)
    dlq_ex = await broker.declare_exchange(dlq_exchange)

    new_q = await broker.declare_queue(payments_new_queue)
    retry_q = await broker.declare_queue(payments_retry_queue)
    dead_q = await broker.declare_queue(payments_dead_queue)

    await new_q.bind(payments_ex, routing_key="payments.new")
    await retry_q.bind(retry_ex, routing_key="payments.retry")
    await dead_q.bind(dlq_ex, routing_key="payments.dead")

    logger.info(f"Outbox processor started (poll_interval={settings.outbox.POLL_INTERVAL}s)")

    try:
        while True:
            try:
                count = await process_outbox_once(broker)
                if count:
                    logger.info(f"Outbox: {count} event(s) published")
            except Exception as exc:
                logger.error(f"Outbox processor error: {exc}", exc_info=True)
            await asyncio.sleep(settings.outbox.POLL_INTERVAL)
    finally:
        await broker.stop()


if __name__ == "__main__":
    asyncio.run(main())

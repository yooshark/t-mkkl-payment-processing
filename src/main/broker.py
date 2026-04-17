from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from faststream.rabbit.schemas import ExchangeType

from src.main.app_config import AppSettings

payments_exchange = RabbitExchange(
    "payments",
    type=ExchangeType.DIRECT,
    durable=True,
)

payments_retry_exchange = RabbitExchange(
    "payments.retry",
    type=ExchangeType.DIRECT,
    durable=True,
)

dlq_exchange = RabbitExchange(
    "payments.dlq",
    type=ExchangeType.DIRECT,
    durable=True,
)

payments_new_queue = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.retry",
        "x-dead-letter-routing-key": "payments.retry",
    },
)

payments_retry_queue = RabbitQueue(
    "payments.retry",
    durable=True,
    arguments={
        "x-message-ttl": 10000,
        "x-dead-letter-exchange": "payments",
        "x-dead-letter-routing-key": "payments.new",
    },
)

payments_dead_queue = RabbitQueue(
    "payments.dead",
    durable=True,
)


def broker_factory(settings: AppSettings) -> RabbitBroker:
    return RabbitBroker(settings.RABBITMQ_URL)

from datetime import datetime

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.postgres.models.base import Base, IntIdMixin
from src.main.enums import OutboxStatus


class PaymentOutbox(Base, IntIdMixin):
    __tablename__ = "payment_outbox"

    event_type: Mapped[str] = mapped_column(
        String(255),
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
    )

    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(
            OutboxStatus,
            name="payment_outbox_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(server_default="0")

    sent_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

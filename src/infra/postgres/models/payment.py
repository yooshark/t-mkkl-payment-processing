from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.postgres.models.base import Base, UUIDMixin
from src.main.enums import Currency, PaymentStatus


class Payment(Base, UUIDMixin):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
    )

    currency: Mapped[Currency] = mapped_column(
        SQLEnum(
            Currency,
            name="payment_currency",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        nullable=True,
    )

    payment_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
    )

    webhook_url: Mapped[str]

    processed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

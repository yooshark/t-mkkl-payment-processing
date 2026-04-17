from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from src.main.enums import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Payment amount")
    currency: Currency
    description: str | None = Field(default=None, max_length=500)
    payment_metadata: dict[str, Any] | None = Field(default=None, description="Arbitrary JSON metadata")
    webhook_url: HttpUrl | None = Field(default=None, description="URL to send status notification")


class PaymentResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentDetail(BaseModel):
    id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    payment_metadata: dict[str, Any] | None = Field(default=None)
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaymentCreatedEvent(BaseModel):
    payment_id: str
    amount: Decimal
    currency: Currency
    webhook_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

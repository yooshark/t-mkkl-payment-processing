from datetime import datetime
from uuid import UUID

from sqlalchemy import UUID as PGUUID
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class IntIdMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __mapper_args__ = {"eager_defaults": True}

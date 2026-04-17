from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from starlette import status

from src.modules.payments.controller import PaymentControllerDep
from src.modules.payments.schemas import PaymentCreate, PaymentDetail, PaymentResponse

router = APIRouter(prefix="/payments")


@router.get("/{payment_id}")
async def get(payment_id: UUID, controller: PaymentControllerDep) -> PaymentDetail:
    payment = await controller.get_payment_details(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not found")
    return PaymentDetail.model_validate(payment)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post(
    body: PaymentCreate,
    controller: PaymentControllerDep,
    idempotency_key: Annotated[str, Header(...)],
) -> PaymentResponse:
    return await controller.create_payment(body, idempotency_key)

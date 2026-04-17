from fastapi import APIRouter

from src.modules.payments.router import router as payment_router
from src.modules.utils.router import router as utils_router

router = APIRouter(prefix="/api")
router.include_router(
    utils_router,
)
router.include_router(
    payment_router,
)

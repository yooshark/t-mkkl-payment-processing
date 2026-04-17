import asyncio
import logging
from typing import Any

import httpx

from src.main.app_config import AppSettings, get_settings

logger = logging.getLogger(__name__)


class WebhookDeliveryError(RuntimeError):
    pass


async def send_webhook(url: str, payload: dict[str, Any]) -> None:
    settings = get_settings(AppSettings)
    last_exc: Exception | None = None

    async with httpx.AsyncClient(timeout=settings.webhook.TIMEOUT) as client:
        for attempt in range(settings.webhook.RETRY_ATTEMPTS):
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info(f"Webhook delivered on attempt {attempt + 1}: {url}")
                return
            except httpx.HTTPError as exc:
                last_exc = exc
                delay = settings.webhook.RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    f"Webhook attempt {attempt + 1}/{settings.webhook.RETRY_ATTEMPTS} failed"
                    f" ({exc}). Retrying in {delay:.1f}s…",
                )
                if attempt < settings.webhook.RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(delay)

    raise WebhookDeliveryError(
        f"Failed to deliver webhook to {url} after {settings.webhook.RETRY_ATTEMPTS} attempts",
    ) from last_exc

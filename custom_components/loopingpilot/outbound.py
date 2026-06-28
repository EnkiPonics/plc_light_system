# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Outbound feed sender for LoopingPilot."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def post_feed(
    session: aiohttp.ClientSession,
    endpoint_url: str,
    api_key: str,
    payload: dict[str, Any],
) -> str:
    """Sendet den Loop-Feed-Payload per HTTP POST.

    Gibt die receipt_id aus der Antwort zurück.
    Raises: aiohttp.ClientError, asyncio.TimeoutError, ValueError
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with session.post(
        endpoint_url,
        json=payload,
        headers=headers,
        timeout=_TIMEOUT,
    ) as response:
        response.raise_for_status()
        data: dict = await response.json()

    receipt_id: str | None = data.get("receipt_id")
    if not receipt_id:
        raise ValueError(f"Kein receipt_id in Antwort: {data}")
    return receipt_id

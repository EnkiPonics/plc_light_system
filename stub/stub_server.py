# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""LoopingPilot Stub-Endpoint (FastAPI).

Startet einen minimalen HTTP-Server, der Loop-Feed-Payloads entgegennimmt
und eine Receipt-ID zurückgibt. Dient als Platzhalter für LoopingPilot.

Verwendung:
    pip install fastapi uvicorn
    uvicorn stub_server:app --host 0.0.0.0 --port 8765 --reload
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status

app = FastAPI(title="LoopingPilot Stub", version="0.2.0")
logger = logging.getLogger("loopingpilot_stub")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")


@app.post("/api/v1/feed/loop", status_code=status.HTTP_200_OK)
async def receive_loop_feed(request: Request) -> dict:
    """Nimmt ein Loop-Feed-Payload entgegen und bestätigt den Empfang.

    Erwartetes Payload-Format::

        {
            "loop_name": str,
            "sent_at": ISO-8601,
            "lookback_seconds": int,
            "components": [
                {
                    "id": str,
                    "name": str,
                    "type": "fish_tank" | "plant_bed" | "greenhouse",
                    "measurements": {
                        "<rolle>": [{"ts": float, "value": str}, ...]
                    }
                }
            ]
        }
    """
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Ungültiges JSON") from exc

    receipt_id = str(uuid.uuid4())
    loop_name: str = payload.get("loop_name", "unbekannt")
    components: list = payload.get("components", [])

    total_points = sum(
        len(pts)
        for comp in components
        for pts in comp.get("measurements", {}).values()
    )
    summary = {
        comp.get("name", comp.get("id", "?")): sum(
            len(pts) for pts in comp.get("measurements", {}).values()
        )
        for comp in components
    }

    logger.info(
        "RECEIPT %s | Loop: %s | Komponenten: %d | Messpunkte gesamt: %d | %s",
        receipt_id,
        loop_name,
        len(components),
        total_points,
        summary,
    )

    return {
        "status": "received",
        "receipt_id": receipt_id,
        "loop_name": loop_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health() -> dict:
    """Einfacher Health-Check."""
    return {"status": "ok"}

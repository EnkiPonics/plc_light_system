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

app = FastAPI(title="LoopingPilot Stub", version="0.1.0")
logger = logging.getLogger("loopingpilot_stub")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")


@app.post("/api/v1/feed/loop", status_code=status.HTTP_200_OK)
async def receive_loop_feed(request: Request) -> dict:
    """Nimmt ein Loop-Feed-Payload entgegen und bestätigt den Empfang."""
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Ungültiges JSON") from exc

    receipt_id = str(uuid.uuid4())
    loop_id = payload.get("loop_id", "unbekannt")
    series = payload.get("series", {})
    punkt_zusammenfassung = {rolle: len(s.get("points", [])) for rolle, s in series.items()}

    logger.info(
        "RECEIPT %s | Loop: %s | Serien: %s",
        receipt_id,
        loop_id,
        punkt_zusammenfassung,
    )

    return {
        "status": "received",
        "receipt_id": receipt_id,
        "loop_id": loop_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health() -> dict:
    """Einfacher Health-Check."""
    return {"status": "ok"}

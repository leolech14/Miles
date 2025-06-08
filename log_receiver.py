#!/usr/bin/env python3
"""Log receiver webhook server for CI pipeline logs."""

import json
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class LogPayload(BaseModel):
    run_id: str
    step: str
    log: str


app = FastAPI(title="CI Log Receiver", version="1.0.0")


@app.post("/")
async def receive_log(payload: LogPayload) -> Dict[str, str]:
    """Receive and store CI step logs."""
    try:
        # Print one-line summary
        log_preview = (
            payload.log[:100] + "..." if len(payload.log) > 100 else payload.log
        )
        print(f"[{payload.run_id}] {payload.step}: {log_preview}")

        # Ensure logs directory exists
        logs_dir = Path("received_logs")
        logs_dir.mkdir(exist_ok=True)

        # Append to NDJSON file
        log_file = logs_dir / f"{payload.run_id}.ndjson"
        with open(log_file, "a", encoding="utf-8") as f:
            json.dump(payload.dict(), f)
            f.write("\n")

        return {"status": "received", "run_id": payload.run_id, "step": payload.step}

    except Exception as e:
        print(f"Error processing log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting CI Log Receiver on port 5051...")
    print("Use Ctrl+C for graceful shutdown")

    uvicorn.run(app, host="0.0.0.0", port=5051, log_level="info", access_log=True)

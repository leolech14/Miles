#!/usr/bin/env python3
"""Log receiver webhook server for CI pipeline logs."""

import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class LogPayload(BaseModel):
    run_id: str
    step: str
    log: str


app = FastAPI(title="CI Log Receiver", version="1.0.0")


@app.post("/")
async def receive_log(payload: LogPayload) -> dict[str, str]:
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
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting CI Log Receiver on port 5051...")
    print("Use Ctrl+C for graceful shutdown")

    uvicorn.run(
        app, host="127.0.0.1", port=5051, log_level="info", access_log=True
    )  # Bind to localhost only

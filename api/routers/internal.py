"""
Internal trigger endpoints — called by an external cron service (e.g. cron-job.org)
to run the daily and weekly monitoring jobs on schedule.

Protect these with the INTERNAL_SECRET env var to prevent unauthorised triggering.
"""

import os
import traceback
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Annotated

router = APIRouter()

_SECRET = os.getenv("INTERNAL_SECRET", "")


def _check_secret(x_internal_secret: str | None):
    if not _SECRET:
        return
    if x_internal_secret != _SECRET:
        raise HTTPException(status_code=401, detail="Unauthorised")


@router.post("/run/daily")
def trigger_daily(x_internal_secret: Annotated[str | None, Header()] = None):
    _check_secret(x_internal_secret)
    try:
        from scheduler.runner import daily_job
        daily_job()
        return {"status": "ok", "job": "daily"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})


@router.post("/run/weekly")
def trigger_weekly(x_internal_secret: Annotated[str | None, Header()] = None):
    _check_secret(x_internal_secret)
    try:
        from scheduler.runner import weekly_job
        weekly_job()
        return {"status": "ok", "job": "weekly"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

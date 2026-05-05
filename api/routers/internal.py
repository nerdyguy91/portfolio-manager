"""
Internal trigger endpoints — called by an external cron service (e.g. cron-job.org)
to run the daily and weekly monitoring jobs on schedule.

Protect these with the INTERNAL_SECRET env var to prevent unauthorised triggering.
"""

import os
from fastapi import APIRouter, HTTPException, Header
from typing import Annotated

from scheduler.runner import daily_job, weekly_job

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
    daily_job()
    return {"status": "ok", "job": "daily"}


@router.post("/run/weekly")
def trigger_weekly(x_internal_secret: Annotated[str | None, Header()] = None):
    _check_secret(x_internal_secret)
    weekly_job()
    return {"status": "ok", "job": "weekly"}

"""
FastAPI application entry point.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import portfolio, alerts, market, macro
from tools.db import init_db

init_db()

app = FastAPI(title="Portfolio Monitor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(alerts.router,    prefix="/alerts",    tags=["alerts"])
app.include_router(market.router,    prefix="/market",    tags=["market"])
app.include_router(macro.router,     prefix="/macro",     tags=["macro"])


@app.get("/risk-score")
def get_risk_score():
    from tools.risk_score import compute_risk_score
    score = compute_risk_score()
    return {"risk_score": score}


@app.get("/regime")
def get_regime():
    from tools.rules.regime_classifier import run
    return run()


@app.get("/health")
def health():
    return {"status": "ok"}

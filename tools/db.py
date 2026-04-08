"""
SQLAlchemy models and CRUD helpers for the portfolio monitoring system.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, Boolean,
    DateTime, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/portfolio.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Portfolio(Base):
    __tablename__ = "portfolio"
    ticker = Column(String, primary_key=True)
    shares = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=True)
    sector = Column(String, nullable=True)
    sector_avg_yield = Column(Float, nullable=True)  # manual input for yield spike check


class MarketData(Base):
    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)       # individual stock or '^FTSE' or '^VIX'
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    __table_args__ = (UniqueConstraint("ticker", "timestamp"),)


class FinancialData(Base):
    __tablename__ = "financial_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False)
    eps = Column(Float, nullable=True)
    dividend_per_share = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    dividend_history = Column(Text, nullable=True)  # JSON array string
    timestamp = Column(DateTime, nullable=False)


class MacroData(Base):
    __tablename__ = "macro_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator = Column(String, nullable=False)  # us_2y_yield / us_10y_yield / uk_10y_gilt / commodity_index
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    __table_args__ = (UniqueConstraint("indicator", "timestamp"),)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)   # Critical / High / Medium / Low
    asset = Column(String, nullable=True)        # ticker, index, macro indicator, or None
    message = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)    # JSON from explanation engine
    needs_review = Column(Boolean, default=False)
    suppressed = Column(Boolean, default=False)
    suppressed_until = Column(DateTime, nullable=True)
    risk_score = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False)


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    suggested_allocation_change = Column(String, nullable=True)
    direction = Column(String, nullable=True)    # increase / decrease / rotate
    timestamp = Column(DateTime, nullable=False)


class RunLog(Base):
    __tablename__ = "run_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String, nullable=False)    # daily / weekly
    status = Column(String, nullable=False)      # started / completed / failed
    regime_state = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False)


def init_db():
    Base.metadata.create_all(engine)


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Portfolio ---

def upsert_portfolio(ticker: str, shares: float, cost_basis: float = None,
                     sector: str = None, sector_avg_yield: float = None):
    with SessionLocal() as db:
        existing = db.get(Portfolio, ticker)
        if existing:
            existing.shares = shares
            if cost_basis is not None:
                existing.cost_basis = cost_basis
            if sector is not None:
                existing.sector = sector
            if sector_avg_yield is not None:
                existing.sector_avg_yield = sector_avg_yield
        else:
            db.add(Portfolio(
                ticker=ticker, shares=shares, cost_basis=cost_basis,
                sector=sector, sector_avg_yield=sector_avg_yield
            ))
        db.commit()


def get_portfolio(db: Session = None) -> list[Portfolio]:
    close = db is None
    db = db or SessionLocal()
    try:
        return db.query(Portfolio).all()
    finally:
        if close:
            db.close()


# --- Market Data ---

def insert_market_data(ticker: str, price: float, timestamp: datetime = None):
    ts = timestamp or now()
    with SessionLocal() as db:
        existing = db.query(MarketData).filter_by(ticker=ticker, timestamp=ts).first()
        if not existing:
            db.add(MarketData(ticker=ticker, price=price, timestamp=ts))
            db.commit()


def get_market_data(ticker: str, limit: int = 90) -> list[MarketData]:
    with SessionLocal() as db:
        return (db.query(MarketData)
                .filter(MarketData.ticker == ticker)
                .order_by(MarketData.timestamp.desc())
                .limit(limit)
                .all())


# --- Financial Data ---

def insert_financial_data(ticker: str, eps: float, dividend_per_share: float,
                          market_cap: float, dividend_history: str):
    with SessionLocal() as db:
        db.add(FinancialData(
            ticker=ticker, eps=eps, dividend_per_share=dividend_per_share,
            market_cap=market_cap, dividend_history=dividend_history,
            timestamp=now()
        ))
        db.commit()


def get_latest_financial(ticker: str) -> FinancialData | None:
    with SessionLocal() as db:
        return (db.query(FinancialData)
                .filter(FinancialData.ticker == ticker)
                .order_by(FinancialData.timestamp.desc())
                .first())


# --- Macro Data ---

def insert_macro_data(indicator: str, value: float, timestamp: datetime = None):
    ts = timestamp or now()
    with SessionLocal() as db:
        existing = db.query(MacroData).filter_by(indicator=indicator, timestamp=ts).first()
        if not existing:
            db.add(MacroData(indicator=indicator, value=value, timestamp=ts))
            db.commit()


def get_macro_series(indicator: str, limit: int = 200) -> list[MacroData]:
    with SessionLocal() as db:
        return (db.query(MacroData)
                .filter(MacroData.indicator == indicator)
                .order_by(MacroData.timestamp.desc())
                .limit(limit)
                .all())


def get_latest_macro(indicator: str) -> MacroData | None:
    series = get_macro_series(indicator, limit=1)
    return series[0] if series else None


# --- Alerts ---

def create_alert(type: str, severity: str, message: str, asset: str = None,
                 risk_score: int = None) -> Alert:
    with SessionLocal() as db:
        alert = Alert(
            type=type, severity=severity, asset=asset,
            message=message, risk_score=risk_score, timestamp=now()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert


def suppress_alert(alert_id: int, suppressed_until: datetime):
    with SessionLocal() as db:
        alert = db.get(Alert, alert_id)
        if alert:
            alert.suppressed = True
            alert.suppressed_until = suppressed_until
            db.commit()


def update_alert_explanation(alert_id: int, explanation: str, needs_review: bool = False):
    with SessionLocal() as db:
        alert = db.get(Alert, alert_id)
        if alert:
            alert.explanation = explanation
            alert.needs_review = needs_review
            db.commit()


def get_recent_alert(type: str, asset: str, within_hours: int = 24) -> Alert | None:
    from datetime import timedelta
    cutoff = now() - timedelta(hours=within_hours)
    with SessionLocal() as db:
        return (db.query(Alert)
                .filter(
                    Alert.type == type,
                    Alert.asset == asset,
                    Alert.timestamp >= cutoff,
                    Alert.suppressed == False
                )
                .order_by(Alert.timestamp.desc())
                .first())


def get_active_alerts(limit: int = 50) -> list[Alert]:
    with SessionLocal() as db:
        return (db.query(Alert)
                .filter(Alert.suppressed == False)
                .order_by(Alert.timestamp.desc())
                .limit(limit)
                .all())


# --- Actions ---

def create_action(alert_id: int, action_type: str, description: str,
                  suggested_allocation_change: str = None,
                  direction: str = None) -> Action:
    with SessionLocal() as db:
        action = Action(
            alert_id=alert_id, action_type=action_type, description=description,
            suggested_allocation_change=suggested_allocation_change,
            direction=direction, timestamp=now()
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action


def get_actions_for_alert(alert_id: int) -> list[Action]:
    with SessionLocal() as db:
        return db.query(Action).filter(Action.alert_id == alert_id).all()


# --- Run Log ---

def log_run(run_type: str, status: str, regime_state: str = None,
            risk_score: int = None, error: str = None):
    with SessionLocal() as db:
        db.add(RunLog(
            run_type=run_type, status=status, regime_state=regime_state,
            risk_score=risk_score, error=error, timestamp=now()
        ))
        db.commit()


# --- Severity ordering ---

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def severity_increased(old: str, new: str) -> bool:
    return SEVERITY_ORDER.get(new, 0) > SEVERITY_ORDER.get(old, 0)


if __name__ == "__main__":
    init_db()
    print("Database initialised.")

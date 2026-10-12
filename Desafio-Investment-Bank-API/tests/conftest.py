import os
os.environ["DATABASE_URL"] = "sqlite:///./test_qi.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.models import *
from src.connectors.market_data import MarketDataConnector
from app import app


@pytest.fixture(autouse=True)
def fake_market(monkeypatch):
    data = {
        "quoted_at": "2026-10-11T12:00:00+00:00",
        "fx": {
            "USD": {"buy_rate": "5.20", "sell_rate": "5.25"},
            "EUR": {"buy_rate": "6.05", "sell_rate": "6.12"},
            "JPY": {"buy_rate": "0.0340", "sell_rate": "0.0345"},
        },
        "cdi": "0.1490",
        "selic": "0.1500",
        "ir": "0.1500",
        "iof": "0.0038",
    }
    monkeypatch.setattr(MarketDataConnector, "market_data", lambda self: data)
    monkeypatch.setattr(MarketDataConnector, "fx_rate", lambda self, code: {"currency_code": code, **data["fx"][code], "quoted_at": data["quoted_at"]})
    monkeypatch.setattr(MarketDataConnector, "index_rate", lambda self, code: {"index_code": code, "rate": data[code.lower()]})


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    session.add_all([
        ClientCategory(code="PF", min_investment=2000),
        ClientCategory(code="PJ", min_investment=5000),
        AccountStatus(code="pending"), AccountStatus(code="open"),
        AccountStatus(code="blocked"), AccountStatus(code="closed"),
        Currency(code="USD", name="Dólar americano"),
        Currency(code="EUR", name="Euro"),
        Currency(code="JPY", name="Iene japonês"),
    ])
    session.flush()
    session.add_all([
        InvestmentFund(currency_code="USD", name="Investimento em Dólar", risk_level="moderate"),
        InvestmentFund(currency_code="EUR", name="Investimento em Euro", risk_level="moderate"),
        InvestmentFund(currency_code="JPY", name="Investimento em Iene", risk_level="moderate"),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    def override():
        yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

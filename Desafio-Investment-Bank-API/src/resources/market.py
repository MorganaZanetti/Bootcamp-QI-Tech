from decimal import Decimal
from fastapi import APIRouter, HTTPException
from src.connectors.market_data import MarketDataConnector

router = APIRouter(prefix="/v1", tags=["Mercado"])


@router.get("/market-data")
def market_data():
    try:
        return MarketDataConnector().market_data()
    except Exception:
        raise HTTPException(503, "Não foi possível consultar a API de dados de mercado.")


@router.get("/fx-rates/{currency_code}")
def fx_rates(currency_code: str):
    code = currency_code.upper()
    if code not in ("USD", "EUR", "JPY"):
        raise HTTPException(404, "Moeda não disponível para o projeto.")
    try:
        return MarketDataConnector().fx_rate(code)
    except Exception:
        raise HTTPException(503, "Não foi possível consultar a cotação.")


@router.get("/index-rates/{index_code}")
def index_rates(index_code: str):
    code = index_code.upper()
    if code not in ("CDI", "SELIC", "IR", "IOF"):
        raise HTTPException(404, "Taxa não disponível.")
    try:
        return MarketDataConnector().index_rate(code)
    except Exception:
        raise HTTPException(503, "Não foi possível consultar a taxa.")

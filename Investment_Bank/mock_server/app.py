from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Investment Bank - Mock Market API")

# Uma única API mock fornece todos os dados externos usados pelo projeto.
FX = {
    "USD": {"buy_rate": "5.20", "sell_rate": "5.25"},
    "EUR": {"buy_rate": "6.05", "sell_rate": "6.12"},
    "JPY": {"buy_rate": "0.0340", "sell_rate": "0.0345"},
}

MARKET = {
    "cdi": "0.1490",       # taxa anual de referência para a simulação
    "selic": "0.1500",     # taxa anual de referência para a simulação
    "ir": "0.1500",        # alíquota simplificada para o projeto
    "iof": "0.0038",       # alíquota simplificada para o projeto
}


@app.get("/market-data")
def market_data():
    return {
        "quoted_at": datetime.now(timezone.utc).isoformat(),
        "fx": FX,
        **MARKET,
    }


@app.get("/fx/{currency_code}")
def fx(currency_code: str):
    code = currency_code.upper()
    if code not in FX:
        raise HTTPException(404, "Moeda não encontrada.")
    return {
        "currency_code": code,
        **FX[code],
        "quoted_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/indices/{index_code}")
def index(index_code: str):
    code = index_code.lower()
    if code not in MARKET:
        raise HTTPException(404, "Índice/taxa não encontrado.")
    return {
        "index_code": code.upper(),
        "rate": MARKET[code],
        "date": datetime.now(timezone.utc).date().isoformat(),
    }

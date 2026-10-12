from fastapi import FastAPI
from src.resources.auth import router as auth_router
from src.resources.accounts import router as accounts_router
from src.resources.transactions import router as transactions_router
from src.resources.investments import router as investments_router
from src.resources.market import router as market_router
from src.resources.manager import router as manager_router

app = FastAPI(title="INVESTMENT BANK API", version="1.0.0")
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(investments_router)
app.include_router(market_router)
app.include_router(manager_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

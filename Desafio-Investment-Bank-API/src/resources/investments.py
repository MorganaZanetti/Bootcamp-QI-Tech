from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.resources.dependencies import current_client
from src.schema.investments import InvestmentRequest, SimulationRequest
from src.controllers.investment import InvestmentController

router = APIRouter(prefix="/v1/investments", tags=["Investimentos"])


@router.get("/metrics")
def metrics(amount_brl: Decimal | None = Query(default=None, gt=0), client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        return InvestmentController(db).metrics(client, amount_brl)
    except ValueError as error:
        raise HTTPException(503, str(error))


@router.post("/applications", status_code=201)
def apply(data: InvestmentRequest, checking_account_key: str = Query(...), investment_account_key: str = Query(...), client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        order = InvestmentController(db).apply(client, checking_account_key, investment_account_key, data.fund_key, data.amount_brl)
        return {"order_id": order.id, "message": "Aplicação realizada com sucesso."}
    except ValueError as error:
        db.rollback()
        raise HTTPException(400, str(error))


@router.get("/positions/{investment_account_key}")
def positions(investment_account_key: str, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        return InvestmentController(db).positions(client, investment_account_key)
    except ValueError as error:
        raise HTTPException(400, str(error))


@router.get("/statement/{investment_account_key}")
def investment_statement(investment_account_key: str, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        return InvestmentController(db).statement(client, investment_account_key)
    except ValueError as error:
        raise HTTPException(400, str(error))


@router.post("/simulation/{investment_account_key}")
def simulation(investment_account_key: str, data: SimulationRequest, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        return InvestmentController(db).simulate(client, investment_account_key, data.target_brl)
    except ValueError as error:
        raise HTTPException(400, str(error))

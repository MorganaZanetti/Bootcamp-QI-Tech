import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.controllers.manager import ManagerController

router = APIRouter(prefix="/v1/manager", tags=["Gerente"])


def validate_manager_key(x_manager_key: str = Header(...)):
    expected_key = os.getenv("MANAGER_KEY", "manager123")
    if x_manager_key != expected_key:
        raise HTTPException(401, "Chave de gerente inválida.")
    return x_manager_key


@router.get("/investment-accounts/pending")
def pending_investment_accounts(manager_key: str = Depends(validate_manager_key), db: Session = Depends(get_db)):
    accounts = ManagerController(db).pending_investment_accounts()
    return [
        {"account_number": account.account_number, "client_id": account.client_id, "status": "pending"}
        for account in accounts
    ]


@router.post("/investment-accounts/{account_key}/approve")
def approve_investment_account(account_key: str, manager_key: str = Depends(validate_manager_key), db: Session = Depends(get_db)):
    try:
        account, status = ManagerController(db).decide_investment_account(account_key, True, manager_key)
        return {"account_number": account.account_number, "status": status, "message": "Conta de investimento aprovada com sucesso."}
    except ValueError as error:
        db.rollback()
        raise HTTPException(409, str(error))


@router.post("/investment-accounts/{account_key}/reject")
def reject_investment_account(account_key: str, manager_key: str = Depends(validate_manager_key), db: Session = Depends(get_db)):
    try:
        account, status = ManagerController(db).decide_investment_account(account_key, False, manager_key)
        return {"account_number": account.account_number, "status": status, "message": "Solicitação de conta de investimento rejeitada."}
    except ValueError as error:
        db.rollback()
        raise HTTPException(409, str(error))

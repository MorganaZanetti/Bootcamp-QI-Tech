from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.resources.dependencies import current_client
from src.controllers.current_account import CurrentAccountController
from src.repositories.accounts import AccountRepository

router = APIRouter(prefix="/v1/accounts", tags=["Contas"])


@router.post("/investment", status_code=201)
def request_investment_account(client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        account = CurrentAccountController(db).request_investment_account(client)
        return {
            "account_number": account.account_number,
            "status": "pending",
            "account_type": account.account_type,
            "message": "Solicitação de conta de investimento enviada para aprovação do gerente.",
        }
    except ValueError as error:
        db.rollback()
        raise HTTPException(409, str(error))


@router.get("")
def list_accounts(client=Depends(current_client), db: Session = Depends(get_db)):
    repo = AccountRepository(db)
    accounts = CurrentAccountController(db).list(client)
    return [
        {
            "agency": account.agency,
            "account_number": account.account_number,
            "type": account.account_type,
            "status": repo.status_by_id(account.status_id).code,
            "balance": account.balance,
        }
        for account in accounts
    ]


@router.get("/{account_number}/statement")
def checking_statement(account_number: str, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        account, entries = CurrentAccountController(db).statement(client, account_number)
        labels = {
            "deposit": "Depósito",
            "transfer_out": "Transferência enviada",
            "transfer_in": "Transferência recebida",
            "pix_out": "PIX enviado",
            "pix_in": "PIX recebido",
            "investment_out": "Aplicação em investimento",
            "investment_in": "Crédito de investimento",
            "transaction": "Movimentação",
        }
        return {
            "agency": account.agency,
            "account_number": account.account_number,
            "balance": account.balance,
            "entries": [
                {
                    "type": entry.entry_type,
                    "description": labels.get(entry.entry_type, "Movimentação"),
                    "amount": entry.amount,
                    "balance_after": entry.balance_after,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ],
        }
    except ValueError as error:
        raise HTTPException(404, str(error))

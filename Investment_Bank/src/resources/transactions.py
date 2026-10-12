from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.resources.dependencies import current_client
from src.schema.transactions import DepositRequest, TransferRequest, PixRequest
from src.controllers.transaction import TransactionController
from src.validators import only_digits

router = APIRouter(prefix="/v1/accounts", tags=["Transações"])


@router.post("/{account_key}/deposits", status_code=201)
def deposit(account_key: str, data: DepositRequest, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        account = TransactionController(db).deposit(client, account_key, data.amount)
        return {"message": "Depósito realizado com sucesso.", "balance": account.balance}
    except ValueError as error:
        db.rollback()
        raise HTTPException(400, str(error))


@router.post("/{account_key}/transfers", status_code=201)
def transfer(account_key: str, data: TransferRequest, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        account = TransactionController(db).transfer(client, account_key, data.destination_account_key, data.amount)
        return {"message": "Transferência realizada com sucesso.", "balance": account.balance}
    except ValueError as error:
        db.rollback()
        raise HTTPException(400, str(error))


@router.post("/{account_key}/pix", status_code=201)
def pix(account_key: str, data: PixRequest, client=Depends(current_client), db: Session = Depends(get_db)):
    try:
        account = TransactionController(db).pix(client, account_key, only_digits(data.destination_document), data.amount)
        return {"message": "PIX realizado com sucesso.", "balance": account.balance}
    except ValueError as error:
        db.rollback()
        raise HTTPException(400, str(error))

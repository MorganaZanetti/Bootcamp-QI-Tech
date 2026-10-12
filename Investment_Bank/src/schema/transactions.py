from decimal import Decimal
from pydantic import BaseModel, Field


class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class TransferRequest(BaseModel):
    destination_account_key: str
    amount: Decimal = Field(gt=0)


class PixRequest(BaseModel):
    destination_document: str
    amount: Decimal = Field(gt=0)

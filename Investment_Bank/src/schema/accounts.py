from decimal import Decimal
from pydantic import BaseModel, Field
class AccountCreate(BaseModel): account_type: str=Field(pattern="^(checking|investment)$")
class AccountResponse(BaseModel): account_key: str; account_type: str; status: str; agency: str; account_number: str; balance: Decimal

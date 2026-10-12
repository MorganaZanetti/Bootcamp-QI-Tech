from decimal import Decimal
from pydantic import BaseModel, Field


class InvestmentRequest(BaseModel):
    fund_key: str
    amount_brl: Decimal = Field(gt=0)


class RedemptionRequest(BaseModel):
    fund_key: str
    amount_fx: Decimal = Field(gt=0)


class SimulationRequest(BaseModel):
    target_brl: Decimal = Field(gt=0)
    monthly_contribution_brl: Decimal = Field(default=Decimal("0"), ge=0)

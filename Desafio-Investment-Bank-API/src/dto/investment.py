from dataclasses import dataclass
from decimal import Decimal
@dataclass(slots=True)
class InvestmentAnalysisDTO:
    invested_brl: Decimal; current_brl: Decimal; return_brl_percent: Decimal; current_fx: Decimal; current_reference_value: Decimal; cdi_comparison_percent: Decimal

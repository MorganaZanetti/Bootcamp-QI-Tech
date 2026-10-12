from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
@dataclass(slots=True)
class FxRateDTO:
    currency_code: str; buy_rate: Decimal; sell_rate: Decimal; quoted_at: datetime; is_stale: bool=False

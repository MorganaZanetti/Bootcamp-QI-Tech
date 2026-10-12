from sqlalchemy import select
from src.repositories.base import BaseRepository
from src.models import FxRate, Currency, CdiRate
class MarketRepository(BaseRepository):
    def latest_fx(self,code): return self.db.scalar(select(FxRate).where(FxRate.currency_code==code).order_by(FxRate.quoted_at.desc()).limit(1))
    def fx_history(self,code): return list(self.db.scalars(select(FxRate).where(FxRate.currency_code==code).order_by(FxRate.quoted_at.desc())))

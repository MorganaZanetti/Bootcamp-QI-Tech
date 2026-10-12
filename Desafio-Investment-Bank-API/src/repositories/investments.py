from sqlalchemy import select
from src.repositories.base import BaseRepository
from src.models import InvestmentFund, Position, InvestOrder


class InvestmentRepository(BaseRepository):
    def fund_by_key(self, key):
        # Mantido para compatibilidade com a base; aceita ID numérico ou código da moeda.
        try:
            fund_id = int(key)
            return self.db.get(InvestmentFund, fund_id)
        except (ValueError, TypeError):
            return self.db.scalar(select(InvestmentFund).where(InvestmentFund.currency_code == str(key).upper()))

    def fund_by_id(self, fund_id):
        return self.db.get(InvestmentFund, fund_id)

    def fund_by_currency(self, currency_code):
        return self.db.scalar(select(InvestmentFund).where(InvestmentFund.currency_code == currency_code.upper()))

    def funds(self):
        return list(self.db.scalars(select(InvestmentFund).order_by(InvestmentFund.id)))

    def position(self, account_id, fund_id, lock=False):
        stmt = select(Position).where(Position.account_id == account_id, Position.fund_id == fund_id)
        if lock:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def positions(self, account_id):
        return list(self.db.scalars(select(Position).where(Position.account_id == account_id)))

    def orders(self, account_id):
        return list(self.db.scalars(select(InvestOrder).where(InvestOrder.investment_account_id == account_id).order_by(InvestOrder.created_at.desc())))

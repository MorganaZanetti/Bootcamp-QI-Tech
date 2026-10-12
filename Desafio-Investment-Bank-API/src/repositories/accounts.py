from sqlalchemy import select
from src.repositories.base import BaseRepository
from src.models import Account, AccountStatus, Entry


class AccountRepository(BaseRepository):
    def status(self, code):
        return self.db.scalar(select(AccountStatus).where(AccountStatus.code == code))

    def status_by_id(self, status_id):
        return self.db.scalar(select(AccountStatus).where(AccountStatus.id == status_id))

    def by_key(self, key, lock=False):
        # Nome mantido da base. Externamente usamos o número da conta, não UUID.
        stmt = select(Account).where(Account.account_number == str(key))
        if lock:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def by_number(self, account_number):
        return self.db.scalar(select(Account).where(Account.account_number == str(account_number)))

    def client_accounts(self, client_id):
        return list(self.db.scalars(select(Account).where(Account.client_id == client_id)))

    def investment_accounts_by_status(self, status_id):
        return list(self.db.scalars(select(Account).where(Account.account_type == "investment", Account.status_id == status_id)))

    def entries(self, account_id):
        return list(self.db.scalars(select(Entry).where(Entry.account_id == account_id).order_by(Entry.created_at.desc())))

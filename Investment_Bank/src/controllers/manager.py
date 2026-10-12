from sqlalchemy import select
from src.models import AccountStatusHistory, Manager
from src.repositories.accounts import AccountRepository


class ManagerController:
    def __init__(self, db):
        self.db = db
        self.accounts = AccountRepository(db)

    def pending_investment_accounts(self):
        pending = self.accounts.status("pending")
        return self.accounts.investment_accounts_by_status(pending.id)

    def _manager(self, manager_key):
        manager = self.db.scalar(select(Manager).where(Manager.manager_key == manager_key))
        if manager:
            return manager
        # Mantém os testes locais/SQLite funcionais; no PostgreSQL o gerente já é seedado no database.sql.
        manager = Manager(manager_key=manager_key, name="Gerente Principal")
        self.db.add(manager)
        self.db.flush()
        return manager

    def decide_investment_account(self, account_key, approve, manager_key):
        account = self.accounts.by_key(account_key, lock=True)
        if not account or account.account_type != "investment":
            raise ValueError("Conta de investimento não encontrada.")
        current_status = self.accounts.status_by_id(account.status_id)
        if current_status.code != "pending":
            raise ValueError("A solicitação já foi analisada.")
        manager = self._manager(manager_key)
        new_status = self.accounts.status("open" if approve else "closed")
        account.status_id = new_status.id
        self.db.add(AccountStatusHistory(account_id=account.id, status_id=new_status.id, manager_id=manager.id))
        self.db.commit()
        return account, new_status.code

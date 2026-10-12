import random
from decimal import Decimal
from src.models import Account, AccountStatusHistory
from src.repositories.accounts import AccountRepository


class CurrentAccountController:
    def __init__(self, db):
        self.db = db
        self.repo = AccountRepository(db)

    def request_investment_account(self, client):
        for account in self.repo.client_accounts(client.id):
            if account.account_type == "investment":
                status = self.repo.status_by_id(account.status_id)
                if status and status.code in ("pending", "open"):
                    raise ValueError("Já existe uma conta de investimento pendente ou aberta.")
        pending_status = self.repo.status("pending")
        account = Account(
            client_id=client.id,
            status_id=pending_status.id,
            account_type="investment",
            agency="0001",
            account_number=str(random.randint(100000, 999999)),
            balance=Decimal("0"),
        )
        self.db.add(account)
        self.db.flush()
        self.db.add(AccountStatusHistory(account_id=account.id, status_id=pending_status.id, manager_id=None))
        self.db.commit()
        self.db.refresh(account)
        return account

    def list(self, client):
        return self.repo.client_accounts(client.id)

    def statement(self, client, account_number):
        account = self.repo.by_number(account_number)
        if not account or account.client_id != client.id or account.account_type != "checking":
            raise ValueError("Conta corrente não encontrada.")
        return account, self.repo.entries(account.id)

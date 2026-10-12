from decimal import Decimal
from src.models import Entry, Event
from src.repositories.accounts import AccountRepository
from src.repositories.clients import ClientRepository


class TransactionController:
    def __init__(self, db):
        self.db = db
        self.repo = AccountRepository(db)
        self.clients = ClientRepository(db)

    def deposit(self, client, account_key, amount):
        amount = Decimal(amount)
        account = self.repo.by_key(account_key, lock=True)
        if not account or account.client_id != client.id or account.account_type != "checking":
            raise ValueError("Conta corrente não encontrada.")
        account.balance += amount
        self.db.add(Entry(account_id=account.id, entry_type="deposit", amount=amount, balance_after=account.balance))
        self.db.add(Event(account_id=account.id, detail={"type": "deposit"}))
        self.db.commit()
        return account

    def transfer(self, client, source_key, destination_key, amount, movement="transfer"):
        amount = Decimal(amount)
        source = self.repo.by_key(source_key, lock=True)
        destination = self.repo.by_key(destination_key, lock=True)
        if not source or source.client_id != client.id or source.account_type != "checking":
            raise ValueError("Conta de origem não encontrada.")
        if not destination:
            raise ValueError("Conta de destino não encontrada.")
        if source.id == destination.id:
            raise ValueError("As contas de origem e destino devem ser diferentes.")
        if source.balance < amount:
            raise ValueError("Saldo insuficiente.")
        source.balance -= amount
        destination.balance += amount
        self.db.add_all([
            Entry(account_id=source.id, entry_type=f"{movement}_out", amount=-amount, balance_after=source.balance),
            Entry(account_id=destination.id, entry_type=f"{movement}_in", amount=amount, balance_after=destination.balance),
            Event(account_id=source.id, detail={"type": "transfer_out"}),
            Event(account_id=destination.id, detail={"type": "transfer_in"}),
        ])
        self.db.commit()
        return source

    def pix(self, client, source_key, destination_document, amount):
        destination_client = self.clients.by_document(destination_document)
        if not destination_client:
            raise ValueError("Destinatário do PIX não encontrado.")
        destination_accounts = [
            account for account in self.repo.client_accounts(destination_client.id)
            if account.account_type == "checking"
        ]
        if not destination_accounts:
            raise ValueError("Conta corrente do destinatário não encontrada.")
        return self.transfer(client, source_key, destination_accounts[0].account_number, amount, movement="pix")

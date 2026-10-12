import random
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from src.models import Client, NaturalPerson, LegalEntity, Account, AccountStatusHistory
from src.repositories.clients import ClientRepository
from src.repositories.accounts import AccountRepository
from src.security import hash_password, verify_password, create_token
from src.validators import only_digits, is_valid_cpf


class AuthenticationController:
    def __init__(self, db):
        self.db = db
        self.repo = ClientRepository(db)
        self.accounts = AccountRepository(db)

    def _account_number(self):
        while True:
            number = str(random.randint(100000, 999999))
            if not self.accounts.by_number(number):
                return number

    def _create_open_checking_account(self, client):
        open_status = self.accounts.status("open")
        if not open_status:
            raise ValueError("Status 'open' não encontrado.")
        account = Account(client_id=client.id, status_id=open_status.id, account_type="checking", agency="0001", account_number=self._account_number(), balance=Decimal("0.00"))
        self.db.add(account)
        self.db.flush()
        self.db.add(AccountStatusHistory(account_id=account.id, status_id=open_status.id, manager_id=None))
        return account

    def register_natural_person(self, data):
        cpf = only_digits(data.cpf)
        if not is_valid_cpf(cpf):
            raise ValueError("CPF inválido.")
        category = self.repo.category("PF")
        if not category:
            raise ValueError("Categoria PF não encontrada.")
        try:
            client = Client(category_id=category.id, email=data.email, password_hash=hash_password(data.password))
            self.db.add(client)
            self.db.flush()
            self.db.add(NaturalPerson(client_id=client.id, cpf=cpf, full_name=data.full_name, birth_date=data.birth_date))
            self._create_open_checking_account(client)
            self.db.commit()
            self.db.refresh(client)
            return client
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Cliente já cadastrado.")
        except Exception:
            self.db.rollback()
            raise

    def register_legal_entity(self, data):
        cnpj = only_digits(data.cnpj)
        if len(cnpj) != 14:
            raise ValueError("CNPJ inválido.")
        category = self.repo.category("PJ")
        if not category:
            raise ValueError("Categoria PJ não encontrada.")
        try:
            client = Client(category_id=category.id, email=data.email, password_hash=hash_password(data.password))
            self.db.add(client)
            self.db.flush()
            self.db.add(LegalEntity(client_id=client.id, cnpj=cnpj, legal_name=data.legal_name))
            self._create_open_checking_account(client)
            self.db.commit()
            self.db.refresh(client)
            return client
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Cliente já cadastrado.")
        except Exception:
            self.db.rollback()
            raise

    def login(self, document, password):
        client = self.repo.by_document(only_digits(document))
        if not client or not verify_password(password, client.password_hash):
            raise ValueError("Documento ou senha inválidos.")
        return create_token(str(client.id))

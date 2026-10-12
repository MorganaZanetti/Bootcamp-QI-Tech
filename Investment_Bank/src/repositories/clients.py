from sqlalchemy import select
from src.repositories.base import BaseRepository
from src.models import Client, ClientCategory, NaturalPerson, LegalEntity


class ClientRepository(BaseRepository):
    def category(self, code):
        return self.db.scalar(select(ClientCategory).where(ClientCategory.code == code))

    def by_key(self, key):
        # Nome mantido por compatibilidade com a base; a autenticação usa ID numérico.
        try:
            client_id = int(key)
        except (ValueError, TypeError):
            return None
        return self.db.get(Client, client_id)

    def by_document(self, document):
        np = self.db.scalar(select(NaturalPerson).where(NaturalPerson.cpf == document))
        if np:
            return self.db.get(Client, np.client_id)
        le = self.db.scalar(select(LegalEntity).where(LegalEntity.cnpj == document))
        return self.db.get(Client, le.client_id) if le else None

    def category_for_client(self, client):
        return self.db.get(ClientCategory, client.category_id)

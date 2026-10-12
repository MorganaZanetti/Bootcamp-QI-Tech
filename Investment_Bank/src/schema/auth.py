from datetime import date
from pydantic import BaseModel, Field
class NaturalPersonRegister(BaseModel):
    email: str; password: str=Field(min_length=8); cpf: str; full_name: str; birth_date: date
class LegalEntityRegister(BaseModel):
    email: str; password: str=Field(min_length=8); cnpj: str; legal_name: str
class LoginRequest(BaseModel):
    document: str; password: str

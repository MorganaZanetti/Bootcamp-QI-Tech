from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.schema.auth import NaturalPersonRegister, LegalEntityRegister, LoginRequest
from src.controllers.authentication import AuthenticationController

router = APIRouter(prefix="/v1/auth", tags=["Autenticação"])


@router.post("/register/natural-person", status_code=201)
def register_natural_person(data: NaturalPersonRegister, db: Session = Depends(get_db)):
    try:
        AuthenticationController(db).register_natural_person(data)
        return {"message": "Cliente cadastrado com sucesso. Conta corrente criada automaticamente."}
    except ValueError as error:
        raise HTTPException(400, str(error))


@router.post("/register/legal-entity", status_code=201)
def register_legal_entity(data: LegalEntityRegister, db: Session = Depends(get_db)):
    try:
        AuthenticationController(db).register_legal_entity(data)
        return {"message": "Cliente cadastrado com sucesso. Conta corrente criada automaticamente."}
    except ValueError as error:
        raise HTTPException(400, str(error))


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        return {
            "access_token": AuthenticationController(db).login(data.document, data.password),
            "token_type": "bearer",
        }
    except ValueError as error:
        raise HTTPException(401, str(error))

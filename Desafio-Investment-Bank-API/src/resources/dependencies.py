from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.security import decode_token
from src.repositories.clients import ClientRepository

def current_client(authorization: str=Header(...), db: Session=Depends(get_db)):
    try:
        scheme,token=authorization.split(" ",1)
        if scheme.lower()!="bearer": raise ValueError
        key=decode_token(token); client=ClientRepository(db).by_key(key)
        if not client: raise ValueError
        return client
    except Exception: raise HTTPException(401,"Token inválido ou expirado.")

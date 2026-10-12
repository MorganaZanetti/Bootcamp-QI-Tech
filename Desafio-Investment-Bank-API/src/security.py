from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

import jwt
from src.config import settings

_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_token(client_key: str) -> str:
    # O parâmetro foi mantido para preservar a base do projeto.
    # O valor enviado agora é o ID numérico interno, nunca um UUID.
    payload = {"sub": str(client_key), "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])["sub"]

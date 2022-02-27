from datetime import datetime, timezone
from hashlib import sha256


def encode_password(password: str) -> str:
    return sha256(str(password).encode()).hexdigest()


def now() -> datetime:
    return datetime.now(tz=timezone.utc)

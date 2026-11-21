"""비밀번호 저장: PBKDF2-HMAC-SHA512 (schema.md "비밀번호 저장"). 원문은 어디에도 남기지 않는다."""

import base64
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha512"
ITERATIONS = 200_000
SALT_BYTES = 16


def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iterations)


def hash_password(password: str, *, iterations: int = ITERATIONS) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = _derive(password, salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"{ALGORITHM}${iterations}${salt_b64}${digest_b64}"


def verify_password(password: str, stored: str | None) -> bool:
    """저장된 반복 횟수로 다시 계산해 비교한다. 저장 값이 없거나 형식이 깨졌으면 False."""
    if stored is None:
        return False
    try:
        algorithm, iterations_text, salt_b64, digest_b64 = stored.split("$")
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(digest_b64, validate=True)
    except ValueError:  # 개수 불일치 · 숫자 아님 · base64 오류(binascii.Error는 ValueError 하위)
        return False
    if algorithm != ALGORITHM or iterations <= 0:
        return False
    try:
        actual = _derive(password, salt, iterations)
    except UnicodeEncodeError:  # 짝 없는 surrogate 등 UTF-8로 못 바꾸는 입력
        return False
    return hmac.compare_digest(actual, expected)

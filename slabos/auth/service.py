import secrets
import string
import time
import hashlib


def generate_auth_pin(length: int = 4) -> str:
    """Generate a cryptographically secure numeric PIN."""
    if not isinstance(length, int) or length <= 0:
        length = 4
    return "".join(secrets.choice(string.digits) for _ in range(length))


def verify_api_pin(provided_pin: str, expected_pin: str) -> bool:
    """Validate a PIN using constant-time comparison."""
    if not isinstance(provided_pin, str) or not isinstance(expected_pin, str):
        return False
    return secrets.compare_digest(provided_pin.strip(), expected_pin.strip())


def create_share_token(
    filepath: str,
    secret_key: str,
    expiry_seconds: int = 86400,
) -> str:
    """Create a temporary file-share token."""
    if not isinstance(filepath, str) or not isinstance(secret_key, str):
        return "ERROR:INVALID_INPUT"

    if not isinstance(expiry_seconds, int) or expiry_seconds <= 0:
        expiry_seconds = 86400

    expiry = int(time.time()) + expiry_seconds
    raw_payload = f"{filepath}:{secret_key}:{expiry}"
    token_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:16]

    return f"{expiry}:{token_hash}"


def verify_token_access(token: str, active_tokens: dict) -> bool:
    """Validate whether a file-share token is active and unexpired."""
    if not isinstance(token, str) or not isinstance(active_tokens, dict):
        return False

    try:
        expiry_str, _token_hash = token.split(":")
        if int(time.time()) > int(expiry_str):
            return False
        return token in active_tokens
    except ValueError:
        return False

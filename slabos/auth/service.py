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


class AuthService:
    """Coordinates SlabOS master and guest authentication."""

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def authenticate(self, provided_pin: str, session_pin: str) -> tuple[bool, bool]:
        """Return (is_authorized, is_admin)."""
        if not provided_pin:
            return False, False

        if verify_api_pin(provided_pin, session_pin):
            return True, True

        config = self.config_manager.load_or_create()
        guest_pins = config.get("guest_pins", {})

        if provided_pin in guest_pins:
            return True, False

        return False, False

    def create_guest_pin(self) -> str:
        """Create and persist a new guest PIN."""
        config = self.config_manager.load_or_create()
        guest_pins = config.setdefault("guest_pins", {})

        new_guest = generate_auth_pin(4)
        guest_pins[new_guest] = "active"

        self.config_manager.save(config)
        return new_guest
